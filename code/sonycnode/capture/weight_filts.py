import numpy as np

__author__ = "Charlie Mydlarz"
__credits__ = "Mohit Sharma, Justin Salamon"
__version__ = "0.1"
__status__ = "Development"


class Weighting(object):
    """
    This class contains methods to calculate A & C weighting values for fast and slow integration periods in the
    frequency domain - accurate to ANSI S1.4-1983, ANSI S1.42-2001, IEC 61672-1:2013 and JIS C 1509-1:2005

    It also carries out all FFT functionality for the SPL feature extraction processes

    Parameters to be passed:
        - fs : sample rate recorder script is running at

        - slowdelta: calibration value for SPL offset
    """

    fs = 48000
    nfft = 32768

    slowdelta = 1.0
    fastdelta = 0.125

    freq_array = []

    filteramps = []

    sp_slow = []

    def __init__(self, fs):
        self.fs = fs

        # Generate filter values and pack into slow and fast tuple variables containing A and C weighting arrays
        self.filter_design()

        # Preallocate spectrum aray for fast setting
        self.sp_slow = np.empty([int(self.slowdelta / self.fastdelta), self.nfft / 2 + 1])

        self.slow_window = np.hanning(fs * self.slowdelta)
        self.fast_window = np.hanning(fs * self.fastdelta)

    def filter_design(self):

        # Calculate frequency resolution based on the lowest center frequency octave band required
        fft_res = 1.36491 * (9.843 / 24.803)
        ideal_nfft = int(fft_res * self.fs)
        self.nfft = 2 ** (ideal_nfft - 1).bit_length()

        # Create array of frequency bin values for octave band segmentation
        self.freq_array = np.linspace(0, self.fs / 2.0, 1 + self.nfft / 2)

        amp_array = np.copy(self.freq_array)

        # Constant values for A and C weighting calculation
        c1 = 3.5041384e16
        c2 = 20.598997 ** 2
        c3 = 107.65265 ** 2
        c4 = 737.86223 ** 2
        c5 = 12194.217 ** 2

        # Set offset on any zero values to remove log(0) situations
        amp_array[amp_array == 0] = 1e-17
        amp_array **= 2

        # A weighting amplitude calculation
        num = c1 * (amp_array ** 4)
        den = ((c2 + amp_array) ** 2) * (c3 + amp_array) * (c4 + amp_array) * ((c5 + amp_array) ** 2)
        a_amp_array = num / den

        c1 = 2.242881e16

        # C weighting amplitude calculation
        num = c1 * (amp_array ** 2)
        den = ((c2 + amp_array) ** 2) * ((c5 + amp_array) ** 2)
        c_amp_array = num / den

        self.filteramps.extend([a_amp_array, c_amp_array])

    def filter_apply_fast(self, sp):

        sp_a_weighted = sp * self.filteramps[0]
        sp_c_weighted = sp * self.filteramps[1]

        out_array = np.vstack((sp, sp_a_weighted, sp_c_weighted))
        return out_array

    def filter_apply_slow(self, sp):
        sp_filt = sp * self.filteramps
        out_array = np.vstack((sp, sp_filt))
        return out_array

    def fft_signal(self, buf, speed='s'):
        # FFT input buffer using appropriate FFT size for octave band analysis
        if speed == 's':
            sp = abs(np.fft.rfft(buf * self.slow_window, n=self.nfft))
            sp[sp == 0] = 1e-17
            return sp**2
        else:
            idx = 0
            buf_len = int(np.floor(self.fs * self.fastdelta))
            for x in range(0, len(buf), buf_len):
                win_sp = abs(np.fft.rfft(buf[x:x + buf_len] * self.fast_window, n=self.nfft))
                win_sp[win_sp == 0] = 1e-17
                # sp.append(win_sp)
                self.sp_slow[idx] = win_sp**2
                idx += 1
            return self.sp_slow




