__author__ = "Mohit Sharma"
__credits__ = "Charlie Mydlarz, Justin Salamon, Mohit Sharma"
__version__ = "0.1"
__status__ = "Development"

import pyaudio
from sonycnode.utils import sonyc_logger as loggerClass


# logger_path = os.path.abspath('../utils/sonyc_logger.py')
# loggerClass = imp.load_source('sonyc_logger', logger_path)

class devices(object):
    """ Sonyc.devices will hold information for
    getting information related to the audio
    devices connected to the host machine """

    def __init__(self):
        # Creating an instance of pyaudio.PyAudio
        self.p = pyaudio.PyAudio()
        self.logger = loggerClass.sonycLogger(loggername="RecorderHwInfo")

    def list_devices(self):
        """ This method will list all the devices
        connected to host machine along with its
        Index value"""
        # self.logger.debug('List of devices: ')
        # print('Index\tValue\n===============')
        for i in range(self.p.get_device_count()):
            devinfo = self.p.get_device_info_by_index(i)
            # Convert dictionary key:value pair to a tuple
            for k in list(devinfo.items()):
                name, value = k
                if 'name' in name:
                    yield k
                    #print i, '\t', value
                    #self.logger.debug(str(i)+" : "+str(value))

    def device_features(self, index, rates=None, channels=None):
        """ This method will tell you what
        features are supported by device. Pass
        the index value as argument. Optional arguments:
        rates, channels
        """
        self.index = index
        self.rates = []
        self.channels = channels

        if rates:
            self.rates.append(rates)
        else:
            # General Sample rates obtained from
            # http://wiki.audacityteam.org/wiki/Sample_Rates#Bandwidth 
            self.rates = [8000.0, 11025.0, 22050.0, 32000.0,
                          44100.0, 48000.0, 64000.0, 88200.0,
                          96000.0]

        if self.channels:
            pass
        else:
            self.channels = self.max_input_channels(self.index)

        # print self.device_name(self.index), 'supports:'
        self.logger.debug(str(self.device_name(self.index)) + " supports ")
        print '=============================================='

        # Check all the samples supported
        for samples in self.rates:
            try:
                if (self.p.is_format_supported(samples,
                                               input_device=self.index,
                                               input_channels=self.channels,
                                               input_format=pyaudio.paInt16)):
                    print 'Sampling: ', samples, '\tchannels: ', self.channels
                    self.logger.debug("Samples: " + str(samples) + "Channels: " + str(channels))
            except:
                pass

    def device_name(self, index):
        """ Returns Device name corresponding to
        index value passed
        """
        self.index = index
        return str(self.p.get_device_info_by_index(self.index)
                   ['name'])

    def max_input_channels(self, index):
        """ Returns maximum input channels supported by
        the device whose index value is passed
        """
        self.index = index
        return int(self.p.get_device_info_by_index(self.index)
                   ['maxInputChannels'])

    def default_samplerate(self, index):
        """ Returns default sample rate for the
        device whose index value is passed
        """
        self.index = index
        return int(self.p.get_device_info_by_index(self.index)
                   ['defaultSampleRate'])

    def input_latency(self, index):
        """ Returns the default input latency
        for the device whose index value is passed
        """
        self.index = index
        return float(self.p.get_device_info_by_index(self.index)
                     ['defaultLowInputLatency'])


if __name__ == '__main__':
    d = devices()
    d.list_devices()
