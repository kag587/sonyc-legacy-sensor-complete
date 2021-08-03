import socket
import subprocess
import os
import re
import fcntl
import struct
import pycurl
import certifi
import cStringIO
import multiprocessing
import json
import time
from random import choice
from shutil import copyfile
from sonycnode.utils import misc
from sonycnode.network import vpnswitch
from sonycnode.network import ifconfig as ifc
from sonycnode.utils import sonyc_logger as loggerClass

logger      = loggerClass.sonycLogger(loggername="netmanager")
ifconfig    = ifc.Ifconfig()

parser      = misc.load_settings()

ifacename   = parser.get('network', 'ifname').strip("'\"")
ap_path     = parser.get('network', 'ap_path').strip("'\"")
#trusted_ap = ["s0nycL1f3l1ne"] # .. for dev
trusted_ap  = map(lambda x: x.split('.conf')[0],
                  os.listdir(ap_path))
dns_servers = json.loads(parser.get('network', 'dns_servers'))
vpn_servers = json.loads(parser.get('network', 'vpn_servers'))


use_tls     = parser.getboolean('network', 'use_https')
server_port = 443

#mac_address = getMac(ifacename)

# ---
#    Functions for managing network connectivity
# ---

def getMac(ifacename):
    """
    Returns MAC address of the interface
    `ifacename`
    Prameters
    ---------
    ifacename: str
        interface name. e.g. "wlan0"
    Returns
    -------
    mac_address: str
        mac address for `ifacename`
    """
    try:
        return ifconfig.parameters(ifacename).get('mac', '')

    #try:
    #    sck = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    #    mac = fcntl.ioctl(sck.fileno(),
    #                      0x8927, #SIOCSIFWHADDR
    #                      struct.pack('256s', ifacename[:15]))
    #    mac_address = ''.join(['%.2x:'%ord(char) for char in mac[18:24]])[:-1]
    #    return mac_address
    except Exception as ex:
        logger.error("Error getting Mac address "+str(ex))

def getIP(ifacename):
    """
    Returns IP address of the interface 
    `ifacename`
    Parameters
    ----------
    ifacename: str
        interface name. e.g. "wlan0"
    Returns
    -------
    ip_address: str
        ip address for `ifacename`
    """
    try:
        return ifconfig.parameters(ifacename).get('inet', '')
        #sck = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        #return socket.inet_ntoa(fcntl.ioctl(
        #    sck.fileno(),
        #    0x8915,
        #    struct.pack('256s', ifacename[:15])
        #)[20:24])
    except Exception as ex:
        logger.error("Error getting ip address: " + str(ex))


def connectivity(host=None, port=None, iface=None, timeout=5):
    """
    Check connectivity by creating a TCP stream with
    the host and port. 
    
    Parameters
    ----------
    host: str
        ip address of the host
    port: int
        port of the host to connect to
    timeout: int, optional
        timeout before closing the tcp stream

    Returns
    -------
    connectivity: bool
        True if setting up stream was successful
        False if timeout
    """
    s = None
    try:
        socket.setdefaulttimeout(timeout)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if iface:
            # from socket.h, SO_BINDTODEVICE is mapped to 25
            s.setsockopt(socket.SOL_SOCKET, 25, iface)
        s.connect((host, port))
        s.shutdown(2)
        s.close()
        return True
    except Exception as ex:
        #logger.warning(str(ex) + " for " + str(host))
        return False

def copyWpaConfigFile(ap_name):
    """
    Copy the wpa_supplicant configuration file
    from the `./aps` folder to /etc/wpa_supplicant/wpa_supplicant.conf
    
    Parameters
    ----------
    ap_name: str
        `ap_name` should match the essid in the `trusted_ap` list
    
    Returns
    -------
    status: bool
        False if the exception was raised when copying
    """
    try:
        logger.info("Copying config for: " + str(ap_name))
        copyfile(os.path.join(ap_path, str(ap_name) + ".conf"), "/etc/wpa_supplicant/wpa_supplicant.conf")
        return True
    except Exception as ex:
        logger.error("Error copying to wpa_supplicant: "+str(ex))
        return False


def parseWpaConfigFile():
    """
    Parse the wpa_supplicant.conf file.
    Returns
    -------
    wpa_dict: dict
        key value pair containing values from
        the config file
    """
    wpa_fname = "/etc/wpa_supplicant/wpa_supplicant.conf"
    wpa_conf = None
    wpa_dic = {}
    
    def _todic(x):
        if len(x) > 1:
            wpa_dic.update({x[0]: x[1].strip('"')})
    
    try:
        with open(wpa_fname) as fh:
            wpa_conf = fh.read()
        map(_todic, map(lambda x: x.split("="), wpa_conf.split()))
        for lines in wpa_conf.splitlines():
            match = re.match(".*(\sssid=)(?P<ssid>[^\\n]*).*", lines)
            if match:
                wpa_dic.update({'ssid': match.groupdict()['ssid'].strip('"')})
    except Exception as ex:
        logger.error("Error parsing wpa_supplicant: "+str(ex))
        wpa_dic.update({'ssid': 'n/a'})
    
    return wpa_dic
    
    
def restartIface(ifname=None):
    """
    Restart the network interface

    Parameters
    ----------
    ifname: str
        Interface name
    
    Returns
    -------
    ifstatus: bool
        False if Interface `ifname` could not 
        be brought up
    """
    logger.info("Restarting Interface")
    try:
        vpnswitch.disableVPN()
        ifdown_command = ['sudo', 'ifdown', ifname, '--force', '&&', 'sleep 5']
        ifup_command = ['sudo', 'ifup', ifname, '&&', 'sleep 5']
        logger.debug("Putting interface down")
        misc.execute(ifdown_command)
        time.sleep(5)
        logger.debug("Putting interface up")
        misc.execute(ifup_command)
        return True
    except Exception as ex:
        logger.error("Cannot bring interface up: "+str(ex))
        return False

    
def connectedToInternet(iface=None):
    """
    Function to check if the device can connect to one of dns servers
    Returns
    -------
    connected: bool
        True if connected to Internet
    """
    return connectivity(host=choice(dns_servers), iface=iface, port=53, timeout=5)


def connectedToVPN():
    """
    Function to check if the device can connect to one of the vpn servers
    Returns
    -------
    connected: bool
        True if connected to vpn
    """
    return connectivity(host=choice(vpn_servers), iface=None, port=server_port, timeout=5)


def connectToVPN():
    """
    Function to handle connecting to VPN
    """
    if not connectedToVPN():
        # Connect to VPN
        vpnswitch.enableVPN()
        time.sleep(2)
        vpnswitch.updateIptables(getIP("tun0")+"/24")
