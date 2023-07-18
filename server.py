from flask import Flask, render_template, request, Blueprint
from pymongo import MongoClient
import json 
import os 


app = Flask(__name__)
client = MongoClient(os.getenv("MONGO_CONNECTION_STRING"))


db = client["Hashed"]
v1 = Blueprint('v1', __name__, url_prefix = '/api/v1')

def check_api_key(key):
    accounts_col = db["accounts"]
    check_key = accounts_col.find_one({ "key": key})
    return check_key

@app.route('/')
def home():
    #i love sex squishey this function makes me want to have sex 
    return render_template('index.html')

#@v1.route('/upload')
@app.route('/api/v1/upload', methods = ['POST'])
def upload():
    api_key = request.headers.get('api-key')
    filename = request.headers.get('file-name')
    if "Cf-Connecting-IP" in request.headers:
        ip = request.headers["Cf-Connecting-IP"]
    else:
        ip = request.remote_addr
    if api_key is None:
        return json.dumps("{'error : 'ApiKey not provided'}"), 400
    if filename == None:
        return "{'error' : 'filename is blank'}",400

    # print(check_api_key(api_key))  

    if check_api_key(api_key):
        return " {'file':'uploaded lol'} ", 200
    
    else:
        return " {'error': 'Invalid ApiKey'} ", 403

    #im sex
    return "file_uploaded"


@app.route('/user/login')
def login():
    #again , i am sex 
    return "Hello, World!"




if __name__ == '__main__':
    app.run(debug=True)
