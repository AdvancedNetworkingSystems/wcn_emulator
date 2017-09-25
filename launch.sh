#!/bin/sh

#python nepa_test.py -f conf/prince.ini -t RING9
#python nepa_test.py -f conf/prince.ini -t RING16
#python nepa_test.py -f conf/prince.ini -t RING25
#python nepa_test.py -f conf/prince.ini -t RING36

#python nepa_test.py -f conf/prince.ini -t GRID9
#python nepa_test.py -f conf/prince.ini -t GRID16
#python nepa_test.py -f conf/prince.ini -t GRID25
#python nepa_test.py -f conf/prince.ini -t GRID36

python nepa_test.py -f conf/prince.ini -t MESH9
python nepa_test.py -f conf/prince.ini -t MESH16
python nepa_test.py -f conf/prince.ini -t MESH25
python nepa_test.py -f conf/prince.ini -t MESH36

python nepa_test.py -f conf/prince.ini -t LINEAR9
python nepa_test.py -f conf/prince.ini -t LINEAR16
python nepa_test.py -f conf/prince.ini -t LINEAR25
python nepa_test.py -f conf/prince.ini -t LINEAR36
