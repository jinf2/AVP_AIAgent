import feedparser
import boto3
from openai import OpenAI
import requests
import re
import os
from datetime import datetime
from bs4 import BeautifulSoup
from langchain_community.llms import Ollama

ssm = boto3.client('ssm',region_name='us-east-2')
parameter = ssm.get_parameter(Name='/openai/api_key', WithDecryption=True)

# openai.api_key=parameter['Parameter']['Value']

client = OpenAI(
    api_key=""
)

def extract_GPT_3(article_content):
    prompt = f"Please reply this massage in one sentence:{article_content} "
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "system", "content": "Talking with GPT"},
                  {"role": "user", "content": prompt}],
        max_tokens=100
    )
    return response.choices[0].message.content

def trylink(text):
    return extract_GPT_3(text)

if __name__ == "__main__":
    text="Hi what is your name?"
    print(trylink(text))