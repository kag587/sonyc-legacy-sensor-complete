__author__ = "Charlie Mydlarz"
__credits__ = "Mohit Sharma, Justin Salamon"
__version__ = "0.1"
__status__ = "Development"

import os
import time
import numpy as np
import csv
from weight_filts import Weighting
from level_calcs import Amplitude
from octave_filts import Octave
import tarfile
import shutil

from cStringIO import StringIO

# from sonycnode.utils import sonyc_logger as loggerClass
# from sonycnode.network import netmanager

class Extractor(object):
    """
    This class contains methods for
    SPL feature extraction

    Parameters to be passed:
        - fs : sample rate recorder script is running at

        - cal_val : calibration value for SPL offset

        - tmpfs_path : path to RAM based tmpfs

        - data_path : path to data storage path (/mnt/sonycdata)
    """

    weighting = []
    levels = []
    octave = []

    json_data = []
    cal_val = 0
    fs = 48000
    starttime = 0
    mac_add = 'FFFFFFF'

    col_heads = []

    temp_slow_data_file = []
    temp_fast_data_file = []

    slow_path = ''
    fast_path = ''
    data_path = ''

    slow_csv_writer = []
    fast_csv_writer = []

    packet_delta = 60

    packet_idx = 0

    def __init__(self, fs, cal_val, tmpfs_path, data_path):
        # Initialize required extraction components
        # netman = netmanager.Network("wlan0")
        # self.mac_add = str(netman._getMac()).replace(":", "")

        self.cal_val = cal_val
        self.fs = fs

        # self.logger = loggerClass.sonycLogger(loggername="Extractor")

        # Initialize instance of filter & level calc class
        self.weighting = Weighting(self.fs)
        self.levels = Amplitude(self.fs)
        self.octave = Octave(self.fs, self.weighting.freq_array, self.cal_val)

        # Setup column heads for CSV output and append to deque
        self.column_setup()

        # TODO: write to temp file get path from recorder
        self.slow_path = tmpfs_path + '/slow_temp.csv'
        self.fast_path = tmpfs_path + '/fast_temp.csv'

        self.data_path = data_path + '/'

        if os.path.exists(self.slow_path):
            os.remove(self.slow_path)
        if os.path.exists(self.fast_path):
            os.remove(self.fast_path)

        self.temp_slow_data_file = open(self.slow_path, 'w')
        self.temp_fast_data_file = open(self.fast_path, 'w')

        self.slow_csv_writer = csv.writer(self.temp_slow_data_file, delimiter=',')
        self.fast_csv_writer = csv.writer(self.temp_fast_data_file, delimiter=',')

        self.write_row_to_file(self.col_heads, True, True)
        self.write_row_to_file(self.col_heads, False, True)



    def write_row_to_file(self, row, slow_row, is_header):

        if not is_header:
            string_row = np.char.mod('%.2f', row)
        else:
            string_row = row

        try:
            if slow_row:

                self.slow_csv_writer.writerow(string_row)

            else:
                self.fast_csv_writer.writerow(string_row)
        except Exception, e:
            self.logger.error('Error writing row to file, row may be lost: ' + str(e))

        return 0

    def move_from_temp_file(self):
        # TODO: Remove before deployment
        # t1 = time.time()

        self.temp_slow_data_file.seek(0)
        self.temp_fast_data_file.seek(0)


        t = str(time.time() - self.packet_delta)

        # Check if location file exists, if not prepend t_ to filename to indicate testing
        if os.path.exists(os.path.join(os.path.expanduser("~sonyc"), 'location')):
            tar_path = self.data_path + self.mac_add + '_' + t + '_data.tar'
        else:
            tar_path = self.data_path + 't_' + self.mac_add + '_' + t + '_data.tar'

        data_path_name = self.data_path + self.mac_add + '_' + t

        try:
            print('Opening tar file: ' + tar_path)
            tar = tarfile.open(tar_path, 'w')

            fsrc = open(self.slow_path, "rb")
            fsrc.flush()
            fdst = open(data_path_name + '_slow.csv', "wb")
            fsrc.seek(0, 0)
            fdst.seek(0, 0)
            # TODO: file is complete at fdst point - the taring produces the missing data?????
            # TODO: try presaving all file names earlier to reduce confusion and aid in debugging
            print('Copying slow file to SD: ' + data_path_name + '_slow.csv')
            shutil.copyfileobj(fsrc, fdst)
            fdst.flush()
            # tar.add(data_path_name + '_slow.csv')
            tar.add(data_path_name + '_slow.csv', arcname=self.mac_add + '_' + t + '_slow.csv', recursive=False)
            print('Slow file added to tar')
            fsrc = open(self.fast_path, "rb")
            fdst = open(data_path_name + '_fast.csv', "wb")
            fsrc.seek(0, 0)
            fdst.seek(0, 0)
            print('Copying fast file to SD: ' + data_path_name + '_fast.csv')
            shutil.copyfileobj(fsrc, fdst)
            fdst.flush()
            # tar.add(data_path_name + '_fast.csv')
            tar.add(data_path_name + '_fast.csv', arcname=self.mac_add + '_' + t + '_fast.csv', recursive=False)
            print('Fast file added to tar')

            tar.close()
            print('Tar file closed')
            os.remove(self.data_path + self.mac_add + '_' + t + '_slow.csv')
            os.remove(self.data_path + self.mac_add + '_' + t + '_fast.csv')
            print('Removed originals')

        except Exception, e:
            self.logger.error('Error copying db data file from tmpfs to data folder and taring, data file may be lost: ' + str(e))

        try:
            print('Opening slow temp file for writing: ' + self.slow_path)
            self.temp_slow_data_file = open(self.slow_path, 'w')
            print('Opening fast temp file for writing: ' + self.fast_path)
            self.temp_fast_data_file = open(self.fast_path, 'w')

            print('Creating CSV writers')
            self.slow_csv_writer = csv.writer(self.temp_slow_data_file, delimiter=',')
            self.fast_csv_writer = csv.writer(self.temp_fast_data_file, delimiter=',')

            print('Writing column headers to temp files')
            self.write_row_to_file(self.col_heads, True, True)
            self.write_row_to_file(self.col_heads, False, True)

        except Exception, e:
            self.logger.error('Error opening temp file for writing, data file may be lost: ' + str(e))

        # print 'File move: ' + str('%.2f' % (1000 * (time.time() - t1))) + 'ms'

    def column_setup(self):
        self.col_heads = ['time', 'dBZS', 'dBAS', 'dBCS']
        [self.col_heads.append('dBZ1_' + "%.0f" % i) for i in self.octave.cent_f_sioct]
        [self.col_heads.append('dBZ3_' + "%.0f" % i) for i in self.octave.cent_f_thoct]

    def extract(self, sbuf):

        t = time.time()

        self.starttime = t - 1

        # audio_buf = np.array(unpack("%ih" % (len(sbuf) / 2), sbuf)) / pow(2, 15)
        audio_buf = np.fromstring(sbuf, dtype=np.int16) / 32768.0

        # FFT input buffer & square values to save doing this later
        sp_slow = self.weighting.fft_signal(audio_buf, speed='s')
        sp_fast = self.weighting.fft_signal(audio_buf, speed='f')

        sp_slow_filtered = self.weighting.filter_apply_slow(sp_slow)
        sp_fast_filtered = self.weighting.filter_apply_fast(sp_fast)

        slow_levels = self.levels.get_decibel(sp_slow_filtered, len(audio_buf) * self.weighting.slowdelta, self.cal_val)
        slow_octave_levels = self.octave.oct_vals_slow(sp_slow_filtered[0])

        # Add data to file as single csv row
        self.write_row_to_file(np.concatenate([np.array([self.starttime]), slow_levels, slow_octave_levels]), True, False)

        fast_levels = self.levels.get_decibel(sp_fast_filtered, len(audio_buf) * self.weighting.fastdelta, self.cal_val)
        fast_octave_levels = self.octave.oct_vals_fast(sp_fast_filtered[0:8])

        for j in range(0, 8):
            fast_row_level = np.concatenate([np.array([fast_levels[j]]),
                                                   np.array([fast_levels[j + 8]]),
                                                   np.array([fast_levels[j + 16]])])

            self.write_row_to_file(np.concatenate([np.array([self.starttime + (j * 0.125)]), fast_row_level,
                                                   fast_octave_levels[j]]), False, False)

        self.packet_idx += 1


        # print str(self.packet_idx) + ' \t-> ' + str('%.2f' % (1000 * (time.time() - t))) + 'ms'

        if self.packet_idx == self.packet_delta:
            self.move_from_temp_file()
            self.packet_idx = 0

    # def percentiles(self, dBZF, dBAF, dBCF):
    #     # TODO: implement at server, not here, keep implementation as its quite nifty
    #     # or on node after arbritrary time periods
    #     per_vals = [1, 5, 10, 50, 90, 95]
    #     blk = np.vstack([dBZF, dBAF, dBCF])
    #     np.sort(blk)
    #     th_oct_vals = [np.max(i) for i in blk]
    #     return th_oct_vals

# Left here for development
# Generates a single impulse file meaning it has equal energy across the full frequency range
if __name__ == '__main__':

    feat_extractor = Extractor(48000, 0, '.', '.')
    t = time.time()
    for i in range(0, 61):
        test_signal = np.zeros(48000)
        test_signal[0] = 1.0
        # x = np.arange(48000)
        # test_signal = np.sin(2 * np.pi * 1000 * x / 48000)
        buf = StringIO()

        in_sig = np.int16(test_signal * 32767)

        buf.write(in_sig)
        
        feat_extractor.extract(buf.getvalue())
    
    print 'Time to execute: ' + str(1000 * (time.time() - t)) + 'ms'



    




