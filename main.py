from multiprocessing import Process
from queue import Queue
import time
from transitions import *
from stepmotor.py import Stepper


class Controller(object):
    def __init__(self):
        self.states = ["INIT", "STILL", "ERROR", "MOVING"]
        self.transitions = [
            {"trigger": "config", "source": "INIT", "dest": "STILL"},
            {"trigger": "api_move", "source": "STILL", "dest": "MOVING",
             "conditions": "correct_inputs", "after": "engine_move"},
            {"trigger": "api_move", "source": "STILL", "dest": "ERROR", "unless": "correct_inputs"},
            {"trigger": "reached_destination", "source": "MOVING", "dest": "STILL", "after": "check_position"},
            {"trigger": "fail", "source": "MOVING", "dest": "ERROR"},
            {"trigger": "error_solved", "source": "ERROR", "dest": "STILL"},
            {"trigger": "error_unsolved", "source": "ERROR", "dest": "INIT", "after": "reconfig"}
        ]

        self.parameters = None
        self.engine_pointer = None

    def config(self):
        """Initialise the environment"""
        return True

    def api_move(self):
        """Receive a movement command from the API"""
        return True

    def correct_inputs(self):
        """Check the inputs for the engine movement"""
        angle = self.parameters
        try:
            angle = float(angle)
        except (ValueError, TypeError):
            return False

        self.parameters = angle
        return True

    def engine_move(self):
        """Send the command to the engine"""
        angle = self.parameters
        motor = self.engine_pointer
        error = None

        motor.move(angle)

        if error is None:
            self.to_STILL()
        else:
            self.to_ERROR()


def api_reader(queue, controller):
    """Read from the api queue"""
    while True:
        # Read the message
        msg = queue.get()

        # Unpack the message
        command = msg[0]
        parameters = msg[1]
        if command == "move":
            angle = parameters
            controller.parameters = angle
            controller.api_move()
            break


def engine_reader(queue):
    """Read from the engine queue"""


def writer(count, queue):
    ## Write to the queue
    for ii in xrange(0, count):
        queue.put(ii)             # Write 'count' numbers into the queue
    queue.put('DONE')


if __name__ == '__main__':
    engine_queue = Queue()
    engine = Stepper(0, 1, 2, 3)

    controller = Controller()
    controller.engine_pointer = engine

    reader_p = Process(target=reader, args=((engine_queue),))
#     for count in [10**4, 10**5, 10**6]:
#         queue = Queue()   # reader() reads from queue
#                           # writer() writes to queue
#         reader_p = Process(target=reader, args=((queue),))
#         reader_p.daemon = True
#         reader_p.start()        # Launch reader() as a separate python process
#
#         _start = time.time()
#         writer(count, queue)    # Send a lot of stuff to reader()
#         reader_p.join()         # Wait for the reader to finish
#         print "Sending %s numbers to Queue() took %s seconds" % (count,
#             (time.time() - _start))
