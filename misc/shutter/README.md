
```commandline
sudo dtoverlay pwm-2chan
pinctrl -p

 1: 3v3
 2: 5v
 3: ip    pu | hi // GPIO2 = input
 4: 5v
 5: ip    pu | hi // GPIO3 = input
 6: gnd
 7: ip    pu | hi // GPIO4 = input
 8: ip    pn | hi // GPIO14 = input
 9: gnd
10: ip    pu | hi // GPIO15 = input
11: ip    pd | lo // GPIO17 = input
12: a5    pd | lo // GPIO18 = *PWM0_0*
13: ip    pd | lo // GPIO27 = input
14: gnd
15: ip    pd | lo // GPIO22 = input
16: ip    pd | lo // GPIO23 = input
17: 3v3
18: ip    pd | lo // GPIO24 = input
19: ip    pd | lo // GPIO10 = input
20: gnd
21: ip    pd | lo // GPIO9 = input
22: ip    pd | lo // GPIO25 = input
23: ip    pd | lo // GPIO11 = input
24: ip    pu | hi // GPIO8 = input
25: gnd
26: ip    pu | hi // GPIO7 = input
27: ip    pu | hi // GPIO0 = input
28: ip    pu | hi // GPIO1 = input
29: ip    pu | hi // GPIO5 = input
30: gnd
31: ip    pu | hi // GPIO6 = input
32: ip    pd | lo // GPIO12 = input
33: ip    pd | lo // GPIO13 = input
34: gnd
35: a5    pd | lo // GPIO19 = *PWM0_1*
36: ip    pd | lo // GPIO16 = input
37: ip    pd | lo // GPIO26 = input
38: ip    pd | lo // GPIO20 = input
39: gnd
40: ip    pd | lo // GPIO21 = input
```

to move the pwm to gpio12 and gpio13:
```
sudo dtoverlay pwm-2chan pin=12 pin2=13
```

To test the servo
```commandline
sudo python3 ~/indi-allsky/misc/shutter/shutter_pwm_fixed_180dg.py
Solar Shutter active on GPIO 18 (Hardware PWM). Default state: CLOSED.
[00:15:47] Sunshade closed.
[00:15:48] Sunshade opened.
[00:15:54] Sunshade closed.
...
```

Or 
```commandline
sudo python3 ~/indi-allsky/misc/shutter/shutter_sg90_90d.py 
Solar Shutter active on GPIO 18 (SG90 90-degree range). Default state: CLOSED.
[00:16:12] Sunshade closed (90°).
[00:16:13] Sunshade opened (0°).
[00:16:18] Sunshade closed (90°).
```

