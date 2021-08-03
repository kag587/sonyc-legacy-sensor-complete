import logging
import logging.handlers
import os
import socket
import fcntl
import struct
import sys
from subprocess import check_output


class Filter(logging.Filter):
    def filter(self, record):
        return not record.levelno > 30


def getMac(ifname):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        mac = fcntl.ioctl(s.fileno(),
                          0x8927,  # SIOCSIFHWADDR
                          struct.pack('256s', ifname[:15]))
        mac_formatted = ''.join(['%.2x:' % ord(char) for char in mac[18:24]])[:-1]
        return mac_formatted
    except Exception as e:
        pass

class ContextFilter(logging.Filter):
    """
    Class to inject contextual information into the log
    """
    try:
        git_hash = check_output("git --git-dir /home/sonyc/sonycnode/.git rev-parse --short HEAD".split()).strip()
    except:
        git_hash = 'unknown'
        
    def filter(self, record):
        record.git_hash = ContextFilter.git_hash
        return True
    
def sonycLogger(loggername):
    """
    Create Logging files for Sonyc's Network Manager
    """
    LOG_FNAME = os.path.join("/mnt/sonycdata",
                             loggername)
    logger = logging.getLogger(loggername)
    
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s [#%(git_hash)7s] [%(name)8s] [%(levelname)7s] "
                                  "(%(module)s.%(filename)s.%(funcName)s() : %(lineno)s) -- %(message)s",
                                  datefmt="%d-%m-%Y %H:%M:%S")

    f_contextFilter = ContextFilter()
    logger.addFilter(f_contextFilter)
    
    # Set up TimedRotatingFileHandler with MemoryHandler
    f_handler = logging.handlers.TimedRotatingFileHandler(
        LOG_FNAME, when="midnight", interval=1, backupCount=5)
    f_handler.suffix = getMac('eth0') + '--%b-%d-%Y--%H-%M-%S.log'
    f_handler.setFormatter(formatter)
    memoryHandler = logging.handlers.MemoryHandler(capacity=2000, target=f_handler)

    # Set up stdout StreamHandler
    s_handler = logging.StreamHandler(stream=sys.stdout)
    s_handler.setLevel(logging.INFO)
    s_handler.setFormatter(formatter)
    s_handler.addFilter(Filter())

    # Set up stderr StreamHandler
    e_handler = logging.StreamHandler(stream=sys.stderr)
    e_handler.setLevel(logging.ERROR)
    e_handler.setFormatter(formatter)

    # Add Handlers to the module
    logger.addHandler(s_handler)
    logger.addHandler(e_handler)
    logger.addHandler(memoryHandler)
    return logger

'''
if __name__ == "__main__":
    sonyc_logger = sonycLogger()
    for i in range(20):
        time.sleep(.2)
        sonyc_logger.debug('i = %d'%i)
'''
