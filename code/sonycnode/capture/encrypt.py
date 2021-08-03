__author__ = "Mohit Sharma"
__credits__ = "Charlie Mydlarz, Justin Salamon, Mohit Sharma"
__version__ = "0.1"
__status__ = "Development"

from Crypto.Cipher import AES
from Crypto.PublicKey import RSA
from Crypto import Random
import base64
import os
import tarfile
from sonycnode.utils import sonyc_logger as loggerClass
from sonycnode.network import netmanager

class Encryption(object):
    """ Encryption & Compression for the audio
    files and keys.
    parameters:
        - RSA Key Path
    """

    def __init__(self, rsa_pub_key):
        self.logger = loggerClass.sonycLogger(loggername="Encrypt")
        self._BLOCK_SIZE = 32
        self._PADDING = '{'
        self._rsa_pub_key = rsa_pub_key
        self.outdir = '/mnt/sonycdata'
        self.netman = netmanager
        self.mac_add = str(self.netman.getMac("eth0")).replace(":", "").lower()

    def pad(self, message):
        self.logger.debug("Padding the file")
        return message + (self._BLOCK_SIZE -
                          len(message) %
                          self._BLOCK_SIZE) * self._PADDING

    # Encrypt the Audio data using AES                                           
    def EncryptAES(self, fname, path=os.getcwd()):
        """ Encrypt the audio with AES 4096
        Parameters:
        - fname: name of the file to be encrypted
        - path: Location to save encrypted file
            default: current dir
        """
        self.path = os.path.join(path, fname)
        self._aes_key = Random.new().read(AES.key_size[2])
        self._cipher = AES.new(self._aes_key)

        # Read file to be encrypted
        self.logger.debug('Reading file to be encrypted')

        with open(os.path.join(self.path, fname), 'r') as f:
            self.message = f.read()

        # Encrypt the file
        self.logger.debug('Encrypting the file')
        self.enc_message = (base64.b64encode(self._cipher.encrypt(self.pad(self.message))))
        # Encrypt the AES Key
        self.logger.debug('Encrypting the keyfile')
        self.enc_key = self._EncryptAES_key(self._aes_key)

        # Write encrypted file and encrypted key
        self.logger.debug("Writing encrypted file and key")
        try:
            with open(self.path + '.enc', 'wb') as f1:
                f1.write(self.enc_message)
            # self.logger.debug('Writing encrypted audio to file')
            with open(self.path + '.key', 'wb') as f2:
                f2.write(self.enc_key[0])
            self.logger.debug('Writing encrypted key to file')
        except Exception, e:
            print 'Error Encrypting File ' + str(e)
            self.logger.error('Error Encrypting File ' + str(e))
        finally:
            self.logger.info('Compressing all files')
            # Compress to tar.gz
            self._compressFlac(fname)

    def _compressFlac(self, fname):
        try:
            # Dirty Hack to remove '.flac' at 
            # end of self.path
            fname_noext = os.path.basename(fname)[:-5]

            # Check if location file exists, if not prepend t_ to filename to indicate testing
            if os.path.exists(os.path.join(os.path.expanduser("~sonyc"), 'location')):
                gz_fname = os.path.join(self.outdir, '%s_' % self.mac_add + fname_noext) + '.tar.gz'
            else:
                gz_fname = os.path.join(self.outdir, 't_%s_' % self.mac_add + fname_noext) + '.tar.gz'

            tar = tarfile.open(gz_fname, 'w:gz')

            for files in [self.path + '.enc', self.path + '.key']:
                # tar.add(files)
                tar.add(files, arcname=os.path.basename(files))
                self.logger.debug('Compressing ' + str(files))
            tar.close()
        except Exception, e:
            self.logger.error('Error Compressing Files: ' + str(e))
        finally:
            # Return self.enc_message, self.enc_key
            self.logger.debug("Removing encryped file and key from disk")
            os.remove(self.path + '.enc')
            os.remove(self.path + '.key')
            # Removing wave and flac files after successful taring
            self.logger.debug('Removing Flac and Wav files')
            os.remove(self.path[:-5] + '.wav')
            # removing flac file
            os.remove(self.path)

    # Encrypt the AES key using RSA
    # Private Method.
    def _EncryptAES_key(self, aes_key):
        """ Encrypt the AES keys using RSA
        Private method
            Parameters:
            - rsa_key_path
            - aes_key
        """
        self._key_path = self._rsa_pub_key
        self._aes_key = aes_key
        try:
            with open(os.path.abspath(self._key_path), 'r') as f:
                self._temp = f.read()
            self._rsa_key = RSA.importKey(self._temp)
            self.enc_key = self._rsa_key.encrypt(self._aes_key, 32)
            self.logger.debug('Encrypting AES key using RSA')
        except Exception, e:
            print 'Error Encrypting AES key using RSA ' + str(e)
            self.logger.error('Error Encrypting AES key using RSA ' + str(e))
        finally:
            return self.enc_key
