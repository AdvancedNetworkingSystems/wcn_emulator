#!/usr/bin/env bash
for file in $(ls $1*_prince.log | sort -g);
do
  echo $file >> /tmp/gnuplot
  cut $file -f1,3 >> /tmp/gnuplot
  echo >> /tmp/gnuplot
  echo >> /tmp/gnuplot
done
gnuplot -e "plot for [i=0:24] 'h'.i.'_'.i.'_prince.log' using 1:3 title 'Node h'.i"
