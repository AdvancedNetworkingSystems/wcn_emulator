#!/bin/bash


runtest () 
{
  testFile=$1
  topoFile=$2
  testRun=$3
  runs=$4
  breaking=$5
  commandName="sudo ./wcn_simulator.py  -f $testFile -t $testRun -g $topoFile"
  testCommand=$6

  returnValue=0 

  echo "Running $runs tests";

  errors=0
  for i in `seq $runs`;
   do 
    sudo rm /tmp/*edges;
    sudo rm /tmp/*rt;
    sudo rm -rf $testRun* 
    echo $PWD
    echo $testCommand
    echo $commandName
    eval $commandName;
    eval $testCommand &> /tmp/testoutput.txt
    grep -q NOK /tmp/testoutput.txt;
    if [ $? == 0 ] ; then
      echo "Found an error";
      errors=$(($errors+1))
      if [ $breaking == 1 ]; then
        break;
      fi
    fi;
    egrep -q "^OK" /tmp/testoutput.txt;
    if [ $? == 1 ] ; then
      echo "You have no OK route found!";
      errors=$(($errors+1))
      if [ $breaking == 1 ]; then
        break;
      fi
    fi;

  done
  echo $PWD
  echo "found $errors error in $runs runs"
  returnValue=$errors
}


totError=0
dataDir="data/random/"
for f in `ls $dataDir/*edges`; do
  echo $f
  #testCommand="python ../dummy_routing_protocol/snippets/test_output.py /tmp/ $f"
  testCommand="cd scripts; ./compare_topologies_recursively.py  /tmp/dummyrouting ../$f; cd ../"
  runtest "conf/dummyrouting.ini" $f \
    "dummyRoutingCrashTest" 1 1 "$testCommand"
  totError=$(($totError+$returnValue))
done;
echo "Test Concluded with $totError erros!"


