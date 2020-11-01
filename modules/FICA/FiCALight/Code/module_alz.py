#-*- coding: utf-8 -*-
import os, sys

from moduleInterface.defines   import *
from moduleInterface.interface import ModuleComponentInterface


class ModuleALZ(ModuleComponentInterface):
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

        self.set_attrib(ModuleConstant.NAME,"ALZ")
        self.set_attrib(ModuleConstant.VERSION,"0.2")
        self.set_attrib(ModuleConstant.AUTHOR,"JH,GM")

        self.fp = None
        self.off_t           = Offset_Info()
        self.off_t.name      = "alz"    # alias
        self.off_t.signature = "alz"    # signature in C_defy.SIGNATURE

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

    def signature(self, current_offset, sig_FOOTER):
        search_range = int((self.get_attrib(ModuleConstant.IMAGE_LAST) - self.get_attrib(ModuleConstant.IMAGE_BASE)) / (self.uClusterSize * 1))  # 1 => sizeof(UCHAR)

        for i in range(0, search_range+1):
            self.fp.seek(current_offset + i * self.uClusterSize)
            temp = self.fp.read(self.uClusterSize)

            sOffset = temp.find(sig_FOOTER)

            if sOffset > 0:
                # Ramslack Check Routine
                ramslack = 0x200 - (sOffset % 0x200) - len(sig_FOOTER) -1
                if ramslack == 0:
                    qwDataSize = i * self.uClusterSize + sOffset + len(sig_FOOTER)
                    return (True, current_offset, qwDataSize, Offset_Info.VALID|Offset_Info.UNIT)
                else :
                    # 1 byte of Next to the Footer Signature is Felexible byte
                    while ramslack > 0:
                        if temp[sOffset+ramslack+len(sig_FOOTER)] != 0 :
                            break
                        ramslack -= 1
                    if ramslack == 0 :
                        qwDataSize = i * self.uClusterSize + sOffset + len(sig_FOOTER)
                        return (True, current_offset, qwDataSize,Offset_Info.VALID|Offset_Info.UNIT)
        #if sOffset == -1 :
        return (False, 0, -1, Offset_Info.NONE)


    def carve(self):
        sigALZ_FOOTER = b'\x43\x4C\x5A\x02'

        self.fp = open(self.get_attrib(ModuleConstant.FILE_ATTRIBUTE), 'rb')

        self.offset = self.signature(self.get_attrib(ModuleConstant.IMAGE_BASE), sigALZ_FOOTER)
        self.off_t.append(self.offset[1],self.offset[1]+self.offset[2],self.offset[3])
        self.fp.close()


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

    file = ModuleALZ()
    try:
        file.set_attrib(ModuleConstant.FILE_ATTRIBUTE,sys.argv[1])   # Insert File
    except:
        print("This moudule needs exactly one parameter.")
        sys.exit(1)

    file.set_attrib(ModuleConstant.IMAGE_BASE,0)  # Set offset of the file base
    file.set_attrib(ModuleConstant.IMAGE_LAST, ModuleALZ.CONST_SEARCH_SIZE)  # Set offset of the file Last
    cret = file.execute()
    print(cret)

    sys.exit(0)