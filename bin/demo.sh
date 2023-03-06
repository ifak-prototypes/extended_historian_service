#!/usr/bin/env bash

SCRIPTPATH="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"
cd $SCRIPTPATH/..
source ./venv/bin/activate

# start the ./tests/integration/test.py file
python ./test/integration_test.py
