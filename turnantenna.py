from multiprocessing import Process, Queue
from queue import Empty
from .controller import Controller
from .stepmotor import engine_main
from .api import api_reader

controller = None


def main():
    global controller
    engine_q = Queue()
    api_q = Queue()
    api_reader_p = Process(target=api_reader, args=(api_q, ))
    engine_p = Process(target=engine_main, args=(engine_q, ))
    controller = Controller(api_q, engine_q)

    api_reader_p.start()
    engine_p.start()
    controller.api_config()

    while True:
        # Read new messages
        error = None
        api_msg = None
        engine_msg = None

        try:
            api_msg = api_q.get(block=False)
        except Empty:
            pass
        try:
            engine_msg = engine_q.get(block=False)
        except Empty:
            pass

        if engine_msg and engine_msg["id"] == "1":
            if engine_msg["status"] == "reached_dest":
                controller.engine_reached_destination()

        # Unpack the API message
        if api_msg and api_msg["id"] == "1":
            api_command = api_msg["command"]
            api_parameter = api_msg["parameter"]

            if api_command == "move":
                controller.parameters = api_parameter
                controller.api_move()
            if api_command == "init":
                controller.api_init()
