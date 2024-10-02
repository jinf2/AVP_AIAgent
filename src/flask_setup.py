from flask import Flask,jsonify,request

app = Flask(__name__)
app.json.sort_keys = False

#news_monitor_API_start
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
        print(data['words'])
        new = Autogen_try.background()
        question = data['words']
        answer = new.do_conv(question)
    return answer

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
