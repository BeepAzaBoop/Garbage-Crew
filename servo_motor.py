from gpiozero import AngularServo
from gpiozero.pins.pigpio import PiGPIOFactory
from subprocess import Popen, PIPE, CalledProcessError
import time
from time import sleep
def start_pigpiod():
    try:
        p = Popen(["sudo", "pigpiod"], stdout=PIPE, stderr=PIPE, shell = True)
        out, err = p.communicate(timeout = 2)
        if b"already running" in err:
            print("pigpiod is already running")
        else: print("pigpiod started successfully")
    except CalledProcessError as e:
        print(f"Error starting pigpiod: {e}")
    except TimeoutError:
        print("Timeout while starting pigpiod")

start_pigpiod()
time.sleep(0.5)

factory = PiGPIOFactory()
servo = AngularServo(14, min_angle= -90, max_angle=90, pin_factory=factory)

# servo motor control functions
def sort_to_compost():
    try:
        servo.angle = 60
        time.sleep(3.0) 
        servo.angle = 0   
    except Exception as e:
        print(f"Error controlling servo for compost: {e}")

def sort_to_recyclable():
    try:
        servo.angle = 60
        time.sleep(2.0)
        servo.angle = 0
    except Exception as e:
        print(f"Error controlling servo for recyclable: {e}")

def sort_to_trash():
    try:
        servo.angle = 60
        time.sleep(1.0)
        servo.angle = 0
    except Exception as e:
        print(f"Error controlling servo for trash: {e}")