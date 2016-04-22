NePA TesT is a front-end for mininet which
setups experiment on a given (networkx) network

Setup
=====

NePA TesT requires a patched version of Mininet.
Please refer to:
[NePA wiki](https://ans.disi.unitn.it/redmine/projects/community-newtork-emulator/wiki)
for the detailed setup.

Usage
=====

To run a test you need a configuration file
(to be placed in conf/) and the test class code
(to be placed in test_code/).
Then run
$>python wcn_emulator -f <conf_file> -t <test>
where <test> identifies a test case in 
<conf_file>. 
Each test case must specify an implementation
of MininetTest through the argoment "testClass"/
Each MininetTest class has the runTest method
which starts what the test needs and then waits
for completion.
This waiting can be implemented with self.wait()
function which sleeps for the desired amount of
time and optionally logs resource usage.

For example:

 * self.wait(self.duration) # will wait till the end
 * self.wait(self.duration, log_resources={'cpu': 'cpu_usage'}, 2) # will wait till the 
end of the test while sampling every 2 seconds
the cpu load and saving the results in a file 
called 'cpu_usage'.

Other than 'cpu', also 'net' and 'mem' can be
logged; 'mem' makes NePA TesT logging the amount
of available RAM (free or released) and the
amount of swap memory used; 'net' makes instead
logging both the fraction of received packets
over sent packets and the fraction of received
bytes over sent bytes since the beginning of the
test.
It is important to always specify the destination
file of the logs (even the same for all the
resources).

Test
====

NePA TesT stores test files in the Test folder.
Tests follows the pytest approach, to run them
simply install the pytest module and run
$>python -m pytest 
in the root folder

Troubleshooting
===============

If something fails system may remain unstable.
In this case try typing:
$> sudo mn -c

How to
======

Use a custom delay distribution for the links
---------------------------------------------

Through network_builder.py is possible to set
some parameters of the links, e.g., loss,
bandwidth, mean delay, delay jitter and delay
distribution.

Available delay distributions are placed in
/usr/lib/tc/ and the defaults one are normal,
pareto, paretonormal and experimental.

Given sample delay values is possible to build
a custom distribution and use it in mininet.
The following is an extraction from this [netem article](http://piao-tech.blogspot.it/2009/10/how-to-create-netem-distribution-tables.html).

 1. git clone git://git.kernel.org/pub/scm/linux/kernel/git/shemminger/iproute2.git
 2. compile these netem utilities:
    cd iproute2/netem
    gcc -o maketable maketable.c -lm
    gcc -o stats stats.c -lm
 3. fill data.txt with samples from the
    distribution (in ms), e.g.,
    ping -c10 google.com | grep -Eo 'time=[0-9.]+'| grep -Eo '[0-9.]+' > data.txt
 4. build a netem distribution
    ./maketable data.txt > mydist.dist
 5. put mydist.dist in /usr/lib/tc/
 6. compute mean and standard deviation (sigma)
    ./stats data.txt
 7. use the following configuration parameters:
    link_mean_delay = <mean>ms
    link_delay_sd = <sigma>ms
    link_delay_distribution = mydist 
