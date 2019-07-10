from defines         import *
from interface       import ModuleComponentInterface

import os,sys
import signal
import argparse

from module_sql import *
from module_reg import *
from module_pe  import *
from module_pf  import *
from module_mft import *
from module_lnk import *
from module_idx import *
from module_evt import *


class Actuator(object):
    def __init__(self):
        self.loadDefaultModule()

    def loadDefaultModule(self):
        self.evt = ModuleEvt()
        self.idx = ModuleIdx()
        self.lnk = ModuleLNK()
        self.mft = ModuleMFTEntry()
        self.pe  = ModulePEParser()
        self.pf  = ModulePrefetch()
        self.reg = ModuleRegEntry()
        self.sql = ModuleSql()

        self.dict = {
            "event":self.evt,
            "index":self.idx,
            "link":self.lnk,
            "mft":self.mft,
            "pe":self.pe,
            "prefetch":self.pf,
            "registry":self.reg,
            "sqlite":self.sql,
        }

    def unloadDefaultModule(self):
        del self.evt
        del self.idx
        del self.lnk
        del self.mft
        del self.pe
        del self.pf
        del self.reg
        del self.sql
        self.dict = {}

    def loadModule(self,name,module):
        self.dict.update({name:module})

    def unloadModule(self,name):
        return self.dict.pop(name,None)

    def set(self,key,attr,value):
        obj = self.dict.get(key)
        if(obj==None):
            return False
        obj.set_attrib(attr,value)
        return True

    def get(self,key,attr):
        obj = self.dict.get(key)
        if(obj==None):
            return False
        return obj.get_attrib(attr)

    def call(self,key,cmd,option):
        obj = self.dict.get(key)
        if(obj==None):
            return [(False,0,ModuleConstant.INVALID)]
        return obj.execute(cmd,option)


if __name__ == '__main__':

    def signal_handler(signal,frame):
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    mod    = Actuator()
    parser = argparse.ArgumentParser(description="select run mode")
    parser.add_argument("-t",action="store",dest="target",type=str,default='n',     required=True)
    parser.add_argument("-f",action="store",dest="file",type=str,default='n',       required=True)
    parser.add_argument("-e",action="store",dest="encode",type=str,default='euc-kr',required=False)
    parser.add_argument("-b",action="store",dest="block",type=int,default=1024,     required=False)
    parser.add_argument("-from",action="store",dest="start",type=int,default=0,     required=False)
    parser.add_argument("-to",action="store",dest="end",type=int,default=0,         required=False)

    args = parser.parse_args()

    _requeset = args.target
    _file     = args.file
    _encode   = args.encode
    _base     = args.start
    _last     = args.end
    _block    = args.block

    if(_block<=0):
        print("Error")
        sys.exit(0)

    mod.set(_requeset,ModuleConstant.FILE_ATTRIBUTE,_file)          # File to carve
    mod.set(_requeset,ModuleConstant.IMAGE_BASE,_base)              # Set start offset of the file base
    mod.set(_requeset,ModuleConstant.IMAGE_LAST,_last)              # Set last offset of the file base
    mod.set(_requeset,ModuleConstant.ENCODE,_encode)                # Set encode type
    mod.set(_requeset,ModuleConstant.CLUSTER_SIZE,_block)           # Set cluster size

    cret = mod.call(_requeset,None,None)
    print(cret)

    sys.exit(0)
