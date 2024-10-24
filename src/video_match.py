import boto3
from  openai import OpenAI
import json
import os
import pinecone
import pandas as pd
import csv
import ast
import numpy as np

#get openai key
ssm = boto3.client('ssm',region_name='us-east-2')
parameter = ssm.get_parameter(Name='/openai/api_key', WithDecryption=True)

class background():
    def __init__(self):
        self.LPVT_data = pd.read_csv('LPVT_data.csv')
        self.client = OpenAI(api_key=parameter['Parameter']['Value'])


    def run_GPT(self, prompt):
        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an AI assistant with medical knowledge. The student is currently practicing the lumbar puncture procedure. 'LPVT_data' contains the complete operation steps of the lumbar puncture procedure. 'Clip Name' refers to the name of the step clip, for example, P6 represents the sixth major step, and P6-1 represents the second sub-step within the sixth major step (sub-steps are numbered starting from 0, and currently, there is no seventh major step). 'Step Name' refers to the name of the sub-step. 'Duration (second)' is the playback duration of each sub-step video. 'Visual Component' describes the description of the content displayed to the student in the video demonstration.The student will ask questions related to the procedure steps. Answer the student's question and guide them on how to proceed to the next step based on the 'Visual Component. Also provide the 'Clip Name'fro step."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=200
        )
        return response.choices[0].message.content

    def do_conv(self, question):
        prompt = f"LPVT_data:{self.LPVT_data}, user question:{question}"
        answer = self.run_GPT(prompt)
        # self.history.append({"role": "user", "content": question})
        # self.history.append({"role": "AI", "content": answer})
        # if os.path.exists('talk_record.json') and os.path.getsize('talk_record.json') > 0:
        #     with open('talk_record.json', 'r', encoding='utf-8') as f:
        #         try:
        #             existing_data = json.load(f)
        #         except json.JSONDecodeError:
        #             existing_data = {"conversations": []}
        # else:
        #     existing_data = {"conversations": []}
        # existing_data["conversations"].extend(self.history)
        
        # with open('talk_record.json', 'w', encoding='utf-8') as f:
        #     json.dump(existing_data, f, ensure_ascii=False, indent=4)     
        # self.get_sound(answer)
        return answer

if __name__ == "__main__":
    new = background()
    # I just start,what should I do first?
    question = "What should I do after drawing Iodine?"
    answer = new.do_conv(question)
    print(answer)