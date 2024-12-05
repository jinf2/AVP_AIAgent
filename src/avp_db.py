import boto3
from  openai import OpenAI
import json
import os
import pinecone
import pandas as pd
import csv
import ast
import numpy as np

import boto3

# Create DynamoDB client
class upload_background():
    def __init__(self):
        self.ssm = boto3.client('ssm', region_name='us-east-2')
        self.s3_client = boto3.client('s3', region_name='us-east-2')
        self.dynamodb = boto3.resource('dynamodb', region_name='us-east-2')
        self.dynamodb_client = boto3.client('dynamodb', region_name='us-east-2')
        response = self.dynamodb_client.list_tables()
        print("Tables:", response['TableNames'])
        # with open('current_data.json', 'r', encoding='utf-8') as json_file:
        #     self.current_data = json.load(json_file)

    def Upload(self, data):
        User_table = self.dynamodb.Table('AVP_user')
        Record_table = self.dynamodb.Table('upload_record')
        #1 Check the User is new in User_table? If new, add a new line in User_table. If not new, check it is first time push or not?
        response = User_table.get_item(Key={"user_id": data["user_id"]})
        bucket_name = 'avpuserata'
        file_key = f'sessionlog_link/{data["user_id"]}.json'
        if 'Item' in response:
            return "Old ID"
            # if data["start_time"]:

            # # if new upload? 1.  
            # else:

        else:
            #If new, add a new line in User_table:1. get new sessionlog_link 2.train total=0, upload time=1
            #1. get new sessionlog_link
            file_content={"conversations": [
                {
                    "role": "user",
                    "content": "what is your name?"
                },
                {
                    "role": "AI",
                    "content": "Hello! My name is Assistant. How can I assist you today?"
                }]}
            self.s3_client.put_object(
                Bucket=bucket_name,
                Key=file_key,
                Body=json.dumps(file_content),
                ContentType='application/json'
            )
            presigned_url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': bucket_name, 'Key': file_key},
                ExpiresIn=3600 
            )
            #2.train_total=0, upload_time=1
            User_table_item={
                'user_id': data["user_id"],
                'sessionlog_link':presigned_url,
                'train_total': 0,
                'upload_time' : 1
            }
            User_table.put_item(Item=User_table_item)
            #3.add a new line in Record_table:
            Record_table_item={
                'user_id': data["user_id"],
                'upload_number':1,
                'start_step': data["user_id"],
                'start_time': data["start_time"],
                'end_step': data["end_step"],
                'end_time': data["end_time"]
            }
            Record_table.put_item(Item=Record_table_item)
            return "new ID"

if __name__ == "__main__":
    new = upload_background()
    data={
            "end_time": "2024-12-05T01:02:10.696Z",
            "user_id": "try",
            "start_time": "2024-12-05T01:02:05.929Z",
            "start_step": "P1-1",
            "end_step": "P1-2"
        }
    
    answer = new.Upload(data)
    print(answer)
