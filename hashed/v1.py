from flask import Flask, render_template, request, Blueprint,jsonify
from hashed.tools import *
from hashed.constants import *
import secrets
import time
import hashlib
import random
import os

v1 = Blueprint('v1', __name__, url_prefix='/api/v1')

#upload method
@v1.route('/upload', methods=['POST'])
def upload():
    # get the headers required for this route
    api_key = request.headers.get(API_KEY_FIELD)
    filename = request.headers.get(UPLOAD_FILE_NAME_FIELD)
    encryption_key = request.headers.get(ENCRYPTION_KEY_FIELD)

    if api_key is None:
        return {'error': 'API Key header not provided'}, 400

    if filename is None:
        return {'error': 'File Name header is blank'}, 400

    verification_result = verify_request(request, api_key)
    if not verification_result['success']:
        return jsonify({'error': verification_result['message']}, verification_result["code"])
    
    file_data = request.data
    if not verify_upload(file_data, api_key):
        return jsonify({'error': 'Either no file data provided or file size is too large'}), 400

    upload_result = encrypted_upload(file_data,encryption_key,api_key,filename)
    if not upload_result['success']:
        return jsonify({'error': upload_result['error']}),upload_result['code']
    else:
        return jsonify({'message' :upload_result['message']}),upload_result['code']
    
    
@v1.route('/redeem', methods=['POST'])
def redeem():
    api_key = request.headers.get(API_KEY_FIELD)
    key = request.get_json().get(ACTIVATION_KEY)

    if key is None:
        return jsonify({'error': 'Invalid request, Activation Key is required'}), 400
    
    license = keys.find_one({LICENSE_KEY: key})
    if not license:
        return jsonify({'error': 'Activation Key not Found in DB'}), 400
    
    if api_key is None:
        return make_account(request, license)
    
    else:
        account = check_api_key(api_key)
        if not account:
            return jsonify({'error': 'API key Invalid '}), 400
        expiry = redeem_license(account, license)
        return jsonify({'expiry': expiry}), 200


@v1.route('/login', methods=['POST'])
def login():
    api_key = request.headers.get(API_KEY_FIELD)
    verification_result = verify_request(request, api_key)
    if not verification_result['success']:
        return {'error': verification_result['message']}, verification_result["code"]
    account = check_api_key(api_key)
    if not account:
        return {'error': 'API key Invalid '}, 400

    account = {
        ACCOUNT_API_KEY: account[ACCOUNT_API_KEY],
        ACCOUNT_EXPIRY_FIELD: account[ACCOUNT_EXPIRY_FIELD],
        ACCOUNT_TIER_ID: account[ACCOUNT_TIER_ID]
    }
    return {'account': account}, 200 


