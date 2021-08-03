import os
from subprocess import Popen, PIPE
import psutil
import re
import socket
import glob
import csv
from datetime import datetime
from sonycnode.utils import sonyc_logger as loggerClass
from sonycnode.utils import misc
from sonycnode.network import netmanager
from sonycnode.network import ifconfig as ifc

parser = misc.load_settings()
iface = parser.get('network', 'ifname').strip("'\"")
location_path = parser.get('status_ping', 'location_file').strip("'\"")
logger = loggerClass.sonycLogger(loggername="DevStatus")
netman = netmanager
ifconfig = ifc.Ifconfig()
laeq_store_dir = '/tmp/laeq_store_dir'


def handle_exception(function):
    def wrapper_function(*args, **kwargs):
        try:
            return function(*args, **kwargs)
        except Exception as e:
            logger.error("Error with " + str(function.func_name) + ":" + str(e), exc_info=True)
            return {}

    return wrapper_function


def getlocation():
    try:
        with open(location_path, 'r') as f:
            lat = f.readline().rstrip()
            lon = f.readline().rstrip()
        return {"lat": lat, "lon": lon}
    except Exception as e:
        return {}


def getwificonninfo():
    try:
        current_wireless_info = ifconfig.current_wireless_info(iface)
        sig_qual = float(current_wireless_info.get('link', '-1').split("/")[0])
        sig_stre = float(current_wireless_info.get('signal', '-1').split("/")[0])
        return {"sig_qual": sig_qual, "sig_stre": sig_stre}
    except Exception as e:
        logger.error("Error obtaining wifi info: " + e.message)
        return {}


@handle_exception
def cpuStats():
    logger.debug('Obtaining cpustats')
    cpu_cur_freq = re.findall(r'\b[\d]+',
                              misc.execute(["vcgencmd",
                                            "measure_clock",
                                            "arm"])[0])[-1].split()[0]
    cpu_temp = re.findall(r'\b[\d?(.\d)]+\b',
                          misc.execute(["vcgencmd", "measure_temp"])[0])[0].split()[0]
    cpu_load = re.findall(r'[\d(?/?.\d)]+',
                          misc.execute(["cat", "/proc/loadavg"])[0])
    cpu_stats = {'cpu_cur_freq': cpu_cur_freq,
                 'cpu_temp': cpu_temp,
                 'cpu_load_1': cpu_load[0],
                 'cpu_load_5': cpu_load[1],
                 'cpu_load_15': cpu_load[2],
                 'running_proc': cpu_load[3].split('/')[1], }
    return cpu_stats


@handle_exception
def memoryStats():
    logger.debug('Obtaining memstats')
    mem = psutil.virtual_memory()
    mem_available = str(mem.available).replace('L', '')
    mem_used = str(mem.used).replace('L', '')
    mem_total = str(mem.total).replace('L', '')
    mem_percent = mem.percent
    mem_stats = {'mem_available': mem_available,
                 'mem_used': mem_used,
                 'mem_total': mem_total,
                 'mem_percent': mem_percent}
    return mem_stats


@handle_exception
def networkStats():
    logger.debug('Obtaining netstats')
    wlan0_ip = netmanager.getIP("wlan0")
    tun0_ip = netmanager.getIP("tun0")
    wlan0_mac = netmanager.getMac("wlan0")
    eth0_mac = netmanager.getMac("eth0")
    eth0_ip = netmanager.getIP("eth0")
    recd_bytes = str(psutil.net_io_counters().bytes_recv).replace('L', '')
    tx_bytes = str(psutil.net_io_counters().bytes_sent).replace('L', '')

    network_stats = {
        'AP': netmanager.parseWpaConfigFile()['ssid'],
        'RX_packets': recd_bytes,
        'TX_packets': tx_bytes,
        'wlan0_ip': wlan0_ip,
        'wlan0_mac': wlan0_mac,
        'tun0_ip': tun0_ip,
        'eth0_mac': eth0_mac,
        'eth0_ip': eth0_ip
    }
    return network_stats


@handle_exception
def usbStats():
    logger.debug('Obtaining usbstats')

    mic_comm = 'lsusb | grep "Cypress\|JMTek"'
    process = Popen(mic_comm, stdout=PIPE, shell=True)
    (mic_resp, err) = process.communicate()

    wifi_comm = "lsusb | grep 'WLAN\|802.11\|Wireless\|wireless' | awk -F ':' '{ print $3 }'"
    process = Popen(wifi_comm, stdout=PIPE, shell=True)
    (wifi_resp, err) = process.communicate()

    if 'Device' not in mic_resp.strip():
        mic_connected = 0
        logger.debug("USB microphone disconnected - not listed when running lsusb")
    else:
        mic_connected = 1

    usb_stats = {'mic_connected': mic_connected, 'wifi_adapter': wifi_resp[5:].strip()}
    return usb_stats


@handle_exception
def storageStats():
    logger.debug('Obtaining storagestats')
    root_usage = psutil.disk_usage("/").percent
    music_usage = psutil.disk_usage("/mnt/sonycdata").percent
    tmp_usage = psutil.disk_usage(os.path.expanduser("/tmp")).percent
    varlog_usage = psutil.disk_usage("/var/log").percent
    storage_stats = {'varlog_usage': varlog_usage,
                     'root_usage': root_usage,
                     'data_usage': music_usage,
                     'tmp_usage': tmp_usage}
    return storage_stats


@handle_exception
def gitStats():
    logger.debug("Parsing GitStats")
    uptodate = 0
    # misc.execute(['git', '-C', '/home/sonyc/sonycnode', 'remote', 'update'])[0]
    local_hash = misc.execute(['git', '-C', '/home/sonyc/sonycnode', 'rev-parse', 'HEAD'])[0].strip()
    remte_hash = misc.execute(['git', '-C', '/home/sonyc/sonycnode', 'rev-parse', 'origin/master'])[0].strip()

    if local_hash == remte_hash:
        uptodate = 1

    git_stats = {
        'branch': misc.execute(['git', '-C', '/home/sonyc/sonycnode', 'rev-parse', '--abbrev-ref', 'HEAD'])[0].strip(),
        'commit_date': misc.execute(['git', '-C', '/home/sonyc/sonycnode', 'log', '-1', '--format=%ci'])[0].strip(),
        'commit': misc.execute(['git', '-C', '/home/sonyc/sonycnode', 'rev-parse', '--short', 'HEAD'])[0].strip(),
        'uptodate': uptodate
    }
    return git_stats


@handle_exception
def positionStats():
    try:
        logger.debug('Obtaining positionstats')
        with open(location_path, 'r') as f:
            lat = f.readline().rstrip()
            lon = f.readline().rstrip()
        return {'position': {"lat": lat, "lon": lon}}
    except Exception as e:
        return {}


@handle_exception
def levelStatus():
    """
    Read the sound pressure level data from the laeq.spl file
    """
    laeq_file = os.path.join(laeq_store_dir, "laeq.spl")
    if not os.path.exists(laeq_file):
        return {}

    try:
        # open the spl file
        with open(laeq_file, 'rb') as csvfile:
            reader = csv.reader(csvfile)
            lzeq, laeq, lceq, cur_time, time_out = reader.next()
            return {"lzeq": lzeq,
                    "laeq": laeq,
                    "lceq": lceq,
                    "level_time": datetime.fromtimestamp(float(cur_time)).isoformat()
                    }
    except Exception as ex:
        logger.warning("Error in obtaining sound level stats: " + str(ex))


def deviceStats():
    cpu_stats = cpuStats()
    mem_stats = memoryStats()
    network_stats = networkStats()
    storage_stats = storageStats()
    git_stats = gitStats()
    position_stats = positionStats()
    level_stats = levelStatus()
    wifi_stats = getwificonninfo()
    usb_stats = usbStats()

    status_ping = {}
    status_ping.update(usb_stats)
    status_ping.update(cpu_stats)
    status_ping.update(mem_stats)
    status_ping.update(network_stats)
    status_ping.update(wifi_stats)
    status_ping.update(storage_stats)
    status_ping.update(git_stats)
    status_ping.update(position_stats)
    status_ping.update(level_stats)
    status_ping.update({'time': datetime.utcnow().isoformat(),
                        'fqdn': socket.getfqdn()
                        })
    return status_ping
