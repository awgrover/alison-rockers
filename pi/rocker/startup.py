#!/usr/bin/env python3

# This starts things w/in the gui,
# so needs to go at xsession startup,
# so:
# edit /etc/xdg/lxsession/LXDE/autostart
#   @python3 /home/pi/rocker/startup.py > /home/pi/rocker/log/startup.log 2>&1
#   (?? logging where)

from time import sleep

import sys; sys.path.append('lib')
from rocker_lib import *

sleep(5)

try:
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
