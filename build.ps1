# CARPE Forensics
# version 200909

python -m venv ./venv
.\venv\Scripts\activate

.\venv\Scripts\pip install -r requirements.txt
.\venv\Scripts\pip install https://github.com/msuhanov/yarp/archive/1.0.30.tar.gz

git clone https://github.com/dfrc-korea/carpe-pytsk.git
cd carpe-pytsk
git clone https://github.com/sleuthkit/sleuthkit.git --branch sleuthkit-4.6.7
..\venv\Scripts\python.exe setup.py build
..\venv\Scripts\python.exe setup.py install
cd ..