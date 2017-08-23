#!/bin/sh

python nepa_test.py -f conf/prince.ini -t RING9
python nepa_test.py -f conf/prince.ini -t RING16
python nepa_test.py -f conf/prince.ini -t RING25
python nepa_test.py -f conf/prince.ini -t RING36

python nepa_test.py -f conf/prince.ini -t GRID9
python nepa_test.py -f conf/prince.ini -t GRID16
python nepa_test.py -f conf/prince.ini -t GRID25
python nepa_test.py -f conf/prince.ini -t GRID36

