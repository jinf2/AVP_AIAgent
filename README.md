# AVP_AIAgent

## Prerequisites
```
Python 3.9.16
```
## Setup
1. Use "venv" to build python environment

2. Clone the Repository:
```
git clone https://github.com/jinf2/AVP_AIAgent.git
```

3. Install Dependencies:
```
pip install -r requirements.txt
```

## How to use API

1. In other terminal, run:
```
python flask_setup.py
```

## API Reference

#### UPLOAD the user data

```http
  POST http://3.147.114.98:5000/upload
```

| Parameter | Type     | Description                |
| :-------- | :------- | :------------------------- |
| `api_key` | `string` | **Required**. Your API key |

| Input_type | Output_type     | Description                |
| :-------- | :------- | :------------------------- |
| `json` | `string` | If upload have error, which means the result without userID, it will reply "No user_id, Upload Unsuccessful :(" else reply "Upload Successful :)"|

Input_example:
```
{
    "start_time": "2024-12-12T01:10:55.431Z",
    "end_step": "P7",
    "end_time": "2024-12-12T01:12:29.310Z",
    "start_step": "P7",
    "user_id": "Gg"
}
```
Output_example:
```
No user_id, Upload Unsuccessful :(
```
```
Upload Successful :)
```

#### GET GPT RESULT

```http
  POST http://3.147.114.98:5000/search
```

| Parameter | Type     | Description                |
| :-------- | :------- | :------------------------- |
| `openai/api_key` | `string` | **Required**. Your API key |
| `pinecone/api_key` | `string` | **Required**. Your API key |

| Input_type | Output_type     | Description                |
| :-------- | :------- | :------------------------- |
| `json` | `json` | |

Input_example:
```
{
    "words":"hello"
}
```
Output_example:
```
{
    "answer": 'Answer to the student question',
    "animation_clip":[P6, P6-1],
    "audio_url": "audio/output.mp3"
}
```

#### GET GPT RESULT

```http
  GET http://3.147.114.98:5000/audio/<filename>
```
| Input_type | Output_type     | Description                |
| :-------- | :------- | :------------------------- |
| Nothing | `mp3` | Reply a mp3 file, which have the sound of GPT result|


## Codebase Structure

```javascript
AVP/
  AVP_AIAgent/
    - requirements.txt
    - README.md
    - src/
      -- flask_setup.py
      -- Autogen_try.py
      -- avp_db.py
      -- talk_record.json
      -- output.mp3
      -- LPVT_RAG_Basic_Knowledge.txt
      -- medical_info.json
      -- talk_record.json
      -- medical_embed.json
      -- current_data.json
      -- _pycache_/
  venv/
```


