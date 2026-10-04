# Shutter

## Overview

indi-allsky supports an optional positional servo shutter controlled by the capture worker. Select **Shutter - Positional Servo [PWM]** in the Devices configuration to enable it. With the default empty driver selection, shutter control is disabled.

The application opens the shutter for daytime camera exposures, including daytime SQM exposures, and closes it once the camera reports that exposure/readout has completed. Nighttime operation is not supported.

## Configuration

Configure these fields in the Devices tab:

| Setting             | Default             | Description                                                                                |
|---------------------|---------------------|--------------------------------------------------------------------------------------------|
| GPIO Pin            | Unset               | Blinka board pin connected to the servo signal input; set this before enabling the driver. |
| Open Pulse Width    | `1000` microseconds | PWM pulse width for the open position.                                                     |
| Closed Pulse Width  | `2000` microseconds | PWM pulse width for the closed position.                                                   |
| Servo Settling Time | `1.0` seconds       | Delay after each position command; opening waits this long before exposure starts.         |

The servo PWM signal runs at 50 Hz. Pulse widths must be between 500 and 2500 microseconds and the open and closed values must differ. These defaults are starting values only: servo travel and safe endpoints vary by model and mechanism. Calibrate pulse widths and settling time for the installed hardware to avoid driving the servo against its mechanical stops.

At capture-worker startup, the application makes a best-effort move to CLOSED. Before each daytime exposure it commands OPEN and waits the configured settling time before issuing the camera exposure. It keeps the shutter open until the camera reports that exposure/readout is complete, then commands CLOSED before image processing or saving. The capture loop remains authoritative for exposure timing; a separate polling daemon or image-database query is not used.

At shutdown, the application attempts to move CLOSED and releases the PWM resource.

## Errors and capture continuity

Shutter initialization or control errors are logged and do not block camera capture. If a position command fails, the application makes a best-effort command to OPEN; a failure of that recovery command is also logged. If initialization fails, shutter control is unavailable for that capture-worker run. The servo has no position feedback, so a successful command does not guarantee that the requested physical position was reached.

## Hardware and scope

Use a positional servo controlled by PWM. The GPIO signal pin, open/closed pulse widths, and settling time are configurable. Do not power the servo directly from an SBC GPIO pin; use a suitable servo power supply and follow board and servo requirements for signal reference and wiring.

Nighttime shutter operation, rain-triggered closure, and relay/MOSFET binary actuators are not supported. The standalone script in `misc/solar_shutter_indi.py` is a prototype and is not used by the integrated feature.

## GPIO permissions

If you receive a `PermissionDenied` exception when accessing GPIO pins, see the [GPIO Permissions guide](https://github.com/aaronwmorris/indi-allsky/wiki/GPIO-Permissions).
