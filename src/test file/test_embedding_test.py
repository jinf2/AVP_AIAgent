import boto3
from  openai import OpenAI
import json
import os
import csv

ssm = boto3.client('ssm',region_name='us-east-2')
parameter = ssm.get_parameter(Name='/openai/api_key', WithDecryption=True)

client = OpenAI(api_key=parameter['Parameter']['Value'])

def get_embedding(text, model="text-embedding-3-small"):
   text = text.replace("\n", " ")
   response = client.embeddings.create(input = [text], model=model).data[0].embedding
   return response

with open('talk_record.json', 'r', encoding='utf-8') as f:
   conversation_data = json.load(f)
with open('embedd.csv', mode='w', newline='', encoding='utf-8') as file:
   writer = csv.writer(file)
   writer.writerow(['role', 'content', 'embedding'])
   for message in conversation_data['conversations']:
      embedding = get_embedding(message['content'])
      writer.writerow([message['role'], message['content'], embedding])


# df['ada_embedding'] = df.combined.apply(lambda x: get_embedding(x, model='text-embedding-3-small'))
# df.to_csv('embedd.csv', index=False)