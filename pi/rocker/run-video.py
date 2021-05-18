#!/usr/bin/env python3
# Figure out which video to run,
# setup black background, ensure video is running.
# Detect jumper setup to decide on video/message.

import subprocess, atexit, sys, os
from datetime import datetime
import time

# features we need: zenity
# detect setup: wait till ready, change detect
# show black-background, start video
# ensure video

AppDir = "/home/pi/rocker"
Logfile = AppDir + "/rocker.log"
LoggerProcess = 'rocker-logger'
# nb, ground is phsical 39
# because we pulse the RF signal, we need a timeout:
ButtonTimeout = 5 # consider the button still "on" for this many seconds
APin = 21 # physical pin 40
FIXME: just a "B" pin, absence = A
BPin = 26 # physical pin 37

def close_process(procs):
    for proc in procs:
        proc.kill()

def log(message):
    # timestamp string to our log for the logger-terminal to show
    with open(Logfile, 'a') as lh:
        lh.write("{:} {:} {:}\n".format(datetime.now().isoformat(), sys.argv[0], message))

def ensure_logger():
    proc = subprocess.run(['which','lxterminal'], stdout=subprocess.DEVNULL)
    if proc.returncode != 0:
        print("No lxterminal!")
        while(1):
            pass
    print("lxterminal!")

    if subprocess.run(['pidof', LoggerProcess], stdout=subprocess.DEVNULL).returncode != 0:
        # we want an easy to identify name: LoggerProcess
        subprocess.Popen([LoggerProcess, '-e', "tail -f "+Logfile], executable='lxterminal', close_fds=True)
        log("")
        log("Alison Safford Rocker Pi")

    print("started")

def ensure_zenity():
    proc = subprocess.run(['which','zenity'], stdout=subprocess.DEVNULL)
    if proc.returncode == 0:
        print("zenity!")
        proc = subprocess.Popen(['zenity', '--info', '--text', sys.argv[0]])
        atexit.register(close_process, [proc])
        return # ok
    
    # Complain
    log("Need zenity installed")
    subprocess.run(['lxterminal', '-e', "echo 'Need zenity installed.'; while true; do true; done"])

def alert(message):
    return subprocess.Popen(['zenity', '--info', '--text', message])

import select
def std_available(message):
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
    global last
    if not ('last' in globals()):
        last = 0
    global last_button_time
    if not ('last_button_time' in globals()):
        last_button_time = None
    
    which = last
    
    if std_available("isatty: type A or B or space (and return) to change"):
        possible = sys.stdin.read(1)
        if possible == "\n":
            # nb: you don't see the return when you hit return, you see a previous return...
            return last # ignore
        which = None if possible == ' ' else possible
        print(">'{:}' '{:}'-> '{:}'".format(possible, last, which))
    else:
        # check gpio
        if buttons['A'].is_pressed:
            which = 'A'
        elif buttons['B'].is_pressed:
            which = 'B'
        else:
            which = None

    changed = False
    if which != last:
        print("Changed to '{:}'".format(which))
        last=which
        changed = True

    action(changed, last, *more)

    return last

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
    global procs
    if not ('procs' in globals()):
        procs = []
        atexit.register(close_process, procs)
    global running # video that should be running
    if not ('running' in globals()):
        running = None

    if changed:
        running = _run_video(procs, which_jumper, videos)
    elif running:

        # single letter status
        proc = subprocess.run( ['ps', '-h', '-o', 's', '-p', str(running.pid)], capture_output=True)
        # byte-string, not string
        if proc.returncode != 0 or proc.stdout == b"Z\n" :
            if proc.stdout == b"Z\n":
                log("zombie")
                running.wait()
            log("Video unexpectedly stopped for {:}".format(which_jumper))
            running = _run_video(procs, which_jumper, videos)

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
