from flask import jsonify

class Errors():
    """
    A collection of static methods for generating standard error responses.
    Each method corresponds to a specific type of error and returns a response
    with an appropriate HTTP status code and message.
    """
    @staticmethod
    def no_api_key(code = 400):
        #error 
        response = jsonify({'message': 'Error: API Key header is blank. Please provide a valid API Key.'})
        response.status_code = code
        return response
    
    @staticmethod
    def api_key_invalid(code = 400):
        response = jsonify({'message': 'Error: API key header is invalid. Please check your API key and try again.'})
        response.status_code = code
        return response
    
    @staticmethod
    def no_filename(code = 400):
        response = jsonify({'message': 'Error: file name header is blank. Please provide a file name.'})
        response.status_code = code
        return response
     
    @staticmethod
    def verification_error(verification_result):
        response = jsonify({'message': verification_result['message']})
        response.status_code = verification_result["code"]
        return response
    
    @staticmethod
    def ip_unauthorized(code =403):
        response = jsonify({'message':'Access denied: Your IP address seems to be coming from a VPN or Proxy service. Please disable these services and try again. IMPORTANT: Violation of our Terms of Service, including account sharing, will result in immediate and permanent termination of your account.'})
        response.status_code = code
        return response
    
    @staticmethod 
    def no_activation_key(code = 400):
        response = jsonify({'message': 'Error: Activation key data is blank. Please provide a valid activation key.'})
        response.status_code = code
        return response
    
    @staticmethod 
    def invalid_activation_key(code = 400):
        response = jsonify({'message': 'Error: Activation key data is invalid. Please provide a valid activation key.'})
        response.status_code = code
        return response

    @staticmethod 
    def invalid_encryption_hex(code = 400):
        response = jsonify({'message': 'Error: Encryption key data is invalid. Please provide a valid hex.'})
        response.status_code = code
        return response

    @staticmethod 
    def invalid_encryption_hex_length(code = 400):
        response = jsonify({'message': 'Error: Encryption key data needs to be 32 characters in length. Please provide a valid hex'})
        response.status_code = code
        return response


    @staticmethod 
    def filesize_over_tier_max(code = 413):
        response = jsonify({'message': 'Error: Uploaded File data empty or size over the max file size according to your tier. Upgrade your account or compress the file'})
        response.status_code = code
        return response
    
    @staticmethod
    def file_not_found(code = 404):
        response = jsonify({'message':'Error: File not found'})
        response.status_code = code
        return response 
    