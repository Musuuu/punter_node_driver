import unittest
from mock import patch
from stepmotor import Stepper, ConfigurationError
import functools


def stub_wiringPiSetup():
    """Simulates the correct initialization of the board"""
    return True


def pinMode(pin, mode):
    """Change the mode o a pin"""
    if mode in ("1", "0"):
        return True
    else:
        raise ValueError('You tried to set the ', pin, ' pin with an incorrect status. '
                         'Select 0 for input and 1 for output mode')


def track_calls(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        wrapper.has_been_called = True
        return func(*args, **kwargs)
    wrapper.has_been_called = False
    return wrapper


# def stub_digitalWrite(pin=None, value=None):
#     """Change the value of a digital pin ('0' = OFF or '1' = ON)"""
#     # Assure that Stepper's attribute *inp* exists
#     # try:
#     #     Stepper.inp
#     # except AttributeError:
#     #     Stepper.inp = [None, None, None, None]
#     #
#     # if int(value) in (0, 1):
#     #     Stepper.inp[pin] = value
#     #     return Stepper.inp
#     # else:
#     #     raise ValueError('You tried to set the ', pin, ' pin with an incorrect value. Only *0* and *1* are accepted')
#
#     if pin in test_engine.inp:
#         if int(value) in (0, 1):
#             return True
#         else:
#             raise ValueError('You tried to set the ', pin, ' pin with an incorrect value. Only *0* and *1* are accepted')
#     else:
#         raise ValueError('The pin that you\'re trying to set is not in use')


class PrimesTestCase (unittest.TestCase):
    """Tests for the stepper class"""

    # # # # # # # # # # # # # # # # # # # # # #
    # # #   Setting up test boundaries    # # #
    # # # # # # # # # # # # # # # # # # # # # #

    @patch('wiringpi.wiringPiSetup', stub_wiringPiSetup)
    # @patch('wiringpi.pinMode', pinMode)
    def setUp(self):
        self.test_engine = Stepper(0, 1, 2, 3)

    @track_calls
    def stub_digitalWrite(pin, value):
        if int(value) in (0, 1) and int(pin) == pin:
            return True
        else:
            raise ValueError('You tried to set the pin #', pin+1, ' with an incorrect value. '
                             'Only *0* and *1* are accepted')

    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
    # # #   Test if parameters are correctly initialised    # # #
    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

    def test_initial_number_of_steps(self):
        self.assertEqual(self.test_engine.num_step, 0)

    def test_initial_rotation_array(self):
        self.assertEqual(self.test_engine.half, [[1, 0, 0, 1],
                                                 [1, 0, 0, 0],
                                                 [1, 1, 0, 0],
                                                 [0, 1, 0, 0],
                                                 [0, 1, 1, 0],
                                                 [0, 0, 1, 0],
                                                 [0, 0, 1, 1],
                                                 [0, 0, 0, 1]])

    def test_initial_acceleration_range(self):
        self.assertEqual(self.test_engine.acc, 1000)
        self.assertEqual(self.test_engine.dec, 1000)

    def test_initial_speed(self):
        self.assertEqual(self.test_engine.actspeed, 0)

    # # # # # # # # # # # # # # # # # # # # # # #
    # # #   Test the methods of the class   # # #
    # # # # # # # # # # # # # # # # # # # # # # #

    def test_set_pins1(self):
        """Tests if the pins are selected correctly"""
        self.assertEqual([0, 1, 2, 3], self.test_engine.inp)

    def test_set_pins2(self):
        """Tests if the correct exception is raised when the user tries to use the same pin more times"""
        with self.assertRaises(ConfigurationError) as context:
            self.test_engine.inp = self.test_engine.set_pins(1, 1, 1, 1)
        self.assertNotEqual("ConfigurationError", context.exception)    # Ok if there is a configuration error

    def test_set_pins3(self):
        """Tests if the correct exception is raised when the user gives an empty variable as pin number"""
        with self.assertRaises(NameError) as context:
            self.test_engine.inp = self.test_engine.set_pins(0, 1, 2, a)
        self.assertNotEqual("NameError", context.exception)

    def test_set_pins4(self):
        """Tests if the correct exception is raised when the user doesn't give an integer as pin number"""
        with self.assertRaises(TypeError) as context:
            self.test_engine = self.test_engine.set_pins(0, 1, 2, [1, 2])
        self.assertNotEqual("TypeError", context.exception)

        with self.assertRaises(TypeError) as context:
            self.test_engine = self.test_engine.set_pins(0, 1, 2, {1:"hello", 2:"world"})
        self.assertNotEqual("TypeError", context.exception)

    def test_set_pins5(self):
        """Tests if the correct exception is raised when the user give an char as pin number"""
        with self.assertRaises(ValueError) as context:
            self.test_engine = self.test_engine.set_pins(0, 1, 2, "hello")
        self.assertNotEqual("ValueError", context.exception)

    def test_set_pins6(self):
        """Tests if the correct exception is raised when the user give a negative pin number"""
        with self.assertRaises(ValueError) as context:
            self.test_engine = self.test_engine.set_pins(0, 1, 2, -5)
        self.assertNotEqual("ValueError", context.exception)

    @patch('wiringpi.digitalWrite', stub_digitalWrite)
    def test_stop(self):
        """Tests if the *stop* method works as expected"""
        self.test_engine.stop()
        self.assertTrue(self.stub_digitalWrite.has_been_called)


if __name__ == '__main__':
    unittest.main()
