from hashed.file import file

import pytest
import json
from flask import Flask
from hashed.file import file
from hashed.constants import *

app = Flask(__name__)
app.register_blueprint(file)

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client
        