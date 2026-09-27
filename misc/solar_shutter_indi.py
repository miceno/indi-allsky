#!/usr/bin/env python3
"""
Indi-AllSky Integrated Module: Dynamic Solar Shutter Controller
Queries indi-allsky configuration and image records to match the active day cycle and exposure times.
"""

import os
import sys
import time
import logging
from datetime import datetime
from pathlib import Path

import lgpio
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm.exc import NoResultFound


sys.path.insert(0, str(Path(__file__).parent.absolute().parent))

from indi_allsky.config import IndiAllSkyConfig
from indi_allsky.flask import create_app
from indi_allsky.flask.models import IndiAllSkyDbImageTable


app = create_app()
app.app_context().push()

# Logging architecture mirroring indi-allsky
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

# Hardware Configuration
GPIO_PIN = 18
CHIP_NUM = 0

# Safety Constraints (Fallback defaults if DB is temporarily locked)
DEFAULT_CYCLE = 120
LEAD_TIME = 2  # Timing cushion before shutter release (seconds)
MIN_DURATION = 3  # Minimum safe window for exposure + I/O write (seconds)
IMAGE_PROCESSING_OVERHEAD = 2.5  # Processing and disk I/O margin (seconds)


class IndiAllSkyShutter:
    def __init__(self, pin, chip=0):
        self.pin = pin
        self.chip_handle = None

        try:
            self.chip_handle = lgpio.gpiochip_open(chip)
            logging.info(f"Connected to GPIO chip {chip} via lgpio module.")
        except lgpio.error as e:
            logging.critical(f"Hardware Layer Blocked: {e}")
            sys.exit(1)

    def _query_indi_config(self):
        """Read the configured daytime capture interval."""
        try:
            config = IndiAllSkyConfig().config
            return float(config.get("EXPOSURE_PERIOD_DAY", DEFAULT_CYCLE))
        except (NoResultFound, SQLAlchemyError, TypeError, ValueError) as e:
            logging.warning(f"Database read delay or config missing, using fallback cycle. Error: {e}")
        return DEFAULT_CYCLE

    def _query_dynamic_exposure(self):
        """Fetches the actual exposure length of the last successfully recorded day image."""
        try:
            image = IndiAllSkyDbImageTable.query\
                .order_by(IndiAllSkyDbImageTable.id.desc())\
                .first()

            if image and image.exposure:
                exposure_seconds = float(image.exposure)
                dynamic_duration = max(MIN_DURATION, exposure_seconds + IMAGE_PROCESSING_OVERHEAD)
                return dynamic_duration
        except (SQLAlchemyError, TypeError, ValueError) as e:
            logging.debug(f"Could not read dynamic exposure column, using safe margin: {e}")
        return MIN_DURATION

    def move_shutter(self, position):
        """Drives the SG90/TS90MD via hardware timed duty-cycles."""
        if not self.chip_handle:
            return
        try:
            if position == "open":
                logging.info("Opening solar shutter to safe Park Position (0° North).")
                lgpio.tx_servo(self.chip_handle, self.pin, 600)
                time.sleep(0.5)
            elif position == "close":
                logging.info("Closing solar shutter over the cúpula (90° Cover).")
                lgpio.tx_servo(self.chip_handle, self.pin, 1500)
                time.sleep(1.0)
                # Detach hardware signal immediately to prevent gear stripping from Ourense wind
                lgpio.tx_servo(self.chip_handle, self.pin, 0)
        except lgpio.error as err:
            logging.error(f"Hardware execution error: {err}")

    def start_sync_loop(self):
        logging.info("Solar Shutter Subsystem running. State: CLOSED (Protected).")
        self.move_shutter("close")

        while True:
            try:
                # 1. Pull current dynamic values from indi-allsky relational database
                capture_cycle = self._query_indi_config()
                photo_duration = self._query_dynamic_exposure()

                # 2. Track timing window
                now = datetime.now()
                cycle_seconds = (now.minute * 60 + now.second) % capture_cycle

                # 3. Handle activation sequence
                if cycle_seconds == (capture_cycle - LEAD_TIME):
                    logging.info(f"Sync event triggered. Cycle: {capture_cycle}s | Expected Photo Window: {photo_duration}s")
                    self.move_shutter("open")

                    # Keep open through lead window and the dynamically calculated exposure time
                    time.sleep(LEAD_TIME + photo_duration)

                    self.move_shutter("close")

                time.sleep(0.4)  # Conservative polling frequency

            except KeyboardInterrupt:
                logging.info("Keyboard interrupt caught. Exiting daemon context.")
                break
        self.cleanup()

    def cleanup(self):
        if self.chip_handle:
            try:
                lgpio.tx_servo(self.chip_handle, self.pin, 0)
                lgpio.gpiochip_close(self.chip_handle)
                logging.info("Lgpio factory resources released. System Offline.")
            except lgpio.error:
                pass


if __name__ == "__main__":
    if os.getuid() != 0:
        logging.critical("Root access required to interface with Trixie's native pinctrl driver.")
        sys.exit(1)

    shutter_app = IndiAllSkyShutter(pin=GPIO_PIN, chip=CHIP_NUM)
    shutter_app.start_sync_loop()
