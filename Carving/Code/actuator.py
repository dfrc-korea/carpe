from defines         import *
from interface       import ModuleComponentInterface

import os,sys

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

    mod = Actuator()
    _requeset = sys.argv[1]
    try:
        mod.set(_requeset,ModuleConstant.FILE_ATTRIBUTE,sys.argv[2])   # Insert File
    except:
        print("This moudule needs exactly one parameter.")
        sys.exit(1)

    mod.set(_requeset,ModuleConstant.IMAGE_BASE,0)                     # Set offset of the file base
    mod.set(_requeset,ModuleConstant.CLUSTER_SIZE,1024)
    cret = mod.call(_requeset,None,None)

    print(cret)
