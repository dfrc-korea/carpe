#!/bin/sh
# CARPE Forensics
# version 201118

python -m venv ./venv
source ./venv/bin/activate

./venv/bin/pip install -r requirements.txt
./venv/bin/pip install https://github.com/msuhanov/yarp/archive/1.0.30.tar.gz