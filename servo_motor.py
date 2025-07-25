from gpiozero import AngularServo
from gpiozero.pins.pigpio import PiGPIOFactory
from subprocess import run, CalledProcessError
import time

def start_pigpiod():
    try:
        result = run("sudo pigpiod", shell=True, capture_output=True, timeout=2)
        if b"already running" in result.stderr:
            print("pigpiod already running")
        else:
            print("Started pigpiod")
    except (CalledProcessError, TimeoutError):
        print("Failed to start pigpiod")

start_pigpiod()
time.sleep(0.5)

factory = PiGPIOFactory()
servo = AngularServo(14, pin_factory=factory, min_angle=0, max_angle=360)
servo.angle = 360

def move_servo(angle, delay):
    try:
        servo.angle = angle
        time.sleep(delay)
        servo.angle = 360
    except Exception as e:
        print(f"Servo error: {e}")

def sort_to_compost():
    move_servo(90, 1.5)

def sort_to_recyclable():
    move_servo(90, 1.0)

def sort_to_trash():
    move_servo(90, 0.5)
