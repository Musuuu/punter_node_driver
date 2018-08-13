from multiprocessing import Process, Queue
from queue import Empty
from controller import Controller
from stepmotor import engine_main
from api import run
import time
import logging
import argparse

controller = None


def main():
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

    global controller
    engine_q = Queue()
    api_q = Queue()
    api_reader_p = Process(target=run, args=(api_q, ))
    engine_p = Process(target=engine_main, args=(engine_q, ))
    controller = Controller(api_q, engine_q)

    api_reader_p.start()
    engine_p.start()
    controller.api_config()

    while True:
        # Read new messages
        try:
            api_msg = api_q.get(block=False)
            if api_msg["dest"] != "controller":
                api_q.put(api_msg)
                api_msg = None
        except Empty:
            api_msg = None
        try:
            engine_msg = engine_q.get(block=False)
            if engine_msg["dest"] != "controller":
                engine_q.put(engine_msg)
                engine_msg = None
        except Empty:
            engine_msg = None
        time.sleep(0.1)

        if engine_msg or api_msg:
            logging.info("engine:{}".format(engine_msg))
            logging.info("api:{}\n\n".format(api_msg))

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


if __name__ == '__main__':
    main()
