import boto3
from  openai import OpenAI
from pathlib import Path
# from autogen import Agent
import json
import os
import pinecone
import pandas as pd
import csv
import ast
import re
import numpy as np

#get openai key
ssm = boto3.client('ssm',region_name='us-east-2')
parameter_openai = ssm.get_parameter(Name='/openai/api_key', WithDecryption=True)
parameter_pinecone = ssm.get_parameter(Name='/pinecone/api_key', WithDecryption=True)

class background():
    def __init__(self):
        with open('LPVT_RAG_Basic_Knowledge.txt', 'r', encoding='utf-8') as txt_file:
            med_data = txt_file.read()
        self.medical_info = med_data

        if os.path.exists('talk_record.json') and os.path.getsize('talk_record.json') > 0:
            with open('talk_record.json', 'r', encoding='utf-8') as json_file:
                talk_data = json.load(json_file)
        else:
            talk_data = {"conversations": []} 
        self.talk_record = talk_data
        # self.talk_record = json.dumps(talk_data)
        
        self.client = OpenAI(api_key=parameter_openai['Parameter']['Value'])
        self.history = []

        # df['ada_embedding'] = df.combined.apply(lambda x: self.get_embedding(x, model='text-embedding-3-small'))
        # df.to_csv('embedded_result.csv', index=False)
        self.pinecone = pinecone.Pinecone(api_key=parameter_pinecone['Parameter']['Value'])
        self.LPVT_data = pd.read_csv('LPVT_data.csv')
        
    def run_GPT(self, prompt):
        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an AI assistant with medical knowledge, please use the talk_record which stores the previous conversations and medical_info which may related to user question to help answer the user's question. If the provided information not relative to question. Do not use it.Just answer the question directly"},
                {"role": "user", "content": prompt}
            ],
            max_tokens=100
        )
        return response.choices[0].message.content

    # Main GPT function
    def run_GPT_video(self, prompt):
        response = self.client.chat.completions.create(
            # "gpt-3.5-turbo"
            # "gpt-4.5-preview"
            # "gpt-4o"
            model="gpt-4o",
            messages=[
                {
                    "role": "system", 
                    "content": (
                        "You are a medical school instructor guiding students who are practicing spinal tap procedures in VR.\n\n"

                        "Your job is to:\n"
                        "1. Gently and professionally answer the student's question.\n"
                        "2. Use data from these sources if available:\n"
                        "   - talk_record: prior student-instructor conversation\n"
                        "   - medical_info: related medical knowledge\n"
                        "   - LPVT_data: step-by-step lumbar puncture procedure\n\n"

                        "For LPVT_data:\n"
                        "- 'Clip Name' = step ID (e.g., P6 = major step 6, P6-1 = substep 1 of step 6)\n"
                        "- 'Step Name' = substep description\n"
                        "- 'Visual Component' = what the student sees in the clip\n"
                        "- 'Duration (second)' = video length\n\n"

                        "Instructions for response:\n"
                        "1.Speak in a warm, encouraging, and competent tone like a supportive instructor.\n"
                        "2.Guide the student on how to proceed, based on 'Visual Component' where applicable.\n"
                        "3.If the answer relates to procedural clips, include clip names in this format:\n"
                        "  [P8-0, blank, P8-1, blank, P8-2]\n"
                        "  (always insert 'blank' between clips)\n"
                        "4.If no video clip is needed, return an empty list []\n\n"

                        "Return a valid JSON object in **this exact format**:\n"
                        "{\n"
                        "  \"Question_answer\": \"Answer to the student question\",\n"
                        "  \"animation_clip\": ['P6', 'blank', 'P6-1']\n"
                        "}\n\n"

                        "Important:\n"
                        "Ensure the JSON syntax uses double quotes, not single quotes.")},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            max_tokens=500,
            temperature=0.6
        )
        return response.choices[0].message.content

    #Get GPT answer with sound
    def get_sound(self, text):
        speech_file_path = Path(__file__).parent / "output.mp3"
        response = self.client.audio.speech.create(
            model="tts-1",
            voice="alloy",
            speed=1.3,
            input=text,
            # instructions="Speak in a cheerful, professional and positive tone.",
        )
        response.stream_to_file(speech_file_path)
        return

    #Get sentence embedding
    def get_embedding(self, text, model="text-embedding-3-small"):
        text = text.replace("\n", " ")
        response = self.client.embeddings.create(input = [text], model=model).data[0].embedding
        return response

    #Get talk embedding file(not in used)
    def get_talk_embedding(self):
        with open('talk_record.json', 'r', encoding='utf-8') as f:
            conversation_data = json.load(f)
        with open('talk_embedd.csv', mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            for message in conversation_data['conversations']:
                embedding = self.get_embedding(message['content'])
                writer.writerow([embedding])
        return

    #Get knowledge embedding file
    def get_knowledge_embedding(self):
        with open('LPVT_RAG_Basic_Knowledge.txt', 'r', encoding='utf-8') as file:
            content = file.read()
        paragraphs = content.split('\n\n')  
        paragraphs = [para.strip() for para in paragraphs if para.strip()]
        existing_data = {"vectors": []}
        i=0
        for line in paragraphs:
            embedding = self.get_embedding(line)
            embedding = list(map(float, embedding))
            existing_data["vectors"].append({"id" : f"vec{i}", 
                                            "values" : embedding, 
                                            "metadata": {"sentence":line}
                                            })
            i=i+1
        with open('medical_embed.json', 'w', encoding='utf-8') as f:
            json.dump(existing_data, f, ensure_ascii=False, indent=4)     
        return

    #Do retrieval by pinecone 
    def retrieval(self, query_text):
        index_name = "medical-doc-index"
        if index_name not in self.pinecone.list_indexes().names():
            self.pinecone.create_index(
                name=index_name, 
                dimension=1536, 
                metric='euclidean',
                spec=pinecone.ServerlessSpec(
                    cloud='aws',
                    region='us-east-1'
                )
            )
        index = self.pinecone.Index(index_name)
        new_content = False
        if new_content:
            self.get_knowledge_embedding()
            with open('medical_embed.json', 'r', encoding='utf-8') as json_file:
                medical_data = json.load(json_file)
                index.upsert(
                    vectors = medical_data["vectors"][0:len(medical_data["vectors"])],
                    namespace= f"medical1"
                )
        query_embed = self.get_embedding(query_text)
        query_embed = list(map(float, query_embed))
        if any(np.isnan(query_embed)) or any(np.isinf(query_embed)):
            print("Query embedding contains NaN or Infinity values. in")
        if len(query_embed) != 1536:
            print(f"Invalid vector length: {len(query_embed)}. Expected length is 1536.")
            return None
        result = index.query(
            namespace="medical1",
            vector=[query_embed], 
            top_k=3,
            include_metadata=True
            )
        return result
    
    #Main function for doing conversition with RAG
    def do_conv_RAG(self, question):
        self.history.append({"role": "user", "content": question})
        retrieval_result = self.retrieval(question)
        retrieval_text = []
        with open('medical_embed.json', 'r', encoding='utf-8') as json_file:
            medical_file = json.load(json_file)
        for i in range(len(retrieval_result['matches'])):
            if i == 0:
                retrieval_text.append(retrieval_result['matches'][0]['metadata']['sentence'])
            elif(retrieval_result['matches'][i]["score"]<1.5):
                retrieval_text.append(retrieval_result['matches'][i]['metadata']['sentence'])
        # print("retrieval_result is")
        # print(retrieval_text)

        # prompt = f"Please use below information, answer student question in a gentle, encouraging, caring tone and in the role of a medical instructor. In medical_info part, they have these content may related to question from student:{retrieval_text}, talk_record:{self.talk_record},LPVT_data:{self.LPVT_data},student question:{question} Make the answers more colloquial and answer questions in a different way than providing information. Please don't use metaphors. Do NOT use any modal or greeting phrases like 'hey', 'hey there', or 'hello' at the beginning of the answer."

        prompt = f"""
            Please answer the student's question in the role of a medical instructor. Speak in a gentle, encouraging, and caring tone.

            Use the following context:
            - medical_info: background medical knowledge related to the student's question : {retrieval_text}
            - talk_record: previous conversation history : {self.talk_record}
            - LPVT_data: lumbar puncture procedural steps : {self.LPVT_data}
            - student_question: {question}

            Your answer should be **colloquial and conversational**, but professional. Avoid just restating medical facts—engage with the student naturally as if in a one-on-one setting. Do **not** use metaphors.  

            Also, **do NOT** start the response with any greeting phrases like "hey", "hey there", or "hello". Start directly with your response.

            Respond clearly, and guide the student step by step when appropriate.
        """
        answer = self.run_GPT_video(prompt)
        # answer = answer.replace("'", '"') 
        # match = re.search(r'\{.*\}', answer)
        # if match:
        #     answer = match.group()
        answer_jason = json.loads(answer)
        self.history.append({"role": "AI", "content": answer_jason})
        if os.path.exists('talk_record.json') and os.path.getsize('talk_record.json') > 0:
            with open('talk_record.json', 'r', encoding='utf-8') as f:
                try:
                    existing_data = json.load(f)
                except json.JSONDecodeError:
                    existing_data = {"conversations": []}
        else:
            existing_data = {"conversations": []}
        existing_data["conversations"].extend(self.history)
        
        with open('talk_record.json', 'w', encoding='utf-8') as f:
            json.dump(existing_data, f, ensure_ascii=False, indent=4)     
        self.get_sound(answer_jason['Question_answer'])
        return answer_jason

    def do_conv_video(self, question):
        prompt = f"LPVT_data:{self.LPVT_data}, user question:{question}"
        answer = self.run_GPT_video(prompt)
        return answer

    #Main function for doing conversition without RAG
    def do_conv(self, question):
        self.history.append({"role": "user", "content": question})
        prompt = f"talk_record:{self.talk_record},  medical_info:{self.medical_info}, user question:{question}"
        answer = self.run_GPT(prompt)
        self.history.append({"role": "AI", "content": answer})
        if os.path.exists('talk_record.json') and os.path.getsize('talk_record.json') > 0:
            with open('talk_record.json', 'r', encoding='utf-8') as f:
                try:
                    existing_data = json.load(f)
                except json.JSONDecodeError:
                    existing_data = {"conversations": []}
        else:
            existing_data = {"conversations": []}
        existing_data["conversations"].extend(self.history)
        
        with open('talk_record.json', 'w', encoding='utf-8') as f:
            json.dump(existing_data, f, ensure_ascii=False, indent=4)     
        self.get_sound(answer)
        return answer

if __name__ == "__main__":
    new = background()
    question = "What should I do for Identifying Landmarks?"
    answer = new.do_conv_RAG(question)
    print(answer)


