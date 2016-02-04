
import sys
sys.path.append('../')
from network_builder import *
from os import kill, path, makedirs
from matplotlib.pyplot import ion
from random import sample, randint

from test_generic import *

class pingTest(MininetTest):

    def __init__(self, mininet, duration=10):

        super(pingTest, self).__init__(mininet, path, duration)


    def launchPing(self, host):

        idps = randint(0,100)
        logfile = self.prefix + host.name.split('_')[0] + \
            "-" + str(idps) + "_ping_$(date +%s).log"

        cmd = "ping " + self.destination
        params = {}
        params['>'] = logfile
        params['2>'] = logfile

        return self.bgCmd(host, True, cmd,
            *reduce(lambda x, y: x + y, params.items()) )

    def runTest(self):
        info("*** Launching Ping test\n")
        info("Data folder: "+self.prefix+"\n")

        for h in self.getAllHosts():
            self.launchPing(h)

        info("Waiting completion...\n")
        self.wait(self.duration, log_resources={'net': 'netusage.csv'})
        self.killAll()

class pingRandomTest(pingTest):

    def __init__(self, mininet, name, args):

        duration = int(args["duration"])
        super(pingRandomTest, self).__init__(mininet, duration)
        h =  self.getHostSample(1)
        self.destination = self.getHostSample(1)[0].defaultIntf().ip
        self.setPrefix(name)


