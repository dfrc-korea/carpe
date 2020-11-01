#-*- coding: utf-8 -*-

#!/usr/bin/python3

#!/Author : Gibartes

from moduleInterface.defines   import *
from moduleInterface.interface import ModuleComponentInterface
from structureReader import structureReader as sr

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
        self.flag       = None

        self.set_attrib(ModuleConstant.NAME,"mft")
        self.set_attrib(ModuleConstant.VERSION,"0.2")
        self.set_attrib(ModuleConstant.AUTHOR,"HK")
        self.set_attrib(ModuleConstant.RETURN_SET,False)
        
        self.off_t           = Offset_Info()
        self.off_t.name      = "mft"    # alias
        self.off_t.signature = "MFT"    # signature in C_defy.SIGNATURE
    
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
        header  = sr._MFTEntryHeader()
        result  = self.parser.bexecute(header.MFTEntryHeader,'int',offset,os.SEEK_SET,'little')
        if(result==False):
            return False
        
        if(self.parser.get_value("signature")!=ModuleMFTEntry.MFT_SIGNATURE_LE):
            return False
        size     = self.parser.get_value("used_size")
        fixup    = self.parser.bread_raw(offset+int(self.parser.get_value("off_fixup")), \
                                        int(self.parser.get_value("num_fixup"))*2,      \
                                        os.SEEK_SET)
        
        fixup_val  = fixup[0:2]
        fixup_pg   = self.parser.bread_raw(offset+ModuleMFTEntry.MFT_ENTRY_PAGE_SIZE-2,2,os.SEEK_SET)

        if(fixup_val!=fixup_pg):     # This is not MFT entry
            return False

        if(self.parser.byte2int(fixup_pg)==0):
            return False

        fixup_pg = self.parser.bread_raw(offset+ModuleMFTEntry.MFT_ENTRY_SIZE-2,2,os.SEEK_SET)

        if(fixup_val!=fixup_pg):
            self.off_t.append(offset,offset+ModuleMFTEntry.MFT_ENTRY_PAGE_SIZE,Offset_Info.NONE)
            return True

        lastSig    = self.parser.bread_raw(offset+size-8,8,os.SEEK_SET)
        
        if(b'\xFF\xFF' not in lastSig):
            return False
        
        self.off_t.append(offset,offset+ModuleMFTEntry.MFT_ENTRY_PAGE_SIZE,Offset_Info.VALID|Offset_Info.MERGEABLE|Offset_Info.GROUPABLE)
        return True

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
            self.__read(offset)
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
            return None
        self.carve()
        return self.off_t

if __name__ == '__main__':

    mft = ModuleMFTEntry()
    try:
        mft.set_attrib(ModuleConstant.FILE_ATTRIBUTE,sys.argv[1])   # Insert MFT File
    except:
        print("This moudule needs exactly one parameter.")
        sys.exit(1)

    mft.set_attrib(ModuleConstant.IMAGE_BASE,0)  # Set offset of the file base
    cret = mft.execute()
    print(cret.contents)
    sys.exit(0)
