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
        self.init()

    def init(self):
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

        self.importList = {}

    def clear(self):
        del self.evt
        del self.idx
        del self.lnk
        del self.mft
        del self.pe
        del self.pf
        del self.reg
        del self.sql
        self.dict = {}

        for k,v in self.importList.items():
            self.unloadPlugin(k)

    def loadPlugin(self,module):
        tmp = __import__(module,fromlist=[module])
        self.importList.update({module:tmp})
        return tmp

    def unloadPlugin(self,module):
        tmp = self.importList.pop(module,None)
        if(tmp!=None):
            try:del tmp
            except:pass
        return tmp

    def checkImportedPlugin(self,module):
        return (True if module in self.importList.keys() else False)[0]

    def loadModule(self,name,module):
        self.dict.update({name:module})

    def unloadModule(self,name):
        return self.dict.pop(name,None)

    def call(self,key,cmd,option):
        obj = self.dict.get(key)
        if(obj==None):
            return [(False,0,ModuleConstant.INVALID)]
        return obj.execute(cmd,option)

    def get(self,key,attr):
        obj = self.dict.get(key)
        if(obj==None):
            return False
        return obj.get_attrib(attr)

    def set(self,key,attr,value):
        obj = self.dict.get(key)
        if(obj==None):
            return False
        obj.set_attrib(attr,value)
        return True


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
    parser.add_argument("-cmd",action="store",dest="cmd",type=str,default=None,     required=False)
    parser.add_argument("-opt",action="store",dest="option",type=bool,default=True, required=False)

    args = parser.parse_args()

    _request  = args.target
    _file     = args.file
    _encode   = args.encode
    _base     = args.start
    _last     = args.end
    _block    = args.block
    _cmd      = args.cmd
    _opt      = args.option

    if(_block<=0):
        print("[!] Error")
        sys.exit(0)

    if(_request not in mod.dict.keys()):
        print("[!] Unsupport type")
        sys.exit(0)

    print("[*] Start to verify type of the file.")

    mod.set(_request,ModuleConstant.FILE_ATTRIBUTE,_file)          # File to carve
    mod.set(_request,ModuleConstant.IMAGE_BASE,_base)              # Set start offset of the file base
    mod.set(_request,ModuleConstant.IMAGE_LAST,_last)              # Set last offset of the file base
    mod.set(_request,ModuleConstant.ENCODE,_encode)                # Set encode type
    mod.set(_request,ModuleConstant.CLUSTER_SIZE,_block)           # Set cluster size

    cret = mod.call(_request,_cmd,_opt)

    print("[*] Result :\n(Start offset, Valid size, Record Type)")
    print(cret)

    sys.exit(0)
