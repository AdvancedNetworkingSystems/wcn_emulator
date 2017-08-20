import signal
import os
import multiprocessing as mp
from random import sample
from psutil import Process
from time import sleep

from mininet.log import info, error, debug, output
from logsys import log_sys_resources


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

    def execute(self, host, force_multiple_processes, *args):

        tmp_wait = host.waiting

        if force_multiple_processes:
            host.waiting = False
        ret = host.cmd(*(args))
        host.waiting = tmp_wait
        return ret

    def bgCmd(self, host, force_multiple_processes, *args):
        # here it's a little workaround for tracing the resulting pid
        # it launch the new process using the mininet interface
        # but it check the newly created process id using psutil
        host_proc = Process(host.pid)
        host_ps = set(host_proc.children())
        debug("Sending cmd: \n\t" + str(" ".join(args)) + "\n")

        # disable bg process output
        tmp_wait = host.waiting
        host.waiting = False
        host.sendCmd(*(("set +m",)))
        host.waiting = tmp_wait

        if force_multiple_processes:
            host.waiting = False
        host.sendCmd(*(args + ("&",)))
        sleep(0.5)
        try:
            pid = (set(host_proc.children()).difference(host_ps)).pop().pid
            info("BGProcess: " + str(pid) + "; ")
            self.pendingProc[pid] = host
        except:
            info("*** Unable to launch command:\n\t " + str(" ".join(args)))
            return None
        return pid

    def sendSig(self, pid, sig=signal.SIGTERM):
        try:
            info("Killing BGProcess: " + str(pid) + "; ")
            os.kill(pid, sig)
        except OSError:
            error("Error while killing process " + str(pid))
            pass

    def killProc(self, pid, sig=signal.SIGTERM, wait=False):
        active_procs = self.pendingProc.keys()
        if active_procs.count(pid) == 1:
            self.sendSig(pid, sig)
            if wait:
                self.pendingProc[pid].monitor()
            del self.pendingProc[pid]
        else:
            error("killProc: process %d not found" % pid)

    def killAll(self):
        from subprocess import call
        for pid in self.pendingProc.keys():
            self.sendSig(pid, signal.SIGKILL)
            # self.pendingProc[pid].monitor() # wait exiting
        self.pendingProc.clear()
        call(["killall", "olsrd"])  # BAD TRICK to be sure olsrd die
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

    def wait(self, time, log_resources=None, log_interval=1):
        if (log_resources):
            p = mp.Process(target=log_sys_resources,
                           args=(self.prefix, log_resources, log_interval))
            p.start()
        sleep(time)
        if log_resources:
            p.terminate()
