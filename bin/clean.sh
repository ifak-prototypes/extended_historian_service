#!/usr/bin/env bash

SCRIPTPATH="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"
cd $SCRIPTPATH

# remove test data and log files
find ../demo -name 'data' -exec rm -r {} \;
find ../demo -name 'logfile.txt' -exec rm {} \;

# remove python cache files and egg-infos
find ../src -name '__pycache__' -exec rm -r {} \;
find ../src -name '*\.egg-info' -exec rm -r {} \;
find ../demo -name '__pycache__' -exec rm -r {} \;
find ../demo -name '*\.egg-info' -exec rm -r {} \;
