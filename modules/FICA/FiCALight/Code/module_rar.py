#-*- coding: utf-8 -*-
#!/usr/bin/python3

#!/Author : Gibartes

from moduleInterface.defines   import *
from moduleInterface.interface import ModuleComponentInterface
from structureReader import structureReader as sr
import sys
import os
import struct

from rar_define import *

## rar constants ##
# block types
class RAR_CONSTANT:
    # Method Const
    RAR     = b"Rar"
    RAR_ID  = b"Rar!\x1a\x07\x00"
    RAR5_ID = b"Rar!\x1a\x07\x01\x00"
    ZERO    = b"\0"
    EMPTY   = b""
    
    NONE   = -1
    RAR_V3 = 3
    RAR_V5 = 5
    BSIZE  = 32 * 1024
    SFX_MAX_SIZE = 2 * 1024 * 1024


class ModuleRAR(ModuleComponentInterface):
    SECTOR = 512

    def __init__(self):
        super().__init__()                  # Initialize Module Interface
        self.fileSize   = 0
        self.offset     = list()
        self.parser     = sr.StructureReader()

        self.set_attrib(ModuleConstant.NAME,"RAR")
        self.set_attrib(ModuleConstant.VERSION,"0.2")
        self.set_attrib(ModuleConstant.AUTHOR,"HK,GM")

        self.off_t           = Offset_Info()
        self.off_t.name      = "rar"    # alias
        self.off_t.signature = "rar"    # signature in C_defy.SIGNATURE
    
    def __reinit__(self):
        self.fileSize   = 0
        self.offset     = list()
        self.missing    = 0
        self.off_t.clear() 

    def __del__(self):
        self.parser.cleanup()

    """ Module Methods """

    def __get_rar_version(self,offset=0):
        """Check quickly whether file is rar archive."""
        buf = self.parser.bread_raw(offset,len(RAR_CONSTANT.RAR5_ID))
        if(buf.startswith(RAR_CONSTANT.RAR_ID)):
            return RAR_CONSTANT.RAR_V3
        if(buf.startswith(RAR_CONSTANT.RAR5_ID)):
            return RAR_CONSTANT.RAR_V5
        return RAR_CONSTANT.NONE
  
    def __evaluate(self):
        fn = self.attrib.get(ModuleConstant.FILE_ATTRIBUTE)
        if(fn==None):
            return ModuleConstant.Return.EINVAL_ATTRIBUTE
        try:
            fd = os.open(fn,os.O_RDONLY)
            os.close(fd)
        except:return ModuleConstant.Return.EINVAL_FILE
        return ModuleConstant.Return.SUCCESS

    def __read(self,offset,version):
        rfiles = RarFileParser()
        length = rfiles.parse(self.attrib.get(ModuleConstant.FILE_ATTRIBUTE),
                     version,
                     self.get_attrib(ModuleConstant.IMAGE_BASE),
                     self.get_attrib(ModuleConstant.IMAGE_LAST))
        if(length<=0):
            return [(False,0,-1,Offset_Info.NONE)]
        return (True,offset,length,Offset_Info.VALID|Offset_Info.UNIT)

    def carve(self):
        self.__reinit__()
        self.parser.get_file_handle(
            self.get_attrib(ModuleConstant.FILE_ATTRIBUTE),
            self.get_attrib(ModuleConstant.IMAGE_BASE),1
        )

        start   = self.get_attrib(ModuleConstant.IMAGE_BASE)
        last    = self.get_attrib(ModuleConstant.IMAGE_LAST)
        if(last==0):
            last    = self.parser.bgoto(0,os.SEEK_END)   
        self.parser.bgoto(start,os.SEEK_SET)

        version = self.__get_rar_version()
        if(version<0):
            return (False,0,-1,Offset_Info.NONE)

        self.fileSize = 0
        self.offset = self.__read(start,version)
        self.off_t.append(self.offset[1],self.offset[1]+self.offset[2],self.offset[3])
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
        ret = self.__evaluate()
        if(ret!=ModuleConstant.Return.SUCCESS):
            return None
        self.carve()
        return self.off_t                  # return <= 0 means error while collecting information


if __name__ == '__main__':

    rar = ModuleRAR()
    try:
        rar.set_attrib(ModuleConstant.FILE_ATTRIBUTE,sys.argv[1])   # Insert MFT File
    except:
        print("This moudule needs exactly one parameter.")
        sys.exit(1)

    rar.set_attrib(ModuleConstant.IMAGE_BASE,0)  # Set offset of the file base
    cret = rar.execute()
    print(cret)
    sys.exit(0)
