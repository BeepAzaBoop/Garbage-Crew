#!/usr/bin/env python3
from ev3dev2.motor import LargeMotor, OUTPUT_A, SpeedPercent
import time

panel_left = LargeMotor(OUTPUT_A)
speed = SpeedPercent(50)

print("Compost detected → moving panel left.")
panel_left.on_for_degrees(speed, 45)
time.sleep(0.5)
panel_left.on_for_degrees(speed, -45)
print("Compost action completed.")
