import time
from sonycnode.utils import sonyc_logger as loggerClass
from sonycnode.utils import misc
import pycurl
import cStringIO

logger = loggerClass.sonycLogger(loggername="VPNSwitch")

parser = misc.load_settings()

# For debuging (or vms) we may want to allow all connections through eth0
allow_full_eth0 = parser.getboolean('network', 'allow_full_eth0')


def get_wanIp():
    """
    Get Wan IP
    """
    try:
        response = cStringIO.StringIO()
        c = pycurl.Curl()
        c.setopt(c.URL, "https://api.ipify.org?format=plain")
        c.setopt(c.WRITEFUNCTION, response.write)
        c.setopt(c.CONNECTTIMEOUT, 5)
        c.setopt(c.TIMEOUT, 8)
        c.perform()
        wanip = response.getvalue()
        c.close()
        return wanip
    except Exception as ex:
        logger.error("Error obtaining WAN IP: " + str(ex))


# wanip = "40.121.86.94"

def vpn_service(command):
    """
    Stop/Re/Start VPN service
    Parameters
    ----------
    command : str
        perform operation on vpn service
        example: 
        stop    : stop the vpn service
        start   : start the vpn service
        restart : restart the vpn service
    """
    logger.info(command.lower() + " VPN service")
    misc.execute(["service", "openvpn", command.lower()])


def vpn_rules(vpn_subnet="10.8.0.0/24"):
    """
    iptable rules for forcing all communications
    over vpn
    Parameters
    ----------
    wanip : str
        WAN IP obtained when connected to vpn server
    vpn_subnet : str
        Subnet and subnet mask (CIDR notation) of the 
        vpn network
        default : 10.8.0.0/24
    Returns
    -------
    None
    """
    # wan_ip = get_wanIp()
    logger.info("Appending VPN rules")
    rules = [
        ['iptables', '-P', 'INPUT', 'DROP'],
        ['iptables', '-P', 'FORWARD', 'ACCEPT'],
        ['iptables', '-P', 'OUTPUT', 'ACCEPT'],
        ['iptables', '-A', 'INPUT', '!', '-i', 'tun0', '-m', 'iprange', '--src-range', '10.8.0.1-10.255.255.255', '-j',
         'REJECT', '--reject-with', 'icmp-port-unreachable'],
        ['iptables', '-A', 'OUTPUT', '!', '-o', 'tun0', '-m', 'iprange', '--src-range', '10.8.0.1-10.255.255.255', '-j',
         'REJECT', '--reject-with', 'icmp-port-unreachable'],
        ['iptables', '-A', 'INPUT', '-i', 'tun0', '-p', 'icmp', '-m', 'iprange', '--src-range',
         '10.8.0.1-10.255.255.255', '-j', 'ACCEPT'],
        ['iptables', '-A', 'INPUT', '-i', 'tun0', '-p', 'tcp', '-m', 'iprange', '--src-range',
         '10.8.0.1-10.255.255.255', '-m', 'multiport', '--dports', '22', '-j', 'ACCEPT'],
        ['iptables', '-A', 'INPUT', '-m', 'state', '--state', 'RELATED,ESTABLISHED', '-j', 'ACCEPT'],
        ['iptables', '-A', 'INPUT', '-i', 'lo', '-j', 'ACCEPT'],
        ['iptables', '-A', 'INPUT', '-p', 'tcp', '--dport', '22', '-m', 'state', '--state', 'NEW,ESTABLISHED', '-j',
         'ACCEPT'],
    ]
    if allow_full_eth0:
        rules += [
            ['iptables', '-A', 'INPUT', '-i', 'eth0', '-j', 'ACCEPT'],
        ]
    rules += [
        ['iptables', '-A', 'INPUT', '!', '-i', 'tun0', '-m', 'iprange', '--src-range', '10.8.0.1-10.255.255.255', '-j',
         'REJECT', '--reject-with', 'icmp-port-unreachable'],
        ['iptables', '-A', 'INPUT', '-i', 'tun0', '-p', 'icmp', '-m', 'iprange', '--src-range',
         '10.8.0.1-10.255.255.255', '-j', 'ACCEPT'],
        ['iptables', '-A', 'INPUT', '-i', 'tun0', '-p', 'tcp', '-m', 'iprange', '--src-range',
         '10.8.0.1-10.255.255.255', '-m', 'multiport', '--dports', '22', '-j', 'ACCEPT'],
        ['iptables', '-A', 'OUTPUT', '-m', 'state', '--state', 'RELATED,ESTABLISHED', '-j', 'ACCEPT'],
        ['iptables', '-A', 'OUTPUT', '-o', 'lo', '-j', 'ACCEPT'],
        ['iptables', '-A', 'OUTPUT', '-o', 'tun0', '-p', 'icmp', '-m', 'iprange', '--dst-range',
         '10.8.0.1-10.255.255.255', '-j', 'ACCEPT'],
        ['iptables', '-A', 'OUTPUT', '-p', 'udp', '-m', 'multiport', '--dports', '1194,1195', '-j', 'ACCEPT'],
        ['iptables', '-A', 'OUTPUT', '-p', 'tcp', '-m', 'multiport', '--dports', '53', '-j', 'ACCEPT'],
        ['iptables', '-A', 'OUTPUT', '-p', 'udp', '-m', 'multiport', '--dports', '53', '-j', 'ACCEPT'],
        ['iptables', '-A', 'OUTPUT', '-p', 'tcp', '-m', 'multiport', '--dports', '443', '-j', 'ACCEPT']
        ['iptables', '-A', 'OUTPUT', '-p', 'tcp', '-m', 'multiport', '--dports', '80', '-j', 'ACCEPT'],
    ]

    # rules = [
    #     ["iptables", "-F"],
    #     ["iptables", "-X"],
    #     ["iptables", "-t", "nat", "-F"],
    #     ["iptables", "-t", "nat", "-X"],
    #     ["iptables", "-t", "mangle", "-F"],
    #     ["iptables", "-t", "mangle", "-X"],
    #     ["iptables", "-P", "INPUT", "ACCEPT"],
    #     ["iptables", "-P", "FORWARD", "ACCEPT"],
    #     ["iptables", "-P", "OUTPUT", "ACCEPT"]
    # ]

    """
    rules = [
        ["iptables", "-P", "INPUT", "DROP"],
        ["iptables", "-P", "FORWARD", "DROP"],
        ["iptables", "-P", "OUTPUT", "DROP"],
        ["iptables", "-F"],
        ["iptables", "-X"],
        ["iptables", "-t", "nat", "-F"],
        ["iptables", "-t", "nat", "-X"],
        ["iptables", "-t", "mangle", "-F"],
        ["iptables", "-t", "mangle", "-X"],
        ["iptables", "-A", "INPUT", "-m", "state", "--state", "INVALID", "-j", "DROP"],
        ["iptables", "-A", "INPUT", "-p", "tcp", "--tcp-flags", "ALL ACK,RST,SYN,FIN", "-j", "DROP"],
        ["iptables", "-A", "INPUT", "-p", "tcp", "--tcp-flags", "SYN,FIN", "SYN,FIN", "-j", "DROP"],
        ["iptables", "-A", "INPUT", "-p", "tcp", "--tcp-flags", "SYN,RST", "SYN,RST", "-j", "DROP"],
        ["iptables", "-A", "INPUT", "-f", "-j", "DROP"],
        ["iptables", "-A", "INPUT", "-p", "tcp", "--tcp-flags", "ALL", "ALL", "-j", "DROP"],
        ["iptables", "-A", "INPUT", "-p", "tcp", "--tcp-flags", "ALL", "NONE", "-j", "DROP"],
        ["iptables", "-A", "INPUT", "-i", "lo", "-j", "ACCEPT"],
        ["iptables", "-A", "INPUT", "-m", "state", "--state", "RELATED,ESTABLISHED", "-j", "ACCEPT"],
        ["iptables", "-A", "INPUT", "-i", "tun0", "-j", "ACCEPT"],
        ["iptables", "-A", "INPUT", "-s", "192.168.0.0/24", "-d", "192.168.0.0/24", "-j", "ACCEPT"],
        ["iptables", "-A", "INPUT", "-s", vpn_subnet, "-d", vpn_subnet, "-j", "ACCEPT"],
        ["iptables", "-A", "INPUT", "-j", "DROP"],
        ["iptables", "-A", "FORWARD", "-j", "REJECT", "--reject-wth", "icmp-admin-prohibited"],
        ["iptables", "-A", "OUTPUT", "-o", "tun0", "-j", "ACCEPT"],
        ["iptables", "-A", "OUTPUT", "-d", wan_ip, "-j", "ACCEPT"],
        ["iptables", "-A", "OUTPUT", "-m", "state", "--state", "ESTABLISHED,RELATED", "-j", "ACCEPT"],
        ["iptables", "-A", "OUTPUT", "-s", "192.168.0.0/24", "-d", "192.168.0.0/24", "-j", "ACCEPT"],
        ["iptables", "-A", "OUTPUT", "-s", vpn_subnet, "-d", vpn_subnet, "-j", "ACCEPT"],
        ["iptables", "-A", "OUTPUT", "-j", "REJECT", "--reject-with", "icmp-admin-prohibited"]
        ]
    """
    """
    rules = [
        ["iptables", "-t", "nat", "-F"],
        ["iptables", "-t", "nat", "-X"],
        ["iptables", "-t", "mangle", "-F"],
        ["iptables", "-t", "mangle", "-X"],
        ["iptables", "-A", "INPUT", "-i", "lo", "-j", "ACCEPT"],
        ["iptables", "-A", "OUTPUT", "-o", "lo", "-j", "ACCEPT"],
        ["iptables", "-A", "OUTPUT", "-d", "255.255.255.255", "-j", "ACCEPT"],
        ["iptables", "-A", "INPUT", "-s", "255.255.255.255", "-j", "ACCEPT"],
        ["iptables", "-A", "INPUT", "-s", vpn_subnet, "-d", vpn_subnet, "-j", "ACCEPT"],
        ["iptables", "-A", "OUTPUT", "-s", vpn_subnet, "-d", vpn_subnet, "-j", "ACCEPT"],
        ["iptables", "-A", "FORWARD", "-i", iface, "-o", "tun0", "-j", "ACCEPT"],
        ["iptables", "-A", "FORWARD", "-i", "tun0", iface, "-j", "ACCEPT"],
        ["iptables", "-t", "nat", "-A", "POSTROUTING", "-o", "tun0", "-j", "MASQUERADE"],
        ["iptables", "-A", "OUTPUT", "-o", "wlan0", "!", "-d", wanip, "-j", "DROP"]
        ]
    """

    for rule in rules:
        misc.execute(rule)


def flush_rules():
    """
    flush all iptable rules
    """
    logger.info("Flushing VPN rules")
    rules = [
        ["iptables", "-F"],
        ["iptables", "-P", "INPUT", "ACCEPT"],
        ["iptables", "-P", "OUTPUT", "ACCEPT"],
        ["iptables", "-P", "FORWARD", "ACCEPT"]
    ]
    for rule in rules:
        misc.execute(rule)


def check_rules(rule=None):
    """
    Check if particular rule exists in iptables
    Parameters
    ----------
    rule : str
        rule to be checked in the CURRENT/ RUNNING iptables
    Returns
    -------
    Bool
        True if rule exists
        False if it doesn't exists
    """
    logger.info("Checking VPN rules")
    if rule:
        out, err = misc.execute(["iptables", "-C"] + rule.split(' '))
    else:
        c.perform()
        wanip = response.getvalue()
        response.seek(0)
        response.truncate()
        out, err = misc.execute(["iptables", "-C", "OUTPUT", "-d", wanip, "-j", "ACCEPT"])
    if err:
        return False
    else:
        return True


def enableVPN():
    """
    Command to enable VPN
    """
    # To be safe, restart VPN
    flush_rules()
    vpn_service("restart")


def disableVPN():
    """
    Command to disable VPN
    """
    # Stop vpn service
    vpn_service("stop")
    flush_rules()


def updateIptables(vpn_subnet="10.8.0.0/24"):
    """
    Command to update IPtables for security
    """
    flush_rules()
    vpn_rules(vpn_subnet)
