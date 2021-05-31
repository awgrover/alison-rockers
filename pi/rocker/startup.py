#!/usr/bin/env python3

# This starts things w/in the gui,
# so needs to go at xsession startup,
# so:
# edit /etc/xdg/lxsession/LXDE/autostart
#   @python3 /home/pi/rocker/startup.py > /home/pi/rocker/log/startup.log 2>&1
#   (?? logging where)

from time import sleep

import sys; sys.path.append('lib')
from pathlib import Path
import subprocess
from rocker_lib import *

def kill_lxpanel():
    if not Path("/home/pi/leave-lxpanel").exists():
       subprocess.run(['killall', '--signal', 'HUP', 'lxpanel'], stdout=subprocess.DEVNULL)

if Path("/home/pi/no-rocker").exists():
    print("no-rocker!")
    exit(0)

sleep(5)

try:
    kill_lxpanel()
    ensure_logger()
    ensure_zenity()
    sleep(3)
    while(True):
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
