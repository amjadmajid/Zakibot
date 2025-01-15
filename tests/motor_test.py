import sys
import os
import unittest
from unittest.mock import patch

# Add parent directory to sys.path
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, parent_dir)

from MotorModule import Motor

class TestMotor(unittest.TestCase):
    @patch('RPi.GPIO.output')
    def test_motor_stop(self, mock_output):
        motor = Motor(13, 5, 6, 27, 17, 12)
        motor.stop(2)
        self.assertTrue(mock_output.called)

if __name__ == "__main__":
    unittest.main()
