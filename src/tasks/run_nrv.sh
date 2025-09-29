#!/bin/bash

shopt -s expand_aliases
alias python=python3

export PYTHONPATH="/home/ay49514/rmbits/src:$PYTHONPATH"
export PYTHONPATH="/home/ay49514/rmbits/src/datamanager:$PYTHONPATH"
export PYTHONPATH="/home/ay49514/rmbits/src/utils:$PYTHONPATH"

python /home/ay49514/rmbits/src/tasks/weekly/s3nrv.py



