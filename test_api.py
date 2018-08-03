from . import api
import json
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


def test_index_page():
    """Test the if the first page is correctly created"""
    assert requests.get('http://localhost:5000/').text == "Welcome to the Turnantenna project"


def test_init_engine():
    """Test the initialisation of a new engine"""
    # # The two variables are equivalent                NOT WORKING CODE: api.engines doesn't make changes on the
    # assert api.engines == test_engines                                  engine variable in the flask server
    # api.engines = {"spam": "eggs"}
    #
    # # Test the effective change in the values
    # assert api.engines != test_engines
    result = requests.post('http://localhost:5000/api/v1.0/init', json={'id': '1'}).text
    json_result = json.loads(result)
    corrected_test_engines = {"engines": test_engines}

    # The json values are equivalent again
    assert json.dumps(json_result, sort_keys=True).replace("\\", "") \
           == json.dumps(corrected_test_engines, sort_keys=True).replace("\\", "")


def test_wrong_init_engine():
    """Test the error message for a bad initialization"""
    # Forget the required engine 'id'
    result = requests.post('http://localhost:5000/api/v1.0/init')
    assert result.status_code == 400

    # Specify a bad 'id' value
    result = requests.post('http://localhost:5000/api/v1.0/init', json={'id': 'foo'})
    assert result.status_code == 400

    # Specify a good 'id' value, but it is out of range
    result = requests.post('http://localhost:5000/api/v1.0/init', json={'id': '3'})
    assert result.status_code == 400

    # Specify a bad 'id' type
    result = requests.post('http://localhost:5000/api/v1.0/init', json={'id': 1})
    assert result.status_code == 400


def test_check_the_initial_position():
    """Test if the initial engine respond correctly"""
    # Correct request
    result = requests.get('http://localhost:5000/api/v1.0/position', json={'id': '1'}).text
    json_result = json.loads(result)
    assert json_result == {'position': None}


def test_wrong_check_of_initial_position():
    """Test if the initial engine respond correctly to the errors"""
    # Forget the required engine 'id'
    result = requests.get('http://localhost:5000/api/v1.0/position')
    assert result.status_code == 400

    # Specify a bad 'id' value
    result = requests.get('http://localhost:5000/api/v1.0/position', json={'id': 'foo'})
    assert result.status_code == 400

    # Specify a good 'id' value, but it is out of range
    result = requests.get('http://localhost:5000/api/v1.0/position', json={'id': '3'})
    assert result.status_code == 400
    print(api.engines)


def test_move():
    """Test if the 'move' command works well"""
    # Correct request
    result = requests.post('http://localhost:5000/api/v1.0/move', json={'id': '1', 'angle': '100'}).text
    json_result = json.loads(result)
    assert json_result['engines'][0]['position'] == '100'


def test_wrong_move():
    """Test if the 'move' command handles correctly bad requests"""
    # Forget the request json
    result = requests.post('http://localhost:5000/api/v1.0/move')
    assert result.status_code == 400

    # Specify a bad id value
    result = requests.post('http://localhost:5000/api/v1.0/move', json={'id': 'foo', 'angle': '100'})
    assert result.status_code == 404

    # Specify a bad angle value
    result = requests.post('http://localhost:5000/api/v1.0/move', json={'id': '1', 'angle': 100})
    assert result.status_code == 400