from flask import Flask,jsonify,request,send_from_directory

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

@app.route('/search', methods=['POST'])
def search():
    import Autogen_try
    if request.method == 'POST':
        data=request.get_json(force=True) 
        print("question:"+data['words'])
        new = Autogen_try.background()
        question = data['words']
        answer = new.do_conv(question)
        print("answer:"+answer)
        return jsonify({
            "answer": answer,
            "audio_url": "output.mp3"
        })

@app.route('/audio', methods=['POST'])
def get_audio():
    if request.method == 'POST':
        data=request.get_json(force=True) 
        AUDIO_FOLDER = '/home/ec2-user/AVP/AVP_AIAgent/src/'
    return send_from_directory(AUDIO_FOLDER, data['audio_url'], mimetype='audio/mpeg')

# @app.route('/audio/<filename>', methods=['GET'])
# def get_audio(filename):
#     AUDIO_FOLDER = '/home/ec2-user/AVP/AVP_AIAgent/src/'
#     return send_from_directory(AUDIO_FOLDER, filename, mimetype='audio/mpeg')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
