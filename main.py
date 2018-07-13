from multiprocessing import Process, Queue
# from queue import Queue
import time
from transitions import *
from stepmotor.py import Stepper


class Controller(object):
    def __init__(self):
        self.states = ["INIT", "STILL", "ERROR", "MOVING"]
        self.transitions = [
            {"trigger": "config", "source": "INIT", "dest": "STILL", "before": "setup_environment"},
            {"trigger": "api_move", "source": "STILL", "dest": "MOVING",
             "conditions": "correct_inputs", "after": "engine_move"},
            {"trigger": "api_move", "source": "STILL", "dest": "ERROR", "unless": "correct_inputs"},
            {"trigger": "api_stop", "source": "MOVING", "dest": "STILL", "after": "engine_stop"},
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
        self.prev_position = self.potentiometer_queue.get()
        ....

    def engine_move(self):
        """Send the command to the engine"""
        angle = self.parameters
        motor = self.engine_pointer
        error = None

        motor.move(angle)

        if error is None:
            self.reached_destination()
        else:
            self.fail()

    def check_position(self):
        """Check if everything went well"""
        position = self.potentiometer_queue.get()
        turn_angle = self.parameters
        wanted = self.prev_position + turn_angle

        if position != wanted:
            raise EnvironmentError("position was not matched")





def api_reader(queue, controller):
    """..."""


def potentiometer_reader(queue):
    """Read the position of the potentiometer"""
    position = queue.get()
    # ......

    return position

def engine_driver(queue):
    """Give commands to the engine queue"""


def writer(count, queue):
    ## Write to the queue
    for ii in xrange(0, count):
        queue.put(ii)             # Write 'count' numbers into the queue
    queue.put('DONE')


if __name__ == '__main__':
    engine_q, api_q, potentiometer_q = Queue()

    api_reader_p = Process(target=api_reader, args=(api_q, controller,))
    potentiometer_reader_p = Process(target=potentiometer_reader, args=(potentiometer_q,))
    engine_driver_p = Process(target=engine_driver, args=(engine_q,))

    api_reader_p.start()
    potentiometer_reader_p.start()

    engine = Stepper(0, 1, 2, 3)
    controller = Controller()
    controller.engine_pointer = engine
    controller.potentiometer_queue = potentiometer_q

    while True:
        # Read the message
        msg = api_q.get()

        # Unpack the message
        command = msg[0].upper()
        parameters = msg[1]

        if command == "MOVE":
            angle = parameters
            controller.parameters = angle
            controller.api_move()

        elif command == "STOP":
            controller.api_stop()
