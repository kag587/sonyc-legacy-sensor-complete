import re
from subprocess import Popen, PIPE
from sonycnode.utils.misc import execute
from sonycnode.utils import sonyc_logger as loggerClass

class WLan(object):
    def __init__(self, iface):
        self.logger = loggerClass.sonycLogger(loggername="iw")
        self._frequencies = self._frequencies()
        self.iface = iface

    @classmethod
    def parameters(cls):
        return[
            '(Cell )(?P<Cell>([^- ]*))',
            '.*(Address:\s+?)(?P<mac>[^\s]*).*',
            '.*(ESSID:)"(?P<essid>[^\"]*).*',
            '.*(Protocol:)(?P<protocol>[^\\N]*).*',
            '.*(Mode:)(?P<mode>[^\\N]*).*',
            '.*(Frequency:)(?P<freq>[^GHz]*).*',
            '.*(Channel)(?P<channel>[^\)]*).*',
            '.*(Encryption key:)(?P<enc_key>[^\\N]*).*',
            '.*(Bit Rates:)(?P<bitrate>[^\\N]*).*',
            '.*(IE: IEEE)(?P<wpa2>[^\\N]*).*',
            '.*(IE: WPA)(?P<wpa>[^\\N]*).*',
            '.*(Group Cipher :)(?P<group_cipher>[^\\N]*).*',
            '.*(Pairwise Ciphers )(?P<pairwise_cipher>[^\\N]*).*',
            '.*(Authentication Suites )(?P<auth_suites>[^\\N]*).*',
            '.*(Quality=)(?P<quality>[^\/]*).*',
            '.*(Signal level=)(?P<signal>[^\/]*).*'
        ]

    def scan(self, hidden_essid=None):
        if hidden_essid:
            proc = Popen('iwlist {iface} scan essid "{hidden}"'.
                         format(iface=self.iface,
                                hidden=hidden_essid),
                         shell=True,
                         stdout=PIPE,
                         stderr=PIPE)
            scan_str, error = proc.communicate()
        else:
            scan_str, error = execute("iwlist {iface} scan".
                                      format(iface=self.iface).
                                      split(" "))
        if error:
            self.logger.warning("Error running scan: " + str(error))
        else:
            # Split the output
            scan_list = map(lambda x: x.splitlines(), re.split('\s(?=\Cell*)', scan_str))[1:]
            cell_count = len(scan_list)
            cellinfo = [{} for _ in range(cell_count)]
            for cell in scan_list:
                cell_count -= 1
                for parameter in self.parameters():
                    match = filter(None,
                                   map(lambda cellparam: re.match(parameter,
                                                                  cellparam),
                                       cell))
                    if match:
                        map(lambda info:
                            cellinfo[cell_count].update(info.groupdict()),
                            match)
        return iter(cellinfo)

    def _frequencies(self):
        """
        All the frequencies related information
        """
        out, err = execute("iw phy".split(" "))
        freqs = re.findall(".*MHz.*$", out, re.MULTILINE)
        return filter(None,
                      map(lambda x: x.strip('\t*\' ')
                          if 'disabled' not in x else None,
                          freqs))

    def supported_frequencies(self):
        """
        All the frequencies supported by the wireless adapter
        """
        return iter(map(lambda x: x.split(' ')[0], self._frequencies))

    def freq_tx_power(self):
        """
        Returns a tuple of frequencies and configured transmission power
        """
        return iter(map(lambda x: (float(x.split(' ')[0])/1000,
                                   float(x.split(' ')[3].strip('()\''))),
                        self._frequencies))
