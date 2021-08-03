import supervisor.xmlrpc
import xmlrpclib
import psutil
import os
import operator
import json
import subprocess
import time
import sched
from sonycnode.utils import sonyc_logger as loggerClass
from sonycnode.utils import misc
from sonycnode.capture import info

sc     = sched.scheduler(time.time, time.sleep)
logger = loggerClass.sonycLogger(loggername="ProcessMonitor")
parser = misc.load_settings()

RUNNING_STATENAME     = ["RUNNING"]
NOT_RUNNING_STATENAME = ["STARTING", "BACKOFF",
                         "FATAL", "UNKNOWN"]
STOPPED_STATENAME     = ["STOPPING", "STOPPED", "EXITED"]

class RestartingSupervisordException(Exception):
    def __init__(self, message):
        super(RestartingSupervisordException, self).__init__(message)
        self.errors = 1001

        
class SupervisorCommands(object):
    
    def __init__(self):
        self.proxy = xmlrpclib.ServerProxy('http://127.0.0.1',
                                           transport=supervisor.xmlrpc.SupervisorTransport(
                                               None, None,
                                               'unix:///tmp/supervisor.sock'))

    def supervisordIsRunning(self):
        """
        Returns
        -------
        supervisor_status: True if supervisor is running
        else, returns error codes
        """
        supervisor_state = self.proxy.supervisor.getState()
        if supervisor_state['statecode'] == 1:
            logger.info("Supervisord: "+str(supervisor_state["statename"]))
            return True
        else:
            logger.warning("Supervisord: "+str(supervisor_state["statename"]))
            return supervisor_state['statecode']
    
    def supervisordPID(self):
        """
        Returns
        -------
        PID of supervisord
        """
        return self.proxy.supervisor.getPID()

    def restartSupervisord(self):
        """
        Restart supervisord
        """
        self.proxy.supervisor.restart()
    
    def processInfo(self, proc_name):
        """
        Process info for `proc_name`
        Parameters
        ----------
        proc_name: str
        proccess name
        Returns
        -------
        proc_info: dict
        dictionary containing information
        about the process
        """
        return self.proxy.supervisor.getProcessInfo(proc_name)

    def processIsRunning(self, proc_name):
        """
        Returns True if `proc_name` is running
        Parameters
        ----------
        proc_name: str
            process name
        Returns
        -------
        process_running: bool
            True if `proc_name` is running
        """
        return self.processInfo(proc_name)['statename'] == 'RUNNING'

    def startProcess(self, proc_name):
        """
        Start `proc_name`
        Parameters
        ----------
        proc_name: str
        process name
        Returns
        -------
        True if start was successful
        """
        if self.processInfo(proc_name)['statename'] in RUNNING_STATENAME:
            return True
        else:
            return self.proxy.supervisor.startProcess(proc_name)

    def stopProcess(self, proc_name):
        """
        Stop `proc_name`
        Parameters
        ----------
        proc_name: str
        process name
        Returns
        -------
        True if stop was successful
        """
        if self.processInfo(proc_name)['statename'] in STOPPED_STATENAME:
            return True
        else:
            return self.proxy.supervisor.stopProcess(proc_name)

    def restartProcess(self, proc_name):
        """
        Restart `proc_name`
        Parameters
        ----------
        proc_name: str
        process name
        Returns
        -------
        True if start was successful
        """
        if not self.processInfo(proc_name)['statename'] in STOPPED_STATENAME:
            self.proxy.supervisor.stopProcess(proc_name)
        return self.proxy.supervisor.startProcess(proc_name)

if __name__ == "__main__":
    cm = SupervisorCommands()
    # Dictionary of processes --> {group: [processes]}
    process_dict = json.loads(parser.get('processes', 'process_groups'))
    # Flattened list of all processes inside groups
    processes = [x for y in process_dict.viewvalues() for x in y]
    # All groups
    groups = [x for x in process_dict.viewkeys()]

    def memory_usage(proc_name):
        """
        Return memory usage for process `proc_name`
        Parameters
        ----------
        proc_name
        process name
        Returns
        -------
        mem_percent: float
        memory utilization percent
        """
        proc_pid = cm.processInfo(proc_name)['pid']
        if proc_pid is not 0:
            proc = psutil.Process(proc_pid)
            return float(proc.memory_percent()) > 60.0

    def cpu_usage(proc_name):
        """
        Return current cpu utilization percent
        Paramters
        ---------
        proc_name: str
        process id of the process
        Returns
        -------
        cpu_percent: float
        cpu utilization percent
        """
        proc_pid = cm.processInfo(proc_name)['pid']
        if proc_pid is not 0:
            proc = psutil.Process(proc_pid)
            return float(proc.cpu_percent()) > 50.0

    def initialize():
        try:
            global cm
            # Check if supervisord is running. If not, restart it
            if not cm.supervisordIsRunning:
                logger.info(str(cm.supervisordPID()))
                cm.restartSupervisord()
                logger.info("Restarting Supervisord")
                raise RestartingSupervisordException("Hold On!.. Restarting Supervisord")

            # Stop all processes
            # map(lambda proc: cm.stopProcess(proc), processes)

            # Start all processess in groups
            for group, proc in process_dict.viewitems():
                # check if process is already running
                running_processes = set(map(lambda proc:
                                            cm.processIsRunning(proc),
                                            processes))
                logger.info("Starting processes in group: "+str(group))
                map(lambda x: cm.startProcess(x),
                    set(processes) - running_processes)
                # sleep before starting next process (Required?)
                # time.sleep(1)
                
        except RestartingSupervisordException:
            # New proxy for supervisor
            cm = SupervisorCommands()

        except Exception as e:
            logger.warning("Error in Initialization: "+str(e))

    def runTask(sc):
        global cm
        try:
            for group, proc in process_dict.viewitems():
                # Check if process is running, cpu and ram utilization
                # are within limits. If not, restart the process group

                # if not (all(map(lambda x: cm.processIsRunning(x), proc)) and
                #        (all(map(lambda x: memory_usage(x), proc)) and
                #         (all(map(lambda x: cpu_usage(x), proc))))):
                
                if not all(map(lambda x: cm.processIsRunning(x), proc)):
                    logger.warning("Restarting "+str(group))
                    # Restart all processes in that group
                    map(lambda x: cm.restartProcess(x), proc)

                elif all(
                    map( operator.and_,
                        map(lambda x: memory_usage(x), proc),
                        map(lambda x: cpu_usage(x), proc)) ):
                    logger.warning("CPU/RAM utilization > threshold")
                    logger.warning("Restarting "+str(group))
                    # Restart all processes in that group
                    map(lambda x: cm.restartProcess(x), proc)
                
        except Exception as ex:
            logger.critical("Error in Process_monitor: "+str(ex), exc_info=True)
            
        finally:
            # Monitor every 5 seconds
            sc.enter(5, 1, runTask, (sc,))

    initialize()
    sc.enter(5, 1, runTask, (sc,))
    sc.run()
