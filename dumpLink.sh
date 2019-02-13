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
		date +%s
		timestamp=$(date +%s%N) #ns
		timestamp_short="${timestamp%????????}" #ms
		timestamp_rounded=$timestamp_short
		echo "/lin" | nc 127.0.0.1 2008 > $1/$timestamp_rounded
		sleep 0.1
	fi
done
