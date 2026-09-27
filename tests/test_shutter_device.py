import sys
import types
import unittest
from unittest.mock import patch

from indi_allsky.devices.exceptions import DeviceControlException
from indi_allsky.devices.shutters.shutterBase import ShutterBase
from indi_allsky.devices.shutters.shutterPwm import ShutterPwm


class FakePwmOut:
    def __init__(self, pin, frequency):
        self.pin = pin
        self.frequency = frequency
        self.duty_cycle = None
        self.deinitialized = False

    def deinit(self):
        self.deinitialized = True


class ShutterPwmTest(unittest.TestCase):
    def make_shutter(self):
        board = types.ModuleType('board')
        board.D18 = object()

        pwmio = types.ModuleType('pwmio')
        pwmio.PWMOut = FakePwmOut

        with patch.dict(sys.modules, {'board': board, 'pwmio': pwmio}):
            with patch('indi_allsky.devices.shutters.shutterPwm.time.sleep'):
                return ShutterPwm(
                    {},
                    pin_1_name='D18',
                    open_pulse_us=1000,
                    closed_pulse_us=2000,
                    settle_time=1.0,
                )


    def test_shutter_pwm_sets_servo_pulses_and_releases_pwm(self):
        shutter = self.make_shutter()

        self.assertIsNone(shutter.state)
        self.assertEqual(shutter.pwm.frequency, 50)

        with patch('indi_allsky.devices.shutters.shutterPwm.time.sleep') as sleep_mock:
            shutter.state = ShutterBase.OPEN
            self.assertEqual(shutter.pwm.duty_cycle, int(1000 * 50 * 65535 / 1000000))

            shutter.state = ShutterBase.CLOSED
            self.assertEqual(shutter.pwm.duty_cycle, int(2000 * 50 * 65535 / 1000000))
            self.assertEqual(sleep_mock.call_count, 2)

        shutter.deinit()
        self.assertTrue(shutter.pwm.deinitialized)


    def test_shutter_rejects_invalid_servo_configuration(self):
        invalid_settings = (
            (1000, 1000, 1.0),
            (499, 2000, 1.0),
            (1000, 2501, 1.0),
            (1000, 2000, 31.0),
        )

        for open_pulse_us, closed_pulse_us, settle_time in invalid_settings:
            with self.subTest(
                open_pulse_us=open_pulse_us,
                closed_pulse_us=closed_pulse_us,
                settle_time=settle_time,
            ):
                with self.assertRaises(ValueError):
                    ShutterPwm(
                        {},
                        pin_1_name='D18',
                        open_pulse_us=open_pulse_us,
                        closed_pulse_us=closed_pulse_us,
                        settle_time=settle_time,
                    )


    def test_shutter_wraps_pwm_output_errors(self):
        board = types.ModuleType('board')
        board.D18 = object()

        class FailingPwmOut:
            def __init__(self, pin, frequency):
                raise OSError('PWM unavailable')

        pwmio = types.ModuleType('pwmio')
        pwmio.PWMOut = FailingPwmOut

        with patch.dict(sys.modules, {'board': board, 'pwmio': pwmio}):
            with self.assertRaises(DeviceControlException):
                ShutterPwm(
                    {},
                    pin_1_name='D18',
                    open_pulse_us=1000,
                    closed_pulse_us=2000,
                    settle_time=1.0,
                )


if __name__ == '__main__':
    unittest.main()
