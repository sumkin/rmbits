#!/bin/bash

shopt -s expand_aliases
alias python=python3

export PYTHONPATH="/home/ay49514/rmbits/src:$PYTHONPATH"
export PYTHONPATH="/home/ay49514/rmbits/src/datamanager:$PYTHONPATH"
export PYTHONPATH="/home/ay49514/rmbits/src/utils:$PYTHONPATH"
export PYTHONPATH="/home/ay49514/pyairport/pyairport:$PYTHONPATH"

python /home/ay49514/rmbits/src/tasks/daily/s3baf2odcsv.py 
python /home/ay49514/rmbits/src/tasks/daily/s3bif2csv.py 
python /home/ay49514/rmbits/src/tasks/daily/s3yield2csv.py 
python /home/ay49514/rmbits/src/tasks/daily/s3yldlkppkl.py

