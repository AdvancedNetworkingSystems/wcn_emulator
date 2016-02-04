import psutil as psu
from time import sleep, time


def fprint(filename, data):
    if filename and len(filename) > 0 and data:
        f = open(filename, 'a')
        f.write(str(time()) + "," + str(data) + "\n")
        f.close()


def log_sys_resources(prefix, resources, interval=1):
    '''
    interval must be in second
    resources must be a dictionary with value equal to the filename
    '''
    if not prefix:
        prefix = "."
    if resources and 'net' in resources:
        iostat = psu.net_io_counters()
        pkts_recv = iostat.packets_recv
        pkts_sent = iostat.packets_sent
        bytes_recv = iostat.bytes_recv
        bytes_sent = iostat.bytes_sent

    while(True):
        if resources and 'cpu' in resources:
            fprint(prefix + "/" + resources['cpu'], psu.cpu_percent())
        if resources and 'mem' in resources:
            fprint(prefix + "/" + resources['mem'],
                   str(psu.virtual_memory().available) + "," +
                   str(psu.swap_memory().used))
        if resources and 'net' in resources:
            iostat = psu.net_io_counters()
            if iostat.packets_sent - pkts_sent > 0:
                fprint(prefix + "/" + resources['net'],
                       str((iostat.packets_recv - pkts_recv) /
                           float(iostat.packets_sent - pkts_sent)) + "," +
                       str((iostat.bytes_recv - bytes_recv) /
                           float(iostat.bytes_sent - bytes_sent)))
            else:
                fprint(prefix + "/" + resources['net'], "0,0")
        if interval:
            sleep(float(interval))
