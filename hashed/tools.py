from flask import Flask, render_template, request, Blueprint
from hashed.constants import *
from pathvalidate import sanitize_filename
from ipaddress import ip_interface
from pymongo import MongoClient
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from Crypto.Random import get_random_bytes
import secrets
import time
import hashlib
import random
import json
import sys
import os

client = MongoClient(os.getenv('MONGO_CONNECTION_STRING'))

db = client['Hashed']
accounts = db['accounts']
keys = db['keys']
storage = db['storage']
tiers = db['tiers']


def is_hex(s):
    try:
        int(s, 16)
        return True
    except ValueError:
        return False
    
def process_ip(ip_address):
    ip_address = anonymize_ip(ip_address)
    hashed_ip = hashlib.sha256(bytes(ip_address, 'utf-8')).hexdigest()
    return hashed_ip
    
def save_file(data,cipher_iv,encryption_key,file_name):
    file_id = ''.join(random.choice('0123456789') for _ in range(FILE_ID_LENGTH))
    file = storage.find_one({STORAGE_FILE_ID:file_id})
    if file is not None:
        raise ValueError("a file with this ID already exists")
    
    file_data = {
        STORAGE_FILE_ID:file_id,
        STORAGE_FILE_NAME:sanitize_filename(file_name),
        STORAGE_FILE_PASSWORD:hashlib.sha256(bytes(encryption_key, 'utf-8')).hexdigest(),
        STORAGE_FILE_FLAGGED: False,
        STORAGE_FILE_CIPHER_IV: cipher_iv
    }
    print(file_data)
    storage.insert_one(file_data)
    print('inserted file data into db')
    with open(FILE_SAVE_LOCATION + file_id +'.hashed', 'wb+') as file:
        file.write(data)
    
    return file_id

    
def encrypt_data(data, hex_key):
    #checks for key shit
    assert is_hex(hex_key), 'Invalid key hex'
    assert len(hex_key) == 32, 'Invalid key length!'
    #encrypt the data with the key 
    key = bytes.fromhex(hex_key)
    cipher = AES.new(key, AES.MODE_CBC)
    encrypted_data = cipher.encrypt(pad(data, AES.block_size))
    #we have to save the iv too to decrypt the file shits 
    return encrypted_data, cipher.iv.hex()


def decrypt_data(data, hex_key, hex_iv):
    assert is_hex(hex_key), 'Invalid key hex'
    assert len(hex_key) == 32, 'Invalid key length!'
    assert is_hex(hex_iv), 'Invalid iv hex'
    
    cipher_iv = bytes.fromhex(hex_iv)
    key = bytes.fromhex(hex_key)
    
    cipher = AES.new(key,AES.MODE_CBC,iv=cipher_iv)
    decrypted_bytes = unpad(cipher.decrypt(data),AES.block_size)
    
    return decrypted_bytes


def decrypt_file(file_id, encryption_key):
    file_data = storage.find_one({STORAGE_FILE_ID:file_id})
    if file_data is None:
        return ValueError("File cannot be none")
    hashed_key = hashlib.sha256(bytes(encryption_key, 'utf-8')).hexdigest()
    if not hashed_key == file_data[STORAGE_FILE_PASSWORD]:
        return ValueError("Invalid encryption Key")
    file_path = FILE_SAVE_LOCATION + file_id +'.hashed'
    if not os.path.exists(file_path):
        return FileNotFoundError("File could not be found")
    with open(file_path, 'rb') as file:
        data = file.read()
    
    decrypted_data = decrypt_data(data,encryption_key,file_data[STORAGE_FILE_CIPHER_IV])
    return decrypted_data


def encrypted_upload(data,encryption_key,api_key,file_name):
    if encryption_key == None:
        encryption_key = secrets.token_bytes(16).hex() #128 bit key 
        
    if len(encryption_key) != 32:
        return {'success':False, 'error':'encryption hex needs to be 32 characters in length', 'code': 400}
    
    if not is_hex(encryption_key):
        return {'success': False, 'error':'encryption key is not valid hex', 'code': 400}
    
    encrypted_data = encrypt_data(data,encryption_key)
    file_id = save_file(encrypted_data[0],encrypted_data[1],encryption_key,file_name)
    
    return {'success':True,"message":{'url':'http://localhost:5000/file/raw/'+str(file_id)+"/"+str(encryption_key)},'code':200}

def verify_upload(data, api_key):
    if not data:
        return False

    file_size = sys.getsizeof(data)
    file_size_to_mb = file_size / 1024 / 1024
    
    account = accounts.find_one({ACCOUNT_API_KEY:api_key})
    tier  = tiers.find_one({ACCOUNT_TIER_ID:account[ACCOUNT_TIER_ID]})
    print(file_size_to_mb)
    if int(file_size_to_mb) <= int(tier[TIER_LIMITS][TIER_MAX_UPLOAD]):
        return True
    return False

def redeem_license(account, license):
    now = int(time.time())
    if account[ACCOUNT_EXPIRY_FIELD] > now:
        expiry_time = int(account[ACCOUNT_EXPIRY_FIELD]) + int(license[LICENSE_TIME])
        accounts.update_one({ACCOUNT_API_KEY: account[ACCOUNT_API_KEY]}, {'$set': {ACCOUNT_EXPIRY_FIELD: expiry_time}})
        if account['tier-id'] != 0:
            keys.delete_one({LICENSE_KEY: license[LICENSE_KEY]})
    else:
        expiry_time = now + int(license[LICENSE_TIME])
        accounts.update_one({ACCOUNT_API_KEY: account[ACCOUNT_API_KEY]}, {'$set': {ACCOUNT_EXPIRY_FIELD: expiry_time}})
        #CHANGE THIS IMMEDIATELY THIS IS JUST FILLER THAT WILL KEEP THE KEY FROM GETTING DELETED DURING TESTING
        if account['tier-id'] != 0:
            keys.delete_one({LICENSE_KEY: license[LICENSE_KEY]})
    return expiry_time


def make_account(request, license):
    ip_address = process_ip(get_ip(request))
    api_key = "hashed_" + secrets.token_hex(API_KEY_TOKEN_HEX_LENGTH)
    account = {
        ACCOUNT_API_KEY: api_key,
        ACCOUNT_EXPIRY_FIELD: int(time.time()) + int(license[LICENSE_TIME]),
        ACCOUNT_IP_LIST: [str(ip_address)]
    }
    accounts.insert_one(account)
    keys.delete_one({LICENSE_KEY: license[LICENSE_KEY]})
    return {ACCOUNT_API_KEY: api_key}, 200


def anonymize_ip(ip_address):
    if '.' in ip_address:  # IPv4
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
    check_key = accounts.find_one({ACCOUNT_API_KEY: api_key})
    return check_key


def get_ip(request):
    if "Cf-Connecting-IP" in request.headers:
        ip_address = request.headers["Cf-Connecting-IP"]
    else:
        ip_address = request.remote_addr
    return ip_address


def verify_request(request, api_key, add=True, max_ips=ACCOUNT_MAX_IPS):
    if check_api_key(api_key) is None:
        return {'success': False, 'message': 'Invalid API Key header', 'code': 403}

    ip_address = get_ip(request)
    account = check_api_key(api_key)
    ip_list = account[ACCOUNT_IP_LIST]
    hashed_ip = process_ip(ip_address)

    if hashed_ip not in ip_list:
        if len(ip_list) < max_ips and add is True:
            ip_list.append(hashed_ip)
            accounts.update_one({ACCOUNT_API_KEY: api_key},
                                {"$push": {ACCOUNT_IP_LIST: hashed_ip}})
        else:
            return {'success': False, 'message': 'IP not authorized please turn off any VPN or Proxy service. Account sharing will lead to permanent termination of your account', 'code': 403}

    return {'success': True, 'message': '', 'code': 200}
