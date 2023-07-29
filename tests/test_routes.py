import pytest
import json
from flask import Flask
from hashed.v1 import v1 
from hashed.constants import *
from hashed.errors import Errors as errors
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
    
#TODO add test for bad api_key headers 


def test_upload_missing_headers(client):
    #Test for missing api key header
    response = client.post('/api/v1/upload', headers = {UPLOAD_FILE_NAME_FIELD:'test.txt'})
    expected_response = errors.no_api_key()
    assert response.status_code == expected_response.status_code
    assert response.json == expected_response.json
    #test for missing file name header 
    response = client.post('/api/v1/upload', headers = {API_KEY_FIELD:'hashed_testkey'})
    expected_response = errors.no_filename()
    assert response.status_code == expected_response.status_code
    assert response.json == expected_response.json
    
def test_empty_upload_data(client):
    response = client.post('/api/v1/upload', headers = {UPLOAD_FILE_NAME_FIELD:'test.txt', API_KEY_FIELD:'hashed_testkey'},data = "")
    expected_response = errors.filesize_over_tier_max()
    assert response.status_code == expected_response.status_code
    assert response.json == expected_response.json
    
def test_upload_normal(client):
    response = client.post('/api/v1/upload', headers = {UPLOAD_FILE_NAME_FIELD:'test.txt', API_KEY_FIELD:'hashed_testkey'},data = bytes('test','utf-8'))
    assert response.status_code == 200
    assert response.json.get('message') != None

def test_upload_bad_hex(client):
    response = client.post('/api/v1/upload', headers = {UPLOAD_FILE_NAME_FIELD:'test.txt', API_KEY_FIELD:'hashed_testkey',ENCRYPTION_KEY_FIELD:"bad_encryption_key"},data = bytes('test','utf-8'))
    expected_response = errors.invalid_encryption_hex_length()
    print(f'{response.json = }')
    print(f'{expected_response.json = }')
    assert response.status_code == expected_response.status_code
    assert response.json == expected_response.json
    response = client.post('/api/v1/upload', headers = {UPLOAD_FILE_NAME_FIELD:'test.txt', API_KEY_FIELD:'hashed_testkey',ENCRYPTION_KEY_FIELD:"11111111111111111111111111111k"},data = bytes('test','utf-8'))
    print(f'{response.json = }')
    print(f'{expected_response.json =}')
    expected_response2 = errors.invalid_encryption_hex()
    assert response.status_code == expected_response.status_code
    assert response.json == expected_response.json
    
def test_encryption_and_decryption(client):
    response = client.post('/api/v1/upload', headers = {UPLOAD_FILE_NAME_FIELD:'test.txt', API_KEY_FIELD:'hashed_testkey'},data = bytes('test','utf-8'))
    assert response.status_code == 200
    assert response.json.get('message') != None
    url = response.json['message']['url'].split('/')
    file_key = url[6]   
    file_id = url[5]
    response = client.get(f'file/raw/{file_id}/{file_key}')
    assert response.data == bytes("test", 'utf-8')
    assert response.status_code == 200

####################################################
#################### Redeem Tests ##################
####################################################
    
def test_redeem_invalid_key(client):
    response = client.post("/api/v1/redeem",headers = {API_KEY_FIELD:'hashed_testkey'}, json = {ACTIVATION_KEY:'123'})
    expected_response = errors.invalid_activation_key()
    assert response.status_code == expected_response.status_code
    assert response.json == expected_response.json
    
def test_redeem_missing_key(client):
    response = client.post('api/v1/redeem', headers = {API_KEY_FIELD:'hashed_testkey'}, json ={})
    expected_response = errors.no_activation_key()
    assert response.status_code == expected_response.status_code
    assert response.json == expected_response.json

def test_redeem_normal(client):
    response = client.post('api/v1/redeem', headers = {API_KEY_FIELD:'hashed_testkey'}, json  = {ACTIVATION_KEY:'redeem_testkey'})
    assert response.json.get('message').get('expiry') != None
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
    expected_response = errors.api_key_invalid()
    assert response.status_code == expected_response.status_code
    assert response.json == expected_response.json

def test_login_no_api_key(client):
    response = client.post('api/v1/login')
    expected_response = errors.api_key_invalid()
    assert response.status_code == expected_response.status_code
    assert response.json == expected_response.json
    
    

