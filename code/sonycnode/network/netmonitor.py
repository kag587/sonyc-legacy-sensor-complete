import multiprocessing
import time
import atexit
import sched
import os
import socket
import json
from collections import deque, Counter
from multiprocessing.connection import Client
from sonycnode.network import netmanager as nm
from sonycnode.network import iw
from sonycnode.network import ifconfig as ifc
from sonycnode.network import vpnswitch
from sonycnode.utils import sonyc_logger as loggerClass
from sonycnode.utils import misc
from sonycnode.utils.misc import run_once

logger       = loggerClass.sonycLogger(loggername="netmonitor")
sc           = sched.scheduler(time.time, time.sleep)
parser       = misc.load_settings()

IFNAME       = parser.get('network', 'ifname').strip("'\"")
CHECK_EVERY  = parser.getint('network', 'monitor_every')

# For some reason x.strip(.conf) was removing 'n' from nyu-legacy
# so using split('.conf')[0]
ap_path      = parser.get('network', 'ap_path').strip("'\"")
TRUSTED_AP   = map(lambda x: x.split('.conf')[0],
                 os.listdir(ap_path))
HIDDEN_AP    = json.loads(parser.get('network', 'hidden_aps'))
PREFERRED_AP = parser.get('network', 'preferred_ap').strip("'\"")
IPC_PORT     = parser.getint('network', 'ipc_port')
IPC_AUTH     = parser.get('network', 'ipc_auth').strip("'\"")
MONITOR_NETWORK     = parser.getboolean('network', 'monitor_network')


wlan = iw.WLan(iface=IFNAME)
ifconfig = ifc.Ifconfig()

logger.setLevel(20)


def _setup(ev, vpn_ev, ap_ev,
           intstat, vpnstat,
           ap_dict):
    """
    Setup the global events that will be used
    to trigger monitoring functions
    Paramters
    ---------
    ev: `multiprocessing.Event`
        This will be used to trigger non VPN
        monitoring function
    vpn_ev: `multiprocessing.Event`
        This will be used to trigger VPN monitoring
        function
    intstat: `multiprocessing.Manager.Value`
        `Value` object to store the status of non vpn
        traffic
    vpnstat: `multiprocessing.Manager.Value`
        `Value` object to store the status of VPN traffic
    ap_dict: `multiprocessing.Manager.dict`
        `dictionary containing scanned and trusted AP
    """
    monitorInternet.flag   = ev
    monitorVPN.flag        = vpn_ev
    monitorAP.flag         = ap_ev
    monitorInternet.status = intstat
    monitorVPN.status      = vpnstat
    monitorAP.ap_dict      = ap_dict


def monitorInternet(*args):
    """
    Monitor non VPN traffic for connectivity.
    calling function will tell when to start
    monitoring the non VPN traffic by setting
    the global event. Refer `_setup()`
    """
    multiprocessing.current_process().name = "MonitorInternet"
    # Always Run
    while True:
        # blocking wait
        if MONITOR_NETWORK:
            monitorInternet.flag.wait()
            monitorInternet.status.value = nm.connectedToInternet()
        else:
            monitorInternet.status.value = True
        time.sleep(5)


def monitorVPN(*args):
    """
    Monitor VPN connection. calling function will
    set the global event to inform when to start
    monitoring. Refer `_setup()`
    """
    multiprocessing.current_process().name = "MonitorVPN"
    while True:
        # blocking wait
        if MONITOR_NETWORK:
            monitorVPN.flag.wait()
            monitorVPN.status.value = nm.connectedToVPN()
        else:
            monitorVPN.status.value = True
        time.sleep(5)


def monitorAP(*args):
    """
    Monitor surrounding Access Points and return the
    accesspoints that match the whitelisted accesspoints
    sorted by link quality
    """
    multiprocessing.current_process().name = "MonitorAP"
    while True:
        if MONITOR_NETWORK:
            try:
                # blocking wait
                monitorAP.flag.wait()
                # whitelisted scanned APs
                wl_ap = []
                logger.info("Scanning AP")

                # Scan for all trusted AP (incl. hidden)
                for hap in HIDDEN_AP:
                    scanned_aps = [ap for ap in wlan.scan(hap)]
                    wl_ap.extend([ap for ap in scanned_aps if (
                        ap['essid'] in ap_dict["TRUSTED"]
                        and (ap['essid'] not in map(lambda x: x['essid'], wl_ap))
                    )])

                # sort whitelisted AP based on quality
                wl_ap.sort(key=lambda x: x['quality'], reverse=True)
                # Add scanned APs to shared dictionary
                monitorAP.ap_dict["SCANNED"] = wl_ap

                # Manually delete objects
                del wl_ap
                wl_ap = None
            except Exception as e:
                logger.warning('monitorAP fail - possible scan failure: ' + e.message)
        else:
            monitorAP.ap_dict["SCANNED"] = []
        time.sleep(10)


def killChildProc(*processes):
    """
    Kills child processes before terminating
    due to some non-fatal (and non signal)
    interrupt. e.g. ctrl c or an exception
    """
    for process in processes:
        logger.warning("Killing: " + str(process))
        process.terminate()


def closeClient(conn_handler):
    """
    close connection with uploader
    """
    conn_handler.close()


def connectToAP(ap_name):
    """
    Convinitent method to connect to the AP
    by calling `nm.copyWpaConfigFile(<apname>)`
    and `nm.restartIface(<ifname>)`

    Parameters
    ----------
    ap_name: str
        Access point to connect to.
    .. note: ap_name should be same as ssid
             observed while scanning
    """
    # Check if already connected to same AP
    if not nm.parseWpaConfigFile()['ssid'] == ap_name:
        logger.info("Will Connect to New AP: " + str(ap_name))
        # Disable VPN
        vpnswitch.disableVPN()
        if nm.copyWpaConfigFile(ap_name):
            if nm.restartIface(IFNAME):
                nm.connectToVPN()
                return True
    else:
        logger.info("Already connected to: " + str(ap_name))
        return True


def enable_routing_policy(iface=None, gw=None, metric=1):
    """
    Enable routing via particular interface.
    This method will automatically detect the gateway (if using dhcp)
    and set the default route via `iface` interface
    """
    try:
        if not iface:
            logger.warning("iface arguement is required.")
            return False
        # get the gateway for the interface
        if not gw:
            gw = ifconfig.get_dhcp_info(iface)['routers']
            if not gw:
                logger.error("Gateway cannot be obtained from dhcp query. ")
                logger.warning("Routing policy will not be changed")
                return False
        policy_set = ifconfig.set_default_route(iface, gw, metric)
        if not policy_set:
            logger.error("Cannot set routing policy via "+str(iface))
            # Might want to restart the interface at this point for it
            # to get configuration from dhcp server ??
            ifconfig.dhcp_route_sos()
            return False
        logger.info("Policy based routing via " + str(iface) + " set.")
        # Make a backup of this policy
        ifconfig.backup_routes()
        return True
    except Exception as ex:
      logger.warning("Error enabling routing policy for {0}: {1}".format(str(iface), str(ex)))


if __name__ == "__main__":
    # Setup for IPC
    READY = False
    address = ('', IPC_PORT)
    while not READY:
        try:
            upload_conn = Client(address, authkey=IPC_AUTH)
            READY = True
        except socket.error as ex:
            if ex.errno == 111:
                logger.error("Uploader not found on port "+str(ex.strerror))
            else:
                logger.critical("Error connecting to uploader: "+str(ex))
            time.sleep(1)
            
    # Manager to be responsible for all processes
    manager = multiprocessing.Manager()

    # Setup Events to trigger monitoring
    intev = manager.Event()
    vpnev = manager.Event()
    apev = manager.Event()

    # Set up shared Value
    vpnstat = manager.Value('vpn', False)
    intstat = manager.Value('internet', False)
    # trusted ap includes hidden aps
    ap_dict = manager.dict({"SCANNED": None,
                            "TRUSTED": TRUSTED_AP+HIDDEN_AP})

    # Setup a pool of 2 processes
    pool = multiprocessing.Pool(3, _setup, (intev, vpnev, apev,
                                            intstat, vpnstat,
                                            ap_dict))

    # Map function and iterable to run in their individual process
    # -- Using imap incase we later want to pass any iterable
    # -- to the processes.
    # -- Passing dummy lists as an iterable for now
    inter = pool.imap(monitorInternet, ['Internet'])
    vpnm = pool.imap(monitorVPN, ['VPN'])
    apscan = pool.imap(monitorAP, ['AP'])

    # graceful exit
    atexit.register(killChildProc, *pool._pool)
    atexit.register(closeClient, upload_conn)

    # No more processes to be created
    pool.close()

    def monitor(sched):
        try:
            # Get only the interfaces that has network connection
            logger.info("Checking for connected interfaces")
            all_interfaces = ifconfig.detect_interfaces()
            live_interfaces = [iface for iface in all_interfaces
                               if nm.connectedToInternet(iface)]
            wired_ifaces, wireless_ifaces = [], []
            # Divide all interfaces into wired and wireless
            for iface in live_interfaces:
                wireless_ifaces.append(iface) if \
                    ifconfig.is_wireless(iface) else \
                    wired_ifaces.append(iface)
            # Starting the connection process
            # 1. Check if PreferredAP can be found
            # Check if Wlan interface is present
            if IFNAME in all_interfaces:
                # Check for Preferred AP in the Scanned AP

                if filter(lambda x: PREFERRED_AP in x['essid'], ap_dict["SCANNED"]):
                    logger.info("Detected Lifeline")
                    # Connect to preferred AP
                    if connectToAP(PREFERRED_AP):
                        logger.info("Flushing VPN rules")
                        vpnswitch.flush_rules()
                        enable_routing_policy(IFNAME, metric=1)
                        intev.set()
                        vpnev.set()
                        return True
            else:
                # warn that wlan interface is not detected
                logger.warning("Wireless Interface is not detected.")
            if wired_ifaces:
                # WARNING -- This will only use first wired
                # interface that it detects
                logger.info("Connected to Wired Lan")
                enable_routing_policy(wired_ifaces[0], metric=1)
                intev.set()
                vpnev.set()
            elif IFNAME in all_interfaces and ap_dict["SCANNED"]:
                logger.info("Trying to connect to network using WiFi")
                # Get strongest APs out of 5 scans
                strongest_ap = deque(maxlen=5)
                while len(strongest_ap) < 5:
                    apev.clear()
                    logger.info("Trial " + str(len(strongest_ap)) +
                                ": " + str(ap_dict["SCANNED"][0]['essid']))
                    strongest_ap.append(ap_dict["SCANNED"][0]['essid'])
                    apev.set()
                    time.sleep(3)
                apcounter = Counter(strongest_ap)
                # Check if the strongest_ap appeared more than 3 times
                if apcounter.most_common(1)[0][1] > 3:
                    # Start sequence of connecting to strongest AP
                    # Disable VPN and Internet monitoring
                    vpnev.clear()
                    intev.clear()
                    if connectToAP(apcounter.most_common(1)[0][0]):
                        # If connected, enable Internet and VPN monitoring
                        intev.set()
                        vpnev.set()
                        # Enable routing policy
                        enable_routing_policy(IFNAME, metric=1)
            else:
                logger.warning("No interface has network connectivity")
            # Make sure we are connected to VPN
            if not vpnstat.value:
                # Check if connected to Internet
                if intstat.value:
                    # changing interface locks up vpn service.
                    # stop vpn monitoring and restart vpn service
                    vpnev.clear()
                    nm.connectToVPN()
                    # Enable vpn service monitoring
                    vpnev.set()
                else:
                    logger.warning("No INET or VPN")
                    # Just to be safe, restart wireless interface
                    # nm.restartIface(IFNAME)
            else:
                # Now that we have VPN, disable Internet monitoring
                # to reduce logging
                intev.clear()
        except Exception as ex:
            logger.warning("Exception in monitor: " + ex.message)
        finally:
            upload_conn.send((intstat.value, vpnstat.value))
            # Schedule to run monitor after a delay of
            # CHECK_EVERY
            sched.enter(CHECK_EVERY, 1, monitor, (sched,))

    # Enable AP scanning
    apev.set()

    # Schedule to run the task in 5 seconds second
    sc.enter(5, 1, monitor, (sc,))
    sc.run()

