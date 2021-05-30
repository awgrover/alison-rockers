#!/usr/bin/env python3
"""
Just open/run the logger till exit. Debugging.
"""

import os
from time import sleep

import sys; sys.path.append('lib')
from rocker_lib import *

ensure_logger()
ensure_zenity()
log("Start")


while(True):
    sleep(10)
