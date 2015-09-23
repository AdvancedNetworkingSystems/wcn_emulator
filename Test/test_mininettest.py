from time import time
import os

from test_generic import MininetTest


def test_mininettest_wait():
    mt = MininetTest(None, None, None)
    mt.prefix = "/tmp"
    begin = time()
    mt.wait(3, {'net': 'netto', 'cpu': 'cippiu', 'mem': 'memory'})
    end = time()
    assert(end - begin < 3.1)
    assert(end - begin > 2.9)
    assert(os.path.isfile("/tmp/netto"))
    os.remove("/tmp/netto")
    assert(os.path.isfile("/tmp/cippiu"))
    os.remove("/tmp/cippiu")
    assert(os.path.isfile("/tmp/memory"))
    os.remove("/tmp/memory")
