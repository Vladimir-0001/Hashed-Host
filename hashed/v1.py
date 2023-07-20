from flask import Flask, render_template, request, Blueprint

from ipaddress import ip_interface

from pymongo import MongoClient

import secrets

import time 

import hashlib

import random

import json 

import os 



v1 = Blueprint('v1',__name__)


client = MongoClient(os.getenv('MONGO_CONNECTION_STRING'))

db = client['Hashed']


accounts = db['accounts']

keys = db['keys']

storage = db['storage']


# ACCOUNT FIELDS & OPTIONS

ACCOUNT_MAX_IPS = 3

ACCOUNT_IP_LIST = 'ip_list'

ACCOUNT_API_KEY = 'api-key'

ACCOUNT_EXPIRY_FIELD = "expiry"


#ENDPOINT FIELDS


API_KEY_FIELD = 'api-key'


#UPLOAD FIELDS

FILE_NAME_FIELD = 'file-name'


#REDEEM FIELDS

ACTIVATION_KEY = 'key'


#Account Activation Settings

REDEEMABLE_KEY = 'license_key'

LICENSE_TIME = 'time'

API_KEY_TOKEN_HEX_LENGTH = 16



v1 = Blueprint('v1', __name__, url_prefix = '/api/v1')

def process_ip(ip_address):

    ip_address = anonymize_ip(ip_address)

    hashed_ip = hashlib.sha256(bytes(ip_address, 'utf-8')).hexdigest()

    return hashed_ip


def redeem_license(account,license):

    now = int(time.time())

    expiry_time = now + int(license[LICENSE_TIME])

    if account[ACCOUNT_EXPIRY_FIELD] < now:

        accounts.update_one({API_KEY_FIELD: account[API_KEY_FIELD]}, {'$set': {ACCOUNT_EXPIRY_FIELD:expiry_time}})

        keys.delete_one({REDEEMABLE_KEY:license[REDEEMABLE_KEY]})

    return expiry_time


def make_account(request,license):

    ip_address = process_ip(get_ip(request))

    api_key = "hashed_" + secrets.token_hex(API_KEY_TOKEN_HEX_LENGTH)

    account = {

        API_KEY_FIELD:api_key,

        ACCOUNT_EXPIRY_FIELD: int(time.time())+int(license[LICENSE_TIME]),

        ACCOUNT_IP_LIST:[str(ip_address)]

    }

    accounts.insert_one(account)

    keys.delete_one({REDEEMABLE_KEY:license[REDEEMABLE_KEY]})

    return {API_KEY_FIELD:api_key},200
    

def anonymize_ip(ip_address):

    if '.' in ip_address:  #IPv4

        ip_parts = ip_address.split('.')

        ip_parts[-1] = '0' 

        anonymized_ip = '.'.join(ip_parts)

    elif ':' in ip_address:  # IPv6

        ip = ip_interface(ip_address + '/64')  

        anonymized_ip = str(ip.network.network_address)
    else:

        raise ValueError(f"Invalid IP address: {ip_address}")

    return anonymized_ip


def check_api_key(api_key):
    print(api_key)

    print({API_KEY_FIELD : api_key})

    check_key = accounts.find_one({API_KEY_FIELD : api_key})

    return check_key


def get_ip(request):


    if "Cf-Connecting-IP" in request.headers:

        ip_address = request.headers["Cf-Connecting-IP"]
    else:

        ip_address = request.remote_addr
    return ip_address


def verify_request(request, api_key, add = True, max_ips = ACCOUNT_MAX_IPS):

    if check_api_key(api_key) == None:

        return {'success': False, 'message':'Invalid API Key header', 'code': 403}
    

    ip_address = get_ip(request)

    account = check_api_key(api_key)

    ip_list = account[ACCOUNT_IP_LIST]

    hashed_ip = process_ip(ip_address)
    

    if hashed_ip not in ip_list:

        if len(ip_list) < max_ips and add == True:

            ip_list.append(hashed_ip)

            accounts.update_one({ ACCOUNT_API_KEY : api_key},{"$push": { ACCOUNT_IP_LIST: hashed_ip}} )
        else:

            return {'success': False, 'message':'IP not authorized please turn off any VPN or Proxy service. account sharing will lead to permanent termination of your account', 'code': 403}
        

    return {'success': True, 'message':'','code': 200}
        
    

@v1.route('/upload', methods = ['POST'])
def upload():

    #get the headers required for this route  

    api_key = request.headers.get(API_KEY_FIELD) 

    filename = request.headers.get(FILE_NAME_FIELD)
    

    if api_key == None:

        return {'error': 'API Key header not provided'}, 400

    if filename == None:

        return {'error' : 'File Name header is blank'}, 400
    

    verification_result = verify_request(request,api_key)
    

    if verification_result['success']:

        return {'file':'uploaded lol'}, 200
    else:

        return {'error': verification_result['message']}, verification_result["code"] 
    
    

    return "file_uploaded"




@v1.route('/redeem',methods=['POST'])

def redeem():

    api_key = request.headers.get(API_KEY_FIELD) 

    key  = request.get_json().get(ACTIVATION_KEY)

    if key == None:

        return {'error': 'invalid request, Activation Key is required'}, 400
    

    if api_key == None:

        license = keys.find_one({REDEEMABLE_KEY: key})
        if not license:

            return {'error':'license Key not Found '}, 400

        return make_account(request,license)

        ELE
    else:
        print(api_key)

        account = check_api_key(api_key)

        license = keys.find_one({REDEEMABLE_KEY: key})
        if not license:

            return{'error':'invalid license key'}, 400 
        if not account:

            return {'error':'Api key Invalid '}, 400

        expiry  = redeem_license(account,license)

        return {'expiry':expiry}, 200



@v1.route('/login')

def login():

    #again , i am sex 

    return "Hello, World!"



