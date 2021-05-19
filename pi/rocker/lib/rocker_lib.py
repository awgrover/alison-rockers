import subprocess, atexit, sys, os
from datetime import datetime

AppDir = "/home/pi/rocker"
LoggerProcess = 'rocker-logger'
Logfile = AppDir + "/log/rocker.log"
JumperFile = AppDir + "/log/jumper-setting"
JumperProcess = "jumper-reader" # also + .py for actual script

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
    print("Ensure {:} AS {:}".format(process_name, command_args))
    executable = command_args.pop(0)
    print("  exec {:} ... {:}".format(executable, command_args))

    proc = subprocess.run(['which', executable], stdout=subprocess.DEVNULL)
    if proc.returncode != 0:
        print("No '{:}'!".format(executable))
        while(1):
            pass
    print(executable + "!")

    if subprocess.run(['pidof', process_name], stdout=subprocess.DEVNULL).returncode != 0:
        # we want an easy to identify name: LoggerProcess
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

def log(message):
    # timestamp string to our log for the logger-terminal to show
    with open(Logfile, 'a') as lh:
        lh.write("{:} {:} {:}\n".format(datetime.now().isoformat(), sys.argv[0], message))

def ab_jumpers():
    # try to log errors only once
    global last_error
    if not ('last_error' in globals()):
        last_error = None

    try:
        with open(JumperFile,mode='r') as f:
            j = f.read().rstrip()
            if not (j in ['A','B']):
                raise ValueError("Expected A|B in {:}, saw: {:}".format(JumperFile, j))
            return j

    except (AttributeError, ValueError, FileNotFoundError) as err: # None does AttributeError
        if str(err) != str(last_error):
            last_error = err
            log("Bad value in {:} : {:}".format(JumperFile, err))
            print(err)
        return 'A' # might as well default to something

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

