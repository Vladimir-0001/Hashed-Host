from flask import Flask, request
import os 
from hashed.v1 import v1
from hashed.file import file

#you can remove or change this if its gay on mac i think the command is  'clear' on mac and linux 
os.system('cls')

app = Flask(__name__)

@app.after_request
def change_server_host(response):
    response.headers['Server'] = "Hashed/1.0.0"
    return response
    

app.register_blueprint(v1)
app.register_blueprint(file)

if __name__ == '__main__':
    app.run(debug=True)
