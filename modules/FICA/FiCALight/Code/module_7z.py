#-*- coding: utf-8 -*-
#!/usr/bin/python3

#!/Author : Gibartes

from moduleInterface.defines   import *
from moduleInterface.interface import ModuleComponentInterface
from structureReader import structureReader as sr
from collections     import OrderedDict
import os,sys,platform
import zlib

class Structure7Z(object):
    SIGNATURE = b'\x37\x7A\xBC\xAF\x27\x1C'

    def __init__(self):
        self.property        = tuple(range(0,0x20))
        self.startheader     = sr.CStructure()

        self.startheader.build(['signature','major','minor','crc32','next_hdr_off','next_hdr_size','next_hdr_crc'],
                               [6,1,1,4,8,8,4])

class Module7Z(ModuleComponentInterface):

    def __init__(self):
        super().__init__()                  # Initialize Module Interface
        self.fileSize   = 0
        self.offset     = list()
        self.missing    = 0
        self.parser     = sr.StructureReader()
        self.structure  = Structure7Z()

        self.set_attrib(ModuleConstant.NAME,"7z")
        self.set_attrib(ModuleConstant.VERSION,"0.1")
        self.set_attrib(ModuleConstant.AUTHOR,"HK")
    
        self.off_t           = Offset_Info()
        self.off_t.name      = "7z"    # alias
        self.off_t.signature = "7z"    # signature in C_defy.SIGNATURE
    
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

    def carve(self):
        self.__reinit__()
        self.parser.get_file_handle(
            self.get_attrib(ModuleConstant.FILE_ATTRIBUTE),
            self.get_attrib(ModuleConstant.IMAGE_BASE),1
        )
        offset  = self.get_attrib(ModuleConstant.IMAGE_BASE)
        last    = self.get_attrib(ModuleConstant.IMAGE_LAST)
        if(last==0):
            last= self.parser.bgoto(0,os.SEEK_END)
        self.parser.bgoto(offset,os.SEEK_SET)

        self.parser.bexecute(self.structure.startheader.data,mode=os.SEEK_CUR)
        if(self.parser.get_value('signature')!=Structure7Z.SIGNATURE):
            self.parser.cleanup()
            return

        self.fileSize = 0
        next_hdr_off  = self.parser.byte2int(self.parser.get_value("next_hdr_off"))
        next_hdr_size = self.parser.byte2int(self.parser.get_value("next_hdr_size"))
        
        self.parser.bgoto(next_hdr_off)
        buffer = self.parser.bread_raw(0,next_hdr_size)
        if(zlib.crc32(buffer)==self.parser.byte2int(self.parser.get_value("next_hdr_crc"))):
            self.fileSize = next_hdr_off+next_hdr_size+0x20 # Header Size(0x20)
            self.off_t.append(self.get_attrib(ModuleConstant.IMAGE_BASE),self.fileSize+self.get_attrib(ModuleConstant.IMAGE_BASE),Offset_Info.VALID|Offset_Info.UNIT)
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
            return (False,ret,Offset_Info.NONE)
        self.carve()
        return self.off_t                  # return <= 0 means error while collecting information


if __name__ == '__main__':

    archive = Module7Z()
    try:
        archive.set_attrib(ModuleConstant.FILE_ATTRIBUTE,sys.argv[1])   # Insert MFT File
    except:
        print("This moudule needs exactly one parameter.")
        sys.exit(1)

    archive.set_attrib(ModuleConstant.IMAGE_BASE,0)  # Set offset of the file base
    cret = archive.execute()
    print(cret)
    print(len(cret))
    sys.exit(0)
