#!/bin/bash

while true; do
	timestamp=$(date +%s%N) #ns
	timestamp_short="${timestamp%??????}" #ms
	echo "/NetworkRoutes" | nc 127.0.0.1 2010 > $1/$timestamp_short
	sleep 0.4
done
