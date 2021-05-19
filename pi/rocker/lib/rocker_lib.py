import subprocess, atexit, sys, os
from datetime import datetime

AppDir = "/home/pi/rocker"
LoggerProcess = 'rocker-logger'
Logfile = AppDir + "/rocker.log"
JumperFile = Appdir + "/jumper-setting"
JumperProcess = "jumper-reader" # also + .py for actual script

# Jumper for A|B designation
# nb, ground is physical 39
BPin = 21 # physical pin 40 to physical pin 39

def ensure_command_exists(executable):
    proc = subprocess.run(['which','zenity'], stdout=subprocess.DEVNULL)
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

def ensure_logger():
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
    if check_jumper_file():
        with open(JumperFile,mode='r') as f:
            try:
                j = f.read().rstrip()
                if not (j in ['A','B']):
                    raise ValueError("Expected A|B in {:}, saw: {:}".format(JumperFile, j))

            except (AttributeError, ValueError) as err: # None does AttributeError
                log("Bad value in {:} : {:}".format(JumperFile, err))
                return 'A' # might as well default to something
            return j

