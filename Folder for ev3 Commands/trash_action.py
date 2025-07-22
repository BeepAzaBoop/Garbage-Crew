#!/usr/bin/env python3
from ev3dev2.motor import LargeMotor, OUTPUT_C, SpeedPercent
import time

trap_motor = LargeMotor(OUTPUT_C)
speed = SpeedPercent(50)

print("Trash detected → opening and closing trap.")
trap_motor.on_for_degrees(speed, -95)  # Open trap
time.sleep(0.5)
trap_motor.on_for_degrees(speed, 95)   # Close trap
print("Trash action completed.")