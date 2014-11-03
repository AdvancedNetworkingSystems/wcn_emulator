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

