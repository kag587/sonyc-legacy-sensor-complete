import numpy as np

__author__ = "Charlie Mydlarz"
__credits__ = "Mohit Sharma, Justin Salamon"
__version__ = "0.1"
__status__ = "Development"


class Amplitude(object):
    """
    This class contains methods to calculate amplitude values from spectral data

    Parameters to be passed:
        - fs : sample rate recorder script is running at

        - slowdelta: calibration value for SPL offset
    """

    fs = 48000

    def __init__(self, fs):
        self.fs = fs

    def get_decibel(self, sp, sig_len, c):

        totalenergy = np.sum(sp, axis=1) / len(sp[0])
        meanenergy = totalenergy / ((1.0 / self.fs) * sig_len)
        db = 10 * np.log10(meanenergy) + c
        return db

    def sq_array(self, in_sp):
        out_sp = in_sp ** 2
        return out_sp

    def sum_array(self, in_sp):
        out_sp = sum(in_sp)
        return out_sp
