from flask import Flask
import os 
from hashed.v1 import v1
from hashed.file import file

#you can remove or change this if its gay on mac i think the command is  'clear' on mac and linux 
os.system('cls')

app = Flask(__name__)

app.register_blueprint(v1, url_prefix = '/api/v1')
app.register_blueprint(file)

if __name__ == '__main__':
    app.run(debug=True)
