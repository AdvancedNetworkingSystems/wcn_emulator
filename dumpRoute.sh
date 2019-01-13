#!/bin/bash
sleep $2
while true; do
	date +%s
	timestamp=$(date +%s%N) #ns
	timestamp_short="${timestamp%????????}" #ms
	timestamp_rounded=$((5*($timestamp_short/5)))
	echo "/NetworkRoutes" | nc 127.0.0.1 2010 > $1/$timestamp_rounded
	sleep 0.5
done
