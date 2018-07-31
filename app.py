from flask import Flask, jsonify, request, abort, make_response
from multiprocessing import Queue


app = Flask(__name__)

queue = Queue()
engines = [
    {}
]


@app.route('/')
def index():
    return "Welcome to the Turnantenna project"


@app.route('/api/v1.0/position', methods=['GET'])
def get_position():
    engine = engines[0]
    if len(engine) == 0:
        abort(404)
    return jsonify({'position': engine['position']})


@app.route('/api/v1.0/create_engine', methods=['POST'])
def create_engine():
    engine = engines[0]
    if len(engine) != 0:
        abort(make_response("Already existent engine. Try to initialize it instead\n", 409))
    engine = {
        'id': 1,
        'description': 'Horizontal engine',
        'position': None,
        'state': u'INIT'
    }
    engines[0] = engine
    return jsonify({'engines': engines}), 201


@app.route('/api/v1.0/init', methods=['POST'])
def init_engine():
    if not request.json or not 'id' in request.json or request.json['id'] != 1:
        abort(400)

    descr = 'Horizontal engine'

    engine = {
        'id': request.json['id'],
        'description': descr,
        'position': None,
        'state': u'INIT'
    }
    engines[0] = engine
    return jsonify({'engines': engines}), 201


@app.route('/api/v1.0/move', methods=['POST'])
def move():
    id = request.json['id']
    angle = request.json['angle']

    if id == 1:
        engine = engines[0]
    else:
        abort(404)
    if len(engine) == 0:
        abort(404)
    if not request.json:
        abort(400)
    if type(angle) is not int:
        abort(400)

    queue.put(
        {
            'engine_id': id,
            'command': 'move',
            'parameter': angle
        }
    )

    # just for test
    engine['position'] = angle
    # will not be pushed

    return jsonify({'engines': engines}), 201


@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)


def api_main(queue):
    pass


if __name__ == '__main__':
    app.run(debug=True)
