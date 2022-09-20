#!/bin/bash

cd /root/ft-to-gsheets || exit
PATH=/usr/local/bin:$
pipenv run python transfer.py

exit 0
