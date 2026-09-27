# Overview
The shutter controller support in indi-allsky is intended to use the GPIO or PWM pins from a SBC such as a Raspberry PI to drive either a MOSFET or relay to manage a shutter or a shader state.

The default functionality is to move the shutter during the day between exposures, so it will be the shutter will cover the camera most of the time, but will move to allow taking exposures. During the night it might also operate and in case of rain, it will protect the camera dome from water drops.

The shutter is actioned by a servo, with two positions: open and close. Open means the shutter is open and the camera can take pictures. Close means the shutter is closed and the camera is covered by the shutter.

## GPIO Permissions
If you receive a `PermissionDenied` exception when accessing GPIO pins

https://github.com/aaronwmorris/indi-allsky/wiki/GPIO-Permissions

## WARNING
**The pins from a SBC cannot be used to directly drive a servo.  Trying to do so WILL damage your system.**