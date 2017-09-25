#!/usr/bin/env bash
folder="$1"
i=0
for i in 0 $2
do
  ip="10.0.$i.1"
  file=h"$i"_"$i"-dump.cap
  echo $ip
  tshark -Y "olsr.message_type eq 201 and ip.src eq $ip" -r $folder$file -T fields -e frame.time_relative -e frame.time_delta_displayed > $folder$file.dat
done
gnuplot -p -e "set key outside right; plot for [i=0:$2] '$folder'.'h'.i.'_'.i.'-dump.cap.dat' using 1:2 every 3:3 title 'Node h'.i"
