
import sys
sys.path.append('../')
from network_builder import *
from os import kill, path, makedirs
from matplotlib.pyplot import ion
from random import sample, randint
import time

from test_generic import *

class princeTest(MininetTest):

    def __init__(self, mininet, duration=10):
        super(princeTest, self).__init__(mininet, path, duration)
        self.mininet = mininet
        self.centList = []
        self.stopNodes = []
        self.stopNodeList = []
        self.olsr_conf_template = """
        DebugLevel  1
        IpVersion 4
        FIBMetric "flat"
        LinkQualityFishEye  0
        LockFile "%s"
        Hna4
        {
        }
        Hna6
        {
        }

        LoadPlugin "../olsrd/lib/netjson/olsrd_netjson.so.1.1"{
            PlParam "accept" "0.0.0.0"
            PlParam "port" "2010"
        }

        LoadPlugin "../olsrd/lib/poprouting/olsrd_poprouting.so.0.1"{
            PlParam "accept" "0.0.0.0"
            PlParam "port" "1234"
        }

        InterfaceDefaults {
        }

        Interface %s
        {
        }
        """

        self.prince_conf_template = """
        {
        	"proto": {
        		"protocol": "olsr",
        		"host": "%s",
        		"port": 2010,
        		"timer_port": 1234,
        		"refresh": 5
        	},
        	"graph-parser": {
        		"heuristic": 1,
        		"weights": 1,
        		"recursive": 0,
        		"stop_unchanged": 0,
        		"multithreaded": 0
        	}
        }
        """
    def launch_sniffer(self, host):

        cmd = "tcpdump -i any -n -X -e "

        logfile = self.prefix + host.name + "-dump.log"

        params = {}
        params['>'] = logfile
        params['2>'] = logfile

        return self.bgCmd(host, True, cmd,
                          *reduce(lambda x, y: x + y, params.items()))



    def launchOLSR(self, host, args):
        cmd = "../olsrd/olsrd " + args

        log_str = "Host " + host.name + " launching command:\n"
        info(log_str)
        info(cmd + "\n")
        logfile = self.prefix + host.name + "_olsr.log"

        params = {}
        params['>'] = logfile
        params['2>'] = logfile

        return self.bgCmd(host, True, cmd,
                          *reduce(lambda x, y: x + y, params.items()))


    def launchPrince(self,host, args):
        cmd = "../poprouting/output/prince " + args

        log_str = "Host " + host.name + " launching command:\n"
        info(log_str)
        info(cmd + "\n")
        logfile = self.prefix + host.name + "_prince.log"

        params = {}
        params['>'] = logfile
        params['2>'] = logfile

        return self.bgCmd(host, True, cmd,
                          *reduce(lambda x, y: x + y, params.items()))


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
        info("*** Launching Prince test\n")
        info("Data folder: "+self.prefix+"\n")

        for idx, h in enumerate(self.getAllHosts()):
            intf = h.intfList()
            intf_list = ' '.join(["\"" + i.name + "\"" for i in intf])
            olsr_conf_file = self.prefix + h.name + "_olsr.conf"
            olsr_lock_file = "/var/run/" + h.name + str(time.time()) + ".lock"
            f_olsr = open(olsr_conf_file, "w")
            print >> f_olsr, self.olsr_conf_template % (olsr_lock_file, intf_list)
            f_olsr.close()
            args_olsr = "-f " + os.path.abspath(olsr_conf_file)

            prince_conf_file = self.prefix + h.name + "_prince.json"
            f_prince = open(prince_conf_file, "w")
            print >> f_prince, self.prince_conf_template % (h.defaultIntf().ip)
            f_prince.close()
            args_prince = os.path.abspath(prince_conf_file)


            launch_pid = self.launchOLSR(h, args_olsr)
            launch_pid = self.launchPrince(h, args_prince)
            self.launch_sniffer(h)

            if h.defaultIntf().ip != self.destination:
                self.launchPing(h)

        info("Waiting completion...\n")
        self.wait(float(self.duration), log_resources={'net': 'netusage.csv'})
        self.killAll()



class princeRandomTest(princeTest):

    def __init__(self, mininet, name, args):

        duration = int(args["duration"])
        super(princeRandomTest, self).__init__(mininet, duration)
        self.destination = self.getHostSample(1)[0].defaultIntf().ip
        self.setPrefix(name)
