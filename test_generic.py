
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

    def hostSentPackets(self,host):
        sent_packets = 0
        sent_bytes = 0
        intfs = host.intfNames()
        for intf in intfs:
            sent_bytes += int(host.cmd("ifconfig",intf ,"| grep -Eo 'TX bytes:[0-9]+' | cut -d':' -f 2"))
            sent_packets += int(host.cmd("ifconfig ",intf ,"| grep -Eo 'TX packets:[0-9]+' | cut -d':' -f 2"))
        return (sent_packets,sent_bytes)

    def hostReceivedPackets(self,host):
        received_packets = 0
        received_bytes = 0
        intfs = host.intfNames()
        for intf in intfs:
            received_bytes += int(host.cmd("ifconfig "+intf +" | grep -Eo 'RX bytes:[0-9]+' | cut -d':' -f 2"))
            received_packets += int(host.cmd("ifconfig "+intf +" | grep -Eo 'RX packets:[0-9]+' | cut -d':' -f 2"))
        return (received_packets,received_bytes)
        
    def generatedPackets(self):
        # if you experience assertion errors, you should
        # try to make sleep the mininet thread for a second
        received_packets = 0
        received_bytes = 0
        sent_packets = 0
        sent_bytes = 0
        hosts = self.net.values()
        for h in hosts:
            p,b = self.hostSentPackets(h)
            sent_packets += p
            sent_bytes += b
            p,b = self.hostReceivedPackets(h)
            received_packets += p
            received_bytes += b
        assert(received_packets == sent_packets)
        assert(received_bytes == sent_bytes)
        return (received_packets,received_bytes)

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
