from flask import Flask, render_template, request, Blueprint
from pymongo import MongoClient
import hashlib
import json 
import os 

v1 = Blueprint('v1',__name__)

client = MongoClient(os.getenv("MONGO_CONNECTION_STRING"))

db = client["Hashed"]
accounts = db["accounts"]

v1 = Blueprint('v1', __name__, url_prefix = '/api/v1')

def anonymize_ip(ip_address):
    ip_parts = ip_address.split('.')
    ip_parts[-1] = '0' 
    anonymized_ip = '.'.join(ip_parts)
    return anonymized_ip

def check_api_key(api_key):
    check_key = accounts.find_one({ "key": api_key})
    # this is dumb it should return a bool not the account 
    return check_key

def verify_ip(api_key, ip_address):
    ip_address = anonymize_ip(ip_address)
    hashed_ip = hashlib.sha256(bytes(ip_address, 'utf-8')).hexdigest()
    account_query = {"key": api_key}
    account = accounts.find_one(account_query)
    ip_list = account['ip_list']
    if hashed_ip not in ip_list:
        if len(ip_list) < 3:
            ip_list.append(hashed_ip)
            accounts.update_one(account_query,{"$push": {"ip_list": hashed_ip}} )
        else:
            return {'success': False, 'message':'IP not authorized please turn off any VPN or Proxy service. account sharing will lead to permanant termination of your account'}
    return {'success': True, 'message':''}
        
    

@v1.route('/upload', methods = ['POST'])
def upload():
    #get the headers required for this route  
    api_key = request.headers.get('api-key') 
    filename = request.headers.get('file-name')

    if "Cf-Connecting-IP" in request.headers:
        ip = request.headers["Cf-Connecting-IP"]
    else:
        ip = request.remote_addr
    if api_key is None:
        return {'error': 'api-key header not provided'}, 400
    if filename == None:
        return {'error' : 'file-name header is blank'},400
    # print(check_api_key(api_key))  
    if check_api_key(api_key):
        ip_verification_result = verify_ip(api_key,ip)
        if ip_verification_result['success']:
            return {'file':'uploaded lol'}, 200
        else:
            return {'error': ip_verification_result['message']}, 403 
    else:
        return {'error': 'Invalid api-key header'}, 403

    #im sex
    return "file_uploaded"


@v1.route('/login')
def login():
    #again , i am sex 
    return "Hello, World!"


