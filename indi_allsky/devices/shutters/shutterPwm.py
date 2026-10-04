import logging
import math
import time

from .shutterBase import ShutterBase

from ..exceptions import DeviceControlException


logger = logging.getLogger('indi_allsky')


class ShutterPwm(ShutterBase):
    PWM_FREQUENCY = 50
    MIN_PULSE_US = 500
    MAX_PULSE_US = 2500

    def __init__(self, *args, **kwargs):
        super(ShutterPwm, self).__init__(*args, **kwargs)

        pin_1_name = kwargs['pin_1_name']
        self.open_pulse_us = int(kwargs['open_pulse_us'])
        self.closed_pulse_us = int(kwargs['closed_pulse_us'])
        self.settle_time = float(kwargs['settle_time'])

        for pulse_us in (self.open_pulse_us, self.closed_pulse_us):
            if not self.MIN_PULSE_US <= pulse_us <= self.MAX_PULSE_US:
                raise ValueError('Servo pulse width must be between 500 and 2500 microseconds')

        if self.open_pulse_us == self.closed_pulse_us:
            raise ValueError('Open and closed servo pulse widths must differ')

        if not math.isfinite(self.settle_time) or not 0 <= self.settle_time <= 30:
            raise ValueError('Servo settling time must be between 0 and 30 seconds')

        logger.info('Initializing PWM SHUTTER device: %s (%d Hz)', str(pin_1_name), self.PWM_FREQUENCY)

        try:
            import board
            import pwmio

            pwm_pin = getattr(board, pin_1_name)
            self.pwm = pwmio.PWMOut(pwm_pin, frequency=self.PWM_FREQUENCY)
        except Exception as e:  # catch all exceptions from the hardware library
            logger.error('GPIO exception: %s', str(e))
            raise DeviceControlException from e

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, new_state):
        if new_state not in (self.OPEN, self.CLOSED):
            raise ValueError('Shutter state must be "open" or "closed"')

        pulse_us = self.open_pulse_us if new_state == self.OPEN else self.closed_pulse_us
        duty_cycle = int((pulse_us * self.PWM_FREQUENCY * (2 ** 16 - 1)) / 1000000)

        try:
            self.pwm.duty_cycle = duty_cycle
        except Exception as e:  # catch all exceptions from the hardware library
            logger.error('GPIO exception: %s', str(e))
            raise DeviceControlException from e

        self._state = new_state
        logger.info('Set shutter state: %s (%d us)', new_state, pulse_us)
        time.sleep(self.settle_time)

    def deinit(self):
        super(ShutterPwm, self).deinit()
        try:
            self.pwm.deinit()
        except Exception as e:  # catch all exceptions from the hardware library
            logger.error('GPIO exception: %s', str(e))
            raise DeviceControlException from e
