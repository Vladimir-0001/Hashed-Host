from io import BytesIO

from flask import Blueprint, Flask, render_template, request, send_file
from hashed.errors import Errors as errors
from hashed.tools import *

file = Blueprint("file",__name__,url_prefix='/file')


@file.route('/raw/<file_id>/<password>')
def raw(file_id, password):
    """return a raw, decrypted version of a file 

    Args:
        file_id (str): the file id of the file
        password (str): the aes password in hex format 

    Returns:
        file :  BytesIO decrypted file 
    """
    #search for the file in the db 
    file = storage.find_one({STORAGE_FILE_ID:file_id})
    if not file:
        return errors.file_not_found()
    try:
        # Decrypt the file and send it. The BytesIO function is used to read the 
        # decrypted file into memory, and send_file is used to send this as a response.
        return send_file(BytesIO(decrypt_file(file_id, password)),as_attachment=False,download_name = file[STORAGE_FILE_NAME])
    except ValueError as e:
        return {"message":"Error "+e}, 400
    