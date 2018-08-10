import unittest
from mock import patch
from .stepmotor import Stepper, ConfigurationError
from unittest import skip
from random import randint
import time
from math import sqrt as sqrt
import argparse
import logging


def stub_wiringPiSetup():
    """Simulates the correct initialization of the board"""
    return True


class PrimesTestCase (unittest.TestCase):
    """Tests for the stepper class"""

    # # # # # # # # # # # # # # # # # # # #
    # # #   Set up test boundaries    # # #
    # # # # # # # # # # # # # # # # # # # #

    @patch('wiringpi.wiringPiSetup', stub_wiringPiSetup)
    def setUp(self):
        self.test_engine = Stepper(0, 1, 2, 3, debug=True)
        self.test_engine.acceleration_factor = 20

    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
    # # #   Test if parameters are correctly initialised    # # #
    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

    def test_initial_number_of_steps(self):
        self.assertEqual(self.test_engine.actual_num_step, 0)

    def test_initial_rotation_array(self):
        self.assertEqual(self.test_engine.half, [[1, 0, 0, 1],
                                                 [1, 0, 0, 0],
                                                 [1, 1, 0, 0],
                                                 [0, 1, 0, 0],
                                                 [0, 1, 1, 0],
                                                 [0, 0, 1, 0],
                                                 [0, 0, 1, 1],
                                                 [0, 0, 0, 1]])

    def test_initial_speed(self):
        self.assertEqual(self.test_engine.actual_speed, 0)

    def test_initial_pin_configuration(self):
        """Tests if the pins are selected correctly"""
        self.assertEqual([0, 1, 2, 3], self.test_engine.inp)

    # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
    # # #   Test the *check_pin* method of the class    # # #
    # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

    def test_check_pins(self):
        """Tests if the correct exception is raised when the user tries to use the same pin more times"""
        with self.assertRaises(ConfigurationError):
            self.test_engine.inp = self.test_engine.check_pins(1, 1, 1, 1)
            self.test_engine.inp = self.test_engine.check_pins(1, 0, 1, 5)
            self.test_engine.inp = self.test_engine.check_pins(0, 1, 2, "a")
            self.test_engine = self.test_engine.check_pins(0, 1, 2, [1, 2])
            self.test_engine = self.test_engine.check_pins(0, 1, 2, {1: "hello", 2: "world"})
            self.test_engine = self.test_engine.check_pins(0, 1, 2, "hello")
            self.test_engine = self.test_engine.check_pins(0, 1, 2, -5)

    # # # # # # # # # # # # # # # # # # # # # # # # # #
    # # #   Test the *stop* method of the class   # # #
    # # # # # # # # # # # # # # # # # # # # # # # # # #

    @patch('wiringpi.digitalWrite')
    def test_stop(self, mock_digitalWrite):
        """Tests if the *stop* method calls wiringpi.digitalWrite method as expected"""
        self.test_engine.stop()
        assert mock_digitalWrite.called

    # # # # # # # # # # # # # # # # # # # # # # # # # #
    # # #   Test the *move* method of the class   # # #
    # # # # # # # # # # # # # # # # # # # # # # # # # #

    def test_correct_move(self):
        """Test the correct behavior with correct parameters"""
        logging.info("Running a simulation of the engine movement. Please wait\n")
        self.test_engine.move(2000, 150)
        self.assertTrue(self.test_engine.stepper_max_speed_is_acceptable)
        self.assertTrue(self.test_engine.stepper_acceleration_is_correct)
        self.assertTrue(self.test_engine.stepper_total_step_number_is_correct)

        self.test_engine.move(100, -250)
        self.assertTrue(self.test_engine.stepper_max_speed_is_acceptable)
        self.assertTrue(self.test_engine.stepper_acceleration_is_correct)
        self.assertTrue(self.test_engine.stepper_total_step_number_is_correct)

    def test_move_with_very_high_speed(self):
        """Test what happen while trying to set extreme high speed"""
        logging.info("Running a simulation of the engine movement. Please wait\n")
        self.test_engine.move(1000, 10000000)
        self.assertTrue(self.test_engine.stepper_max_speed_is_acceptable)
        self.assertTrue(self.test_engine.stepper_acceleration_is_correct)
        self.assertTrue(self.test_engine.stepper_total_step_number_is_correct)

    def test_move_with_very_low_speed(self):
        """Test what happen with a speed very low or equal to 0"""
        logging.info("Running a simulation of the engine movement. Please wait\n")
        self.test_engine.move(20, 0)
        self.assertTrue(self.test_engine.stepper_max_speed_is_acceptable)
        self.assertTrue(self.test_engine.stepper_acceleration_is_correct)
        self.assertTrue(self.test_engine.stepper_total_step_number_is_correct)

        self.test_engine.move(20, 1)
        self.assertTrue(self.test_engine.stepper_max_speed_is_acceptable)
        self.assertTrue(self.test_engine.stepper_acceleration_is_correct)
        self.assertTrue(self.test_engine.stepper_total_step_number_is_correct)

    def test_move_with_invalid_values(self):
        """Test what happen with negative speed, step number and direction"""
        self.assertEqual(self.test_engine.move(-100, -250), "Invalid input. step_num has to be positive")
        self.assertEqual(self.test_engine.move(-100, 250), "Invalid input. step_num has to be positive")

    def test_move_with_wrong_data_types_float(self):
        """Test what happen if user insert floating numbers as inputs"""
        logging.info("Running a simulation of the engine movement. Please wait\n")
        self.test_engine.move(100.123, 100.123)

    def test_move_with_wrong_data_types2(self):
        """Test what happen when wrong data types are passed to the method: chars, lists, tuples and dictionaries"""
        self.assertEqual(self.test_engine.move("foo", 250), "Invalid input. step_num has to be an integer")
        self.assertEqual(self.test_engine.move([10, 10, 10], 250), "Invalid input. step_num has to be an integer")
        self.assertEqual(self.test_engine.move((10, 10, 10), 250), "Invalid input. step_num has to be an integer")
        self.assertEqual(self.test_engine.move({1: 10, 2: "foo"}, 250), "Invalid input. step_num has to be an integer")

        self.assertEqual(self.test_engine.move(100, "foo"), "Invalid input. speed has to be an integer")
        self.assertEqual(self.test_engine.move(100, [10, 10, 10]), "Invalid input. speed has to be an integer")
        self.assertEqual(self.test_engine.move(100, (10, 10, 10)), "Invalid input. speed has to be an integer")
        self.assertEqual(self.test_engine.move(100, {1: 10, 2: "foo"}), "Invalid input. speed has to be an integer")

    def test_move_with_empty_data(self):
        """Test what happen when some data isn't specified"""
        self.assertEqual(self.test_engine.move(None, 250), "Invalid input. You should choose a value for *step_num*")
        self.assertEqual(self.test_engine.move(100, None),
                         "Invalid input. You should choose a value for *speed*. A possible value could be 250 step/s")

    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
    # # #   Test the predictability of the engine's behavior  # # #
    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

    def calculate_theoretical_values(self, input_steps, input_speed, acceleration_factor):
        """Calculate the time and the maximum speed that should be theoretically obtained with an ideal engine"""

        speed = self.test_engine._corrected_speed(input_speed)

        # Intervals step number
        acceleration_steps = self.test_engine._acceleration_steps(input_steps, speed, acceleration_factor)
        constant_speed_steps = input_steps - 2 * acceleration_steps

        # Find time
        t_acc = sqrt(2 * acceleration_steps / acceleration_factor)
        t_maxs = sqrt(2 * constant_speed_steps / acceleration_factor)

        # Find max speed
        max_speed_reachable = acceleration_factor * t_acc

        return [t_acc, t_maxs, max_speed_reachable]

    @staticmethod
    def random_values():
        """Create a set of random variables for an hypothetical engine"""
        steps = randint(1, 5000)
        speed = randint(-600, 600)
        acceleration_factor = randint(1, 50)

        return [steps, speed, acceleration_factor]

    def test_expected_behavior_measuring_time_and_speed(self):
        """Measure the gap between the ideal and the simulated engine"""
        logging.debug("The following 10 tests will be performed with random inputs\n\n")
        for i in range(10):
            c = self.random_values()
            random_steps = c[0]
            random_speed = c[1]
            random_acc = c[2]

            results = self.calculate_theoretical_values(random_steps, random_speed, random_acc)
            t_acc = results[0]
            t_maxs = results[1]
            t_dec = t_acc
            t_tot = t_acc + t_maxs + t_dec
            max_speed = results[2]

            logging.debug("   TEST  # {}".format(i+1))
            logging.debug("Starting simulation with acceleration factor = {}".format(random_acc))
            logging.debug("Theoretical time = {}".format(t_tot))
            logging.debug("Theoretical max speed = {}\n".format(max_speed))

            self.test_engine.acceleration_factor = random_acc
            self.test_engine.move(random_steps, random_speed)

            # Test acceleration time
            acc_time_percentage_error = abs(t_acc - self.test_engine.real_time_acceleration) / t_acc * 100

            # Test constant speed time
            if t_maxs != 0:
                cs_time_percentage_error = abs(t_maxs - self.test_engine.real_time_constant_speed) / t_maxs * 100

            # Test deceleration time
            dec_time_percentage_error = abs(t_dec - self.test_engine.real_time_deceleration) / t_dec * 100

            # Test maximum speed
            speed_percentage_error = abs(max_speed - self.test_engine.max_speed_reached) / max_speed * 100

            self.assertLess(acc_time_percentage_error, 10, "Error > 10%")
            if t_maxs != 0:
                self.assertLess(cs_time_percentage_error, 10, "Error > 10%")
            self.assertLess(dec_time_percentage_error, 10, "Error > 10%")
            self.assertLess(speed_percentage_error, 1, "Error > 1%")


if __name__ == '__main__':
    logging.basicConfig(format='%(levelname)s - %(message)s')

    parser = argparse.ArgumentParser(description="Run a test routine to control the correct execution of the "
                                                 "stepmotor.py file")
    parser.add_argument("-v", "--verbose", action="count", default=0, help="Shows more levels of logging messages")
    args = parser.parse_args()

    # create logger
    logger = logging.getLogger()

    if args.verbose >= 2:
        logger.setLevel(logging.DEBUG)
    elif args.verbose >= 1:
        logger.setLevel(logging.INFO)
    else:
        logger.setLevel(logging.ERROR)
    unittest.main()
