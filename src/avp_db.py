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
        # response = self.dynamodb_client.list_tables()
        # print("Tables:", response['TableNames'])
        # with open('current_data.json', 'r', encoding='utf-8') as json_file:
        #     self.current_data = json.load(json_file)

    def Upload(self, data):
        User_table = self.dynamodb.Table('AVP_user')
        Record_table = self.dynamodb.Table('upload_record')
        #1 Check the User is new in User_table? If new, add a new line in User_table. If not new, check it is first time push or not?
        response_user = User_table.get_item(Key={"user_id": data["user_id"]})
        bucket_name = 'avpuserata'
        file_key = f'sessionlog_link/{data["user_id"]}.json'
        if 'Item' in response_user:
            # data_dict = json.loads(data)
            # check start_time is empty or not.
            if data["start_time"]: # if both have times, means still need update
                cur_uploadtime = response_user['Item'].get('upload_time', 0)
                response_record = Record_table.get_item(Key={"user_id": data["user_id"], "upload_number":cur_uploadtime})
                if response_record['Item'].get('start_time', 0) == data["start_time"]: #it is not first time upload
                    Record_table.update_item(
                        Key={'user_id': data['user_id'],"upload_number":cur_uploadtime},
                        UpdateExpression='SET end_time = :new_end_time',
                        ExpressionAttributeValues={':new_end_time': data["end_time"]},
                        ReturnValues='UPDATED_NEW'  )
                else: #First time upload, upload_time+1
                    print("1")
                    new_uploadtime = cur_uploadtime + 1
                    User_table.update_item(
                        Key={'user_id': data['user_id']},
                        UpdateExpression='SET upload_time = :new_upload_time',
                        ExpressionAttributeValues={':new_upload_time': new_uploadtime},
                        ReturnValues='UPDATED_NEW'  )
                    Record_table_item={
                        'user_id': data["user_id"],
                        'upload_number':new_uploadtime,
                        'start_step': data["user_id"],
                        'start_time': data["start_time"],
                        'end_step': data["end_step"],
                        'end_time': data["end_time"]}
                    Record_table.put_item(Item=Record_table_item)
            else: # if empty, mains that it is last upload
                cur_uploadtime = response_user['Item'].get('upload_time', 0)
                response_record = Record_table.get_item(Key={"user_id": data["user_id"], "upload_number":cur_uploadtime})
                Record_table.update_item(
                        Key={'user_id': data['user_id'],"upload_number":cur_uploadtime},
                        UpdateExpression='SET end_time = :new_end_time',
                        ExpressionAttributeValues={':new_end_time': data["end_time"]},
                        ReturnValues='UPDATED_NEW'  )
                response = self.s3_client.get_object(Bucket=bucket_name, Key=file_key)
                existing_content = response['Body'].read().decode('utf-8')
                existing_content = json.loads(existing_content)
                if os.path.exists('talk_record.json') and os.path.getsize('talk_record.json') > 0:
                    with open('talk_record.json', 'r', encoding='utf-8') as json_file:
                        talk_data = json.load(json_file)
                combined_data = {'conversations': existing_content['conversations'] + talk_data['conversations']}
                self.s3_client.put_object(
                    Bucket=bucket_name,
                    Key=file_key,
                    Body=json.dumps(combined_data, indent=4),
                    ContentType='application/json')
                talk_data = {"conversations": []}
                with open('talk_record.json', 'w', encoding='utf-8') as f:
                    json.dump(talk_data, f, ensure_ascii=False, indent=4)
            return "Old ID"
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
                ContentType='application/json')
            presigned_url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': bucket_name, 'Key': file_key},
                ExpiresIn=3600)
            #2.train_total=0, upload_time=1
            User_table_item={
                'user_id': data["user_id"],
                'sessionlog_link':presigned_url,
                'train_total': 0,
                'upload_time' : 1}
            User_table.put_item(Item=User_table_item)
            #3.add a new line in Record_table:
            Record_table_item={
                'user_id': data["user_id"],
                'upload_number':1,
                'start_step': data["user_id"],
                'start_time': data["start_time"],
                'end_step': data["end_step"],
                'end_time': data["end_time"]}
            Record_table.put_item(Item=Record_table_item)
            return "new ID"

if __name__ == "__main__":
    new = upload_background()
    data={
            "end_time": "2024-12-10T01:02:10.696Z",
            "user_id": "try",
            "start_time": "2024-12-07T01:02:06.929Z",
            "start_step": "P1-1",
            "end_step": "P1-2"
        }
    answer = new.Upload(data)
    print(answer)
