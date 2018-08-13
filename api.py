from flask import Flask, jsonify, request, abort, make_response, flash
from multiprocessing import Queue
from queue import Empty
from potentiometer import *
import requests
api = Flask(__name__)
engines = [
    {
        'type': u'stepper',
        'id': u'1',
        'description': u'Horizontal engine',
        'position': None,
        'state': u'INIT'
    }
]

queue = Queue()


@api.route('/')
def index():
    """First page of the project"""
    return "Welcome to the Turnantenna project"


@api.route('/api/v1.0/position', methods=['GET'])
def get_position():
    """Get the position of the engine"""
    if not request.json or not 'id' in request.json:
        abort(400)
    id = request.json['id']
    engine = engines[0]
    if id != '1':
        abort(404)
    if len(engine) == 0:
        abort(404)

    position = pot_get_position()
    engines[0]["position"] = position

    return jsonify({'position': engine['position']})


@api.route('/api/v1.0/init', methods=['POST'])
def init_engine():
    """Reset all the parameters of the engine"""
    if not request.json or not 'id' in request.json:
        abort(400)
    id = request.json['id']
    if id != '1':
        abort(404)

    descr = u'Horizontal engine'

    engine = {
        'type': u'stepper',
        'id': id,
        'description': descr,
        'position': None,
        'state': u'INIT'
    }

    queue.put(
        {
            'id': id,
            'dest': 'controller',
            'command': 'init',
            'parameter': None
        }
    )

    engines[0] = engine
    return jsonify({'engines': engines}), 201


@api.route('/api/v1.0/move', methods=['POST'])
def move():
    """Send a move request to the api queue, in order to make the engine move"""
    if not request.json or not 'id' in request.json:
        abort(400)

    id = request.json['id']
    angle = request.json['angle']
    if id == '1':
        engine = engines[0]
    else:
        abort(404)
    if type(angle) is not str:
        abort(400)
    if len(engines[0]) == 0:
        abort(404)

    queue.put(
        {
            'id': id,
            'dest': 'controller',
            'command': 'move',
            'parameter': angle
        }
    )

    return jsonify({'engines': engines}), 201


@api.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)


def api_reader(queue):
    logging.basicConfig(format='%(levelname)s - %(message)s')
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbose", action="count", default=0, help="Shows more levels of logging messages")
    args = parser.parse_args()
    logger = logging.getLogger()

    if args.verbose >= 2:
        logger.setLevel(logging.DEBUG)
    elif args.verbose >= 1:
        logger.setLevel(logging.INFO)
    else:
        logger.setLevel(logging.ERROR)

    while True:
        try:
            msg = queue.get(block=False)
            if msg["dest"] != "api":
                queue.put(msg)
                msg = None
        except Empty:
            msg = None
        time.sleep(0.1)

        if msg and msg["id"] == "1":
            command = msg["command"]
            parameter = msg["parameter"]
            if command == "init":
                requests.post('http://localhost:5000/api/v1.0/init', json={'id': '1'})
            if command == "print_error":
                print(parameter)
                # logging.error(parameter)


def run(q):
    global queue
    queue = q 
    api.run(debug=True)


if __name__ == '__main__':
    api.run(debug=True)
