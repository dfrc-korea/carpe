#-*- coding: utf-8 -*-
import os, sys, struct

from moduleInterface.defines   import *
from moduleInterface.interface import ModuleComponentInterface


class ModuleBMP(ModuleComponentInterface):
    CONST_KILOBYTE = 1024
    CONST_MEGABYTE = 1048576
    CONST_GIGABYTE = 1073741824

    CONST_RAMSLACK_COMP_UNIT = 2
    CONST_COMPOUND_MAX = 50*CONST_MEGABYTE
    CONST_SEARCH_SIZE = 200*CONST_MEGABYTE
    CONST_BIG_SEARCH_SIZE = 200*CONST_MEGABYTE

    uClusterSize = 0x1000

    def __init__(self):
        super().__init__()                  # Initialize Module Interface
        self.fileSize   = 0
        self.offset     = list()

        self.set_attrib(ModuleConstant.NAME,"BMP")
        self.set_attrib(ModuleConstant.VERSION,"0.2")
        self.set_attrib(ModuleConstant.AUTHOR,"JH,GM")

        self.fp = None

        self.off_t           = Offset_Info()
        self.off_t.name      = "bmp"    # alias
        self.off_t.signature = "bmp"    # signature in C_defy.SIGNATURE

    def __reinit__(self):
        self.fileSize   = 0
        self.offset     = list()
        self.missing    = 0
        self.off_t.clear() 

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
        self.fp = open(self.get_attrib(ModuleConstant.FILE_ATTRIBUTE), 'rb')
        self.fp.seek(self.get_attrib(ModuleConstant.IMAGE_BASE),os.SEEK_SET)

        # Get BITMAP Header
        temp = self.fp.read(512)
        bfSize = struct.unpack('<I', temp[0x02:0x06])[0]
        # bfReserved1, bfReserved1 value is \x00\x00
        bfReserved1 = temp[0x06:0x08]
        bfReserved2 = temp[0x08:0x0A]

        if bfReserved1 != b'\x00\x00' or bfReserved2 != b'\x00\x00':
            self.offset = (False, 0, -1, Offset_Info.NONE)  # Fail
            return False

        biSize = temp[0x0E:0x12]
        biPlanes = temp[0x1A:0x1C]
        biCompression = struct.unpack('<I', temp[0x1E:0x22])[0]

        if biSize != b'\x28\x00\x00\x00' or biSize != b'\x38\x00\x00\x00':
            if biPlanes != b'\x01\x00' or biCompression > 0x05:
                self.offset = (False, 0, -1, Offset_Info.NONE)  # Fail
                return False
        self.offset = (True, self.attrib.get(ModuleConstant.IMAGE_BASE), bfSize, Offset_Info.VALID|Offset_Info.UNIT)
        self.off_t.append(self.offset[1],self.offset[1]+self.offset[2],self.offset[3])
        
        self.fp.close()
        return True

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
        self.__reinit__()
        ret = self.__evaluate()
        if(ret!=ModuleConstant.Return.SUCCESS):
            return None
        self.carve()
        return self.off_t                  # return <= 0 means error while collecting information


if __name__ == '__main__':

    file = ModuleBMP()
    try:
        file.set_attrib(ModuleConstant.FILE_ATTRIBUTE,sys.argv[1])   # Insert File
    except:
        print("This moudule needs exactly one parameter.")
        sys.exit(1)

    file.set_attrib(ModuleConstant.IMAGE_BASE,0)  # Set offset of the file base
    file.set_attrib(ModuleConstant.IMAGE_LAST, ModuleBMP.CONST_SEARCH_SIZE)  # Set offset of the file last
    cret = file.execute()
    print(cret)

    sys.exit(0)