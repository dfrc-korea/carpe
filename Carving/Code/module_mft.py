#-*- coding: utf-8 -*-

#!/usr/bin/python3

#!/Author : Gibartes

from defines         import *
from interface       import ModuleComponentInterface
from structureReader import structureReader as sr

#from structureReader import StructureReader    as parser
#from structureReader import _MFTEntryHeader as structure

import os,sys,platform

# Desgin  
# "전체" 파일을 탐독해서 MFT 엔트리만 획득
# 리턴 값 : MFT 엔트리 오프셋/크기 튜플 리스트 (offset,size=1024)

class ModuleMFTEntry(ModuleComponentInterface):
    MFT_ENTRY_PAGE_SIZE = 512
    MFT_ENTRY_SIZE      = MFT_ENTRY_PAGE_SIZE * 2
    MFT_SIGNATURE_BE    = 0x46494c45
    MFT_SIGNATURE_LE    = 0x454c4946

    def __init__(self):
        super().__init__()                  # Initialize Module Interface
        self.fileSize   = 0
        self.offset     = list()
        self.missing    = 0
        self.parser     = sr.StructureReader()

        self.set_attrib(ModuleConstant.NAME,"mft")
        self.set_attrib(ModuleConstant.VERSION,"0.1")
        self.set_attrib(ModuleConstant.AUTHOR,"HK")
    
    def __reinit__(self):
        self.fileSize   = 0
        self.offset     = list()
        self.missing    = 0

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
        header = sr._MFTEntryHeader()
        result = self.parser.bexecute(header.MFTEntryHeader,'int',offset,os.SEEK_SET,'little')
        if(result==False):
            return (False,0,-1,ModuleConstant.INVALID)
        
        if(self.parser.get_value("signature")!=ModuleMFTEntry.MFT_SIGNATURE_LE):
            return (False,0,-1,ModuleConstant.INVALID)

        fixup    = self.parser.bread_raw(offset+int(self.parser.get_value("off_fixup")), \
                                        int(self.parser.get_value("num_fixup"))*2,      \
                                        os.SEEK_SET)
        
        fixup_val  = fixup[0:2]
        fixup_pg   = self.parser.bread_raw(offset+ModuleMFTEntry.MFT_ENTRY_PAGE_SIZE-2,2,os.SEEK_SET)
        if(fixup_val!=fixup_pg):     # This is not MFT entry
            return (False,0,-1,ModuleConstant.INVALID)

        fixup_pg = self.parser.bread_raw(offset+ModuleMFTEntry.MFT_ENTRY_SIZE-2,2,os.SEEK_SET)

        if(fixup_val!=fixup_pg):
            return (True,offset,ModuleMFTEntry.MFT_ENTRY_PAGE_SIZE,ModuleConstant.FILE_RECORD) 

        return (True,offset,ModuleMFTEntry.MFT_ENTRY_SIZE,ModuleConstant.FILE_RECORD)

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
            else:self.missing+=1
            offset+=ModuleMFTEntry.MFT_ENTRY_SIZE
        
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
            return [(False,ret,ModuleConstant.INVALID)]
        self.carve()
        if(self.offset==[]):
            return [(False,0,ModuleConstant.INVALID)]
        return self.offset                  # return <= 0 means error while collecting information


if __name__ == '__main__':

    mft = ModuleMFTEntry()
    try:
        mft.set_attrib(ModuleConstant.FILE_ATTRIBUTE,sys.argv[1])   # Insert MFT File
    except:
        print("This moudule needs exactly one parameter.")
        sys.exit(1)

    mft.set_attrib(ModuleConstant.IMAGE_BASE,0)  # Set offset of the file base
    cret = mft.execute()
    print(cret)
    print(len(cret))
    sys.exit(0)
