import pytest
import json
from flask import Flask, jsonify
from . import api
import requests


test_engines = [
    {
        "type": u"stepper",
        "id": u"1",
        "description": u"Horizontal engine",
        "position": None,
        "state": u"INIT"
    }
]


@pytest.fixture
def client(request):
    api = Flask(__name__)
    test_client = api.test_client()

    def teardown():
        pass

    request.addfinalizer(teardown)
    return test_client


def test_index_page():
    """Test the if the first page is correctly created"""
    assert (requests.get('http://localhost:5000/').text == "Welcome to the Turnantenna project")


def test_engine_creation():
    """Test the creation of a new engine"""
    assert (api.engines == test_engines)


def test_init_engine():
    """Test the creation of a new engine"""
    api.engines = {"spam": "eggs"}
    result = requests.post('http://localhost:5000/api/v1.0/init', json={'id': '1'})

    text = result.text
    output = json.loads(text)
    corrected_test_engines = {"engines": test_engines}

    assert json.dumps(output, sort_keys=True).replace("\\", "") == json.dumps(corrected_test_engines, sort_keys=True).replace("\\", "")

