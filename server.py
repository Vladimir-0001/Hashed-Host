from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def home():
    #i love sex squishey this function makes me want to have sex 
    return render_template('index.html')

@app.route('/api/v1/upload')
def upload():
    #im sex
    return "file_uploaded"


@app.route('/user/login')
def login():
    #again , i am sex 
    return "Hello, World!"




if __name__ == '__main__':
    app.run(debug=True)
