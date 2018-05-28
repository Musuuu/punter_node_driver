import unittest
from mock import patch
from stepmotor import Stepper, ConfigurationError
import functools
from unittest import skip

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


class PrimesTestCase (unittest.TestCase):
    """Tests for the stepper class"""

    # # # # # # # # # # # # # # # # # # # # # #
    # # #   Setting up test boundaries    # # #
    # # # # # # # # # # # # # # # # # # # # # #

    @patch('wiringpi.wiringPiSetup', stub_wiringPiSetup)
    # @patch('wiringpi.pinMode', pinMode)
    def setUp(self):
        self.test_engine = Stepper(0, 1, 2, 3)
        self.test_engine.acceleration_factor = 2

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

    @skip("Tested attributes will be removed")
    def test_initial_acceleration_range(self):
        self.assertEqual(self.test_engine.acc, 1000)
        self.assertEqual(self.test_engine.dec, 1000)

    def test_initial_speed(self):
        self.assertEqual(self.test_engine.actspeed, 0)

    # # # # # # # # # # # # # # # # # # # # # # # # # # # #
    # # #   Test the *set_pin* method of the class    # # #
    # # # # # # # # # # # # # # # # # # # # # # # # # # # #

    def test_check_pins1(self):
        """Tests if the pins are selected correctly"""
        self.assertEqual([0, 1, 2, 3], self.test_engine.inp)

    def test_check_pins2(self):
        """Tests if the correct exception is raised when the user tries to use the same pin more times"""
        with self.assertRaises(ConfigurationError):
            self.test_engine.inp = self.test_engine.check_pins(1, 1, 1, 1)

    def test_check_pins3(self):
        """Tests if the correct exception is raised when the user gives an empty variable as pin number"""
        with self.assertRaises(NameError):
            self.test_engine.inp = self.test_engine.check_pins(0, 1, 2, a)

    def test_check_pins4(self):
        """Tests if the correct exception is raised when the user doesn't give an integer as pin number"""
        with self.assertRaises(TypeError):
            self.test_engine = self.test_engine.check_pins(0, 1, 2, [1, 2])

        with self.assertRaises(TypeError):
            self.test_engine = self.test_engine.check_pins(0, 1, 2, {1: "hello", 2: "world"})

    def test_check_pins5(self):
        """Tests if the correct exception is raised when the user give an char as pin number"""
        with self.assertRaises(ConfigurationError):
            self.test_engine = self.test_engine.check_pins(0, 1, 2, "hello")

    def test_check_pins6(self):
        """Tests if the correct exception is raised when the user give a negative pin number"""
        with self.assertRaises(ValueError):
            self.test_engine = self.test_engine.check_pins(0, 1, 2, -5)

    # # # # # # # # # # # # # # # # # # # # # # # # # #
    # # #   Test the *stop* method of the class   # # #
    # # # # # # # # # # # # # # # # # # # # # # # # # #

    @patch('wiringpi.digitalWrite', stub_digitalWrite)
    def test_stop(self):
        """Tests if the *stop* method works as expected"""
        self.test_engine.stop()
        self.assertTrue(self.stub_digitalWrite.has_been_called)

    # # # # # # # # # # # # # # # # # # # # # # # # # #
    # # #   Test the *move* method of the class   # # #
    # # # # # # # # # # # # # # # # # # # # # # # # # #

    def test_correct_move(self):
        """Test the correct behavior with correct parameters"""
        self.test_engine.move(1000, 250, 1)
        # self.test_engine.move(250, rel=100, dir=-1)

    def test_move_with_illogical_values1(self):
        """Test what happen while trying to set extreme high speed"""
        self.test_engine.move(1000, 10000000, 1)

    def test_move_with_illogical_values2(self):
        """Test what happen with speed equal to 0"""
        self.test_engine.move(20, 0, 1)

    def test_move_with_illogical_values3(self):
        """Test what happen with a very low speed"""
        self.test_engine.move(20, 1, 1)

    def test_move_with_illogical_values4(self):
        """Test what happen with negative speed, step number and direction"""
        self.test_engine.move(-100, -250, -1)

    def test_move_with_wrong_data_types1(self):
        """Test what happen with unusual data types"""
        self.test_engine.move(100.123, 100.123, 4.123)

    @patch('wiringpi.digitalWrite', stub_digitalWrite)
    def test_move_with_wrong_data_types2(self):
        """Test what happen when wrong data types are passed to the method: lists"""
        self.test_engine.move([10, 10, 10], 250, 1)
        self.test_engine.move(100, [10, 10, 10], 1)
        self.test_engine.move(100, 250, [10, 10, 10])

    def test_move_with_wrong_data_types3(self):
        """Test what happen when wrong data types are passed to the method: tuples"""
        self.test_engine.move((10, 10, 10), 250, 1)
        self.test_engine.move(100, (10, 10, 10), 1)
        self.test_engine.move(100, 250, (10, 10, 10))

    def test_move_with_wrong_data_types4(self):
        """Test what happen when wrong data types are passed to the method: dictionaries"""
        self.test_engine.move({1: 10, 2: "foo"}, 250, 1)
        self.test_engine.move(100, {1: 10, 2: "foo"}, 1)
        self.test_engine.move(100, 250, {1: 10, 2: "foo"})

    def test_move_with_wrong_data_types5(self):
        """Test what happen when wrong data types are passed to the method: chars"""
        self.test_engine.move("foo", 250, 1)
        self.test_engine.move(100, "foo", 1)
        self.test_engine.move(100, 250, "foo")

    def test_move_with_empty_data(self):
        """Test what happen when some data isn't specified"""
        self.test_engine.move(None, 250, 1)
        self.test_engine.move(100, None, 1)
        self.test_engine.move(100, 250, None)


if __name__ == '__main__':
    unittest.main()
