# this file keeps constants for multiple modules in hashed including account security settings, database keys, and misc settings 
# the goal is to eventually move this to an env its just easier for early development to just have it all here 

FILE_SAVE_LOCATION = 'C:\\Users\\creck\\OneDrive\\Documents\\Hashed Host\\Hashed-Host\\Files\\'

# DATABASE KEYS
ACCOUNT_IP_LIST = 'ip-list'
ACCOUNT_API_KEY = 'api-key'
ACCOUNT_TIER_ID = 'tier-id'
ACCOUNT_EXPIRY_FIELD = "expiry"

STORAGE_FILE_ID = 'file-id'
STORAGE_FILE_NAME = 'file-name'
STORAGE_FILE_CIPHER_IV = 'cipher-iv'
STORAGE_FILE_PASSWORD = 'password'
STORAGE_FILE_FLAGGED = 'flagged'

LICENSE_KEY = 'license-key'
LICENSE_TIME = 'time'

TIER_LIMITS = 'limits'
TIER_MAX_UPLOAD = 'max-upload-mb'

# Account Settings
API_KEY_TOKEN_HEX_LENGTH = 16 #length of the api key + "hashed_{hex}"
ACCOUNT_MAX_IPS = 3 #the max number of ip's per account (Hard Limit)
FILE_ID_LENGTH = 9 #length of the random file_id 


# ENDPOINT FIELDS

API_KEY_FIELD = 'api-key' #global api key header for all requests 

# UPLOAD FIELDS
UPLOAD_FILE_NAME_FIELD = 'file-name' 
ENCRYPTION_KEY_FIELD = 'encryption-key'

# REDEEM FIELDS
ACTIVATION_KEY = 'key'