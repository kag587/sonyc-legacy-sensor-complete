__author__ = "Mohit Sharma"

# ----
# Low level access to Wireless extensions
# This class uses wireless_info and wireless_config struct in iwlib.h
# http://www.mit.edu/afs.new/sipb/project/merakidev/usr/include/iwlib.h
# It also contains methods for makeing and parsing Linux ioctl calls
# ----

import socket
import struct
import fcntl
import array


class Ioctl(object):
    def __init__(self):
        self.fsock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
