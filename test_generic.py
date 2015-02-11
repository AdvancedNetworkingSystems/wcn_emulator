
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

    def bgCmd(self, host, force_multiple_processes, *args):
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
            pid = (set(host_proc.get_children()).difference(host_ps)).\
                    pop().pid
            info("BGProcess: "+str(pid)+"; ")
            self.pendingProc[pid] = host
        except:
            info("*** Unable to launch command:\n\t "+str(args))
            return None
        return pid

    def sendSig(self, pid, sig=signal.SIGTERM):
        if sig == signal.SIGTERM or sig == signal.SIGKILL:
            info("Sending signal to BGProcess: "+str(pid)+"; ")
        try:
            os.kill( pid, sig )
        except OSError as e:
            error("Error while sending " + str(sig) + " to process "+str(pid) + " ")
            error("\nWith error " + str(e))
            pass

    def killAll(self, sig = signal.SIGKILL):
        for pid in self.pendingProc.keys():
            self.sendSig(pid, sig)
            try:
                #check if process still exists
                self.sendSig(pid, 0)
            except OSError:
                # process is not running 
                continue
            else:
                # now it's dead
                self.sendSig(pid, signal.SIGTERM)

        self.pendingProc.clear()
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
