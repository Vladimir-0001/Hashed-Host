from flask import Flask, render_template, request, Blueprint, send_file
from hashed.tools import *
from hashed.errors import Errors as errors
from io import BytesIO

file = Blueprint("file",__name__,url_prefix='/file')


@file.route('/raw/<file_id>/<password>')
def raw(file_id, password):
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
    