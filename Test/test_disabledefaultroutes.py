from time import time
import os

from test_generic import MininetTest


def test_disable_default_routes():
    os.system("sudo rm -rf pingTestNoRoutes_toy*")
    os.system("sudo ./nepa_test.py -f conf/ping.ini -t pingTestNoRoutes")
    for f in os.listdir("."):
        if f.startswith("pingTestNoRoutes_toy"):
            for log in os.listdir(f):
                if log.endswith(".log") and not log.startswith("h1"):
                    with open(f + "/" + log, "r") as log_file:
                        content = log_file.read()
                        assert(content.find("bytes from") == -1) 
    os.system("sudo rm -rf pingTestNoRoutes_toy*")


def test_enable_default_routes():
    os.system("sudo rm -rf pingTest_toy*")
    os.system("sudo ./nepa_test.py -f conf/ping.ini -t pingTest")
    for f in os.listdir("."):
        if f.startswith("pingTest_toy"):
            for log in os.listdir(f):
                if log.endswith(".log"):
                    with open(f + "/" + log, "r") as log_file:
                        content = log_file.read()
                        assert(content.find("Destination Host Unreachable") == -1) 
    os.system("sudo rm -rf pingTest_toy*")
