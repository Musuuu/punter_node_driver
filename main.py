from multiprocessing import Process, Queue, Value
from multiprocessing.Queue import Empty
# from queue import Queue
import time
from transitions import *
from stepmotor.py import Stepper, engine_main
import logging


class Controller(object):
    def __init__(self):
        self.states = ["INIT", "STILL", "ERROR", "MOVING"]
        self.transitions = [
            {"trigger": "api_config", "source": "INIT", "dest": "STILL", "before": "setup_environment"},
            {"trigger": "api_ask_position", "source": "STILL", "dest": "STILL", "before": "pot_tell_position"},
            {"trigger": "api_move", "source": "STILL", "dest": "MOVING", "conditions": "correct_inputs",
             "after": "engine_move"},
            {"trigger": "api_move", "source": "STILL", "dest": "ERROR", "unless": "correct_inputs",
             "after": "handle_error"},
            {"trigger": "api_error", "source": "STILL", "dest": "ERROR", "after": "handle_error"}
            {"trigger": "engine_reached_destination", "source": "MOVING", "dest": "STILL",
             "before": "pot_check_position"},
            {"trigger": "engine_fail", "source": "MOVING", "dest": "ERROR", "after": "handle_error"},
            {"trigger": "error_solved", "source": "ERROR", "dest": "STILL", "after": "pot_tell_position"},
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
            self.error = "Incorrect inputs"
            return False

        self.parameters = angle
        return True

    # Actions

    def setup_environment(self):
        position = potentiometer_queue.get()
        self.prev_position = position
        api_q.put({"position": position})
        ....

    def engine_move(self):
        """Send the command to the engine"""
        angle = self.parameters
        error = False

        if engine_status.value == "still":
            engine_q.put({"command": "move", "parameter": angle})
        else:
            error = True

        if error:
            self.error = "Trying to control the engine when it's busy"
            self.engine_fail()

    @staticmethod
    def pot_get_position(self):
        try:
            position = potentiometer_queue.get(block=False)
        except Empty:
            ...

        return position

    def pot_tell_position(self):
        """Send the current position from the potentiometer to the API"""
        position = self.pot_get_position()
        api_q.put({"position": position})

    def pot_check_position(self):
        """Check if everything went well"""
        position = self.pot_get_position()
        turn_angle = self.parameters
        wanted = self.prev_position + turn_angle

        if position != wanted:
            self.error = "After the movement, the position were not matched"
            self.engine_fail()

    def api_print_error(self, error):
        """Output the error"""
        api_q.put({"error": error})
        self.error_solved()

    def handle_error(self):
        """Try to solve the problem"""
        new_error = self.error
        fixable_errors = ["Incorrect inputs",
                          "Trying to control the engine when it's busy",
                          "After the movement, the position were not matched",
                          "Engine not ready, try again"]

        if new_error in fixable_errors:
            self.api_print_error(new_error)
        else:
            self.error_unsolved()



def api_reader(queue, controller):
    """..."""


def potentiometer_reader(queue):
    """Read the position of the potentiometer"""
    position = self.pot_get_position()
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
                    controller.error = "Engine not ready, try again"
                    controller.api_error()
                elif engine_status.value == "moving":
                    controller.error = "Trying to control the engine when it's busy"
                    controller.api_error()
                else:
                    controller.error = "Unknown engine status"
                    controller.api_error()
