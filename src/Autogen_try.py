import boto3
from  openai import OpenAI
# from autogen import Agent
import json
import os

#get openai key
ssm = boto3.client('ssm',region_name='us-east-2')
parameter = ssm.get_parameter(Name='/openai/api_key', WithDecryption=True)


class background():
    def __init__(self):
        with open('medical_info.json', 'r', encoding='utf-8') as json_file:
            med_data = json.load(json_file)
        self.medical_info = json.dumps(med_data)
        if os.path.exists('talk_record.json') and os.path.getsize('talk_record.json') > 0:
            with open('talk_record.json', 'r', encoding='utf-8') as json_file:
                talk_data = json.load(json_file)
        else:
            talk_data = {"conversations": []} 
        self.talk_record = json.dumps(talk_data)
        self.client = OpenAI(api_key=parameter['Parameter']['Value'])
        self.history = []

    def handle_message(self, prompt):
        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an AI assistant with medical knowledge, please use the talk_record which stores the previous conversations and medical_info to help answer the user's question."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=100
        )
        return response.choices[0].message.content

    def do_conv(self, question):
        self.history.append({"role": "user", "content": question})
        prompt = f"talk_record:{self.talk_record},  medical_info:{self.medical_info}, user question:{question}"
        answer = self.handle_message(prompt)
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
        return answer

if __name__ == "__main__":
    new = background()
    question = "What is the Lumbar Puncture Patient age"
    answer = new.do_conv(question)
    print(answer)


