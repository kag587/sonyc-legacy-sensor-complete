import os
import subprocess
import ConfigParser
from sonycnode.utils import sonyc_logger as loggerClass

logger = loggerClass.sonycLogger(loggername="misc")

def execute(command=None, std_in=subprocess.PIPE,
            std_out=subprocess.PIPE, std_err=subprocess.PIPE):
    """
    Execute shell commands
    
    Parameters
    ----------
    command: list
        command string should be split at every space
        and be passed as a list

    Returns
    -------
    out: str
        string output of the command
    err: bool
        True if error was raised in executing the command
    """
    logger.debug("Executing: "+" ".join(command))
    out = err = False
    try:
        proc = subprocess.Popen([cmd for cmd in command],
                                stdin=std_in,
                                stdout=std_out,
                                stderr=std_err)
        out, err = proc.communicate()
    except Exception as ex:
        logger.error("Error executing: "+" ".join(command)+ " "+ str(ex))
        err = True
    finally:
        return out, err


def load_settings():
    """
    Loads the setting files. Settings will default to the ones in
    the package if configuration files are not found.
    http://stackoverflow.com/questions/3430372/how-to-get-full-path-of-current-files-directory-in-python
    """
    local_dir = os.path.dirname(os.path.abspath(__file__))
    configFileLoc = [os.path.join(local_dir,'settings.conf'),
                     '/etc/sonyc-settings.conf']
    parser = ConfigParser.SafeConfigParser()
    parser.read(configFileLoc)
    return parser

def run_once(func):
    """
    Decorator to run the function
    `func` only once
    """
    def wrapper(*args, **kwargs):
        if not wrapper.has_run:
            wrapper.has_run = True
            return func(*args, **kwargs)
        wrapper.has_run = False
    return wrapper
