#!/bin/bash

while true; do
	timestamp=$(date +%s)
	echo "/NetworkRoutes" | nc 127.0.0.1 2010 > $1/$timestamp
	sleep 1
done
