# Shutter

## First-release specification

Shutter control is a planned first-class indi-allsky feature coordinated with the camera capture loop. This page specifies the intended behavior; it is not yet implemented in the main application. The standalone script in `misc/solar_shutter_indi.py` is a prototype and is not the feature's operational contract.

The first release supports a positional servo with two configured positions:

- **Open:** the camera aperture is unobstructed for an exposure.
- **Closed:** the camera aperture is covered between daytime exposures.

### Daytime capture sequence

When shutter control is enabled:

1. At startup, make a best-effort move to CLOSED.
2. Before each scheduled daytime camera exposure, command OPEN and allow the configured servo travel/settling time before starting the exposure.
3. Keep the shutter open until the camera reports that exposure/readout has completed.
4. Then command CLOSED. Do not keep it open while the image is processed or saved.

The capture loop, rather than a separate polling daemon or image-database query, coordinates these transitions and remains authoritative for exposure cadence. Shutter timing must be coordinated with that schedule; do not start an exposure before the shutter has had time to open.

### Errors and capture continuity

If a shutter-control operation fails, report the error and make a best-effort command to move OPEN. Do not block or abort camera captures because of a shutter-control error. The servo has no position feedback in this specification, so a successful command does not guarantee that the requested physical position was reached.

### Hardware and configuration

The actuator for this release is a positional servo controlled by PWM. The GPIO output, open/closed pulse widths, and travel/settling time must be configurable for the target board and servo; pin numbers, pulse-width values, and delays used by the prototype are not defaults established by this specification.

Power the servo according to its electrical requirements. Do not power it directly from an SBC GPIO pin; use an appropriate servo supply and follow the board and servo requirements for the signal reference and wiring.

### Out of scope

- Nighttime shutter operation.
- Rain-triggered closure. indi-allsky may report rain sensor data, but rain is not a shutter-control trigger in this release.
- Relay/MOSFET binary actuator support.

## GPIO permissions

If you receive a `PermissionDenied` exception when accessing GPIO pins, see the [GPIO Permissions guide](https://github.com/aaronwmorris/indi-allsky/wiki/GPIO-Permissions).
