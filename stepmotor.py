import wiringpi
import time
import threading


class ConfigurationError(Exception):
    """Raise when the user tries to configure the system in a bad way"""


class Stepper:
    def __init__(self, i1, i2, i3, i4):
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
        self.num_step = 0
        self.half = [[1, 0, 0, 1],  # step 0
                     [1, 0, 0, 0],  # step 1
                     [1, 1, 0, 0],  # step 2
                     [0, 1, 0, 0],  # step 3
                     [0, 1, 1, 0],  # step 4
                     [0, 0, 1, 0],  # step 5
                     [0, 0, 1, 1],  # step 6
                     [0, 0, 0, 1]]  # step 7
        self.actspeed = 0
        self.direction = None
        self.actual_speed = 0

        # Hardware constrains
        self.acceleration_factor = 1
        self.MIN_SPEED = 10    # Steps/sec
        self.MAX_SPEED = 1000  # Steps/sec

    def check_pins(self, i1, i2, i3, i4):
        """Control if selected pin numbers are valid"""
        try:
           input_pins = [int(i1), int(i2), int(i3), int(i4)]
        except ValueError:
            raise ConfigurationError("There is at least one pin with an incorrect. Pins must have unique numbers")

        # wiringpi library supports only 17 GPIO pins. See the official documentation for more informations
        for i in range(len(input_pins)):
            if input_pins[i] not in list(range(0, 17)):
                raise ValueError("Error. You have selected at least one invalid pin.")

        if not (input_pins[0] != input_pins[1] != input_pins[2] != input_pins[3]):
            raise ConfigurationError("There are two different pins with the same number. Pins must have unique numbers")

        self.inp = input_pins

    def stop(self):
        wiringpi.digitalWrite(self.inp[0], 0)
        wiringpi.digitalWrite(self.inp[2], 0)
        wiringpi.digitalWrite(self.inp[3], 0)
        wiringpi.digitalWrite(self.inp[1], 0)

    def run_one_step(self):
        """Change the power configuration of the pins in order to do one step in a certain direction."""
        phase = (self.num_step % 8) * self.direction

        # Do the step
        for k in range(0, 4):
            # print(k, self.inp[k], self.half[phase][k])
            wiringpi.digitalWrite(self.inp[k], self.half[phase][k])

    def move(self, step_num=0, speed=0, direction=1):
        """Manages the acceleration, constant movement and deceleration of the stepper"""
        
        # Correct invalid *direction* values and verify inputs validity
        try:
            
            # Set a correct direction value
            direction = int(direction)
            if direction > 0:
                direction = 1
            else:
                direction = -1

            # Manage a negative step_num
            step_num = int(step_num)
            if step_num < 0:
                step_num = step_num * -1
                direction = direction * -1

            # Manage a negative speed
            speed = int(speed)
            if speed < 0:
                speed = speed * -1
                direction = direction * -1
            if speed == 0:
                return self.stop()

        except (TypeError, ValueError):
            return "FATAL ERROR.\nYou tried to move the engine with invalid parameters"

        self.direction = direction

        # Apply hardware's speed limits
        if speed > self.MAX_SPEED:
            speed = self.MAX_SPEED
        if speed < self.MIN_SPEED:
            speed = self.MIN_SPEED

        # Number of steps of the speed changing intervals
        acceleration_steps = int(speed / self.acceleration_factor)

        # Control if the acceleration phases are not too long
        if acceleration_steps > (step_num / 2):
            acceleration_steps = (step_num / 2)

        constant_speed_steps = step_num - (2 * acceleration_steps)

        print("\n acceleration steps=", acceleration_steps, "\n uniform speed steps=", constant_speed_steps)

        self._linear_acceleration(acceleration_steps, acc_is_positive=True)

        # Set the right speed when acceleration phase is too short, and the engine couldn't reach the required speed.
        if speed > self.actual_speed:
            speed = self.actual_speed
        self._move_with_constant_speed(constant_speed_steps, speed)
        self._linear_acceleration(acceleration_steps, acc_is_positive=False)

        # Control message. Helps during tests
        print("\n Final check:\n", self.num_step, self.actual_speed, "\n\n")

    def _move_with_constant_speed(self, steps, speed):
        self.actual_speed = speed
        t = 1 / self.actual_speed

        for s in range(int(steps)):

            # Control message. Helps during tests
            print(self.num_step, t)
            self.run_one_step()
            self.num_step += 1 * self.direction
            time.sleep(t)

    def _linear_acceleration(self, steps, acc_is_positive=True):
        """Make the stepper accelerate/decelerate linearly with the time. Acceleration in controlled trough the
        *self.acceleration_factor* parameter, and its standard value is set to 1"""
        count = 1
        if acc_is_positive:
            acc_or_dec = 1

            # Correct the speed in order to avoid ZeroDivisionError during the first definition of *t*
            self.actual_speed = 1

        elif not acc_is_positive:
            acc_or_dec = -1

        else:
            raise SystemError

        while count <= steps:
            # Set the time between every step (~speed)
            t = 1 / self.actual_speed

            # Control message. Helps during tests
            print(self.num_step, t)
            self.run_one_step()

            # Make the acceleration
            self.actual_speed += 1 * self.acceleration_factor * acc_or_dec
            self.num_step += 1 * self.direction
            time.sleep(t)
            count += 1

        # Set the speed to 0 when the engine ends the deceleration
        if not acc_is_positive:
            self.actual_speed = 0

    # def move(self, speed, rel=1, dir=1):  # speed = step/second Hz
    #
    #     # CONTROL OF INPUTS
    #
    #     # Round the value of the speed to the next integer
    #     speed = int(speed - speed % 1)
    #     if speed not in range(10, 1000):
    #         raise ValueError("The selected value of the speed is not valid. "
    #                          "Choose an integer between ", self.MIN_SPEED, " and ", self.MAX_SPEED, " step/s")
    #
    #     # Control of direction
    #     if dir >= 0:
    #         d = 1
    #     else:
    #         d = -1
    #
    #     refspeed = speed
    #     self.actspeed = 1
    #     dec = self.dec
    #
    #     count=1
    #
    #     # go slower if starting close to the target position
    #     if rel <= self.dec:
    #         dec = rel/2
    #
    #     for s in range(0, int(rel)):
    #         # index of the actual relative position
    #         self.num_step = self.num_step+d
    #
    #         # deceleration starting point
    #         if s == rel - dec:
    #             refspeed = 0
    #         t = 1.0/self.actspeed
    #         actacc = speed/self.acc
    #         print(self.num_step, 1.0/self.actspeed)
    #         phase = self.num_step % 8
    #         for k in range(0, 4):
    #             # print (k, self.inp[k],self.half[phase][k])
    #             wiringpi.digitalWrite(self.inp[k], self.half[phase][k])
    #
    #         # control the speed during the acceleration phase
    #         if self.actspeed < refspeed:
    #             print("+ 100")
    #             self.actspeed = self.actspeed + 1
    #             if self.actspeed > speed:
    #                 self.actspeed = speed
    #
    #         # control the speed during the deceleration phase
    #         elif self.actspeed > refspeed:
    #             print("- 100")
    #             self.actspeed = self.actspeed - 1
    #             if self.actspeed <= 0:
    #                 self.actspeed = 1
    #                 return
    #         time.sleep(t)
    #         count += 1

# motor1 = Stepper(7, 0, 2, 3)
# while 0:
#     motor1.move(2000, int(4096/2), 1)
#     motor1.stop()
#     time.sleep(2)
#     motor1.move(2000, int(4096/2), -1)
#     motor1.stop()
#     time.sleep(2)
