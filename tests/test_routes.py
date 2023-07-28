import pytest
import json
from flask import Flask
from hashed.v1 import v1 
from hashed.constants import *
from hashed.file import file


app = Flask(__name__)
app.register_blueprint(v1)
app.register_blueprint(file)

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client
        

####################################################
#################### Upload Tests ##################
####################################################
    
        
def test_upload_missing_headers(client):
    #Test for missing api key header
    response = client.post('/api/v1/upload', headers = {UPLOAD_FILE_NAME_FIELD:'test.txt'})
    assert response.status_code == 400
    assert response.json == {'error': 'API Key header not provided'}
    #test for missing file name header 
    response = client.post('/api/v1/upload', headers = {API_KEY_FIELD:'hashed_testkey'})
    assert response.status_code == 400
    assert response.json == {'error': 'File Name header is blank'}
    
def test_empty_upload_data(client):
    response = client.post('/api/v1/upload', headers = {UPLOAD_FILE_NAME_FIELD:'test.txt', API_KEY_FIELD:'hashed_testkey'},data = "")
    
    assert response.json == {'error': 'Either no file data provided or file size is too large'}
    assert response.status_code == 400
    
def test_upload_normal(client):
    response = client.post('/api/v1/upload', headers = {UPLOAD_FILE_NAME_FIELD:'test.txt', API_KEY_FIELD:'hashed_testkey'},data = bytes('test','utf-8'))
    assert response.status_code == 200
    assert response.json.get('message') != None

def test_upload_bad_hex(client):
    response = client.post('/api/v1/upload', headers = {UPLOAD_FILE_NAME_FIELD:'test.txt', API_KEY_FIELD:'hashed_testkey',ENCRYPTION_KEY_FIELD:"bad_encryption_key"},data = bytes('test','utf-8'))
    assert response.json == {'error':'encryption hex needs to be 32 characters in length'}
    assert response.status_code == 400
    response = client.post('/api/v1/upload', headers = {UPLOAD_FILE_NAME_FIELD:'test.txt', API_KEY_FIELD:'hashed_testkey',ENCRYPTION_KEY_FIELD:"1111111111111111111111111111111k"},data = bytes('test','utf-8'))
    assert response.json == {'error':'encryption key is not valid hex'}
    assert response.status_code == 400
    
def test_encryption_and_decryption(client):
    response = client.post('/api/v1/upload', headers = {UPLOAD_FILE_NAME_FIELD:'test.txt', API_KEY_FIELD:'hashed_testkey'},data = bytes('test','utf-8'))
    assert response.status_code == 200
    assert response.json.get('message') != None
    url = response.json['message']['url'].split('/')
    file_key = url[6]   
    file_id = url[5]
    response = client.get(f'file/raw/{file_id}/{file_key}')
    assert response.data== bytes("test", 'utf-8')
    assert response.status_code == 200

####################################################
#################### Redeem Tests ##################
####################################################
    
def test_redeem_invalid_key(client):
    response = client.post("/api/v1/redeem",headers = {API_KEY_FIELD:'hashed_testkey'}, json = {ACTIVATION_KEY:'123'})
    assert response.json == {'error': 'Activation Key not Found in DB'}
    assert response.status_code == 400
    
def test_redeem_missing_key(client):
    response = client.post('api/v1/redeem', headers = {API_KEY_FIELD:'hashed_testkey'}, json ={})
    assert response.json == {'error': 'Invalid request, Activation Key is required'}
    assert response.status_code == 400

def test_redeem_normal(client):
    response = client.post('api/v1/redeem', headers = {API_KEY_FIELD:'hashed_testkey'}, json  = {ACTIVATION_KEY:'redeem_testkey'})
    assert response.json.get('expiry') != None
    assert response.status_code == 200
    
####################################################
#################### Login Tests ##################
####################################################

def test_login_normal(client):
    response = client.post('api/v1/login', headers = {API_KEY_FIELD:'hashed_testkey'})
    assert response.status_code == 200
    assert response.json.get('account') != None

def test_login_invalid_api_key(client):
    response = client.post('api/v1/login', headers = {API_KEY_FIELD:'bad_api_key'})
    assert response.status_code == 403
    assert response.json == {'error':'Invalid API Key header'}

def test_login_no_api_key(client):
    response = client.post('api/v1/login')
    assert response.status_code == 403
    assert response.json == {'error':'Invalid API Key header'}
    
    

