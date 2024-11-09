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


    def run_GPT_video(self, prompt):
        response = self.client.chat.completions.create(
            # "gpt-3.5-turbo"
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an AI assistant with medical knowledge. The student is currently practicing the lumbar puncture procedure. 'LPVT_data' contains the complete operation steps of the lumbar puncture procedure. 'Clip Name' refers to the name of the step clip, for example, P6 represents the sixth major step, and P6-1 represents the second sub-step within the sixth major step (sub-steps are numbered starting from 0, and currently, there is no seventh major step). 'Step Name' refers to the name of the sub-step. 'Duration (second)' is the playback duration of each sub-step video. 'Visual Component' describes the description of the content displayed to the student in the video demonstration.The student will ask questions related to the procedure steps. First of all, answer the student's question and guide them on how to proceed to the next step based on the 'Visual Component'. Secondly,you should provide the 'Clip Name' for step and return the string for how to play the video. For example, the question is 'Are there any step related to insert?', the answer acturally about P8-0,P8-1,P8-2. Then, you should provide like [P8-0,blank,P8-1,blank,P8-2]. At the end, the format of answer which AI assistant provide should be '1.Question answer: ; 2. The string for how to play the video'"},
                {"role": "user", "content": prompt}
            ],
            max_tokens=200
        )
        return response.choices[0].message.content

    def do_conv_video(self, question):
        prompt = f"LPVT_data:{self.LPVT_data}, user question:{question}"
        answer = self.run_GPT_video(prompt)
        return answer

if __name__ == "__main__":
    new = background()
    # I just start,what should I do first?
    # "What should I do after drawing Iodine?"
    question = "I just start,what should I do first?"
    answer = new.do_conv(question)
    print(answer)