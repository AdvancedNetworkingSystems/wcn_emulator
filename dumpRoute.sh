#!/bin/bash
dump=false
sigusr1(){
	exit 1
}
sigusr2(){
	dump=true
}
trap 'sigusr1' USR1
trap 'sigusr2' USR2
while true; do
	if $dump; then
		timestamp=$(date +%s%N) #ns
		timestamp_short="${timestamp%????????}" #ms
		timestamp_rounded=$((5*($timestamp_short/5)))
		echo "/NetworkRoutes" | nc 127.0.0.1 2010 > $1/$timestamp_rounded
		sleep 0.1
	fi
done
