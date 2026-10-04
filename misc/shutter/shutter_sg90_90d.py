import os
import time
from datetime import datetime

# Hardware PWM Path under Trixie (pwm-2chan overlay maps GPIO 18 to pwm0)
PWM_CHIP = "/sys/class/pwm/pwmchip0"
PWM_CHANNEL_DIR = f"{PWM_CHIP}/pwm0"  # pwm0 is strictly linked to GPIO 18

CAPTURE_CYCLE = 15  # Interval between photos (120 seconds)
LEAD_TIME = 2  # Seconds BEFORE the photo to open the sunshade
PHOTO_DURATION = 3  # Exposure and processing margin (3 seconds)


def setup_trixie_hardware_pwm():
    """Ensures the hardware driver is exported and listening on GPIO 18."""
    if not os.path.exists(PWM_CHANNEL_DIR):
        try:
            with open(f"{PWM_CHIP}/export", "w") as f:
                f.write("0")  # Export channel 0 (GPIO 18)
            time.sleep(0.3)
        except Exception as e:
            print("Hardware Error: Please run this script with SUDO privileges.")
            exit()

    # Set total frequency period to 50Hz (20,000,000 nanoseconds)
    with open(f"{PWM_CHANNEL_DIR}/period", "w") as f:
        f.write("20000000")

    # Enable the hardware clock channel
    with open(f"{PWM_CHANNEL_DIR}/enable", "w") as f:
        f.write("1")


def move_sunshade(position):
    """
    Controls the SG90 servo using raw hardware pulse times (nanoseconds):
    - open:  600,000  ns (0.6ms pulse) -> 0 degrees (Retracted to the North)
    - close: 1,500,000 ns (1.5ms pulse) -> Exactly 90 degrees (Covering the dome)
    - off:   0 ns -> Detach to protect plastic gears from wind strain
    """
    duty_path = f"{PWM_CHANNEL_DIR}/duty_cycle"

    if position == "open":
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Sunshade opened (0°).")
        with open(duty_path, "w") as f:
            f.write("600000")  # Safe starting pulse for SG90 to avoid jitter
        time.sleep(0.6)  # Wait for physical movement to complete
    elif position == "close":
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Sunshade closed (90°).")
        with open(duty_path, "w") as f:
            f.write("1500000")  # Center position (90 degrees)
        time.sleep(1.0)  # Settle wood arm vibrations
        # Detach signal right after closing to protect gears from Ourense wind forces
        with open(duty_path, "w") as f:
            f.write("0")


try:
    setup_trixie_hardware_pwm()
    print("Solar Shutter active on GPIO 18 (SG90 90-degree range). Default state: CLOSED.")
    move_sunshade("close")  # Initialize protecting the sensor

    while True:
        now = datetime.now()
        cycle_seconds = (now.minute * 60 + now.second) % CAPTURE_CYCLE

        # Trigger window (e.g., at second 118 of the 120s cycle)
        if cycle_seconds == (CAPTURE_CYCLE - LEAD_TIME):
            move_sunshade("open")
            time.sleep(LEAD_TIME + PHOTO_DURATION)
            move_sunshade("close")

        time.sleep(0.5)  # Safe CPU sleep

except KeyboardInterrupt:
    print("\nStopping Solar Shutter daemon...")
finally:
    # Ensure the pulse is turned off safely on exit to detach the servo
    try:
        with open(f"{PWM_CHANNEL_DIR}/duty_cycle", "w") as f:
            f.write("0")
    except:
        pass
    print("System offline.")

