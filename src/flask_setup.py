from flask import Flask,jsonify

app = Flask(__name__)
app.json.sort_keys = False

#news_monitor_API_start
@app.route('/')
def get_items():
    return "Let's try connect!"

@app.route('/connect/<text>')
def connect(text):
    import API_try
    result = API_try.trylink(text)
    return jsonify(result)
    # return{
    #     "msg":"success",
    #     "data":result
    # }

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
