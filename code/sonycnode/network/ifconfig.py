import os
import re
import json
import time
from sonycnode.utils import misc
from sonycnode.utils.misc import execute
from sonycnode.utils import sonyc_logger as loggerClass

parser = misc.load_settings()
dns_servers = json.loads(parser.get('network', 'dns_servers'))
netdir = parser.get('network', 'netdir').strip("'\"")

class Ifconfig(object):
    def __init__(self):
        self.logger = loggerClass.sonycLogger(loggername="ifconfig")
        self.device_expr = '\s*[0-9]+:\s+(?P<device>[a-zA-Z0-9]+).*'
        self.command = self.ip_command()
        self.interfaces = []

    @staticmethod
    def ip_command():
        """
        Obtain the command specific to the distro
        """
        command = 'ip'
        possible_paths = ['/sbin', '/usr/sbin', '/bin', '/usr/bin']
        for command in map(lambda x: os.path.join(x, command), possible_paths):
            if os.path.exists(command):
                break
        return command

    @classmethod
    def iface_params(cls):
        """
        Parameters for Wired Lan
        """
        return [
            '\s*[0-9]+:\s+(?P<device>[a-zA-Z0-9]+).*',
            '.*mtu (?P<mtu>.*).*',
            '.*(inet )(?P<inet>[0-9\.]+).*',
            '.*(inet6 )(?P<inet6>[^/]*).*',
            '.*(inet )[^/]+(?P<netmask>[/][0-9]+).*',
            '.*(ether )(?P<mac>[^\s]*).*',
            '.*inet\s.*(brd )(?P<broadcast>[^\s]*).*',
            '.*inet\s.*(peer )(?P<tun_gw>[^\s]*).*',
            ]

    def is_wireless(self, iface):
        """
        check if interface is wireless or not
        """
        out, err = execute("iwconfig {iface}"
                            .format(iface=iface).split())
        if out:
            if iface == out.splitlines()[0].split(" ")[0]:
                return True
        elif err:
            if iface == err.splitlines()[0].split(" ")[0]:
                return False

    def detect_interfaces(self):
        """
        Detect interfaces on the system
        """
        out, err = execute("ip link show".split(" "))
        if err:
            return []
        iface_expr = '\s*[0-9]+:\s+(?P<device>[a-zA-Z0-9]+).*'
        return re.findall(iface_expr, out)

    @classmethod
    def route_params(cls):
        """
        Parameters for routing information
        """
        return [
            '.*(default via )(?P<default_route>[^\s]*)',#.*',
            '.*(dev )(?P<interface>[a-zA-Z0-9]+).',
            '(?P<route_to>(.+?(?=\svia)+)+)',#.*',
            '.*(via )(?P<route_via>[^\s+]*)',#.*',
            '.*(metric )(?P<metric>[0-9]+)',#.*'
        ]

    def findall(self, command, patterns):
        """
        Perform re.match against all the patterns
        after running the bash command
        Parameters
        ----------
        command: str
            bash command to execute on system
        patterns: list
            list of patterns to match against
        Returns
        -------
        Returns dictionary
        containing the group name (as passed in pattern element)
        and value as the matched value
        """
        out, error = execute(command.split(" "))
        if error:
            return {}
        else:
            params = {}
            for line in out.splitlines():
                for pattern in patterns:
                    match = re.match(pattern, line)
                    if match:
                        params.update(match.groupdict())
        return params

    def iface(self):
        """
        Get interfaces on the device
        """
        # Get all the interfaces
        interfaces = self.findall(command="ip address show",
                                  patterns=[self.device_expr])
        return map(lambda x: x.values()[0], interfaces)

    def parameters(self, interface):
        """
        Get properties for a particular interface
        Parameters
        ----------
        interface: str
            name of the interface to get properties of
            check `get_iface()`
        """
        params = self.findall(command="ip address show {iface}".format(
            iface=interface), patterns=self.iface_params())
        return params

    def get_routes(self, interface):
        """
        Get current routing information for a particular interface.
        If you are using dhcp and configuring routes, prefer calling get_dhcp_info
        """
        # Need to parse it in a better way
        routes = self.findall(command="ip route list dev {iface}".format(
            iface=interface), patterns=self.route_params())
        return routes

    def backup_routes(self, path=netdir):
        """
        Backup network routing rules  to a particular destination
        """
        with open(os.path.join(path, "backup.routes"), 'wb') as fh:
            out, err = execute('ip route save'
                               .split(),
                               std_out=fh)
        if err:
            self.logger.warning("Backing up network routes failed. "+str(err))
            return False
        return True

    def restore_routes(self, path=netdir):
        """
        Restore routes from a particular destination
        """
        with open(os.path.join(path, "backup.routes"), 'rb') as fh:
            out, err = execute("ip route restore"
                               .split(),
                               std_in=fh)
        return out, err

    def flush_default_routes(self):
        """
        Delete default routes from routing table
        """
        # get all interfaces being used for default routing
        ifaces = [iface for iface in self.detect_interfaces()
                  if 'default_route' in
                  self.get_routes(iface).keys()]

        for iface in ifaces:
            while True:
                out, err = execute("ip route del dev {iface}"
                                   .format(iface=iface)
                                   .split())
                if err:
                    break
                time.sleep(0.5)
        return True

    def get_default_route(self):
        """
        Returns current default route information
        """
        route = self.findall(command="ip route get {server}"
                             .format(server=dns_servers[0]),
                             patterns=self.route_params())
        return route


    def set_default_route(self, iface, gw, metric=1):
        """
        Set default route for a particular interface with metric of 1
        Warning.: This will erase all the other default routes
        """
        # Check if default route is already set
        if (self.get_default_route()['interface'] == iface):
            self.logger.info("Route already set.")
            return True
        # Backup current main table
        if self.backup_routes(netdir):
            # Delete all the default routing rules
            if self.flush_default_routes():
                out, err = execute("ip route add default via {gw} dev {iface} metric {metric}"
                                   .format(gw=gw, iface=iface, metric=metric)
                                   .split())
                if err:
                    self.logger.warning("Cannot set default route. "+str(err))
                    self.logger.warning("Rolling back the routing changes")
                    self.restore_routes(netdir)
                    return False
                self.logger.info("Default route set via "+str(gw)+
                            " for interface "+str(iface))
                return True
            else:
                self.logger.warning("Issues in flushing routes."+
                               " Rolling back the routing changes.")
                if self.restore_routes(netdir):
                    self.logger.info("Routing policies restored.")
                return False
        else:
            self.logger.info("Routing policies unchanged.")
            return False


    def dhcp_route_sos(self):
        """
        When all means of setting routing policy fails,
        call this command. This will call the `dhcpcd`
        and load default dhcp settings
        """
        self.logger.critical("Falling back to dhcpcd for default configuration")
        execute("dhcpcd".split())

    def get_dhcp_info(self, iface):
        """
        Uses dhcp client to query the latest lease
        for `iface`
        """
        out, err = execute("dhcpcd -U {iface}"
                           .format(iface=iface)
                           .split())
        dhcp_info = dict((key, value) for key, value in
                         map(lambda x: x.replace("'", '').split('='),
                             out.splitlines()))
        dhcp_info.update(dict((key, int(value)) for key, value in
                              map(lambda x: x.replace("'", '').split('='),
                                  out.splitlines()) if value.isdigit()))
        return dhcp_info

    def current_wireless_info(self, interface):
        """
        Get current wireless connection info
        """
        params = {}
        parameters = [
            ".*(Link Quality=)(?P<link>[^\s^\\N]*).*",
            ".*(Signal level=)(?P<signal>[^\s^\\N]*).*",
            ".*(Noise level=)(?P<noise>[^\s^\\N]*).*",
            ".*(Mode:)(?P<mode>[^\s^\\N]*).*",
            ".*(Frequency=)(?P<freq>[^\s^\\N]*).*",
            ".*(Sensitivity:)(?P<sensitivity>[^\s^\\N]*).*",
            ".*(Encryption key:)(?P<enc_key>[^\s^\\N]*).*",
            ".*(Power Management:)(?P<power_mgmt>[^\s^\\N]*).*",
            ".*(Access Point:)(?P<ap>[^\\N]*).*",
            ".*(Bit Rate:)(?P<bitrate>[^\/s]*).*"
        ]
        # relying on iwconfig for now since developers of iw have
        # warned against parsing the output of iw
        out, err = execute("iwconfig {iface}".
                           format(iface=interface).
                           split(" "))
        if err:
            return {}
        for param in parameters:
            match = filter(None,
                           map(lambda x: re.match(param, x), out.splitlines()))
            if match:
                map(lambda x: params.update(x.groupdict()), match)
        return params
