
import signal
from random import sample
from psutil import Process
from time import sleep

from mininet.log import info, error, debug, output

class MininetTest(object):
    def __init__(self,mininet):
        self.net = mininet
        self.pendingProc = {} 
    
    def getHostSample(self,num):
        hosts = sample(self.net.values(),num)
        return hosts[:num]

    def bgCmd(self,host,force_multiple_processes,*args):
        # here it's a little workaround for tracing the resulting pid
        # it launch the new process using the mininet interface
        # but it check the newly created process id using psutil
        host_proc = Process(host.pid)
        host_ps = set(host_proc.get_children())
        debug("Sending cmd: \n\t"+str(args)+"\n")
        if force_multiple_processes:
            host.waiting = False
        host.sendCmd(*(args+("&",)))
        sleep(0.5)
        try :
            pid = (set(host_proc.get_children()).difference(host_ps)).pop().pid
            info("BGProcess: "+str(pid)+"; ")
            self.pendingProc[pid] = host
        except:
            info("*** Unable to launch command:\n\t "+str(args))
            return None
        return pid

    def sendSig(self,pid,sig=signal.SIGTERM):
        try:
            info("Killing BGProcess: "+str(pid)+"; ")
            kill( pid, sig )
        except OSError:
            error("Error while killing process "+str(pid))
            pass

    def killAll(self):
        for pid in self.pendingProc.keys():
            self.sendSig(pid,signal.SIGKILL)
            self.pendingProc[pid].monitor() # wait exiting
        self.pendingProc.clear()


