
import signal
import os 
from random import sample
from psutil import Process
from time import sleep

from mininet.log import info, error, debug, output 

class MininetTest(object):
    def __init__(self, mininet, path, duration):
        self.net = mininet
        self.pendingProc = {} 
        self.duration = duration
        self.prefix = ''
    
    def getHostSample(self, num):
        hosts = sample(self.net.values(), num)
        return hosts[:num]

    def getAllHosts(self):
        return self.net.values()

    def bgCmd(self,host,force_multiple_processes,*args):
        # here it's a little workaround for tracing the resulting pid
        # it launch the new process using the mininet interface
        # but it check the newly created process id using psutil
        host_proc = Process(host.pid)
        host_ps = set(host_proc.get_children())
        debug("Sending cmd: \n\t"+str(" ".join(args))+"\n")

        # disable bg process output
        tmp_wait = host.waiting
        host.waiting = False
        host.sendCmd(*(("set +m",)))
        host.waiting = tmp_wait

        if force_multiple_processes:
            host.waiting = False
        host.sendCmd(*(args+("&",)))
        sleep(0.5)
        try :
            pid = (set(host_proc.get_children()).difference(host_ps)).pop().pid
            info("BGProcess: "+str(pid)+"; ")
            self.pendingProc[pid] = host
        except:
            info("*** Unable to launch command:\n\t "+str(" ".join(args)))
            return None
        return pid

    def sendSig(self,pid,sig=signal.SIGTERM):
        try:
            info("Killing BGProcess: "+str(pid)+"; ")
            os.kill( pid, sig )
        except OSError:
            error("Error while killing process "+str(pid))
            pass

    def killAll(self):
        for pid in self.pendingProc.keys():
            self.sendSig(pid,signal.SIGKILL)
            self.pendingProc[pid].monitor() # wait exiting
        self.pendingProc.clear()
        info("\n")
        for host in self.net.values():
            host.waiting = False

    def setPrefix(self, name):
        self.prefix = str(name) + '_' + str(self.duration) + '/'
        if not os.path.exists(self.prefix):
                os.makedirs(self.prefix)

    def changePermissions(self):
        os.chmod(self.prefix, 0777)
        for root, dirs, files in os.walk(self.prefix):
            for dir in dirs:
                os.chmod(os.path.join(root, dir), 0777)
            for file in files:
                os.chmod(os.path.join(root, file), 0777)
