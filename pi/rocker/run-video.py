#!/usr/bin/env python3
# Figure out which video to run,
# setup black background, ensure video is running.
# Detect jumper setup to decide on video/message.

import subprocess, atexit, sys, os
from datetime import datetime
import time

from rocker_lib import *

# features we need: zenity
# detect setup: wait till ready, change detect
# show black-background, start video
# ensure video

import select
def std_available(message):
    # read 1 char from stdin
    # non-blocking, but you  have to EOL to send input
    global first_time
    if not ('first_time' in globals()):
        first_time = True
    if first_time:
        first_time = False
        print(message)

    return sys.stdin.isatty() and select.select([sys.stdin], [], [], 0) == ([sys.stdin], [], [])

def react_ab_jumpers(buttons, action, *more):
    # read jumpers
    # call action(A|B) w/ changed
    # return current jumper
    global react_ab_jumpers_last
    if not ('react_ab_jumpers_last' in globals()):
        react_ab_jumpers_last = 0
    
    which = ab_jumper()
    
    changed = False
    if which != react_ab_jumpers_last:
        print("Changed to '{:}'".format(which))
        react_ab_jumpers_last=which
        changed = True

    action(changed, react_ab_jumpers_last, *more)

    return react_ab_jumpers_last

def ensure_video_files():
    videos = { 'A' : [], 'B' : [] }

    for f in os.listdir(AppDir):
        if f.startswith('A-'):
            videos['A'].append(f)
        elif f.startswith('B-'):
            videos['B'].append(f)

    for prefix in videos.keys():
        if not videos[prefix]:
            message = "No videos with prefix '{:}-' found in {:}".format(prefix, AppDir)
            log(message)
            raise Exception(message)
        elif len( videos[prefix] ) != 1:
            message = "More than 1 videos (saw {:}) with prefix '{:}-' found in {:} : {:}".format(len( videos[prefix] ),prefix, AppDir, ", ".join(videos[prefix]) )
            log(message)
            raise Exception(message)

    a = videos['A'][0]
    b = videos['B'][0]
    log(a)
    log(b)
    return { 'A' : a, 'B' : b }

def run_video(changed, which_jumper, videos): # a react_ab_jumpers() fn
    global run_video_procs
    if not ('run_video_procs' in globals()):
        run_video_procs = []
        atexit.register(close_process, run_video_procs)
    global running # video that should be running
    if not ('running' in globals()):
        running = None

    if changed:
        running = _run_video(run_video_procs, which_jumper, videos)
    elif running:

        # single letter status
        proc = subprocess.run( ['ps', '-h', '-o', 's', '-p', str(running.pid)], capture_output=True)
        # byte-string, not string
        if proc.returncode != 0 or proc.stdout == b"Z\n" :
            if proc.stdout == b"Z\n":
                log("zombie")
                running.wait()
            log("Video unexpectedly stopped for {:}".format(which_jumper))
            running = _run_video(run_video_procs, which_jumper, videos)

from gpiozero import Button
def setup_gpio():
    buttons = {}
    buttons['A'] = Button(APin)
    buttons['B'] = Button(BPin)
    return buttons

def _run_video(procs, which_jumper, videos):
    # cleanup
    for p in procs:
        print("kill {:}".format(" ".join(p.args)))
        p.kill()
        p.wait()
    procs.clear()

    if which_jumper == None:
        procs.append( 
            alert("No A/B jumper detected. Place jumper to configure this Pi") 
            )
        return None
    elif which_jumper in videos:
        procs.append(
            subprocess.Popen( ['mirage','-f','empty.jpg'], stderr=subprocess.DEVNULL, close_fds=True) 
            )
        # ensure the "blanking" has time to start
        # because we want it to be below vlc
        time.sleep(2)
        log("Play " + videos[which_jumper])
        procs.append(
            subprocess.Popen(['cvlc', '--quiet', '--no-video-title', '--loop', '-f', videos[which_jumper]], stderr=subprocess.DEVNULL, close_fds=True)
            )

        return procs[-1]
    else:
        procs.append( alert("Internal error, expected [{:}], saw '{:}'".format(", ".join(videos.keys()), which_jumper) ) )
        return None

ensure_logger()
log("Start")

ensure_zenity()
try:
    buttons = setup_gpio()
    videos = ensure_video_files()
    while(True):
        react_ab_jumpers( buttons, run_video, videos )
        time.sleep(0.2)
except Exception as err:
    log("Crashed: {:}".format(err))
    raise err
