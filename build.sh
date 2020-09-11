#!/bin/sh
# CARPE Forensics
# version 200909

python -m venv ./venv
source ./venv/bin/activate

./venv/bin/pip install -r requirements.txt
./venv/bin/pip install https://github.com/msuhanov/yarp/archive/1.0.30.tar.gz


git clone https://github.com/dfrc-korea/carpe-pytsk.git
cd carpe-pytsk
git clone https://github.com/sleuthkit/sleuthkit.git --branch sleuthkit-4.6.7
cd sleuthkit
./bootstrap
cd ..
../venv/bin/python setup.py build
../venv/bin/python setup.py install
cd ..