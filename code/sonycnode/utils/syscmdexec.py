import time
import re
import sched
import os
import glob
import subprocess
from sonycnode.monitor import devstatus as ds
from sonycnode.utils import misc
from sonycnode.utils import sonyc_logger as loggerClass

logger = loggerClass.sonycLogger(loggername="SysCmdExec")

parser = misc.load_settings()
base_dir = parser.get('record', 'out_dir').strip('"')

try:
    DELETE_POLICY = float(parser.get('syscmd', 'delete_policy'))
except:
    logger.error('delete_policy not present or incorrect in settings file, defaulting to 90%')
    DELETE_POLICY = 90

# Run every X seconds
INTERVAL = 5

s = sched.scheduler(time.time, time.sleep)


def run_once(func):
    def wrapper(*args, **kwargs):
        if not wrapper.has_run:
            wrapper.has_run = True
            return func(*args, **kwargs)

    wrapper.has_run = False
    return wrapper


def execute(command):
    out = err = False
    try:
        os.chdir('/home/sonyc/sonycnode')
        cmdlist = command.split('\n')
        for j in cmdlist[1:]:
            logger.info(str(j))
            proc = subprocess.Popen(j,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE,
                                    shell=True)
            out, err = proc.communicate()
            if err:
                print "Error::::: " + str(err)
    except Exception as e:
        logger.error("Erorr Executing: " + str(e))
        err = True
    finally:
        return out, err


def parseCommand(message):
    try:
        with open(os.path.join(os.path.abspath(
                os.path.dirname(__file__)), 'commandmap.conf'),
                'r') as f:
            fi = f.read()
        re_filter = re.compile(r'^(\d+)\s{([^#{}]+)+\s}', re.MULTILINE)
        # greedy search
        cmdmap = re_filter.findall(fi)
        for i in xrange(len(cmdmap)):
            if message in cmdmap[i][0]:
                execute(cmdmap[i][1])
                break

    except Exception as e:
        logger.warning("Cannot open commandmap.conf: " + str(e))


def _getLogFiles():
    log_path = base_dir
    lf = filter(os.path.isfile, glob.glob(log_path + "/*.log"))
    # Get sorted list by mtime
    lf.sort(key=lambda x: os.path.getmtime(x), reverse=True)
    for f in lf:
        yield f


def _getDataFiles():
    data_path = base_dir
    df = filter(os.path.isfile, glob.glob(data_path + "/*.tar.gz"))
    # Get sorted list by mtime
    df.sort(key=lambda x: os.path.getmtime(x))
    # Interleave data
    for f in df[1::2]:
        yield f


def _getSPLDataFiles():
    data_path = base_dir
    df = filter(os.path.isfile, glob.glob(data_path + "/*.tar"))
    # Get sorted list by mtime
    df.sort(key=lambda x: os.path.getmtime(x))
    # Interleave data
    for f in df[1::2]:
        yield f


def runTask(sc, lf_gen, df_gen, spl_gen):
    """
    first delete all log files.
    then go for raw audio data.
    finally start deleting spldata_files.
    """
    datausage = ds.storageStats()['data_usage']
    try:
        if datausage > DELETE_POLICY:
            logger.warning("DEVICE USAGE : " +
                           str(datausage) +
                           '% > THRESHOLD of ' +
                           str(DELETE_POLICY) + '%')
            logger.warning("Removing all log files")
            for f in lf_gen:
                os.remove(f)
    except StopIteration:
        logger.warning("No more log files left")
        lf_gen = _getLogFiles()

    datausage = ds.storageStats()['data_usage']
    try:
        if datausage > DELETE_POLICY:
            data_files = df_gen.next()
            logger.warning("REMOVING : " + str(data_files))
            os.remove(data_files)
    except StopIteration:
        logger.warning("No more data files left. Will remove SPL data now")
        df_gen = _getDataFiles()
        try:
            # make sure data usage is still more than threshold
            datausage = ds.storageStats()['data_usage']
            if datausage > DELETE_POLICY:
                spldata_files = spl_gen.next()
                logger.warning("REMOVING : " + str(spldata_files))
                os.remove(spldata_files)
        except StopIteration:
            logger.warning("No more spl data files left")
            spl_gen = _getSPLDataFiles()

    except Exception as e:
        logger.warning("Error in runTask: " + str(e))
    finally:
        sc.enter(INTERVAL, 1, runTask, (sc, lf_gen, df_gen, spl_gen))


if __name__ == '__main__':
    log_files = _getLogFiles()
    data_files = _getDataFiles()
    spldata_files = _getSPLDataFiles()
    s.enter(1, 1, runTask, (s, log_files, data_files, spldata_files))
    s.run()
