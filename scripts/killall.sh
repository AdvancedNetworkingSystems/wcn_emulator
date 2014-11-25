#!/bin/bash

for i in `ps aux | grep dummy | grep python | awk '{print $2}'`; 
 do sudo kill $i; 
done
for i in `ps aux | grep dummy | grep python | awk '{print $2}'`; 
 do sudo kill -9 $i; 
done
