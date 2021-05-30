import subprocess, atexit, sys, os
from datetime import datetime

import sys; sys.path.append('lib')
from every.every import Every

AppDir = "/home/pi/rocker"
LoggerProcess = 'rocker-logger'
Logfile = AppDir + "/log/rocker.log"
JumperFile = AppDir + "/log/jumper-setting"
JumperProcess = "jumper-reader" # also + .py for actual script

VolumeProcess = 'rf-to-volume'
VideoProcess = 'run-video'

# Jumper for A|B designation
# nb, ground is physical 39
BPin = 21 # physical pin 40 to physical pin 39

# fixme: consider quieting things if headless... xrandr -> "Can't open display" vs /^\S+ connected/

def ensure_command_exists(executable):
    proc = subprocess.run(['which',executable], stdout=subprocess.DEVNULL)
    if proc.returncode != 0:
        log("Need executable '{:}'".format(executable))
        return False
    else:
        return True

def ensure_process(process_name, command_args, logger_message ):
    # Tests for the process_name, starts it if it is not running.
    # sets the "name" of the process for easier identification
    # command_args is: [ executable, *args] (uses subprocess.Popen)
    # logger_message is sent only on startup
    # Does not suppress stderr (does suppress stdout)

    # FIXME: lockfile for "ensure_process"
    executable = command_args.pop(0)

    proc = subprocess.run(['which', executable], stdout=subprocess.DEVNULL)
    if proc.returncode != 0:
        print("No '{:}'!".format(executable))
        while(1):
            pass

    if subprocess.run(['pidof', process_name], stdout=subprocess.DEVNULL).returncode != 0:
        # we want an easy to identify name: LoggerProcess
        print("Ensure {:} AS {:}".format(process_name, command_args))
        print("  exec {:} ... {:}".format(executable, command_args))
        subprocess.Popen([process_name, *command_args], executable=executable, close_fds=True)
        log("")
        log(logger_message)

def ensure_log_dir():
    if subprocess.run(['mkdir','-p', AppDir + "/log"]).returncode != 0:
        print("Couldn't mkdir {:}/log".format(AppDir))

def ensure_logger():
    ensure_log_dir()
    ensure_process(
        LoggerProcess, 
        [ 'lxterminal', '-e', "tail -f "+Logfile ],
        'Alison Safford Rocker Pi'
        )
    print("started")

def ensure_video_process():
    # separate process runs correct video
    ensure_process(
        VideoProcess, 
        [ 'python3', VideoProcess + ".py" ],
        "Startup {:}".format(VideoProcess)
        )

def ensure_volume_process():
    ensure_process(
        VolumeProcess, 
        [ 'python3', VolumeProcess + ".py" ],
        "Startup {:}".format(VolumeProcess)
        )

def ensure_jumper_process():
    # separate process reads/notes which jumper
    ensure_process(
        JumperProcess, 
        [ 'python3', JumperProcess + ".py" ],
        "Startup {:}".format(JumperProcess)
        )

def log(message):
    # timestamp string to our log for the logger-terminal to show
    with open(Logfile, 'a') as lh:
        lh.write("{:} {:} {:}\n".format(datetime.now().isoformat(), sys.argv[0], message))

def ab_jumpers():
    # Don't bash the file, just periodically read it
    global ab_jumpers_interval
    if not ( 'ab_jumpers_interval' in globals()):
        ab_jumpers_interval = Every(0.5)
    global ab_jumpers_last
    if not ( 'ab_jumpers_last' in globals()):
        ab_jumpers_last = 'A'
        log("Init jumper " + ab_jumpers_last)
        print("Init jumper " + ab_jumpers_last)

    # try to log errors only once
    global ab_jumpers_last_error
    if not ('ab_jumpers_last_error' in globals()):
        ab_jumpers_last_error = None

    j=None
    if ab_jumpers_interval():
        try:
            with open(JumperFile,mode='r') as f:
                j = f.read().rstrip()
                if not (j in ['A','B']):
                    raise ValueError("Expected A|B in {:}, saw: {:}".format(JumperFile, j))
                if j != ab_jumpers_last:
                    log("Jumper " + ab_jumpers_last)
                    print("Jumper " + ab_jumpers_last)
                ab_jumpers_last = j

        except FileNotFoundError as err:
            print("First time for " + JumperFile)
            ab_jumpers_last = 'A' # might as well default to something

        except (AttributeError, ValueError, FileNotFoundError) as err: # None does AttributeError
            if str(err) != str(ab_jumpers_last_error):
                ab_jumpers_last_error = err
                log("Bad value in {:} : {:}".format(JumperFile, err))
                print(err)
                if j != ab_jumpers_last:
                    log("Err jumper " + ab_jumpers_last)
                    print("Err jumper " + ab_jumpers_last)
            ab_jumpers_last = 'A' # might as well default to something

    return ab_jumpers_last

def ensure_zenity():
    if ensure_command_exists('zenity'):
        print("zenity!")
        # initial announce
        proc = subprocess.Popen(['zenity', '--info', '--text', sys.argv[0]])
        atexit.register(close_process, [proc])
    else:
        # Extra complain
        subprocess.run(['lxterminal', '-e', "echo 'Need zenity installed.'; while true; do true; done"])

def alert(message):
    return subprocess.Popen(['zenity', '--info', '--text', message])

def close_process(procs):
    for proc in procs:
        proc.kill()

