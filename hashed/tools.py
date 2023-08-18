import hashlib
import json
import os
import random
import secrets
import sys
import time
from ipaddress import ip_interface

from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad, unpad
from flask import Blueprint, Flask, render_template, request
from hashed.constants import *
from hashed.errors import Errors as errors
from pathvalidate import sanitize_filename
from pymongo import MongoClient

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
    #remove the last octet of ipv4 or ipv6 ip's
    ip_address = anonymize_ip(ip_address)
    #hash 256 em
    # you might want to add a salt but its anatomized ip's so who gives a shit
    hashed_ip = hashlib.sha256(bytes(ip_address, 'utf-8')).hexdigest()
    return hashed_ip
    
def save_file(data,cipher_iv,encryption_key,file_name):
    # create a random integer file ID
    file_id = ''.join(random.choice('0123456789') for _ in range(FILE_ID_LENGTH))
    # make sure the file id does'nt already exist in storage 
    file = storage.find_one({STORAGE_FILE_ID:file_id})
    if file is not None:
        raise ValueError("a file with this ID already exists")
    
    # create a database entry for the new file data 
    file_data = {
        STORAGE_FILE_ID:file_id,
        STORAGE_FILE_NAME:sanitize_filename(file_name),
        STORAGE_FILE_PASSWORD:hashlib.sha256(bytes(encryption_key, 'utf-8')).hexdigest(),
        STORAGE_FILE_FLAGGED: False,
        STORAGE_FILE_CIPHER_IV: cipher_iv
    }
    #put it in the db 
    storage.insert_one(file_data)
    print('inserted file data into db')
    #save the file as a .hashed file 
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
    #we have to save the iv too to decrypt the file shit 
    return encrypted_data, cipher.iv.hex()


def decrypt_data(data, hex_key, hex_iv):
    #check for the required data 
    assert is_hex(hex_key), 'Invalid key hex'
    assert len(hex_key) == 32, 'Invalid key length!'
    assert is_hex(hex_iv), 'Invalid iv hex'
    #load the cipher iv and key into bytes from string hex
    cipher_iv = bytes.fromhex(hex_iv)
    key = bytes.fromhex(hex_key)
    
    #create the cipher and decrypt the data 
    # TODO this move this to an encryption method that can be streamed more efficiently like CTR
    cipher = AES.new(key,AES.MODE_CBC,iv=cipher_iv)
    decrypted_bytes = unpad(cipher.decrypt(data),AES.block_size)
    
    return decrypted_bytes


def decrypt_file(file_id, encryption_key):
    #check to make sure the file actually exists 
    file_data = storage.find_one({STORAGE_FILE_ID:file_id})
    if file_data is None:
        return ValueError("File cannot be none")
    #hash the key that was provided 
    hashed_key = hashlib.sha256(bytes(encryption_key, 'utf-8')).hexdigest()
    #cross check the hashed key that was provided with the one stored in file data
    if not hashed_key == file_data[STORAGE_FILE_PASSWORD]:
        return ValueError("Invalid encryption Key")
    #check to make sure the file is actually stored on the server and not just on the db 
    file_path = FILE_SAVE_LOCATION + file_id +'.hashed'
    if not os.path.exists(file_path):
        return FileNotFoundError("File could not be found")
    # open the file with the encrypted bytes 
    with open(file_path, 'rb') as file:
        data = file.read()
    decrypted_data = decrypt_data(data,encryption_key,file_data[STORAGE_FILE_CIPHER_IV])
    return decrypted_data


def encrypted_upload(data,encryption_key,api_key,file_name):
    # if a key is not provided, generate one 
    if encryption_key == None:
        encryption_key = secrets.token_bytes(16).hex() #128 bit key 
    # TODO make the encryption key length customizable 
    if len(encryption_key) != 32:
        error = errors.invalid_encryption_hex_length()
        return {'success': False, 'message':error.json['message'], 'code': error.status_code}
    #checks if the encryption key is a valid hex string so we can convert it to bytes 
    if not is_hex(encryption_key):
        error = errors.invalid_encryption_hex()
        return {'success': False, 'message':error.json['message'], 'code': error.status_code}
   #encrypt and save the data snd get the file id 
    encrypted_data = encrypt_data(data,encryption_key)
    file_id = save_file(encrypted_data[0],encrypted_data[1],encryption_key,file_name)
    # return the raw file
    return {'success':True,"message":{'url':'http://localhost:5000/file/raw/'+str(file_id)+"/"+str(encryption_key)},'code':200}

def verify_upload(data, api_key):
    #check there is some kind of data to encrypt
    if  not data:
        return False

    file_size = sys.getsizeof(data)
    file_size_to_mb = file_size / 1024 / 1024
    #get the account and associated account tier 
    account = accounts.find_one({ACCOUNT_API_KEY:api_key})
    tier  = tiers.find_one({ACCOUNT_TIER_ID:account[ACCOUNT_TIER_ID]})
    # check that the data is not larger than tier limit
    if int(file_size_to_mb) <= int(tier[TIER_LIMITS][TIER_MAX_UPLOAD]):
        return True
    return False

def redeem_license(account, license):
    #get the current time 
    now = int(time.time())
    #see if the the account is expired 
    if account[ACCOUNT_EXPIRY_FIELD] > now:
        # if the current license is'nt expired add the license time to the current expiry time 
        expiry_time = int(account[ACCOUNT_EXPIRY_FIELD]) + int(license[LICENSE_TIME])
        accounts.update_one({ACCOUNT_API_KEY: account[ACCOUNT_API_KEY]}, {'$set': {ACCOUNT_EXPIRY_FIELD: expiry_time}})
        #FIXME move the test tier id to constants  
        #the reason this even exists is for unit tests so it does'nt the test key
        if account['tier-id'] != 0:
            #delete the key once its redeemed 
            keys.delete_one({LICENSE_KEY: license[LICENSE_KEY]})
    else:
        #if the current license is expired or non existent add the license time to the current time
        expiry_time = now + int(license[LICENSE_TIME])
        accounts.update_one({ACCOUNT_API_KEY: account[ACCOUNT_API_KEY]}, {'$set': {ACCOUNT_EXPIRY_FIELD: expiry_time}})
        #FIXME move the test tier id to constants  
        #the reason this even exists is for unit tests so it does'nt delete the test key
        if account['tier-id'] != 0:
            keys.delete_one({LICENSE_KEY: license[LICENSE_KEY]})
    #return the unix epoch expiry time 
    return expiry_time


def make_account(request, license):
    # anatomize and hash ip 
    ip_address = process_ip(get_ip(request))
    # make a random api key
    api_key = "hashed_" + secrets.token_hex(API_KEY_TOKEN_HEX_LENGTH)
    #TODO make a check to see if this api key already exists 
    #fill in the account 
    account = {
        ACCOUNT_API_KEY: api_key,
        ACCOUNT_EXPIRY_FIELD: int(time.time()) + int(license[LICENSE_TIME]),
        ACCOUNT_IP_LIST: [str(ip_address)]
    }
    #add the account to the db and then delete the license key 
    accounts.insert_one(account)
    keys.delete_one({LICENSE_KEY: license[LICENSE_KEY]})
    return {'message':{ACCOUNT_API_KEY: api_key}}, 200


def anonymize_ip(ip_address):
    if '.' in ip_address:  # IPv4
        ip_parts = ip_address.split('.')
        #set the last part of the ip to 0
        ip_parts[-1] = '0'
        anonymized_ip = '.'.join(ip_parts)
    elif ':' in ip_address:  # IPv6
        # add /64 to an ipv6 this could be better
        # TODO better anonymization for ipv6
        ip = ip_interface(ip_address + '/64')
        anonymized_ip = str(ip.network.network_address)
    else:
        raise ValueError(f"Invalid IP address: {ip_address}")
    return anonymized_ip


def check_api_key(api_key):
    #TODO this function seems useless but its heavily utilized
    #maybe add more error handling
    check_key = accounts.find_one({ACCOUNT_API_KEY: api_key})
    return check_key


def get_ip(request):
    #gets the ip from th request object 
    if "Cf-Connecting-IP" in request.headers:
        ip_address = request.headers["Cf-Connecting-IP"]
    else:
        ip_address = request.remote_addr
    return ip_address


def verify_request(request, api_key, add=True, max_ips=ACCOUNT_MAX_IPS):
    #check the api key
    if check_api_key(api_key) is None:
        error = errors.api_key_invalid()
        return {'success': False, 'message': error.json['message'], 'code': error.status_code}

    ip_address = get_ip(request)
    account = check_api_key(api_key)
    ip_list = account[ACCOUNT_IP_LIST]
    hashed_ip = process_ip(ip_address)
    # check if the current ip is in the list of historical access ip's
    if hashed_ip not in ip_list:
        #check to see if the ip limit has been reached and if we should add another account
        if len(ip_list) < max_ips and add is True:
            #if so we add the hashed ip to the ip list then update the db 
            ip_list.append(hashed_ip)
            accounts.update_one({ACCOUNT_API_KEY: api_key},
                                {"$push": {ACCOUNT_IP_LIST: hashed_ip}})
        else:
            error = errors.ip_unauthorized()
            return {'success': False, 'message': error.json['message'], 'code': error.status_code}
                    
    return {'success': True, 'message': '', 'code': 200}
