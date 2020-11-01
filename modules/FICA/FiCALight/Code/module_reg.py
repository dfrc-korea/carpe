#-*- coding: utf-8 -*-

#!/usr/bin/python3

#!/Author : Gibartes

from moduleInterface.defines   import *
from moduleInterface.interface import ModuleComponentInterface
#from defines         import *
#from interface       import ModuleComponentInterface
from structureReader import structureReader as sr
#from structureReader import StructureReader    as parser
#from structureReader import _RegistryStructure as structure

import os,sys,platform

class ModuleRegEntry(ModuleComponentInterface):
    BASE_SIGNATURE_BE = 0x72656766
    BASE_SIGNATURE_LE = 0x66676572
    HBIN_SIGNATURE_BE = 0x6862696E
    HBIN_SIGNATURE_LE = 0x6E696268

    def __init__(self):
        super().__init__()                  # Initialize Module Interface
        self.fileSize   = 0
        self.offset     = list()
        self.missing    = 0
        self.parser     = sr.StructureReader()
        self.flag       = None

        self.set_attrib(ModuleConstant.NAME,"reg")
        self.set_attrib(ModuleConstant.VERSION,"0.1")
        self.set_attrib(ModuleConstant.AUTHOR,"HK")
        self.set_attrib("detailed_type",True)

        self.off_t           = Offset_Info()
        self.off_t.name      = "reg"    # alias
        self.off_t.signature = "reg"    # signature in C_defy.SIGNATURE

    def __reinit__(self):
        self.fileSize   = 0
        self.offset     = list()
        self.missing    = 0
        self.off_t.clear() 

    def __del__(self):
        self.parser.cleanup()

    """ Module Methods """

    def __evaluate(self):
        fn = self.attrib.get(ModuleConstant.FILE_ATTRIBUTE)
        if(fn==None):
            return ModuleConstant.Return.EINVAL_ATTRIBUTE
        try:
            fd = os.open(fn,os.O_RDONLY)
            os.close(fd)
        except:return ModuleConstant.Return.EINVAL_FILE
        return ModuleConstant.Return.SUCCESS

    def __read(self,offset):
        header = sr._RegistryStructure()
        result = self.parser.bexecute(header.BaseBlock,'int',offset,os.SEEK_SET,'little')
        if(result==False):
            return (False,0,-1,ModuleConstant.INVALID)

        if(self.parser.get_value("signature")==ModuleRegEntry.BASE_SIGNATURE_LE):
            return (True,offset,header.BASEBLOCK_SIZE,ModuleConstant.FILE_HEADER)

        result = self.parser.bexecute(header.HiveBin,'int',offset,os.SEEK_SET,'little')
        if(result==False):
            return (False,0,-1,ModuleConstant.INVALID)

        if(self.parser.get_value("signature")==ModuleRegEntry.HBIN_SIGNATURE_LE):
            r = self.parser.get_value("size")
            if(r==0):
            #    # ---> If not binary mode
            #    self.parser.bgoto(-self.parser.get_size()+8)
            #    try:
            #        s = self.parser.byte2int(self.parser.read_raw(0,4,'little'))
            #        if(s!=0):
            #            return (True,offset,s,ModuleConstant.FILE_RECORD)
            #        return (False,0,-1,ModuleConstant.INVALID)
            #    except:return (False,0,-1,ModuleConstant.INVALID)
            #    # <---
                 return (False,0,-1,ModuleConstant.INVALID)
            elif(r==None):
                return (False,0,-1,ModuleConstant.INVALID)
            return (True,offset,r,ModuleConstant.FILE_RECORD)
        return (False,0,-1,ModuleConstant.INVALID)

    def carve(self):
        self.__reinit__()
        self.parser.get_file_handle(
            self.get_attrib(ModuleConstant.FILE_ATTRIBUTE),
            self.get_attrib(ModuleConstant.IMAGE_BASE),1
        )

        offset  = self.get_attrib(ModuleConstant.IMAGE_BASE)
        last    = self.get_attrib(ModuleConstant.IMAGE_LAST)
        if(last==0):
            last    = self.parser.bgoto(0,os.SEEK_END)       
        self.parser.bgoto(offset,os.SEEK_SET)

        while(offset<last):
            res = self.__read(offset)
            
            if(res[0]==True):
                self.offset.append((res[1],res[2],res[3]))
                self.fileSize += res[2]
                offset+=res[2]

            else:
                self.missing+=1
                offset+= sr._RegistryStructure.BASEBLOCK_SIZE
        self.parser.cleanup()

    """ Interfaces """

    def module_open(self,id):               # Reserved method for multiprocessing
        super().module_open()

    def module_close(self):                 # Reserved method for multiprocessing
        pass

    def set_attrib(self,key,value):         # 모듈 호출자가 모듈 속성 변경/추가하는 method interface
        self.update_attrib(key,value)

    def get_attrib(self,key,value=None):    # 모듈 호출자가 모듈 속성 획득하는 method interface
        return self.attrib.get(key)

    def execute(self,cmd=None,option=None): # 모듈 호출자가 모듈을 실행하는 method
        if(cmd=='inspect'):
            return self.flag
        else:
            self.flag = None
            ret = self.__evaluate()
            if(ret!=ModuleConstant.Return.SUCCESS):
                return [(False,ret,ModuleConstant.INVALID)]
            self.carve()
            if(self.offset==[]):
                return [(False,0,ModuleConstant.INVALID)]
            self.flag = "reg"
            return self.offset


if __name__ == '__main__':

    reg = ModuleRegEntry()
    try:
        reg.set_attrib(ModuleConstant.FILE_ATTRIBUTE,sys.argv[1])   # Insert Reg File Or Images
    except:
        print("This moudule needs exactly one parameter.")
        sys.exit(1)

    reg.set_attrib(ModuleConstant.IMAGE_BASE,0)  # Set offset of the file base
    cret = reg.execute()
    print(cret)
    print(len(cret))
    sys.exit(0)
