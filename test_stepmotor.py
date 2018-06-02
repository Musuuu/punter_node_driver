import unittest
from mock import patch
from stepmotor import Stepper, ConfigurationError
from unittest import skip
from random import randint
import time


def stub_wiringPiSetup():
    """Simulates the correct initialization of the board"""
    return True


class TestStepper(Stepper):
    """Add some code in order to make effective tests"""

    def __init__(self, i1, i2, i3, i4):
        super().__init__(i1, i2, i3, i4)
        self.old_speed = self.actual_speed
        self.old_num_step = self.num_step
        self.step_counter = 0
        self.max_speed_reached = 0
        self.real_time_used = 0

        # Control conditions
        # self.stepper_is_really_accelerating = False
        self.stepper_max_speed_is_acceptable = True
        self.stepper_acceleration_rate_is_correct = True
        self.stepper_total_step_number_is_correct = False

    def run_one_step(self):
        super().run_one_step()
        self.step_counter += 1

        if self.actual_speed != self.old_speed:
            if self.actual_speed > self.old_speed:
                if self.actual_speed > self.MAX_SPEED:
                    self.stepper_max_speed_is_acceptable = False
            actual_acceleration_rate = abs(self.actual_speed - self.old_speed)
            if actual_acceleration_rate != self.acceleration_factor:
                self.stepper_acceleration_rate_is_correct = False

        if self.actual_speed > self.max_speed_reached:
            self.max_speed_reached = self.actual_speed
        self.old_speed = self.actual_speed

    def move(self, step_num, speed):
        self.step_counter = 0
        self.max_speed_reached = 0

        start_time = time.time()
        super().move(step_num, speed)
        self.real_time_used = time.time() - start_time

        # avoid to lose some errors sent back with *return* statement
        if super().move(step_num, speed) is not None:
            return super().move(step_num, speed)
        if self.step_counter == self.num_step:
            self.stepper_total_step_number_is_correct = True


class PrimesTestCase (unittest.TestCase):
    """Tests for the stepper class"""

    # # # # # # # # # # # # # # # # # # # #
    # # #   Set up test boundaries    # # #
    # # # # # # # # # # # # # # # # # # # #

    @patch('wiringpi.wiringPiSetup', stub_wiringPiSetup)
    def setUp(self):
        self.test_engine = TestStepper(0, 1, 2, 3)
        self.test_engine.acceleration_factor = 2

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

    def test_initial_speed(self):
        self.assertEqual(self.test_engine.actspeed, 0)

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
        print("Running a simulation of the engine movement. Please wait")
        self.test_engine.move(1000, 250)
        self.assertTrue(self.test_engine.stepper_max_speed_is_acceptable)
        self.assertTrue(self.test_engine.stepper_acceleration_rate_is_correct)
        self.assertTrue(self.test_engine.stepper_total_step_number_is_correct)

        self.test_engine.move(100, -250)
        self.assertTrue(self.test_engine.stepper_max_speed_is_acceptable)
        self.assertTrue(self.test_engine.stepper_acceleration_rate_is_correct)
        self.assertTrue(self.test_engine.stepper_total_step_number_is_correct)

    def test_move_with_very_high_speed(self):
        """Test what happen while trying to set extreme high speed"""
        print("Running a simulation of the engine movement. Please wait")
        self.test_engine.move(1000, 10000000)
        self.assertTrue(self.test_engine.stepper_max_speed_is_acceptable)
        self.assertTrue(self.test_engine.stepper_acceleration_rate_is_correct)
        self.assertTrue(self.test_engine.stepper_total_step_number_is_correct)

    def test_move_with_very_low_speed(self):
        """Test what happen with a speed very low or equal to 0"""
        print("Running a simulation of the engine movement. Please wait")
        self.test_engine.move(20, 0)
        self.assertTrue(self.test_engine.stepper_max_speed_is_acceptable)
        self.assertTrue(self.test_engine.stepper_acceleration_rate_is_correct)
        self.assertTrue(self.test_engine.stepper_total_step_number_is_correct)

        self.test_engine.move(20, 1)
        self.assertTrue(self.test_engine.stepper_max_speed_is_acceptable)
        self.assertTrue(self.test_engine.stepper_acceleration_rate_is_correct)
        self.assertTrue(self.test_engine.stepper_total_step_number_is_correct)

    def test_move_with_invalid_values(self):
        """Test what happen with negative speed, step number and direction"""
        self.assertEqual(self.test_engine.move(-100, -250), "Invalid input. step_num has to be positive")
        self.assertEqual(self.test_engine.move(-100, 250), "Invalid input. step_num has to be positive")

    def test_move_with_wrong_data_types_float(self):
        """Test what happen if user insert floating numbers as inputs"""
        print("Running a simulation of the engine movement. Please wait")
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

    @staticmethod
    def calculate_theoretical_values(input_steps, input_speed, acceleration_factor):
        """Calculate the time and the maximum speed that should be theoretically obtained with an ideal engine"""

        acceleration_steps = int(input_speed / acceleration_factor)
        max_speed_reachable = input_speed
        if acceleration_steps > (input_steps / 2):
            acceleration_steps = int(input_steps / 2)
            max_speed_reachable = acceleration_steps * acceleration_factor
        constant_speed_steps = input_steps - (2 * acceleration_steps)

        t_acc = 0
        for i in range(acceleration_steps):
            t_acc += 1 / (acceleration_factor * (i + 1))

        t_maxs = constant_speed_steps / max_speed_reachable

        t_tot = 2 * t_acc + t_maxs

        return [t_tot, max_speed_reachable]

    def casual_values(self):
        """Create a set of random variables for an hypothetical engine"""
        steps = randint(1, 5000)
        speed = randint(self.test_engine.MIN_SPEED, self.test_engine.MAX_SPEED)
        acceleration_factor = randint(1, 5)

        return [steps, speed, acceleration_factor]

    def test_expected_behavior_measuring_time_and_speed(self):
        """Measure the gap between the ideal and the simulated engine"""
        for i in range(10):
            c = self.casual_values()
            results = self.calculate_theoretical_values(c[0], c[1], c[2])

            print("   TEST  # ", i+1)
            print("Starting simulation with\nSteps = ", c[0], "\nSpeed = ", c[1], "\nAccel. factor = ", c[2])
            print("Theoretical time = ", results[0])
            print("Theoretical max speed = ", results[1])

            self.test_engine.acceleration_factor = c[2]
            self.test_engine.move(c[0], c[1])

            print("Real time used = ", self.test_engine.real_time_used)
            print("Real max speed reached = ", self.test_engine.max_speed_reached)

            if self.test_engine.real_time_used > results[0]:
                time_percentage_error = (abs(self.test_engine.real_time_used / results[0]) - 1) * 100
            else:
                time_percentage_error = (1 - abs(self.test_engine.real_time_used / results[0])) * 100

            if self.test_engine.max_speed_reached > results[1]:
                speed_percentage_error = abs(abs(self.test_engine.max_speed_reached / results[1]) - 1) * 100
            else:
                speed_percentage_error = abs(1 - abs(self.test_engine.max_speed_reached / results[1])) * 100

            print("\nPercentage errors: SPEED = ", speed_percentage_error, "   TIME = ", time_percentage_error)
            print("\n\n")

            self.assertLess(time_percentage_error, 10, "Error < 10%")
            self.assertLess(speed_percentage_error, 1, "Error < 1%")


if __name__ == '__main__':
    unittest.main()
