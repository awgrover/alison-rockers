#!/usr/bin/env python3
"""
Respond to the corresponding keyfob/rocker by fading the LEFT channel volume in/out.

We do need to know if we are "A" or "B", so we know which receiver "data" to look at: see ab_jumpers()

We have "persistance": the transmitter sends a pulse every 4 seconds or so to indicate "on",
so we stay on for that long (at least) before deciding it has gone "off".

Works with the default audio out: either hdmi or headphone-jack.

"""

from time import sleep
from gpiozero import Button

import sys; sys.path.append('lib')
from rocker_lib import *
from every.every import Every

# pin 2 & 4 are 5v, pin 6 is ground
# pin 14 is ground
RFA_Pin = 23 # physical 16
RFB_Pin = 24 # physical 18
# pin 20 is ground

# one shot timer
# False the first time it is tested
rf_persistance = Every( 5, 0)  # only requires a pulse every 5 seconds to stay on

# States
# We only need to be moving towards on/off,
# because we'll stay stuck at max/min when we get there
# which is "on" and "off"
S_RampUp=0; S_RampDown=1;
state = S_RampDown
print("State -> {:}".format(state))

# Volumes are in percent, should be the "volume" control in the UI
min=50
max=100
volume = max
volumeChange = Every( 2.0 / (max-min) ) # take 2 seconds to step down

def setup_gio():
    # RF signals are high?
    rf = {}
    rf['A'] = Button(RFA_Pin)
    rf['B'] = Button(RFB_Pin)
    return rf

def set_volume(volume):
    # cmd = ['amixer', 'set', 'Speaker', '{:}%,{:}%'.format(volume, 100)]
    cmd = ['pactl', '--', 'set-sink-volume', '@DEFAULT_SINK@', '{:}%'.format(volume), '{:}%'.format(100)]
    print(" ".join(cmd))
    subprocess.call(cmd)

ensure_logger()
log("Start")
if not ensure_command_exists('pactl'):
    log("Fail no 'pactl'")
    alert("Fail, no 'pactl'")
set_volume(max)

rf = setup_gio()

while(True):
    which_jumper = ab_jumpers()

    # on rf, we'll start to ramp-up, and keep track of rf_persistance
    if rf[which_jumper].is_pressed:
        rf_persistance.start() # reset
        if state == S_RampDown:
            # new sit'ing
            state = S_RampUp
            print("State -> {:}".format(state))
            log("Sit!")

    # on persistance expire, move towards off
    if rf_persistance():
        state = S_RampDown
        print("xState -> {:}".format(state))
        log("Stand!")

    # rate of volume change
    if volumeChange():
        changed = False
        if (volume > min and state == S_RampDown) or (volume < max and state == S_RampUp):
            volume = volume + (
                -1 if state == S_RampDown else ( 1 if state == S_RampUp else 0)
                )
            changed = True
        #print("  {:}".format(volume)

        # don't waste time setting volume if it hasn't changed
        if changed:
            set_volume(volume)

    if volume == min or volume == max:
        # we can sleep longer, no work to do
        sleep(0.1)
    else:
        # changing volume, so short sleep!
        sleep( volumeChange.interval[0] / 2.0 ) # yea, will be off by 1/4 interval on average
