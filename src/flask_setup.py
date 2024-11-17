from flask import Flask,jsonify,request,send_from_directory
import json

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
    if request.method == 'POST':
        import avp_db
        data=request.get_json(force=True) 
        with open('current_data.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)    
        if "user_id" not in data.keys():
            return "No user_id, Upload Unsuccessful :("
        print("user_id is:"+data["user_id"])
        result = "Upload Successful :)"
        return result

@app.route('/search', methods=['POST'])
def search():
    import Autogen_try
    if request.method == 'POST':
        data=request.get_json(force=True) 
        print("question:"+data['words'])
        new = Autogen_try.background()
        question = data['words']
        answer = new.do_conv_RAG(question)
        print("answer:"+answer['Question_answer'])
        return jsonify({
            "answer": answer['Question_answer'],
            "animation_clip":answer['animation_clip'],
            "audio_url": "audio/output.mp3"
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



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
