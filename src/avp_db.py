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
ssm = boto3.client('ssm',region_name='us-east-2')
dynamodb = boto3.client('dynamodb', region_name='us-east-2')
# List tables (example operation)
response = dynamodb.list_tables()
print("Tables:", response['TableNames'])

# Example: Put an item into a table
# table_name = 'YourTableName'
# dynamodb.put_item(
#     TableName=table_name,
#     Item={
#         'ID': {'S': '123'},
#         'Name': {'S': 'Example Name'}
#     }
# )
# print(f"Item inserted into table {table_name}")