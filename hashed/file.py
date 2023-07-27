from flask import Flask, render_template, request, Blueprint, send_file
from hashed.tools import *
from io import BytesIO

file = Blueprint("file",__name__,url_prefix='/file')


@file.route('/raw/<file_id>/<password>')
def raw(file_id, password):
    file = storage.find_one({STORAGE_FILE_ID:file_id})
    if not file:
        return {"error":"file not found in database"} ,404
    try:
        return send_file(BytesIO(decrypt_file(file_id, password)),as_attachment=False,download_name = file[STORAGE_FILE_NAME])
    except ValueError as e:
        return {"error":e},400
    