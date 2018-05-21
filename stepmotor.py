import wiringpi
import time
import threading


class ConfigurationError(Exception):
    """Raise when the user tries to configure the system in a bad way"""


class Stepper:

    def __init__(self, i1, i2, i3, i4):
        wiringpi.wiringPiSetup()
        self.inp = [None, None, None, None]
        self.set_pins(i1, i2, i3, i4)
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
        self.acc = 1000  # steps
        self.dec = self.acc  # steps
        self.actspeed = 0

    def set_pins(self, i1, i2, i3, i4):
        """Control if selected pin numbers are valid"""
        input_pins = [int(i1), int(i2), int(i3), int(i4)]

        for i in range(len(input_pins)):
            # wiringpi library supports 17 GPIO pins. See the official documentation for more informations
            if input_pins[i] not in list(range(0, 17)):
                raise ValueError("Error. At least on pin has an unreasonable value.")

        if not (input_pins[0] != input_pins[1] != input_pins[2] != input_pins[3]):
            raise ConfigurationError("There are two different pins with the same number. Pins must have unique numbers")

        self.inp = input_pins

    def stop(self):
        wiringpi.digitalWrite(self.inp[0], 0)
        wiringpi.digitalWrite(self.inp[2], 0)
        wiringpi.digitalWrite(self.inp[3], 0)
        wiringpi.digitalWrite(self.inp[1], 0)

    def move(self, speed, rel=1, dir=1):  # speed = step/second Hz
        if dir >= 0:
            d = 1
        else:
            d = -1
        refspeed = speed
        self.actspeed = 1
        dec = self.dec

        if rel <= self.dec:
            dec = rel/2
        for s in range(0, int(rel)):
            self.num_step = self.num_step+d
            if s == rel-dec:
                refspeed = 0
            t=1.0/self.actspeed
            actacc = speed/self.acc
            print(self.num_step, 1.0/self.actspeed)
            fase = self.num_step % 8
            for k in range(0, 4):
#				print k, self.inp[k],self.half[fase][k]
                wiringpi.digitalWrite(self.inp[k], self.half[fase][k])
            if self.actspeed < refspeed:
                print("+ 100")
                self.actspeed = self.actspeed + actacc
                if self.actspeed > speed:
                    self.actspeed = speed

            elif self.actspeed > refspeed:
                print("- 100")
                self.actspeed = self.actspeed - actacc
                if self.actspeed < 0:
                    self.actspeed = 0
                    return
            time.sleep(t)


# motor1 = Stepper(7, 0, 2, 3)
# while 0:
#     motor1.move(2000, int(4096/2), 1)
#     motor1.stop()
#     time.sleep(2)
#     motor1.move(2000, int(4096/2), -1)
#     motor1.stop()
#     time.sleep(2)
