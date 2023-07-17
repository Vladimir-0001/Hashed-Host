<<<<<<< HEAD
from flask import Flask, render_template

app = Flask(__name__)
=======
from flask import Flask, render_template, request, Blueprint
from pymongo import MongoClient
import json 
import os 


app = Flask(__name__)
client = MongoClient(os.getenv("MONGO_CONNECTION_STRING"))


v1 = Blueprint('v1', __name__, prefix = '/api/v1')
>>>>>>> dev

@app.route('/')
def home():
    #i love sex squishey this function makes me want to have sex 
    return render_template('index.html')

<<<<<<< HEAD
@app.route('/api/v1/upload')
def upload():
=======
@v1.route('/upload')
def upload():
    api_key = request.headers.get('api_key')
    filename = request.headers.get('filename')
    if "Cf-Connecting-IP" in request.headers:
        ip = request.headers["Cf-Connecting-IP"]
    else:
        ip = request.remote_addr
    if request.headers.get('ApiKey') is None:
        return json.dumps("{'error : 'ApiKey not provided'}"), 400
    if request.args.get('filename') == None:
        return "{'error' : 'filename is blank'}",400
    
>>>>>>> dev
    #im sex
    return "file_uploaded"


@app.route('/user/login')
def login():
    #again , i am sex 
    return "Hello, World!"




if __name__ == '__main__':
    app.run(debug=True)
