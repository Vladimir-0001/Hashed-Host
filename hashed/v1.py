from flask import Flask, render_template, request, Blueprint,jsonify
from hashed.constants import *
from hashed.errors import Errors as errors
from hashed.tools import *
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
        return errors.no_api_key()

    if filename is None:
        return errors.no_filename()

    verification_result = verify_request(request, api_key)
    if not verification_result['success']:
        errors.verification_error(verification_result)
    
    file_data = request.data
    if not verify_upload(file_data, api_key):
        return errors.filesize_over_tier_max()
    print(encryption_key)
    upload_result = encrypted_upload(file_data,encryption_key,api_key,filename)

    return jsonify({'message':upload_result['message']}),upload_result['code']
    
    
@v1.route('/redeem', methods=['POST'])
def redeem():
    api_key = request.headers.get(API_KEY_FIELD)
    key = request.get_json().get(ACTIVATION_KEY)

    if key is None:
        return errors.no_activation_key()
    
    license = keys.find_one({LICENSE_KEY: key})
    if not license:
        return errors.invalid_activation_key()
    
    if api_key is None:
        return make_account(request, license)
    
    else:
        account = check_api_key(api_key)
        if not account:
            return errors.api_key_invalid()
        expiry = redeem_license(account, license)
        return jsonify({'message':{'expiry': expiry}}), 200


@v1.route('/login', methods=['POST'])
def login():
    api_key = request.headers.get(API_KEY_FIELD)
    
    account = check_api_key(api_key)
    if not account:
        return errors.api_key_invalid()
    
    verification_result = verify_request(request, api_key)
    if not verification_result['success']:
        return errors.verification_error(verification_result)
    
    account = {
        ACCOUNT_API_KEY: account[ACCOUNT_API_KEY],
        ACCOUNT_EXPIRY_FIELD: account[ACCOUNT_EXPIRY_FIELD],
        ACCOUNT_TIER_ID: account[ACCOUNT_TIER_ID]
    }
    return {'account': account}, 200 


