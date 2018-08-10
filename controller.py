from transitions import Machine
from potentiometer import pot_get_position

api_q = None
engine_q = None


class Controller(object):
    states = ["INIT", "STILL", "ERROR", "MOVING"]
    transitions = [
        {"trigger": "api_config", "source": "INIT", "dest": "STILL", "before": "setup_environment"},
        {"trigger": "api_init", "source": "STILL", "dest": "INIT", "after": "api_config"},
        {"trigger": "api_move", "source": "STILL", "dest": "MOVING", "conditions": "correct_inputs",
         "after": "engine_move"},
        {"trigger": "api_move", "source": "STILL", "dest": "ERROR", "unless": "correct_inputs",
         "after": "handle_error"},
        {"trigger": "api_error", "source": "STILL", "dest": "ERROR", "after": "handle_error"},
        {"trigger": "engine_reached_destination", "source": "MOVING", "dest": "STILL",
         "before": "check_position"},
        {"trigger": "engine_fail", "source": "MOVING", "dest": "ERROR", "after": "handle_error"},
        {"trigger": "error_solved", "source": "ERROR", "dest": "STILL", "after": "tell_position"},
        {"trigger": "error_unsolved", "source": "ERROR", "dest": "INIT", "after": ["reconfig", "tell_position"]}
    ]

    def __init__(self, a_q, e_q):
        global api_q
        global engine_q

        api_q = a_q
        engine_q = e_q

        self.parameters = None
        self.prev_position = None
        self.error = None
        self.machine = Machine(model=self, states=Controller.states, transitions=Controller.transitions, initial='INIT')

    # Conditions

    def correct_inputs(self):
        """Check the inputs for the engine movement"""
        try:
            self.parameters = float(self.parameters)
        except (ValueError, TypeError):
            self.error = {
                "error_code": "0",
                "title": "harmless error",
                "detail": "Incorrect inputs"
            }
            return False
        return True

    # Actions

    def setup_environment(self):
        position = pot_get_position()
        self.prev_position = position
        self.parameters = None
        self.error = None
        self.tell_position()

    def engine_move(self):
        """Send the command to the engine"""
        angle = self.parameters
        error = False
        engine_q.put(
            {
                "id": "1",
                "command": "move",
                "parameter": angle
            }
        )

    @staticmethod
    def tell_position():
        """Send the current position from the potentiometer to the API"""
        position = pot_get_position()
        api_q.put(
            {
                "id": "1",
                "command": "update_pos",
                "parameter": position
            }
        )

    def check_position(self):
        """Check if everything went well"""
        position = pot_get_position()
        turn_angle = self.parameters

        if position != (self.prev_position + turn_angle):
            self.error = {
                "error_code": "0",
                "title": "harmless error",
                "detail": "After the movement, the position were not matched"
            }
            self.engine_fail()

    def api_print_error(self, engine_id, engine_error):
        """Output the error"""
        api_q.put(
            {
                "id": engine_id,
                "command": "print_error",
                "parameter": engine_error
            }
        )
        self.error = None

    def handle_error(self):
        """Try to solve the problem"""
        self.api_print_error(engine_id="1", engine_error=self.error)
        if self.error["error_code"] == "0":
            self.error_solved()
        else:
            self.error_unsolved()

    def reconfig(self):
        api_q.put(
            {
                "id": "1",
                "command": "init",
                "parameter": None
            }
        )
        self.tell_position()


