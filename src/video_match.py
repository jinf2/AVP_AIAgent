import boto3
from  openai import OpenAI
import json
import os
import pinecone

#get openai key
ssm = boto3.client('ssm',region_name='us-east-2')
parameter = ssm.get_parameter(Name='/openai/api_key', WithDecryption=True)

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
        
        self.client = OpenAI(api_key=parameter['Parameter']['Value'])
        self.history = []

        # df['ada_embedding'] = df.combined.apply(lambda x: self.get_embedding(x, model='text-embedding-3-small'))
        # df.to_csv('embedded_result.csv', index=False)

    def run_GPT(self, prompt):
        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an AI assistant with medical knowledge. Right now, the students are practicing the lumbar puncture medical procedure. The following will be textual descriptions of the students' procedural steps. Please arrange these texts in the correct professional medical sequence for the procedure."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=100
        )
        return response.choices[0].message.content

    def get_embedding(text, model="text-embedding-3-small"):
        text = text.replace("\n", " ")
        response = self.client.embeddings.create(input = [text], model=model).data[0].embedding
        return response

    def get_talk_embedding():
        with open('talk_record.json', 'r', encoding='utf-8') as f:
            conversation_data = json.load(f)
        with open('embedd.csv', mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(['role', 'content', 'embedding'])
        for message in conversation_data['conversations']:
            embedding = get_embedding(message['content'])
            writer.writerow([message['role'], message['content'], embedding])

    def get_sound(self, text):
        response = self.client.audio.speech.create(
            model="tts-1",
            voice="alloy",
            input=text,
        )
        response.stream_to_file("output.mp3")
        return
    
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