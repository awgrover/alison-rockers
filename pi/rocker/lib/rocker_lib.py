import subprocess, atexit, sys, os

AppDir = "/home/pi/rocker"
LoggerProcess = 'rocker-logger'
Logfile = AppDir + "/rocker.log"

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

