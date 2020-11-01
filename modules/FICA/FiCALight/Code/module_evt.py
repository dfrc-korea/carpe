#-*- coding: utf-8 -*-

#!/usr/bin/python3

#!/Author : Gibartes

from moduleInterface.defines   import *
from moduleInterface.interface import ModuleComponentInterface
from structureReader import structureReader as sr

import binascii
import os,sys,platform

# carving module for evt/evtx
class ModuleEVT(ModuleComponentInterface):
    EVT_SIG     = b"LfLe"
    EVTX_HEADER = b"ElfFile\00"
    EVTX_CHUNK  = b"ElfChnk\00"
    EVTX_RECORD = 0x2a2a
    CHNK_SIZE   = 512
    CHNK_SIZE_X = 0x10000
    def __init__(self):
        super().__init__()                  # Initialize Module Interface
        self.fileSize   = 0
        self.missing    = 0
        self.parser     = sr.StructureReader()
        self.flag       = None

        self.set_attrib(ModuleConstant.NAME,"evt")
        self.set_attrib(ModuleConstant.VERSION,"0.1")
        self.set_attrib(ModuleConstant.AUTHOR,"HK")
        self.set_attrib("detailed_type",True)

        self.off_t           = Offset_Info()
        self.off_t.name      = "evt"    # alias
        self.off_t.signature = "evt"    # signature in C_defy.SIGNATURE

    def __reinit__(self):
        self.fileSize   = 0
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
        header = sr._WindowsEventLogStructure()
        result = self.parser.bexecute(header.evtFileHeader,'byte',offset,os.SEEK_SET,'little')
        if(result==False):
            return (False,0,-1)
        
        # For evt
        if(self.parser.get_value("signature")==ModuleEVT.EVT_SIG):
            self.off_t.name = "evt"
            size = 0
            while(self.parser.get_value("signature")==ModuleEVT.EVT_SIG):
                _tmp = int.from_bytes(self.parser.get_value('size'),'little')
                size+=_tmp
                if(_tmp==0):
                    break
                self.parser.bgoto(-self.parser.get_size()+_tmp)
                self.parser.bexecute(header.evtRecord,'byte',0,os.SEEK_CUR,'little')
            return (True,offset,offset+size)
        
        result = self.parser.bexecute(header.evtxFileChunkHeader,'byte',offset,os.SEEK_SET,'little')
        if(result==False):
            return (False,0,-1)
        _type  = self.parser.get_value("signature")
        if(_type==ModuleEVT.EVTX_HEADER):
            self.off_t.name = "evtx"
            self.parser.bgoto(-self.parser.get_size())
            self.parser.bexecute(header.evtxFileHeader,'byte',0,os.SEEK_CUR,'little')
            _crc = binascii.crc32(self.parser.stream[0:self.parser.get_field_offset("flags")])
            if(_crc == self.parser.byte2int(self.parser.get_value("checksum"))):
                return (True,offset,offset+self.parser.byte2int(self.parser.get_value("hbsize")))
            return (False,0,-1)

        elif(_type==ModuleEVT.EVTX_CHUNK):
            self.off_t.name = "evtx"
            self.parser.bgoto(-self.parser.get_size())
            crc32 = self.parser.byte2int(self.parser.get_value("checksum"))
            __buffer1 = self.parser.stream[0:self.parser.get_field_offset("flags")]
            __buffer2 = self.parser.bread_raw(offset+128,512-128,os.SEEK_SET)
            buffer    = __buffer1+__buffer2
            if(crc32 == binascii.crc32(buffer)):
                return (True,offset,offset+ModuleEVT.CHNK_SIZE_X)
            return (False,0,-1)
        return (False,0,-1)

    def carve(self):
        self.__reinit__()
        self.parser.get_file_handle(
            self.get_attrib(ModuleConstant.FILE_ATTRIBUTE),
            self.get_attrib(ModuleConstant.IMAGE_BASE),1
        )

        offset    = self.get_attrib(ModuleConstant.IMAGE_BASE)
        self.clus = self.get_attrib(ModuleConstant.CLUSTER_SIZE)
        last      = self.get_attrib(ModuleConstant.IMAGE_LAST)
        if(last==0):
            last  = self.parser.bgoto(0,os.SEEK_END)
       
        self.parser.bgoto(offset,os.SEEK_SET)

        while(offset<last):
            self.parser.bgoto(offset)
            res = self.__read(offset)
            if(res[0]==True):
                self.off_t.append(res[1],res[2],Offset_Info.VALID|Offset_Info.UNIT)
                offset=res[2]
            else:
                break
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
        self.flag = None
        ret = self.__evaluate()
        if(ret!=ModuleConstant.Return.SUCCESS):
            return None
        self.carve()
        print(self.off_t.contents)
        return self.off_t              # return <= 0 means error while collecting information


if __name__ == '__main__':

    idx = ModuleEVT()
    try:
        idx.set_attrib(ModuleConstant.FILE_ATTRIBUTE,"login1.evtx")
        #idx.set_attrib(ModuleConstant.FILE_ATTRIBUTE,sys.argv[1])   # Insert .idx File
    except:
        print("This moudule needs exactly one parameter.")
        sys.exit(1)

    idx.set_attrib(ModuleConstant.IMAGE_BASE,0)                     # Set offset of the file base
    idx.set_attrib(ModuleConstant.CLUSTER_SIZE,1024)
    cret = idx.execute()

    sys.exit(0)
