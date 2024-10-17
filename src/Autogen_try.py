import boto3
from  openai import OpenAI
# from autogen import Agent
import json
import os
import pinecone
import pandas as pd
import csv
import ast
import numpy as np

#get openai key
ssm = boto3.client('ssm',region_name='us-east-2')
parameter_openai = ssm.get_parameter(Name='/openai/api_key', WithDecryption=True)
parameter_pinecone = ssm.get_parameter(Name='/pinecone/api_key', WithDecryption=True)


class background():
    def __init__(self):
        with open('medical_info.json', 'r', encoding='utf-8') as json_file:
            med_data = json.load(json_file)
        self.medical_info = med_data
        # self.medical_info = json.dumps(med_data)

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
        


    def run_GPT(self, prompt):
        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an AI assistant with medical knowledge, please use the talk_record which stores the previous conversations and medical_info to help answer the user's question."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=100
        )
        return response.choices[0].message.content

    def get_sound(self, text):
        response = self.client.audio.speech.create(
            model="tts-1",
            voice="alloy",
            input=text,
        )
        response.stream_to_file("output.mp3")
        return

    def get_embedding(self, text, model="text-embedding-3-small"):
        text = text.replace("\n", " ")
        response = self.client.embeddings.create(input = [text], model=model).data[0].embedding
        return response

    def get_talk_embedding(self):
        with open('talk_record.json', 'r', encoding='utf-8') as f:
            conversation_data = json.load(f)
        with open('talk_embedd.csv', mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            # writer.writerow(['role', 'content', 'embedding'])
            for message in conversation_data['conversations']:
                embedding = self.get_embedding(message['content'])
                writer.writerow([embedding])
            # writer.writerow([message['role'], message['content'], embedding])
        return

    def get_knowledge_embedding(self):
        df = pd.read_csv('medical_info.csv')
        with open('medical_embedd.csv', mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(['id', 'embedding'])
            for i, line in df.iterrows():
                text = str(line)
                embedding = self.get_embedding(text)
                embedding_str = json.dumps(embedding)
                writer.writerow([i,embedding_str])
        print('get_knowledge_embedding work')
        return 

    def retrieval(self, query_text):
        print('retrieval work')
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
        self.get_knowledge_embedding()
        df = pd.read_csv('medical_embedd.csv')
        for i, row in df.iterrows():
            if pd.isna(row['embedding']):
                continue
            row_list = json.loads(row['embedding'])
            row_list = list(map(float, row_list))
            if any(np.isnan(row_list)) or any(np.isinf(row_list)):
                print("Query embedding contains NaN or Infinity values. in")
                continue
            if len(row_list) != 1536:
                print(f"Invalid vector length: {len(row_list)}. Expected length is 1536.")
                return None
            index.upsert([(str(i), row_list)])
            # index.upsert([(str(i), list(map(float, row['embedding'])))])
        query_embed = self.get_embedding(query_text)
        query_embed = list(map(float, query_embed))
        if any(np.isnan(query_embed)) or any(np.isinf(query_embed)):
            print("Query embedding contains NaN or Infinity values. in")
        if len(query_embed) != 1536:
            print(f"Invalid vector length: {len(query_embed)}. Expected length is 1536.")
            return None
        print(query_embed)
        result = index.query(
            vector=[query_embed], 
            top_k=3,
            include_metadata=True
            )
        return result
    
    def do_conv_RAG(self, question):
        self.history.append({"role": "user", "content": question})
        retrieval_result = self.retrieval(question)
        print("retrieval_result is")
        print(retrieval_result)
        prompt = f"After retrieval, in medical_info part, they have these content related to question from user:{retrieval_result}, talk_record:{self.talk_record},user question:{question}"
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
    question = "hi,what is your name"
    answer = new.do_conv(question)
    print(answer)


