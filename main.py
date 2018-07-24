from multiprocessing import Process, Queue, Value
from multiprocessing.Queue import Empty
# from queue import Queue
import time
from transitions import *
from stepmotor.py import Stepper, engine_main


class Controller(object):
    def __init__(self):
        self.states = ["INIT", "STILL", "ERROR", "MOVING"]
        self.transitions = [
            {"trigger": "api_config", "source": "INIT", "dest": "STILL", "before": "setup_environment"},
            {"trigger": "api_move", "source": "STILL", "dest": "MOVING",
             "conditions": "correct_inputs", "after": "engine_move"},
            {"trigger": "api_move", "source": "STILL", "dest": "ERROR", "unless": "correct_inputs"},
            {"trigger": "engine_reached_destination", "source": "MOVING", "dest": "STILL", "before": "pot_check_position"},
            {"trigger": "engine_fail", "source": "MOVING", "dest": "ERROR"},
            {"trigger": "error_solved", "source": "ERROR", "dest": "STILL", "after": "pot_check_position"},
            {"trigger": "error_unsolved", "source": "ERROR", "dest": "INIT", "after": "reconfig"}
        ]

        self.parameters = None
        self.prev_position = None
        self.error = None


    # Conditions

    def correct_inputs(self):
        """Check the inputs for the engine movement"""
        angle = self.parameters
        try:
            angle = float(angle)
        except (ValueError, TypeError):
            return False

        self.parameters = angle
        return True

    # Actions

    def setup_environment(self):
        self.prev_position = potentiometer_queue.get()
        ....

    def engine_move(self):
        """Send the command to the engine"""
        angle = self.parameters
        error = None

        if engine_status.value == "still":
            engine_q.put({"command": "move", "parameter": angle})
        else:
            error = "Engine is not ready to move"

        if error:
            self.engine_fail()

    def pot_check_position(self):
        """Check if everything went well"""
        position = potentiometer_queue.get()
        turn_angle = self.parameters
        wanted = self.prev_position + turn_angle

        if position != wanted:
            self.error = "Position were not matched"
            self.engine_fail()


def api_reader(queue, controller):
    """..."""


def potentiometer_reader(queue):
    """Read the position of the potentiometer"""
    position = queue.get()
    # ......

    return position


if __name__ == '__main__':
    controller = Controller()

    engine_q = Queue()
    api_q = Queue()
    potentiometer_q = Queue()

    engine_status = Value('u', None)

    api_reader_p = Process(target=api_reader, args=(api_q, controller,))
    potentiometer_reader_p = Process(target=potentiometer_reader, args=(potentiometer_q,))
    engine_p = Process(target=engine_main, args=(engine_q, engine_status))

    api_reader_p.start()
    potentiometer_reader_p.start()
    engine_p.start()


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

        if engine_msg["status"] == "reached_dest":
            controller.engine_reached_destination()

        # Unpack the API message
        if api_msg:
            api_command = api_msg["command"]
            api_parameter = api_msg["parameter"]

            if api_command == "MOVE":
                if engine_status.value == "still":
                    controller.parameters = api_parameter
                    controller.api_move()
                elif engine_status.value == "init":
                    error = "Engine not ready, try again"
                elif engine_status.value == "moving":
                    error = "Engine busy"
                else:
                    error = "Unknown engine status"

        if error:
            print(error)


