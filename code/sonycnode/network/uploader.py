import os
import time
import sched
import glob
import json
import itertools as it
from random import choice
from multiprocessing.connection import Listener
from sonycnode.utils import sonyc_logger as loggerClass
from sonycnode.utils import misc
from sonycnode.network import uploadmanager
from sonycnode.monitor import devstatus


logger = loggerClass.sonycLogger(loggername="Uploader")

# Read Configuration file
parser = misc.load_settings()

ifacename    = parser.get('network', 'ifname').strip("'\"")
basedir      = parser.get('record', 'out_dir').strip("'\"")
http_servers = json.loads(parser.get('network', 'http_servers'))
vpn_servers  = json.loads(parser.get('network', 'vpn_servers'))
ipc_port     = parser.getint('network', 'ipc_port')
ipc_auth     = parser.get('network', 'ipc_auth').strip("'\"")
upload_types = json.loads(parser.get('upload', 'file_types'))
CA_CRT       = parser.get('network', 'ca_crt').strip("'\"")
USE_TLS      = parser.getboolean('network', 'use_https')
CLIENT_CRT   = parser.get('network', 'client_crt').strip("'\"")
CLIENT_KEY   = parser.get('network', 'client_key').strip("'\"")
CLIENT_PASS  = parser.get('network', 'client_pass').strip("'\"")
CRLFILE      = parser.get('network', 'crlfile').strip("'\"")
PROTOCOL     = 'https' if USE_TLS else 'http'

s            = sched.scheduler(time.time, time.sleep)

INTERNET_CONNECTED = False
VPN_CONNECTED      = False


def getFiles(path, *patterns):
    """
    Return iterator of filenames matching
    `patterns`

    Paramters
    ---------
    path: str
        base path
    patters: iterable
        iterable containing patterns against which
        files will be globbed
        .. note: `patterns` = ending file_pattern

    Returns
    -------
    iterator of filepaths matching `patterns`

    """
    return it.chain.from_iterable(glob.iglob(
        os.path.join(basedir, pattern)) for pattern in patterns)


def getStatus():
    """
    Obtain device status from `devstatus`
    Returns
    -------
    status_ping
        json dump of dictionary contatining status
        of the device
    """
    try:
        return devstatus.deviceStats()
    except Exception as ex:
        logger.warning("Could not obtain Device Status: "+str(ex))


def uploadStatus(status, server):
    """
    Upload Status
    """
    upload_info = None
    logger.debug("Uploading Status")
    with uploadmanager.UploadManager(ifacename=ifacename,
                                     url=PROTOCOL+"://"+server+"/status",
                                     timeout=30,
                                     secure=USE_TLS,
                                     cacert=CA_CRT,
                                     client_cert=CLIENT_CRT,
                                     client_key=CLIENT_KEY,
                                     client_pass=CLIENT_PASS,
                                     crlfile=CRLFILE) as um:
        upload_info = um.uploadStatus(json.dumps(status))

    if upload_info['server-response'] == '10':
        logger.info('Uploaded Device Status')

    return upload_info


def uploadFile(filename, server):
    """
    Upload File
    """
    upload_info = None
    logger.debug("Uploading: " + str(filename))
    ext = "/logs" if filename.endswith('log') else "/upload"
    with uploadmanager.UploadManager(ifacename=ifacename,
                                     url=PROTOCOL+"://"+server+ext,
                                     timeout=30,
                                     secure=USE_TLS,
                                     cacert=CA_CRT,
                                     client_cert=CLIENT_CRT,
                                     client_key=CLIENT_KEY,
                                     client_pass=CLIENT_PASS,
                                     crlfile=CRLFILE) as um:
        upload_info = um.uploadFile(filename)

    if upload_info['server-response'] == 'Upload Successful':
        logger.info("Uploaded: " + os.path.basename(filename))
        os.remove(filename)
    return upload_info


def runTask(sc, conn, fgen):
    upload_status_info = upload_file_info = None
    try:
        global INTERNET_CONNECTED
        global VPN_CONNECTED
        if conn.poll():
            INTERNET_CONNECTED, VPN_CONNECTED = conn.recv()

        if VPN_CONNECTED:
            upload_status_info = uploadStatus(getStatus(), choice(http_servers))
            filename = fgen.next()
            upload_file_info = uploadFile(filename, choice(http_servers))
            logger.info("Transfer Speed: " +
                        str(upload_file_info['speed-upload'] / 1024.0) +
                        " Kbps")

        elif INTERNET_CONNECTED:
            upload_status_info = uploadStatus(getStatus(),
                                              choice(http_servers))
            filename = fgen.next()
            upload_file_info = uploadFile(filename, choice(http_servers))
            logger.info("Transfer Speed: " +
                        str(upload_file_info['speed-upload'] / 1024.0) +
                        " Kbps")
        else:
            logger.warning("No VPN or Internet")

    except StopIteration:
        fgen = getFiles(basedir, *upload_types)

    except Exception as ex:
        logger.error("Error in Uploader: " + str(ex))

    finally:
        if upload_file_info:
            # Run again after the current file is uploaded +2 second
            sc.enter(0, 1, runTask, (sc, conn, fgen))
        else:
            # Try again in 5 seconds
            sc.enter(1, 1, runTask, (sc, conn, fgen))


def networkStatus():
    """
    Updates global variable `VPN_CONNECTED`
    and `INTERNET_CONNECTED` based on
    netmonitor
    """
    # Set up Listener for messages from netmonitor
    logger.info("Waiting for connection on: "+str(ipc_port))
    address = ('', ipc_port)
    listener = Listener(address, authkey=ipc_auth)
    conn = listener.accept()
    logger.info("Connection accepted from: " + str(listener.last_accepted))
    return conn


if __name__ == "__main__":
    conn = networkStatus()
    fgen = getFiles(basedir, *upload_types)
    s.enter(1, 1, runTask, (s, conn, fgen))
    s.run()
