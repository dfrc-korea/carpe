#-*- coding: utf-8 -*-

#!/usr/bin/python3

#!/Author : Gibartes

from defines         import *
from interface       import ModuleComponentInterface
from structureReader import structureReader as sr

#from structureReader import StructureReader    as parser
#from structureReader import _IndexDatStructure as structure

import os,sys,platform

# carving module for index.dat
class ModuleIdx(ModuleComponentInterface):
    SIGNATURE           = b'\x43\x6C\x69\x65\x6E\x74\x20\x55\x72\x6C\x43\x61\x63\x68\x65\x20\x4D\x4D\x46\x20\x56\x65\x72\x20\x35\x2E\x32\x00'
    HASH                = b'\x48\x41\x53\x48'
    HASH_BLK_SIZE       = 128
    ACTIVITY_SIG_URL    = 0x204C5255   #URL
    ACTIVITY_SIG_REDR   = 0x52444552   #REDR
    ACTIVITY_SIG_LEEK   = 0x4b41454c   #LEAK

    def __init__(self):
        super().__init__()                  # Initialize Module Interface
        self.fileSize   = 0
        self.offset     = list()
        self.missing    = 0
        self.parser     = sr.StructureReader()

        self.set_attrib(ModuleConstant.NAME,"idx")
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
        header = sr._IndexDatStructure()
        fileHdr = self.parser.execute(header.IndexDatHeader,'byte',offset,os.SEEK_SET,'little')
        if(fileHdr==False):
            return (False,0,-1,ModuleConstant.INVALID)

        if(self.parser.get_value("signature")==ModuleIdx.SIGNATURE):
            if(self.parser.get_value("size")==b'\x00' or self.parser.get_value("offhtr")==b'\x00'):
                return (False,0,-1,ModuleConstant.INVALID)
       
            return (True,offset,self.get_attrib(ModuleConstant.CLUSTER_SIZE),ModuleConstant.FILE_HEADER)

        self.parser.goto(-self.parser.get_size())
        self.parser.execute(header.HashTableRecord,'byte',0,os.SEEK_CUR,'little')
        
        if(self.parser.get_value("signature")==ModuleIdx.HASH):
            return (True,offset,self.parser.byte2int(self.parser.get_value("nob")) * ModuleIdx.HASH_BLK_SIZE,ModuleConstant.FILE_HEADER)

        self.parser.goto(-self.parser.get_size())
        __size  = 0
        while(True):
            result = self.parser.execute(header.URLRecord,'byte',0,os.SEEK_CUR,'little')
            if(result==False):
                break
            if(self.parser.get_value("fver")!=b'0x05'):
                self.parser.goto(-self.parser.get_size())
                self.parser.execute(header.URLRecord4,'byte',0,os.SEEK_CUR,'little')

            if(self.parser.byte2int(self.parser.get_value("signature")) not in (ModuleIdx.ACTIVITY_SIG_URL,ModuleIdx.ACTIVITY_SIG_REDR,ModuleIdx.ACTIVITY_SIG_LEEK)):
                break

            if(self.parser.byte2int(self.parser.get_value("nob"))==0):
                break

            self.parser.goto(-self.parser.get_size()+ModuleIdx.HASH_BLK_SIZE \
                                * self.parser.byte2int(self.parser.get_value("nob")))
            __size += ModuleIdx.HASH_BLK_SIZE*self.parser.byte2int(self.parser.get_value("nob"))

        if(__size!=0):
            return (True,offset,__size,ModuleConstant.FILE_RECORD)
        
        return (False,0,-1,ModuleConstant.INVALID)

    def __read_cont(self,offset):
        header = sr._IndexDatStructure()
        fileHdr = self.parser.execute(header.IndexDatHeader,'byte',offset,os.SEEK_SET,'little')
        if(fileHdr==False):
            return (False,0,-1,ModuleConstant.INVALID)

        if(self.parser.get_value("signature")!=ModuleIdx.SIGNATURE):
            return (False,0,-1,ModuleConstant.INVALID)

        if(self.parser.get_value("size")==b'\x00' or self.parser.get_value("offhtr")==b'\x00'):
            return (False,0,-1,ModuleConstant.INVALID)
        
        self.parser.goto(-self.parser.get_size()+self.parser.byte2int(self.parser.get_value("offhtr")))
        self.parser.execute(header.HashTableRecord,'byte',0,os.SEEK_CUR,'little')
        if(self.parser.get_value("signature")!=ModuleIdx.HASH):
            return (False,0,-1,ModuleConstant.INVALID)
        
        blksize = self.parser.byte2int(self.parser.get_value("nob")) * ModuleIdx.HASH_BLK_SIZE
        self.parser.goto(-self.parser.get_size()+blksize)
        
        current = self.parser.tell() 
        __size  = 0
        
        while(True):
            result = self.parser.execute(header.URLRecord,'byte',0,os.SEEK_CUR,'little')
            if(result==False):
                break

            if(self.parser.get_value("fver")!=b'0x05'):
                self.parser.goto(-self.parser.get_size())
                self.parser.execute(header.URLRecord4,'byte',0,os.SEEK_CUR,'little')

            if(self.parser.byte2int(self.parser.get_value("signature")) not in (ModuleIdx.ACTIVITY_SIG_URL,ModuleIdx.ACTIVITY_SIG_REDR,ModuleIdx.ACTIVITY_SIG_LEEK)):
                break

            if(self.parser.byte2int(self.parser.get_value("nob"))==0):
                break

            self.parser.goto(-self.parser.get_size()+ModuleIdx.HASH_BLK_SIZE \
                             * self.parser.byte2int(self.parser.get_value("nob")))
            __size += ModuleIdx.HASH_BLK_SIZE*self.parser.byte2int(self.parser.get_value("nob"))

        return (True,offset,current-offset+__size,ModuleConstant.FILE_ONESHOT)
        
    def carve(self,option):
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
        
        if(option==True):
            res = self.__read_cont(offset)
            if(res[0]==True):
                self.offset.append((res[1],res[2],res[3]))
                self.fileSize += res[2]
                offset+=res[2]
            else:
                self.missing+=1
        else:
            while(offset<last):
                res = self.__read(offset)
                if(res[0]==True):
                    self.offset.append((res[1],res[2]+self.parser.align(res[2],clus),res[3]))
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

    def execute(self,cmd=None,option=False): # 모듈 호출자가 모듈을 실행하는 method
        ret = self.__evaluate()
        if(ret!=ModuleConstant.Return.SUCCESS):
            return [(False,ret,ModuleConstant.INVALID)]
        self.carve(option)
        if(self.offset==[]):
            return [(False,0,ModuleConstant.INVALID)]
        return self.offset                  # return <= 0 means error while collecting information


if __name__ == '__main__':

    idx = ModuleIdx()
    try:
        idx.set_attrib(ModuleConstant.FILE_ATTRIBUTE,sys.argv[1])   # Insert .idx File
    except:
        print("This moudule needs exactly one parameter.")
        sys.exit(1)

    idx.set_attrib(ModuleConstant.IMAGE_BASE,0)                     # Set offset of the file base
    idx.set_attrib(ModuleConstant.CLUSTER_SIZE,1024)
    cret = idx.execute()
    print(cret)

    sys.exit(0)