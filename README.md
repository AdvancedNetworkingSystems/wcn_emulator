How to create new test code, lets' say cooltest:
 1 - create a python module cooltest.py in test_code folder 
 2 - create in it a class coolTestClass that derives from MininetTest 
 3 - create a runTest method that will be launched by mininet
 4 - create a configuration file: conf/cooltest.ini
 5 - in the conf file add a stanza with configuration params, like:

     [coolTest]
     testModule = cooltest
     testClass = coolTestClass
     duration = 30
     graphDefinition = data/yourfavouritegraph.edges
 
     where testModule is the name of the python module, testClass is the
     name of the class in the pyhton module to be run, duration is the 
     duration of the experiment, graphDefinition is a network graph. Any
     other option you put here, is passed to your module in a
     dictionary.

 6 - run as root ./wcn_emulator -f conf/cooltest.ini -t coolTest 
 7 - a folder coolTest_DATE/ is created for each run. you should
     redirect there the output of your commands (check the ping.py
     class to see how). 



How to test that things work properly, referring to commit
df12378cb532e18efcab1c9502e5bd5b9c4deb50

I have set up some scripts to test the code:
 - run an emulation, let's say coolTest. This will generate two sets of files in the /tmp
folder /tmp/coolTest*.rt and /tmp/coolTest.edges. The first is a json
formatted log of the routing table of each node plus some more
information (like if the node has failed during the emulation) the
second is the neighborhood of the node. 
 - cd scripts; ./compare_topologies_recursively.py /tmp/coolTest originaltopo.edges-1 
 originaltopo.edges is the original topology passed to mininet. This
will load all the routing tables, navigate recursively all of them to 
test that the shortest paths computed by routing daemon are the same
ones compute via networkx (still no support for ETX). This will output
the number of errors found and generates a file in /tmp/testoutput.txt
where you can check the results.

You can automate this modifying scripts/run_batch_test.sh and running
it. This script will look for topologies defines in data/random, run a
simulation with each of the topology and check the results. You can
generate random topologies with scripts/random_graph_generator.sh


