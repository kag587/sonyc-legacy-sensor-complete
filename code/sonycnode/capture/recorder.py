__author__ = "Mohit Sharma"
__credits__ = "Charlie Mydlarz, Justin Salamon, Mohit Sharma"
__version__ = "0.2"
__status__ = "Development"

import info
import pyaudio
import wave
import time
import os
import multiprocessing
from threading import Thread
from cStringIO import StringIO
import audiotools
import encrypt
from sonycnode.utils import sonyc_logger as loggerClass
from level_feats import Extractor
import numpy as np


# logger_path = os.path.abspath('../utils/sonyc_logger.py')
# loggerClass = imp.load_source('sonyc_logger', logger_path)


class Record(info.devices):
    """ This class contains methods for
    recording audio using async_io technique

    Parameters to be passed:
        - index : Index number of the device
        as detected by the host machine.
        check list_devices()

        - channels : No. of input channels
        default = 1 (Mono)

        - bitdepth : bitdepth for sampling. Default =
        pyaudio.paInt16. Allowed options = paInt8,
        paInt24, paInt32
        (Refer Documentation)

        - rate : sampling rate. Default = 48000

        -frames_per_buffer : no. of samples to be
        held in the buffer before sending to
        callback. Default = 4800

        - endtime : Duration of the recording in
        seconds. Default = 0 (infinity). Output will
        still be one file every minute.
    """

    def __init__(self, index, directory, rsa_key, channels=1,
                 bitdepth=pyaudio.paInt16,
                 rate=48000, frames_per_buffer=4800,
                 interval=10.0, cal_val=74.52,
                 coverage=0.5, min_silence=5.0, silence_sampling='normal',
                 record=False):

        super(Record, self).__init__()
        self.temp_dir = '/tmp'
        self.feat_extractor = Extractor(
            rate, cal_val, self.temp_dir, directory)
        self.logger = loggerClass.sonycLogger(loggername="Recorder")
        self.index = index
        self.directory = directory
        self._record = record
        self.channels = channels
        self.format = bitdepth
        self.rate = rate
        self.frames_per_buffer = frames_per_buffer
        self.cal_val = cal_val
        self.interval = interval
        self._buff1 = StringIO()  # Buffer 1
        self._buff2 = StringIO()  # Buffer 2
        self._featbuff = StringIO()
        self._buffer = self._buff2  # Proxy Buffer
        self._pa = pyaudio.PyAudio()  # Initialize PyAudio
        self._alternate = None
        self.rsa_key = rsa_key
        self._encrypt = encrypt.Encryption(self.rsa_key)
        self.clip_horizon = time.time()
        self.coverage = coverage
        self.min_silence = min_silence
        self.silence_sampling = silence_sampling
        self.callback_update = 0

        # Create data folder if it doesnt exist
        if not os.path.exists(self.directory):
            os.makedirs(self.directory)

        # self.logger.info('Preparing the Recorder')
        # Instantiate Recording stream
        self._recorder = self._pa.open(
            start=False,
            input_device_index=self.index,
            format=self.format,
            channels=self.channels,
            rate=self.rate,
            input=True,
            frames_per_buffer=self.frames_per_buffer,
            stream_callback=self.__recorder_callback)

    def start_recorder(self):
        """ Start recording
        """
        self.logger.info('Starting to record')
        self._recorder.start_stream()

    def stop_recorder(self):
        """ Stop recording
        """
        self.logger.info('Stopping recorder')
        self._recorder.stop_stream()

    def check_callback(self):
        return self.callback_update

    def __del__(self):
        """ Stop recorder and release
        port audio connection
        """
        self.logger.debug('Releasing resources acquired by recorder ')
        self._pa.terminate()
        self._pa = None

    def __alternator(self):
        while True:
            self.logger.debug('Swapping buffer')
            yield self._buff1
            yield self._buff2

    def __writer(self, time_now, buff):
        buff.seek(0)

        fname = os.path.abspath(self.temp_dir + '/' + str(time_now))

        try:
            # Create Wave file and set its   parameters
            wf = wave.open(fname + '.wav', 'wb')
            wf.setnchannels(self.channels)
            wf.setsampwidth(self._pa.get_sample_size(pyaudio.paInt16))
            wf.setframerate(self.rate)

            # Check sample rate 
            # Half of sampling rate ??
            while wf.tell() != self.rate * self.interval:
                wf.writeframes(buff.read())
            self.logger.info('Wave audio written to file')
        except Exception, e:
            self.logger.error('Error writing to Wav file ' + str(e))
        finally:
            if wf:
                wf.close()
                buff.reset()
            self._toflac(fname, time_now)

    def _toflac(self, fname, time_now):
        self.fname = fname
        # Converting WAV encoded audio to FLAC
        try:
            flac_in = audiotools.open(self.fname + '.wav')
            # TODO: Vary compression modes (<8) and see effect on CPU
            # utilization
            temp = flac_in.convert(
                (self.fname + '.flac'), audiotools.FlacAudio,
                compression=audiotools.FlacAudio.COMPRESSION_MODES[8])

            # Check if flac was encoded correctly
            # (Can include a couple more.. but this is
            # sufficient)
            if flac_in.seconds_length() == temp.seconds_length():
                # Encrypt and Compress
                self._encrypt.EncryptAES(self.fname + '.flac')
                self.logger.info('Flac audio written to file')
            else:
                self.logger.error(
                    'Error writing to flac file - length mismatch')

        except Exception, e:
            self.logger.error('Error writing to flac file ' + str(e))
        finally:
            pass
            # Remove wave and flac files.
        self.logger.info(
            'Total time for IO: ' + str(time.time() - time_now) + 's')

    def __recorder_callback(self, in_data, frame_count, time_info,
                            status_flags):
        """ Callback for async recording
            using Dualbuffer
        """

        self.callback_update += 1
        if self.callback_update == 1000:
            self.callback_update = 1

        if status_flags:
            self.logger.error('Input overflow status: ' + str(status_flags))

        self._featbuff.write(in_data)
        if int(self._featbuff.tell()) % (self.rate * 2) == 0:
            # Spawn a new feature extraction thread and throw data to it
            self._time_now = time.time() - 1
            t = Thread(target=self.feat_extractor.extract,
                       args=(self._time_now, self._featbuff.getvalue()))
            t.start()
            self._featbuff.reset()

        # Check if we're recording, if so add to buffer
        if time.time() > self.clip_horizon:
            # Dual Buffer
            self._alternate = self.__alternator()
            self._buffer.write(in_data)

        # Check if buffer has filled to reach clip duration (interval),
        # If so save clip, reset buffer and compute new clip horizon.
        # if int(self._buffer.tell()) % (self.rate * 2 * self.interval) == 0:
        if int(self._buffer.tell()) >= (self.rate * 2 * self.interval):
            self._time_now = time.time() - self.interval
            if self._record:
                # Spawn a new process and throw data to it
                self.logger.debug('Creating new process to write wav file')
                pr = multiprocessing.Process(target=self.__writer,
                                             args=(self._time_now, self._buffer))
                pr.start()

            # Swapping and Clearing buffer
            self.temp = self._buffer
            self._buffer = self._alternate.next()
            self.temp.reset()

            # Compute new horizon
            self.clip_horizon = (
                time.time() + self.__get_silence(
                    self.interval,
                    self.coverage,
                    min_silence=self.min_silence,
                    sampling=self.silence_sampling))

        return None, pyaudio.paContinue

    def __get_silence(self, clip_duration, coverage, min_silence=5.0,
                      sampling='normal'):
        '''Given a clip_duration and desired coverage fraction, compute
        how long the silence between clips needs to be to satisfy the desired
        coverage and add some random variance to the silence based so that it
        gives values sampled from the distribution specified by sampling.

        Parameters
        ----------
        clip_duration : float
            Duration of non-silent clip in seconds
        coverage : float
            Fraction of time to be recorded (non-silence), must be in range
            (0,1]
        min_silence : float
            Minimum silence allowed between clips, in seconds
        sampling : str
            The distribution from which silence durations will be sampled, must
            be 'uniform' or 'normal'.

        Returns
        -------
        silence : float
            The amount of silence to insert between the current and next clip,
            in seconds.
        '''
        # checks and warnings
        if clip_duration <= 0:
            self.logger.warning('Clip duration must be positive, setting to '
                                'default: 10.0')
            clip_duration = 10.0

        if coverage <= 0 or coverage > 1:
            self.logger.warning('Coverage outside the allowed range of (0.1], '
                                'setting to default: 0.5')
            coverage = 0.5

        if min_silence <= 0:
            self.logger.warning('min_silence must be positive, setting to '
                                'default: 5.0')
            min_silence = 5.0

        if sampling not in ['normal', 'uniform']:
            self.logger.warning('Unknown sampling, defaulting to normal.')
            sampling = 'normal'

        # Compute exact silence duration
        silence = (1 - coverage) / float(coverage) * clip_duration

        # If the silence required to obtain the specified coverage is shorter
        # than min_silence we default back to min_silence and report the
        # estimated coverage
        if silence < min_silence:
            est_coverage = (
                clip_duration / float(clip_duration + min_silence) * 100)
            warning_msg = (
                "Coverage too high to meet min_silence of {:.2f} seconds, "
                "returning {:.2f}. Estimated coverage "
                "is {:.2f}%".format(min_silence, min_silence, est_coverage))
            self.logger.warning(warning_msg)
            return min_silence
        else:
            # Add some variance
            mu = silence

            if sampling == 'uniform':
                sigma = np.abs(silence - min_silence)
                max_silence = mu + sigma
                silence += np.random.random_sample() * 2 * sigma - sigma
            elif sampling == 'normal':
                sigma = np.abs(silence - min_silence) / 3.0
                max_silence = mu + sigma * 3
                silence = sigma * np.random.randn() + mu

            # Make sure silence is within limits
            silence = min(max(silence, min_silence), max_silence)

            return silence
