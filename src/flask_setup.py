from flask import Flask,jsonify,request,send_from_directory
from mutagen.mp3 import MP3
import json
import awsgi

app = Flask(__name__)
app.json.sort_keys = False

@app.route('/')
def get_items():
    return "Let's try connect!"

@app.route('/connect/<text>', methods=['GET'])
def connect(text):
    import API_try
    result = API_try.trylink(text)
    return jsonify(result)
    # return{
    #     "msg":"success",
    #     "data":result
    # }

@app.route('/upload', methods=['POST'])
def upload_data():
    import avp_db
    if request.method == 'POST':
        data=request.get_json(force=True) 
        with open('current_data.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)    
        if "user_id" not in data.keys():
            return "No user_id, Upload Unsuccessful :("
        print("user_id is:"+data["user_id"])
        result = "Upload Successful :)"
        # new_upload = avp_db.upload_background()
        # new_upload.Upload(data)
        return result

@app.route('/search', methods=['POST'])
def search():
    import Agent_RAG
    if request.method == 'POST':
        data=request.get_json(force=True) 
        new = Agent_RAG.background()
        question = data['words']
        if data['words'] == "":
            return jsonify({
            "answer": "No problem identified",
            "animation_clip":[],
            "audio_url": "NA"
        })
        answer = new.do_conv_RAG(question)
        print("question:" + question)
        print("answer:" + answer['Question_answer'])
        audio = MP3("/home/ec2-user/AVP/AVP_AIAgent/src/output.mp3")
        audio_length = audio.info.length
        return jsonify({
            "answer": answer['Question_answer'],
            "animation_clip": answer['animation_clip'],
            "audio_url": "audio/output.mp3",
            "audio_length":audio_length
        })

@app.route('/searchstep', methods=['POST'])
def searchstep():
    import Agent_RAG
    if request.method == 'POST':
        data=request.get_json(force=True) 
        new = Agent_RAG.background()
        question = data['words']
        if question == "":
            return jsonify({
            "answer": "No problem identified",
            "animation_clip":[],
            "audio_url": "NA"
        })
        if data["step"]:
            question = question + "Now I'm stuck at " + data["step"]
            answer = new.do_conv_RAG(question)
        print("question:" + question)
        print("answer:" + answer['Question_answer'])
        audio = MP3("/home/ec2-user/AVP/AVP_AIAgent/src/output.mp3")
        audio_length = audio.info.length
        return jsonify({
            "answer": answer['Question_answer'],
            "animation_clip":answer['animation_clip'],
            "audio_url": "audio/output.mp3",
            "audio_length":audio_length
        })

# @app.route('/audio', methods=['POST'])
# def get_audio():
#     if request.method == 'POST':
#         data=request.get_json(force=True) 
#         AUDIO_FOLDER = '/home/ec2-user/AVP/AVP_AIAgent/src/'
#     return send_from_directory(AUDIO_FOLDER, data['audio_url'], mimetype='audio/mpeg')

@app.route('/audio/<filename>', methods=['GET'])
def get_audio(filename):
    AUDIO_FOLDER = '/home/ec2-user/AVP/AVP_AIAgent/src/'
    return send_from_directory(AUDIO_FOLDER, filename, mimetype='audio/mpeg')

@app.route('/video', methods=['POST'])
def video_match():
    import video_match
    if request.method == 'POST':
        data=request.get_json(force=True) 
        print("question:"+data['words'])
        new = video_match.background()
        question = data['words']
        answer = new.do_conv(question)
        print("answer:"+answer)
        return jsonify({
            "answer": answer
        })

# def lambda_handler(event, context):
#     return awsgi.response(app, event, context, base64_content_types={"image/png"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)