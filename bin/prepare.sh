#!/usr/bin/env bash

if [ ! -d "./venv" ]; then
    python -m venv ./venv
fi

source ./venv/bin/activate

python -m pip install --upgrade pip
python -m pip install -e .[server,configurator,arrowhead,application]
