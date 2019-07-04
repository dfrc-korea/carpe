#-*- coding: utf-8 -*-

#!/usr/bin/python3

#!/Author : Gibartes

from defines         import *
from interface       import ModuleComponentInterface
from structureReader import structureReader as sr

#from structureReader import StructureReader    as parser
#from structureReader import _LinkFileStructure as structure

import os,sys,platform

class ModuleLNK(ModuleComponentInterface):

    def __init__(self):
        super().__init__()                  # Initialize Module Interface
        self.fileSize   = 0
        self.offset     = list()
        self.missing    = 0
        self.parser     = sr.StructureReader()

        self.set_attrib(ModuleConstant.NAME,"lnk")
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

    # ShellItemList와 FileLocationInfo의 이름 필드 비교
    def __read(self,offset):
        header = sr._LinkFileStructure()
        size   = 0

        result = self.parser.execute(header.ShellLinkHeader,'int',offset,os.SEEK_SET,'little')
        if(result==False):
            return (False,0,-1,ModuleConstant.INVALID)

        nbase = offset+self.parser.tell()-2
        sitem = nbase+2
        size  += self.parser.get_value("lti")
        size  += 2
        nbase += size
        self.parser.goto(size-2)

        result = self.parser.execute(header.FileLocationInfo,'int',0,os.SEEK_CUR,'little')
        if(result==False):
            return (False,0,-1,ModuleConstant.INVALID)

        size += self.parser.get_size()

        _name= self.parser.get_value("oftlp")
        if(self.parser.get_value("oftnsi")==0):
            _len = self.parser.get_value("oftcp")
        elif(self.parser.get_value("oftcp")==0):
            _len = self.parser.get_value("oftnsi")
        else:
            _len = self.parser.get_value("oftcp") if        \
                        (self.parser.get_value("oftnsi") >  \
                         self.parser.get_value("oftcp"))    \
                   else self.parser.get_value("oftnsi")

        _len  = (_len -_name) if _len -_name >= 0 else (_name-_len)
        _cmp  = None

        try:
            _name = self.parser.read_raw(nbase+_name,_len,os.SEEK_SET).split(b'\\')[-1].split(b'\x00')[0]
        except:
            return (False,0,-1,ModuleConstant.INVALID)
        
        self.parser.goto(sitem,os.SEEK_SET)
        while(self.parser.tell()<nbase):
            result = self.parser.execute(header.ShellItemList,'int',0,os.SEEK_CUR,'little')
            if(result==False):
                return (False,0,-1,ModuleConstant.INVALID)

            if(self.parser.get_value("type") in sr._LinkFileStructure.CLSID.CLSID_ShellFSFolder):
                _cp  = self.parser.tell()
                _cmp = self.parser.read_raw(0,
                                            self.parser.get_value("size")-
                                            self.parser.get_size(),os.SEEK_CUR)
                _cmp = _cmp[10:-1].split(b'\x00')[0]
                if(_name==_cmp):
                    break
                self.parser.goto(_cp,os.SEEK_SET)
            elif(self.parser.get_value("size")==0):
                return (False,0,-1,ModuleConstant.INVALID)
            self.parser.goto(self.parser.get_value("size")-self.parser.get_size())

        return (True,offset,self.get_attrib(ModuleConstant.CLUSTER_SIZE),ModuleConstant.FILE_ONESHOT)
        
    def carve(self):
        self.__reinit__() 
        self.parser.get_file_handle(
            self.get_attrib(ModuleConstant.FILE_ATTRIBUTE),
            self.get_attrib(ModuleConstant.IMAGE_BASE)
        )

        offset  = self.get_attrib(ModuleConstant.IMAGE_BASE)     
        self.parser.goto(offset,os.SEEK_SET)

        res = self.__read(offset)
        if(res[0]==True):
            self.offset.append((res[1],res[2]))
            self.fileSize += res[2]
            offset+=res[2]
        else:
            self.missing+=1
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

    lnk = ModuleLNK()
    try:
        lnk.set_attrib(ModuleConstant.FILE_ATTRIBUTE,sys.argv[1])   # Insert .lnk File
    except:
        print("This moudule needs exactly one parameter.")
        sys.exit(1)

    lnk.set_attrib(ModuleConstant.IMAGE_BASE,0)                     # Set offset of the file base
    lnk.set_attrib(ModuleConstant.CLUSTER_SIZE,1024)
    cret = lnk.execute()
    print(cret)

    sys.exit(0)