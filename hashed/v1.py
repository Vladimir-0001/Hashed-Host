# Import the necessary libraries and modules
import hashlib
import os
import random
import secrets
import time

from flask import Blueprint, Flask, jsonify, render_template, request
from hashed.constants import *
from hashed.errors import Errors as errors
from hashed.tools import *

# Create a Blueprint instance for version 1 of the API with '/api/v1' as a prefix for all routes
v1 = Blueprint('v1', __name__, url_prefix='/api/v1')

# Endpoint for uploading files. 
@v1.route('/upload', methods=['POST'])
def upload():
    # Get the required headers for this route
    api_key = request.headers.get(API_KEY_FIELD)
    filename = request.headers.get(UPLOAD_FILE_NAME_FIELD)
    encryption_key = request.headers.get(ENCRYPTION_KEY_FIELD)

    # Return error messages if necessary headers are missing
    if api_key is None:
        return errors.no_api_key()
    if filename is None:
        return errors.no_filename()

    # Verify the request with the given API key
    verification_result = verify_request(request, api_key)
    if not verification_result['success']:
        errors.verification_error(verification_result)

    # Get the uploaded file data
    file_data = request.data
    if not verify_upload(file_data, api_key):
        return errors.filesize_over_tier_max()

    # Upload the file and return the result as a JSON response
    upload_result = encrypted_upload(file_data, encryption_key, api_key, filename)
    return jsonify({'message':upload_result['message']}), upload_result['code']


# Endpoint for redeeming an activation key. The function is decorated as a Flask route that listens to POST requests
@v1.route('/redeem', methods=['POST'])
def redeem():
    api_key = request.headers.get(API_KEY_FIELD)
    key = request.get_json().get(ACTIVATION_KEY)

    # Return error messages if the necessary data is missing
    if key is None:
        return errors.no_activation_key()

    # Retrieve the license using the activation key
    license = keys.find_one({LICENSE_KEY: key})
    if not license:
        return errors.invalid_activation_key()

    # If no API key was provided, create a new account with the license
    if api_key is None:
        return make_account(request, license)
    else:
        # If an API key was provided, check its validity
        account = check_api_key(api_key)
        if not account:
            return errors.api_key_invalid()

        # Redeem the license and return the expiry date as a JSON response
        expiry = redeem_license(account, license)
        return jsonify({'message':{'expiry': expiry}}), 200


# Endpoint for user login. The function is decorated as a Flask route that listens to POST requests
@v1.route('/login', methods=['POST'])
def login():
    api_key = request.headers.get(API_KEY_FIELD)
    
    # Check the validity of the provided API key
    account = check_api_key(api_key)
    if not account:
        return errors.api_key_invalid()

    # Verify the request with the given API key
    verification_result = verify_request(request, api_key)
    if not verification_result['success']:
        return errors.verification_error(verification_result)

    # Return the account data as a JSON response
    account = {
        ACCOUNT_API_KEY: account[ACCOUNT_API_KEY],
        ACCOUNT_EXPIRY_FIELD: account[ACCOUNT_EXPIRY_FIELD],
        ACCOUNT_TIER_ID: account[ACCOUNT_TIER_ID]
    }
    return {'message':{'account': account}}, 200 
