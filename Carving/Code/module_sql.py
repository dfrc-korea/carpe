#-*- coding: utf-8 -*-

#!/usr/bin/python3

#!/Author : Gibartes

from defines         import *
from interface       import ModuleComponentInterface
from structureReader import structureReader as sr

#from structureReader import StructureReader as parser
#from structureReader import _SQLStructure   as structure


import binascii
import os,sys,platform

# carving module for evt/evtx
class ModuleSql(ModuleComponentInterface):
    SQL_DB_SIGNATURE = 110748049513798795666017677735771517696
    SQL_PAGE_LIST    = (2,5,0xA,0xD)

    def __init__(self):
        super().__init__()                  # Initialize Module Interface
        self.fileSize   = 0
        self.offset     = list()
        self.missing    = 0
        self.parser     = sr.StructureReader()

        self.set_attrib(ModuleConstant.NAME,"sql")
        self.set_attrib(ModuleConstant.VERSION,"0.1")
        self.set_attrib(ModuleConstant.AUTHOR,"HK")

    def __reinit__(self):
        self.flag       = False
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
        header = sr._SQLStructure()
        result = self.parser.bexecute(header.dataBaseHeader,'int',offset,os.SEEK_SET,'big')

        if(self.parser.get_value('signature')==ModuleSql.SQL_DB_SIGNATURE):
            self.pageSize = self.parser.get_value('size_page')
            return (True,offset,self.parser.get_value('size_page'),ModuleConstant.FILE_HEADER)

        self.parser.bgoto(-self.parser.get_size())

        self.parser.bexecute(header.btreePageHeader,'int',0,os.SEEK_CUR,'big')

        if(self.parser.get_value('flag') not in ModuleSql.SQL_PAGE_LIST):
            return (False,0,-1,ModuleConstant.INVALID)

        if(self.parser.get_value('num_of_cells')==0):   # Drop empty pages
            return (False,0,-1,ModuleConstant.INVALID)

        """
        if(self.parser.get_value('num_of_cells')==1):
            self.parser.bgoto((self.parser.get_value('num_of_cells')-1)*2)
            barray     = (self.pageSize,int.from_bytes(self.parser.bread_raw(0,2),'big'))
        else:
            self.parser.bgoto((self.parser.get_value('num_of_cells')-2)*2)
            _barray    = self.parser.bread_raw(0,4)
            barray     = (int.from_bytes(_barray[0:2],'big'),int.from_bytes(_barray[2:4],'big'))

        self.parser.bgoto(current+barray[1],os.SEEK_SET)
        barray = self.parser.bread_raw(0,barray[0]-barray[1])

        # add code to specify sqlite database...
        """
        return (True,offset,self.pageSize,ModuleConstant.FILE_RECORD)

    def __readCont(self,offset):
        header =  sr._SQLStructure()
        result = self.parser.bexecute(header.dataBaseHeader,'int',offset,os.SEEK_SET,'big')

        if(self.parser.get_value('signature')!=ModuleSql.SQL_DB_SIGNATURE):
            self.offset = [(False,0,ModuleConstant.INVALID)]
            return

        self.expectedfileSize = self.parser.get_value('size_database') * \
                                self.parser.get_value('size_page')  # DB Size
        self.pageSize         = self.parser.get_value('size_page')
        self.fileSize         = self.pageSize
        self.offset.append((offset,self.pageSize,ModuleConstant.FILE_HEADER))

        self.parser.bgoto(-self.parser.get_size()+self.pageSize)

        current = self.parser.btell()

        while(current<self.expectedfileSize+offset):
            current = self.parser.btell()
            self.parser.bexecute(header.btreePageHeader,'int',0,os.SEEK_CUR,'big')

            if(self.parser.get_value('flag') not in ModuleSql.SQL_PAGE_LIST):
                self.parser.bgoto(-self.parser.get_size()+self.pageSize)
                return
            if(self.parser.get_value('num_of_cells')==0):
                self.offset.append((current,self.pageSize,ModuleConstant.FILE_RECORD))
                self.parser.bgoto(-self.parser.get_size()+self.pageSize)
                continue

            """
            if(self.parser.get_value('flag')>0x9):
                self.parser.bgoto(-self.parser.get_field_size('pointer'))

            # ---> Internal error of Python ; read (Python is too buggy!)
            if(self.parser.get_value('num_of_cells')==1):
                self.parser.bgoto((self.parser.get_value('num_of_cells')-1)*2)
                barray     = (self.pageSize,int.from_bytes(self.parser.bread_raw(0,2),'big'))
            else:
                self.parser.bgoto((self.parser.get_value('num_of_cells')-2)*2)
                _barray    = self.parser.bread_raw(0,4)
                barray     = (int.from_bytes(_barray[0:2],'big'),int.from_bytes(_barray[2:4],'big'))
            if(barray[0]==0 or (barray[0]<=barray[1])):       # This is a incorrect page
                self.parser.bgoto(current+self.pageSize,os.SEEK_SET)
                continue
            # <---

            self.parser.bgoto(current+barray[1],os.SEEK_SET)
            barray = self.parser.bread_raw(0,barray[0]-barray[1])

            # add code to specify sqlite database...

            """

            self.offset.append((current,self.pageSize,ModuleConstant.FILE_RECORD))
            self.parser.bgoto(current+self.pageSize,os.SEEK_SET)
        return

    def carve(self,option):
        self.__reinit__()
        self.parser.get_file_handle(
            self.get_attrib(ModuleConstant.FILE_ATTRIBUTE),
            self.get_attrib(ModuleConstant.IMAGE_BASE),1
        )

        offset  = self.get_attrib(ModuleConstant.IMAGE_BASE)
        clus    = self.get_attrib(ModuleConstant.CLUSTER_SIZE)
        last    = self.get_attrib(ModuleConstant.IMAGE_LAST)
        if(last==0):
            last    = self.parser.bgoto(0,os.SEEK_END)

        self.parser.bgoto(offset,os.SEEK_SET)
        

        if(option):
            self.__readCont(offset)
        else:
            while(offset<last):
                res = self.__read(offset)
                if(res[0]==True):
                    if(res[2]==0):
                        break
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

    def execute(self,cmd=None,option=True): # 모듈 호출자가 모듈을 실행하는 method
        ret = self.__evaluate()
        if(ret!=ModuleConstant.Return.SUCCESS):
            return [(False,ret,ModuleConstant.INVALID)]
        self.carve(option)
        if(self.offset==[]):
            return [(False,0,ModuleConstant.INVALID)]
        return self.offset                  # return <= 0 means error while collecting information


if __name__ == '__main__':

    idx = ModuleSql()
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
