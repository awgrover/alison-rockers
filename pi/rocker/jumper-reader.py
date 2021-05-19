#!/usr/bin/env python3
"""
Read the A/B jumper, write to a file, so others can share it.

use ab_jumper() to get current value.

"""

import os
import sys; sys.path.append('lib')
from time import sleep

from rocker_lib import *

from gpiozero import Button
def setup_gpio():
    buttons = {}
    buttons['B'] = Button(BPin)
    return buttons

ensure_logger()
ensure_zenity()
log("Start")
buttons = setup_gpio()

first_time = True

jumper_file_temp = JumperFile + '.tmp'

while(True):
    was_jumper = ab_jumpers()
    jumper = 'B' if buttons['B'].is_pressed else 'A'

    # don't write if not changed
    if was_jumper != jumper or (not os.path.exists(JumperFile)):
        with open(jumper_file_temp, mode='w') as f:
            f.write(jumper)
            f.write("\n")
        # 'mv' is atomic in linux
        proc = subprocess.run( ['mv', jumper_file_temp, JumperFile] )
        if proc.returncode != 0:
            log("Fail to mv to "+JumperFile)
        else:
            log("Jumper " + jumper)
            if first_time:
                alert(jumper)
                print("Jumper " + jumper)
    # don't need to check very often
    sleep(0.1)
