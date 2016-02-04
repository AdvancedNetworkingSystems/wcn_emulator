from time import sleep
import os
import multiprocessing as mp

from logsys import fprint, log_sys_resources


def test_fprint_invalid_input():
    fprint(None, None)
    fprint("", None)
    fprint("", 5)
    fprint("ciao", None)
    assert(not os.path.isfile("ciao"))


def test_fprint_valid_input():
    fprint("ciao", 7)
    assert(os.path.isfile("ciao"))
    f = open("ciao", 'r')
    assert(f.readline().split(",")[1] == "7\n")
    f.close()
    os.remove("ciao")


def test_log_sys_resources_invalid_input():
    p = mp.Process(target=log_sys_resources, args=(None, None, None))
    p.start()
    sleep(1)
    p.terminate()

    p = mp.Process(target=log_sys_resources, args=(None, None, 1))
    p.start()
    sleep(1)
    p.terminate()

    p = mp.Process(target=log_sys_resources, args=(None, {}, 1))
    p.start()
    sleep(1)
    p.terminate()


def test_log_sys_resources_valid_input():
    p = mp.Process(target=log_sys_resources, args=(".", {}, 1))
    p.start()
    sleep(1)
    p.terminate()

    p = mp.Process(target=log_sys_resources, args=(".", {'not': 'any'}, 1))
    p.start()
    sleep(1)
    assert(not os.path.isfile("any"))
    p.terminate()

    p = mp.Process(target=log_sys_resources, args=("/tmp", {'net': 'name'}, 1))
    p.start()
    sleep(1)
    assert(os.path.isfile("/tmp/name"))
    p.terminate()
    os.remove("/tmp/name")
