import numpy as np

__author__ = "Charlie Mydlarz"
__credits__ = "Mohit Sharma, Justin Salamon"
__version__ = "0.1"
__status__ = "Development"


class Octave(object):
    """
    This class contains methods to calculate octave band ranges in the frequency domain

    Parameters to be passed:
        - fs : sample rate recorder script is running at

        - slowdelta: calibration value for SPL offset
    """

    fs = 48000

    upper_3_f = []
    lower_3_f = []
    upper_1_f = []
    lower_1_f = []
    amp_idx_3 = []
    amp_idx_1 = []

    amp_array_1 = []
    amp_array_3 = []

    freq_array = []
    freq_array_delta_dbl = 0

    cal_val = 0

    # Center frequency values for 1/1 octave filter
    cent_f_sioct = np.array([31.250, 62.50, 125.0, 250.0, 500.0, 1000.0, 2000.0, 4000.0, 8000.0, 16000.0])

    # Center frequency values for 1/3 octave filter
    cent_f_thoct = np.array([24.803, 31.250, 39.373, 49.606, 62.5, 78.745, 99.213, 125.0, 157.490,
                             198.425, 250.0, 314.980, 396.850, 500.0, 629.961, 793.701, 1000.0,
                             1259.921, 1587.401, 2000.0, 2519.842, 3174.802, 4000.0, 5039.684,
                             6349.604, 8000.0, 10079.368, 12699.208, 16000.0, 20158.737])

    def __init__(self, fs, freq_array, cal_val):
        self.fs = fs
        self.freq_array = freq_array
        self.single_octave_setup()
        self.third_octave_setup()
        self.cal_val = cal_val
        self.freq_array_delta_dbl = 2 * (self.freq_array[1] - self.freq_array[0])

    def single_octave_setup(self):

        # Create upper and lower 1/1 octave frequencies
        self.lower_1_f = [i / 2.0 ** (1.0 / 2.0) for i in self.cent_f_sioct]
        self.upper_1_f = [2.0 ** (1.0 / 2.0) * i for i in self.cent_f_sioct]

        # Preallocate single octave amplitude array
        self.amp_array_1 = np.zeros(len(self.freq_array))

        b = 1
        for i in range(0, len(self.cent_f_sioct)):
            idx_1 = (np.abs(self.freq_array - self.lower_1_f[i])).argmin()
            idx_2 = (np.abs(self.freq_array - self.upper_1_f[i])).argmin()
            self.amp_idx_1.append(slice(idx_1, idx_2))
            for q in range(idx_1, idx_2):
                self.amp_array_1[q] = np.sqrt(
                    1.0 / (1.0 + ((((self.freq_array[q] / self.cent_f_sioct[i]) -
                                    (self.cent_f_sioct[i] / self.freq_array[q])) * (1.507 * b)) ** 6.0))) ** 2.0

    def third_octave_setup(self):

        # Create upper and lower 1/3 octave frequencies
        self.lower_3_f = [i / 2 ** (1.0 / 6.0) for i in self.cent_f_thoct]
        self.upper_3_f = [2 ** (1.0 / 6.0) * i for i in self.cent_f_thoct]

        # Preallocate single octave amplitude array
        self.amp_array_3 = np.zeros(len(self.freq_array))

        b = 3
        for i in range(0, len(self.cent_f_thoct)):
            idx_1 = (np.abs(self.freq_array - self.lower_3_f[i])).argmin()
            idx_2 = (np.abs(self.freq_array - self.upper_3_f[i])).argmin()
            self.amp_idx_3.append(slice(idx_1, idx_2))
            for q in range(idx_1, idx_2):
                self.amp_array_3[q] = np.sqrt(
                    1.0 / (1 + ((((self.freq_array[q] / self.cent_f_thoct[i]) -
                                  (self.cent_f_thoct[i] / self.freq_array[q])) * (1.507 * b)) ** 6))) ** 2

    def oct_vals_slow(self, sp):

        si_oct_vals = [self.get_decibel(sp[i] * self.amp_array_1[i], 48000, self.cal_val) for i in self.amp_idx_1]

        th_oct_vals = [self.get_decibel(sp[i] * self.amp_array_3[i], 48000, self.cal_val) for i in self.amp_idx_3]

        return np.concatenate([si_oct_vals, th_oct_vals])

    def oct_vals_fast(self, sp):

        si_oct_vals = np.empty([len(sp), len(self.amp_idx_1)])
        for j in range(0, len(sp)):
            si_oct_vals[j] = [self.get_decibel(sp[j][i] * self.amp_array_1[i], 6000, self.cal_val) for i in
                              self.amp_idx_1]

        th_oct_vals = np.empty([len(sp), len(self.amp_idx_3)])
        for j in range(0, len(sp)):
            th_oct_vals[j] = [self.get_decibel(sp[j][i] * self.amp_array_3[i], 6000, self.cal_val) for i in
                              self.amp_idx_3]

        return np.concatenate([si_oct_vals, th_oct_vals], axis=1)

    def get_decibel(self, sp, sig_len, c):
        # print len(sp) * self.freq_array_delta
        totalenergy = np.sum(sp) / len(sp)
        meanenergy = totalenergy / (1.0 / (len(sp) * self.freq_array_delta_dbl) * sig_len)
        db = 10 * np.log10(meanenergy) + c
        return db
