import unittest
from mock import patch
from .turnantenna import *
from multiprocessing import Process
import requests
import json

main_p = Process(target=main)
test_engines = [
    {
        "type": u"stepper",
        "id": u"1",
        "description": u"Horizontal engine",
        "position": None,
        "state": u"INIT"
    }
]


def stub_wiringPiSetup():
    """Simulates the correct initialization of the board"""
    return True


class PrimesTestCase (unittest.TestCase):

    @patch('wiringpi.wiringPiSetup', stub_wiringPiSetup)
    def test_starting_flask_server(self):
        """Tests if the flask server responds"""
        main_p.start()
        # Test the initial page
        assert requests.get('http://localhost:5000/').text == "Welcome to the Turnantenna project"

        # Test the initial position
        result = requests.post('http://localhost:5000/api/v1.0/init', json={'id': '1'}).text
        json_result = json.loads(result)
        corrected_test_engines = {"engines": test_engines}
        assert json.dumps(json_result, sort_keys=True).replace("\\", "") \
            == json.dumps(corrected_test_engines, sort_keys=True).replace("\\", "")

        main_p.terminate()
