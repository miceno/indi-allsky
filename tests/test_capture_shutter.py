import unittest

from indi_allsky.devices.exceptions import DeviceControlException

try:
    from indi_allsky.capture import CaptureWorker
except ModuleNotFoundError as e:
    raise unittest.SkipTest('Capture worker dependencies are unavailable: {0}'.format(e.name))


class FakeShutter:
    def __init__(self, events, fail_open_once=False):
        self.events = events
        self.fail_open_once = fail_open_once

    @property
    def state(self):
        return None

    @state.setter
    def state(self, new_state):
        self.events.append(('shutter', new_state))
        if new_state == 'open' and self.fail_open_once:
            self.fail_open_once = False
            raise DeviceControlException('PWM write failed')

    def deinit(self):
        pass


class FakeCamera:
    def __init__(self, events):
        self.events = events

    def setCcdExposure(self, *args, **kwargs):
        self.events.append(('exposure', args, kwargs))


class CaptureShutterTest(unittest.TestCase):
    def make_worker(self, night=False, fail_open_once=False):
        events = []
        worker = CaptureWorker.__new__(CaptureWorker)
        worker.night = night
        worker.shutter = FakeShutter(events, fail_open_once=fail_open_once)
        worker._shutter_exposure_active = False
        worker.indiclient = FakeCamera(events)
        return worker, events

    def test_daytime_exposure_opens_before_capture_and_closes_when_ready(self):
        worker, events = self.make_worker()

        worker.shoot(1.0, 1.0, 1)
        worker._close_shutter_after_exposure()

        self.assertEqual(
            [event[0:2] for event in events],
            [
                ('shutter', 'open'),
                ('exposure', (1.0, 1.0, 1)),
                ('shutter', 'closed'),
            ],
        )
        self.assertFalse(worker._shutter_exposure_active)

    def test_nighttime_exposure_does_not_move_shutter(self):
        worker, events = self.make_worker(night=True)

        worker.shoot(1.0, 1.0, 1)

        self.assertEqual(events[0][0], 'exposure')
        self.assertFalse(worker._shutter_exposure_active)

    def test_shutter_error_recovers_open_without_blocking_exposure(self):
        worker, events = self.make_worker(fail_open_once=True)

        worker.shoot(1.0, 1.0, 1)

        self.assertEqual(
            [event[0:2] for event in events],
            [
                ('shutter', 'open'),
                ('shutter', 'open'),
                ('exposure', (1.0, 1.0, 1)),
            ],
        )
        self.assertTrue(worker._shutter_exposure_active)
