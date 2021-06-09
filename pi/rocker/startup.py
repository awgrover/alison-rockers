#!/usr/bin/env python3

# This starts things w/in the gui,
# so needs to go at xsession startup,
# Note ~/no-rocker inhibit
# Note ~/leave-lxpanel inhibit
# Note jumper on pins 26/20 inhibit

from time import sleep

import sys; sys.path.append('lib')
from pathlib import Path
import subprocess
from rocker_lib import *

# Paired for a jumper:
InhibitingJumper_LOW = 26
InhibitingJumper = 20

def kill_lxpanel():
    if not Path("/home/pi/leave-lxpanel").exists():
       subprocess.run(['killall', '--signal', 'SIGTERM', 'lxpanel'], stdout=subprocess.DEVNULL)

from gpiozero import Button
import RPi.GPIO as GPIO
def setup_gpio():
     # Paired for a jumper
     GPIO.setmode(GPIO.BCM)
     GPIO.setup(InhibitingJumper_LOW, GPIO.OUT)
     GPIO.output(InhibitingJumper_LOW, 0)
     return Button(InhibitingJumper)

def inhibiting_jumper(jumper):
    # true if want-to-inhibit
    return jumper.is_pressed


if Path("/home/pi/no-rocker").exists():
    print("no-rocker!")
    exit(0)

sleep(5)

try:
    jumper = setup_gpio()
    kill_lxpanel()
    ensure_logger()
    ensure_zenity()
    sleep(3)
    while(not inhibiting_jumper(jumper) ):
        ensure_jumper_process()
        sleep(1)
        ensure_volume_process()
        sleep(2)
        ensure_video_process()
        sleep(5)
except Exception as err:
    print("Startup failed " + str(err))
    log("Startup failed " + str(err))
    alert("Startup failed " + str(err))
subprocess.Popen(['lxpanel', '--profile', 'LXDE-pi'], start_new_session=True)
subprocess.Popen(['./stopall','--ignorestartup'], close_fds=True)
