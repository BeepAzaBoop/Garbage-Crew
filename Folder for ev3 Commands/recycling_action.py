#!/usr/bin/env python3
from ev3dev2.motor import LargeMotor, OUTPUT_B, SpeedPercent
import time

panel_right = LargeMotor(OUTPUT_B)
speed = SpeedPercent(50)

print("Recycling detected → moving panel right.")
panel_right.on_for_degrees(speed, 45)
time.sleep(0.5)
panel_right.on_for_degrees(speed, -45)
print("Recycling action completed.")