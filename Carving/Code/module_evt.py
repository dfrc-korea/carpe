#-*- coding: utf-8 -*-

#!/usr/bin/python3

#!/Author : Gibartes

from defines         import *
from interface       import ModuleComponentInterface
from structureReader import structureReader as sr

#from structureReader import StructureReader    as parser
#from structureReader import _WindowsEventLogStructure as structure

import binascii
import os,sys,platform

# carving module for evt/evtx
class ModuleEvt(ModuleComponentInterface):
    EVT_SIG     = b"LfLe"
    EVTX_HEADER = b"ElfFile\00"
    EVTX_CHUNK  = b"ElfChnk\00"
    EVTX_RECORD = 0x2a2a
    CHNK_SIZE   = 512
    def __init__(self):
        super().__init__()                  # Initialize Module Interface
        self.fileSize   = 0
        self.offset     = list()
        self.missing    = 0
        self.parser     = sr.StructureReader()

        self.set_attrib(ModuleConstant.NAME,"evt")
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
        header = sr._WindowsEventLogStructure()
        result = self.parser.execute(header.evtFileHeader,'byte',offset,os.SEEK_SET,'little')
        if(result==False):
            return (False,0,-1,ModuleConstant.INVALID)
        
        # For evt
        if(self.parser.get_value("signature")==ModuleEvt.EVT_SIG):
            size = 0
            while(self.parser.get_value("signature")==ModuleEvt.EVT_SIG):
                _tmp = int.from_bytes(self.parser.get_value('size'),'little')
                size+=_tmp
                if(_tmp==0):
                    break
                self.parser.goto(-self.parser.get_size()+_tmp)
                self.parser.execute(header.evtRecord,'byte',0,os.SEEK_CUR,'little')
            return (True,offset,size,ModuleConstant.FILE_RECORD)
        
        # For evtx
        self.parser.goto(-self.parser.get_size())
        result = self.parser.execute(header.evtxFileChunkHeader,'byte',offset,os.SEEK_SET,'little')
        if(result==False):
            return (False,0,-1,ModuleConstant.INVALID)

        _type  = self.parser.get_value("signature")
        if(_type==ModuleEvt.EVTX_HEADER):
            self.parser.goto(-self.parser.get_size())
            self.parser.execute(header.evtxFileHeader,'byte',0,os.SEEK_CUR,'little')
            _crc = binascii.crc32(self.parser.stream[0:self.parser.get_field_offset("flags")])
            if(_crc == self.parser.byte2int(self.parser.get_value("checksum"))):
                return (True,offset,self.parser.byte2int(self.parser.get_value("hbsize")),ModuleConstant.FILE_HEADER)
            return (False,0,-1,ModuleConstant.INVALID)

        elif(_type==ModuleEvt.EVTX_CHUNK):
            self.parser.goto(-self.parser.get_size()+ModuleEvt.CHNK_SIZE)
            __offset = self.parser.tell()
            while(True):
                result = self.parser.execute(header.evtxEventRecord,'byte',__offset,os.SEEK_SET,'little')
                if(result==False):
                    break
                elif(self.parser.byte2int(self.parser.get_value("signature"))==ModuleEvt.EVTX_RECORD):
                    if(self.parser.byte2int(self.parser.get_value("size"))==0):
                        break                   # Prevent from inifinite loop
                    __offset+=self.parser.byte2int(self.parser.get_value("size"))
                else:break
            if(__offset-offset<=0):
                return (False,0,-1)
            return (True,offset,__offset-offset,ModuleConstant.FILE_RECORD) # This is probably equal with 'off_free'
        
        return (False,0,-1,ModuleConstant.INVALID)

    def carve(self):
        self.__reinit__()
        self.parser.get_file_handle(
            self.get_attrib(ModuleConstant.FILE_ATTRIBUTE),
            self.get_attrib(ModuleConstant.IMAGE_BASE)
        )

        offset  = self.get_attrib(ModuleConstant.IMAGE_BASE)
        clus    = self.get_attrib(ModuleConstant.CLUSTER_SIZE)
        last    = self.get_attrib(ModuleConstant.IMAGE_LAST)
        if(last==0):
            last    = self.parser.goto(0,os.SEEK_END)
       
        self.parser.goto(offset,os.SEEK_SET)

        while(offset<last):
            res = self.__read(offset)
            if(res[0]==True):
                self.offset.append((res[1],res[2],res[3]))
                self.fileSize += res[2]
                offset+=res[2]
                _rest = self.parser.align(res[2],clus)
                if(_rest!=0):
                    offset+=_rest
            else:
                self.missing+=1
                offset+= clus
        
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

    idx = ModuleEvt()
    try:
        idx.set_attrib(ModuleConstant.FILE_ATTRIBUTE,sys.argv[1])   # Insert .idx File
    except:
        print("This moudule needs exactly one parameter.")
        sys.exit(1)

    idx.set_attrib(ModuleConstant.IMAGE_BASE,0)                     # Set offset of the file base
    #idx.set_attrib(ModuleConstant.IMAGE_LAST,65535)
    idx.set_attrib(ModuleConstant.CLUSTER_SIZE,1024)
    cret = idx.execute()
    print(cret)

    idx.set_attrib(ModuleConstant.IMAGE_BASE,65536)                     # Set offset of the file base
    idx.set_attrib(ModuleConstant.IMAGE_LAST,262140)
    idx.set_attrib(ModuleConstant.CLUSTER_SIZE,1024)
    cret = idx.execute()
    print(cret)
    sys.exit(0)