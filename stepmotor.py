import wiringpi
import time
import datetime
from math import sqrt as sqrt
import logging
from queue import Empty
from mock import patch
import argparse
import logging


def stub_wiringPiSetup():
    """Simulates the correct initialization of the board"""
    return True


class ConfigurationError(Exception):
    """Raise when the user tries to configure the system in a bad way"""


class Stepper:
    @patch('wiringpi.wiringPiSetup', stub_wiringPiSetup)
    def __init__(self, i1, i2, i3, i4, debug=False):
        wiringpi.wiringPiSetup()
        self.inp = [None, None, None, None]
        self.check_pins(i1, i2, i3, i4)
        wiringpi.pinMode(i1, 1)
        wiringpi.pinMode(i2, 1)
        wiringpi.pinMode(i3, 1)
        wiringpi.pinMode(i4, 1)
        wiringpi.digitalWrite(i1, 0)
        wiringpi.digitalWrite(i2, 0)
        wiringpi.digitalWrite(i3, 0)
        wiringpi.digitalWrite(i4, 0)
        self.actual_num_step = 0
        self.half = [[1, 0, 0, 1],  # step 0
                     [1, 0, 0, 0],  # step 1
                     [1, 1, 0, 0],  # step 2
                     [0, 1, 0, 0],  # step 3
                     [0, 1, 1, 0],  # step 4
                     [0, 0, 1, 0],  # step 5
                     [0, 0, 1, 1],  # step 6
                     [0, 0, 0, 1]]  # step 7
        self.direction = None
        self.acc_or_dec = None
        self.actual_speed = 0

        # Hardware constrains
        self.acceleration_factor = 1
        self.MIN_SPEED = 10    # Steps/sec
        self.MAX_SPEED = 500  # Steps/sec

        # Debugging variables
        self.debug = False
        if debug:
            self.debug = True
            self.old_speed = self.actual_speed
            self.old_num_step = self.actual_num_step
            self.max_speed_reached = 0
            self.t_start_deceleration = 0
            self.step_start_deceleration = 0
            self.dec_steps = 0
            self.t = 0
            self.absolute_time = 0
            self.real_time_acceleration = 0
            self.real_time_constant_speed = 0
            self.real_time_deceleration = 0

            # outputs ['YYYY-MM-DD', 'hh:mm:ss.milliseconds']
            date = str(datetime.datetime.now()).split(" ")
            actual_time = date[1].split(".")
            # extract YYY-MM-DD
            day = date[0]
            # extract hh:mm:ss
            hour = actual_time[0]

            filepath = "debugfiles/" + "debugging_" + day + "_" + hour + ".dat"
            f = open(filepath, "w+")
            f.write("")
            f.close()
            self.debug_filepath = filepath

            # Control conditions
            self.movement_control_passed = True
            self.stepper_max_speed_is_acceptable = True
            self.stepper_acceleration_is_correct = True
            self.stepper_total_step_number_is_correct = False

    def _convert_angle_to_steps(self, angle):
        """Receive an angle and return a number of steps"""
        tau = self.reducer_index
        r = self.engine_step_per_revolution

        steps = int(round(angle / 360 * r * tau))

        return steps

    def _init_par(self):
        """Initialize parameters"""
        self.old_speed = self.actual_speed
        self.old_num_step = self.actual_num_step
        self.max_speed_reached = 0
        self.t_start_deceleration = 0
        self.step_start_deceleration = 0
        self.dec_steps = 0
        self.t = 0
        self.absolute_time = 0
        self.real_time_acceleration = 0
        self.real_time_constant_speed = 0
        self.real_time_deceleration = 0

    def _movement_did_well(self):
        """Returns true if the movement interval did not raise errors"""
        passed = self.movement_control_passed
        self.movement_control_passed = True

        if passed:
            return True
        else:
            return False

    def check_pins(self, i1, i2, i3, i4):
        """Control if selected pin numbers are valid"""
        try:
            int(i1)
        except ValueError:
            raise ConfigurationError("The first pin ID is not an integer: {}".format(i1))
        try:
            int(i2)
        except ValueError:
            raise ConfigurationError("The second pin ID is not an integer: {}".format(i2))
        try:
            int(i3)
        except ValueError:
            raise ConfigurationError("The third pin ID is not an integer: {}".format(i3))
        try:
            int(i4)
        except ValueError:
            raise ConfigurationError("The fourth pin ID is not an integer: {}".format(i4))

        input_pins = [int(i1), int(i2), int(i3), int(i4)]

        # wiringpi library supports only 17 GPIO pins. See the official documentation for more informations
        for i in range(len(input_pins)):
            if input_pins[i] not in list(range(0, 17)):
                raise ConfigurationError("The pin number "
                                         "{} does not exist. Valid pin numbers are from 0 to 16.".format(i+1))

        # control if there is not a single pin used two times
        if len(set(input_pins)) != 4:
            raise ConfigurationError("There are two different pins with the same number. Pins must have unique numbers")

        self.inp = input_pins

    def _corrected_speed(self, speed):
        if speed >= 0:
            self.direction = 1
        if speed < 0:
            self.direction = -1
            speed = abs(speed)

            # Apply hardware's speed limits
        if speed > self.MAX_SPEED:
            speed = self.MAX_SPEED
        if speed < self.MIN_SPEED:
            speed = self.MIN_SPEED
        return speed

    @staticmethod
    def _acceleration_steps(step_num, speed, acc_factor):
        # Number of steps of the speed changing intervals
        acceleration_steps = int(speed ** 2 / 2 / acc_factor)

        # Control if the acceleration phases are not too long
        if acceleration_steps > (step_num / 2):
            acceleration_steps = int(step_num / 2)
        return acceleration_steps

    @patch('wiringpi.wiringPiSetup', stub_wiringPiSetup)
    def stop(self):
        wiringpi.digitalWrite(self.inp[0], 0)
        wiringpi.digitalWrite(self.inp[2], 0)
        wiringpi.digitalWrite(self.inp[3], 0)
        wiringpi.digitalWrite(self.inp[1], 0)

    @patch('wiringpi.wiringPiSetup', stub_wiringPiSetup)
    def run_one_step(self):
        """Change the power configuration of the pins in order to do one step in a certain direction."""
        self.actual_num_step += 1
        phase = (self.actual_num_step % 8) * self.direction

        # Do the step
        for k in range(0, 4):
            wiringpi.digitalWrite(self.inp[k], self.half[phase][k])

        if self.debug:
            real_acceleration = 0

            # Positive acceleration control
            if self.acc_or_dec == 1:
                self.t = self.absolute_time
                real_acceleration = int(round(2 * self.actual_num_step / self.t**2))

                # Safety control
                if self.actual_speed > self.MAX_SPEED:
                    self.stepper_max_speed_is_acceptable = False

                # Refresh max speed touched
                if self.actual_speed > self.max_speed_reached:
                    self.max_speed_reached = self.actual_speed

            # Negative acceleration control
            if self.acc_or_dec == -1:
                self.dec_steps -= 1
                self.t = self.absolute_time - self.t_start_deceleration
                # from physics ==>   s = -1/2 * a * t^2 + v_0 * t
                real_acceleration = int(round(2 * (self.max_speed_reached / self.t - (self.actual_num_step
                                                   - self.step_start_deceleration) / self.t**2)))

            # Zero acceleration control
            if self.acc_or_dec == 0:
                self.old_num_step = self.actual_num_step

            # To do during acceleration phase
            else:
                if real_acceleration != self.acceleration_factor:
                    logging.warning("At step {} the real acceleration was {} "
                                    "instead of {}.\nSpeed = {} Time = {}\n".format(self.actual_num_step,
                                                                                    real_acceleration,
                                                                                    self.acceleration_factor,
                                                                                    self.max_speed_reached,
                                                                                    self.t))
                    self.movement_control_passed = False

            self.old_num_step = self.actual_num_step
            self.old_speed = self.actual_speed

    def move(self, step_num, speed=200):
        """Manages the acceleration, constant movement and deceleration of the stepper.

        *step_num* can be positive and negative: negative values make the engine turn in the opposite direction;
        *speed* must be positive, and should respect the hardware limitations"""

        # Initialization
        self.actual_num_step = 0
        start_time = time.time()
        differ_time = 0

        # Verify parameters' validity
        if step_num is None:
            return "Invalid input. You should choose a value for *step_num*"
        if speed is None:
            return "Invalid input. You should choose a value for *speed*. A possible value could be 250 step/s"

        try:
            step_num = int(step_num)
        except(TypeError, ValueError):
            return "Invalid input. step_num has to be an integer"
        if step_num < 0:
            return "Invalid input. step_num has to be positive"

        try:
            speed = int(speed)
        except(TypeError, ValueError):
            return "Invalid input. speed has to be an integer"

        speed = self._corrected_speed(speed)
        acceleration_steps = self._acceleration_steps(step_num, speed, self.acceleration_factor)
        constant_speed_steps = step_num - (2 * acceleration_steps)

        if self.debug:
            self._init_par()
            logging.info("Starting a new movement cycle: "
                         "Steps = {}, Speed = {}, Acceleration = {}".format(step_num, speed, self.acceleration_factor))

        self._linear_acceleration(acceleration_steps, acc_is_positive=True)

        if self.debug:
            differ_time = start_time
            self.real_time_acceleration = time.time() - differ_time
            if self._movement_did_well():
                logging.info("Acceleration interval was executed. Everything went well")
            else:
                logging.info("During acceleration interval something unexpected happened")
            logging.debug("Real time spent accelerating is {}".format(self.real_time_acceleration))

        # Set the right speed when acceleration phase is too short, and the engine couldn't reach the required speed.
        if speed > self.actual_speed:
            speed = self.actual_speed

        self._move_with_constant_speed(constant_speed_steps, speed)

        if self.debug:
            differ_time += self.real_time_acceleration
            self.real_time_constant_speed = time.time() - differ_time
            if self._movement_did_well():
                logging.info("Constant speed interval was executed. Everything went well")
            else:
                logging.info("During constant speed interval something unexpected happened")
            logging.debug("Real time spent moving at constant speed is {}".format(self.real_time_constant_speed))
            self.t_start_deceleration = self.absolute_time
            self.step_start_deceleration = self.actual_num_step
            self.old_speed = self.actual_speed

        self._linear_acceleration(acceleration_steps, acc_is_positive=False)

        if self.debug:
            differ_time += self.real_time_constant_speed
            self.real_time_deceleration = time.time() - differ_time

            if self._movement_did_well():
                logging.info("Deceleration interval was executed. Everything went well")
            else:
                logging.info("During deceleration interval something unexpected happened")
            logging.debug("Real time spent decelerating is {}".format(self.real_time_deceleration))

            if self.actual_num_step == step_num:
                self.stepper_total_step_number_is_correct = True
            else:
                logging.warning("Total number of steps done differs from the number specified: "
                                "\nnum of steps wanted : {}".format(step_num) +
                                "\nnum of steps done = {}".format(self.actual_num_step) +
                                "\nwhere {} are acceleration steps, ".format(acceleration_steps) +
                                "and {} are constant speed steps".format(constant_speed_steps))

            logging.info("The whole movement cycle is finish.\n")
            t_tot = self.real_time_acceleration + self.real_time_constant_speed + self.real_time_deceleration
            logging.debug("Max speed reached = {}\n"
                          "Execution was completed in {} seconds\n\n\n"
                          "###########################################################\n\n"
                          "".format(self.max_speed_reached, t_tot))

    def _move_with_constant_speed(self, steps, speed):
        """Make the stepper move with a constant speed.
        Do not call this method manually, it could damage your engine."""
        self.acc_or_dec = 0
        self.actual_speed = speed
        t = 1 / self.actual_speed

        for s in range(int(steps)):
            self.run_one_step()
            if self.debug:
                self.absolute_time += t
                with open(self.debug_filepath, "a") as f:
                    f.write(str(self.absolute_time) + "\t" + str(self.actual_num_step)
                            + "\t" + str(self.actual_speed) + "\n")
            time.sleep(t)

    def _linear_acceleration(self, steps, acc_is_positive):
        """Make the stepper accelerate/decelerate linearly with the time. Acceleration in controlled trough the
        *self.acceleration_factor* parameter, and its standard value is set to 1.
        Do not call this method manually, it could damage your engine."""

        self.acc_or_dec = 1
        t = 0
        n = 0
        count = 1

        if not acc_is_positive:
            # Engine is decelerating
            self.acc_or_dec = -1
            n = steps
            self.dec_steps = n

        while count <= steps:
            if acc_is_positive:
                t = sqrt(2 / self.acceleration_factor) * (sqrt(n+1) - sqrt(n))
            if not acc_is_positive:
                t = sqrt(2 / self.acceleration_factor) * (sqrt(n) - sqrt(n-1))

            time.sleep(t)
            self.actual_speed = 1 / t
            count += 1
            n += self.acc_or_dec * 1

            if self.debug:
                self.t = t
                self.absolute_time += t
                with open(self.debug_filepath, "a") as f:
                    f.write(
                        str(self.absolute_time) + "\t" + str(self.actual_num_step) + "\t" + str(1/t) + "\n")
            self.run_one_step()

        # Set the speed to 0 when the engine ends the deceleration
        if not acc_is_positive:
            self.actual_speed = 0


def engine_main(queue):
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

    engine = Stepper(7, 0, 2, 3)

    while True:
        try:
            msg = queue.get(block=False)
            if msg["dest"] != "engine":
                queue.put(msg)
                msg = None
        except Empty:
            msg = None
        time.sleep(0.1)

        if msg and msg["id"] == "1":
            command = msg["command"]
            parameter = msg["parameter"]
            logging.info("engine received msg: command={},   par={}".format(command, parameter))

            if command == "move":
                angle = parameter
                logging.info("engine is starting")
                engine.move(angle)
                logging.info("engine finished")
                queue.put(
                    {
                        "id": "1",
                        "dest": "controller",
                        "status": "reached_dest"
                    }
                )
                logging.info("engine wrote in queue")
