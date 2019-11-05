#-*- coding: utf-8 -*-

#!/usr/bin/python3

#!/Author : Gibartes

from moduleInterface.defines   import *
from moduleInterface.interface import ModuleComponentInterface
#from defines         import *
#from interface       import ModuleComponentInterface

from structureReader import structureReader as sr
#import _structureReader as sr


import os,sys,platform

class ModuleLNK(ModuleComponentInterface):

    def __init__(self):
        super().__init__()                  # Initialize Module Interface
        self.fileSize   = 0
        self.offset     = list()
        self.missing    = 0
        self.parser     = sr.StructureReader()
        self.flag       = None

        self.set_attrib(ModuleConstant.NAME,"lnk")
        self.set_attrib(ModuleConstant.VERSION,"0.1")
        self.set_attrib(ModuleConstant.AUTHOR,"HK")
        self.set_attrib("detailed_type",True)

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
    def __read(self,offset,__encode):
        header = sr._LinkFileStructure()
        size   = 0
        __flag = 0
        result = self.parser.bexecute(header.ShellLinkHeader,'int',offset,os.SEEK_SET,'little')
        if(result==False):
            return (False,0,-1,ModuleConstant.INVALID)

        flag        = self.parser.get_value("flags")
        isUTF16     = flag & 0x80
        if(isUTF16==0x80):isUTF16=1
        hasRelative = flag & 0x08

        _tmp = self.parser.get_value("lti")
        if(self.parser.get_value('ltime')==0x00):
            self.parser.bgoto(-self.parser.get_field_size('lti'))
            _tmp = self.parser.byte2int(self.parser.bread_raw(0,2))

        nbase = offset+self.parser.btell()-2
        sitem = nbase+2
        size  += _tmp
        size  += 2
        nbase += size
        self.parser.bgoto(size-2)

        _tmp   = self.parser.btell()
        result = self.parser.bexecute(header.FileLocationInfo,'int',0,os.SEEK_CUR,'little')

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
            _name = self.parser.bread_raw(nbase+_name,_len,os.SEEK_SET).split(b'\\')[-1].split(b'\x00')[0].strip()
        except:
            return (False,0,-1,ModuleConstant.INVALID)
        try:
            _name = _name.decode()
        except:
            __flag=1

        if(__flag==1):
            try:_name = _name.decode(__encode)
            except:return (False,0,-1,ModuleConstant.INVALID)

        if(hasRelative==0x08):
            self.parser.bgoto(_tmp+self.parser.get_value("size"),os.SEEK_SET)
            _tmp   = self.parser.btell()
            _len   = self.parser.byte2int(self.parser.bread_raw(0,2,os.SEEK_CUR))*(isUTF16+1)
            if(_len!=0):
                cmp    = self.parser.bread_raw(0,_len).split(b'\\\x00')[-1]
                if(isUTF16):
                    try:
                        cmp = cmp.decode('UTF-16').strip()
                    except:
                        return (False,0,-1,ModuleConstant.INVALID)
                if(_name==cmp):
                    return (True,offset,self.get_attrib(ModuleConstant.CLUSTER_SIZE),ModuleConstant.FILE_ONESHOT)

        else:
            self.parser.bgoto(sitem,os.SEEK_SET)

            while(self.parser.btell()<nbase):
                result = self.parser.bexecute(header.ShellItemList,'int',0,os.SEEK_CUR,'little')
                if(result==False):
                    return (False,0,-1,ModuleConstant.INVALID)

                if(self.parser.get_value("type") in sr._LinkFileStructure.CLSID.CLSID_ShellFSFolder):
                    _len = self.parser.get_value("size")-self.parser.get_size()
                    _cmp = self.parser.bread_raw(0,_len,os.SEEK_CUR)
                    try:
                        _tmp = _cmp[10:-1].split(b'\x00')[0].decode()
                        __flag = 0
                    except:__flag = 1

                    if(__flag):
                        _tmp = _cmp[10:-1].split(b'\x00\x00')[0]
                        if(len(_tmp)%2):_tmp+=b'\x00'
                        try:
                            _tmp = _tmp.decode('utf-16')
                        except:
                            return (False,offset,self.get_attrib(ModuleConstant.CLUSTER_SIZE),ModuleConstant.FILE_ONESHOT)

                    if(_name==_tmp):
                        return (True,offset,self.get_attrib(ModuleConstant.CLUSTER_SIZE),ModuleConstant.FILE_ONESHOT)
                    self.parser.bgoto(-_len+self.parser.get_value("size")-self.parser.get_size())
                    continue

                elif(self.parser.get_value("size")==0):
                    return (False,0,-1,ModuleConstant.INVALID)

                self.parser.bgoto(self.parser.get_value("size")-self.parser.get_size())

        return (False,offset,self.get_attrib(ModuleConstant.CLUSTER_SIZE),ModuleConstant.FILE_ONESHOT)

    def carve(self):
        self.__reinit__()
        self.parser.get_file_handle(
            self.get_attrib(ModuleConstant.FILE_ATTRIBUTE),
            self.get_attrib(ModuleConstant.IMAGE_BASE),1

        )

        offset  = self.get_attrib(ModuleConstant.IMAGE_BASE)
        self.parser.bgoto(offset,os.SEEK_SET)

        res = self.__read(offset,self.get_attrib(ModuleConstant.ENCODE))
        if(res[0]==True):
            self.offset.append((res[1],res[2],res[3]))
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
        if(cmd=='inspect'):
            return self.flag
        else:
            self.flag = None
            ret = self.__evaluate()
            if(ret!=ModuleConstant.Return.SUCCESS):
                return [(False,ret,ModuleConstant.INVALID)]
            self.carve()
            if(self.offset==[]):
                return [(False,0,ModuleConstant.INVALID)]
            self.flag = "lnk"
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
    lnk.set_attrib(ModuleConstant.ENCODE,'euc-kr')
    cret = lnk.execute()
    print(cret)

    sys.exit(0)
