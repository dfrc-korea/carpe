#-*- coding: utf-8 -*-
import os, sys, struct

from defines import ModuleConstant
from interface       import ModuleComponentInterface


class ModulePST(ModuleComponentInterface):
    CONST_KILOBYTE = 1024
    CONST_MEGABYTE = 1048576
    CONST_GIGABYTE = 1073741824

    CONST_RAMSLACK_COMP_UNIT = 2
    CONST_COMPOUND_MAX = 50*CONST_MEGABYTE
    CONST_SEARCH_SIZE = 20*CONST_MEGABYTE
    CONST_BIG_SEARCH_SIZE = 200*CONST_MEGABYTE

    uClusterSize = 0x1000

    def __init__(self):
        super().__init__()                  # Initialize Module Interface
        self.fileSize   = 0
        self.offset     = list()

        self.set_attrib(ModuleConstant.NAME,"DBX")
        self.set_attrib(ModuleConstant.VERSION,"0.1")
        self.set_attrib(ModuleConstant.AUTHOR,"JH")

        self.fp = None


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

        self.fp.seek(0)
        temp = self.fp.read(512)
        fileSize = struct.unpack('<Q', temp[0xB8:0xB8 + 8])[0]

        if fileSize < self.attrib.get(ModuleConstant.IMAGE_LAST) - self.attrib.get(ModuleConstant.IMAGE_BASE):
            self.offset = (True, self.attrib.get(ModuleConstant.IMAGE_BASE), fileSize, ModuleConstant.FILE_ONESHOT)
        else:
            self.offset = (False, 0, -1, ModuleConstant.INVALID)

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
            return [(False,ret)]
        self.carve()
        if(self.offset==[]):
            return [(False,0,ModuleConstant.INVALID)]
        return self.offset                  # return <= 0 means error while collecting information


if __name__ == '__main__':

    file = ModulePST()
    try:
        file.set_attrib(ModuleConstant.FILE_ATTRIBUTE,sys.argv[1])   # Insert File
    except:
        print("This moudule needs exactly one parameter.")
        sys.exit(1)

    file.set_attrib(ModuleConstant.IMAGE_BASE,0)  # Set offset of the file base
    file.set_attrib(ModuleConstant.IMAGE_LAST, ModulePST.CONST_SEARCH_SIZE)  # Set offset of the file Last
    cret = file.execute()
    print(cret)

    sys.exit(0)