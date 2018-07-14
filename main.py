from multiprocessing import Process, Queue
# from queue import Queue
import time
from transitions import *
from stepmotor.py import Stepper, engine_main


class Controller(object):
    def __init__(self):
        self.states = ["INIT", "STILL", "ERROR", "MOVING"]
        self.transitions = [
            {"trigger": "config", "source": "INIT", "dest": "STILL", "before": "setup_environment"},
            {"trigger": "api_move", "source": "STILL", "dest": "MOVING",
             "conditions": "correct_inputs", "after": "engine_move"},
            {"trigger": "api_move", "source": "STILL", "dest": "ERROR", "unless": "correct_inputs"},
            # {"trigger": "api_stop", "source": "MOVING", "dest": "STILL", "after": "engine_stop"},
            {"trigger": "reached_destination", "source": "MOVING", "dest": "STILL", "before": "check_position",
             "after": "engine_stop"},
            {"trigger": "fail", "source": "MOVING", "dest": "ERROR"},
            {"trigger": "error_solved", "source": "ERROR", "dest": "STILL"},
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

        engine_q.put(["move", angle])

        # ... control errors in some way

        if error is None:
            self.reached_destination()
        else:
            self.fail()

    def check_position(self):
        """Check if everything went well"""
        position = potentiometer_queue.get()
        turn_angle = self.parameters
        wanted = self.prev_position + turn_angle

        if position != wanted:
            self.error = "Position were not matched"
            self.fail()

    # @staticmethod
    # def engine_stop(self):
    #     """Set the engine OFF"""
    #     engine_q.push("still", )


def api_reader(queue, controller):
    """..."""


def potentiometer_reader(queue):
    """Read the position of the potentiometer"""
    position = queue.get()
    # ......

    return position


if __name__ == '__main__':
    controller = Controller()

    engine_q, api_q, potentiometer_q = Queue()
    api_reader_p = Process(target=api_reader, args=(api_q, controller,))
    potentiometer_reader_p = Process(target=potentiometer_reader, args=(potentiometer_q,))
    engine_p = Process(target=engine_main, args=(engine_q,))

    api_reader_p.start()
    potentiometer_reader_p.start()
    engine_p.start()

    while True:
        # Read new messages
        error = None
        msg = api_q.get()                               # from API
        engine_status = engine_q.get()[0]               # from Engine

        # Unpack the API message
        command = msg[0].upper()
        parameters = msg[1]

        if command == "MOVE":
            if engine_status == "still":
                angle = parameters
                controller.parameters = angle
                controller.api_move()
            elif engine_status == "init":
                error = "Engine not ready, try again"
            elif engine_status == "moving":
                error = "Engine busy"
            else:
                error = "Unknown engine status"

        # elif command == "STOP":                   CAN'T WORK!!  because api_stop trigger entine _stop that write "stop" in the engine queue,
        #     controller.api_stop()                     but the engine couldn't read the queue until it finishes the movement! It keep going!

        if error:
            print(error)


