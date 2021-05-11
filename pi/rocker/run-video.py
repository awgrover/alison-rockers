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

def react_ab_jumpers(actor, *more):
    # read jumpers
    # call actor(A|B) w/ changed
    # return current jumper
    global last
    if not ('last' in globals()):
        last = None
    
    which = last
    
    if std_available("isatty: type A or B or space (and return) to change"):
        possible = sys.stdin.read(1)
        if possible == "\n":
            # nb: you don't see the return when you hit return, you see a previous return...
            return last # ignore
        which = None if possible == ' ' else possible
    else:
        # check gpio
        pass

    changed = False
    if which != last:
        #print("Changed to '{:}'".format(which))
        last=which
        changed = True

    actor(changed, last, *more)

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
    global running # should be running
    if not ('running' in globals()):
        running = None


    if changed:
        running = _run_video(procs, which_jumper, videos)
    elif running:

        # single letter status
        proc = subprocess.run( ['ps', '-h', '-o', 's', '-p', str(running.pid)], capture_output=True)
        print("runnign? '{:}'".format(proc.stdout))
        # byte-string, not string
        if proc.returncode != 0 or proc.stdout == b"Z\n" :
            if proc.stdout == b"Z\n":
                log("zombie")
                running.wait()
            log("Video unexpectedly stopped for {:}".format(which_jumper))
            running = _run_video(procs, which_jumper, videos)

def _run_video(procs, which_jumper, videos):
    # cleanup
    for p in procs:
        p.kill()
    procs = []

    if which_jumper == None:
        procs.append( 
            alert("No A/B jumper detected. Place jumper to configure this Pi") 
            )
        return None
    elif which_jumper in videos:
        print("change to: {:}".format(which_jumper))
        procs.append(
            subprocess.Popen( ['mirage','-f','empty.jpg'], stderr=subprocess.DEVNULL, close_fds=True) 
            )
        # ensure the "blanking" has time to start
        # because we want it to be below vlc
        time.sleep(2)
        log("Play " + videos[which_jumper])
        procs.append(
            #subprocess.Popen(['cvlc', '--quiet', '--loop', '-f', videos[which_jumper]], close_fds=True)
            subprocess.Popen(['cvlc', '--quiet', '--no-video-title', '--no-loop', '-f', videos[which_jumper]], stderr=subprocess.DEVNULL, close_fds=True)
            )
        return procs[-1]
    else:
        procs.append( alert("Internal error, expected [{:}], saw '{:}'".format(", ".join(videos.keys()), which_jumper) ) )
        return None

ensure_logger()
log("Start")

ensure_zenity()
try:
    videos = ensure_video_files()
    while(True):
        react_ab_jumpers( run_video, videos )
        time.sleep(0.2)
except Exception as err:
    log("Crashed: {:}".format(err))
    raise err

exit(0)

try:
    speaker_test = False
    # speaker_test = subprocess.Popen(['speaker-test', '-t', 'pink', '-c', '1', '-l', '0'], close_fds=True)
    # turn off GUI controls because background, and don't need them
    #speaker_test = subprocess.Popen(['vlc', '--quiet', '--intf', 'dummy', '-f', '/home/pi/rain.mp4'], close_fds=True)
    speaker_test = subprocess.Popen(['vlc', '--quiet', '-f', '/home/pi/rain.mp4'], close_fds=True)

    min=50
    max=100
    while(True):
        for v in range(0,50):
            print("V {:}".format(v))
            # cmd = ['amixer', 'set', 'Speaker', '{:}%,{:}%'.format(v+min, 50-v+50)]
            cmd = ['pactl', '--', 'set-sink-volume', '@DEFAULT_SINK@', '{:}%'.format(v+min), '{:}%'.format(50-v+min)]

            print(" ".join(cmd))
            subprocess.call(cmd)
            time.sleep(0.25)

finally:
    if speaker_test:
        speaker_test.kill()
    print( "exiting\n")
