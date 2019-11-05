#-*- coding: utf-8 -*-

#!/usr/bin/python3

#!/Author : Gibartes

"""
The default attribute of module :
    "name"   :"default",            # Module 이름
    "author" :"carpe",              # Module 제작자
    "ver"    :"0.0",                # Module 버젼
    "param"  :None,                 # Module 파라미터
    "encode" :"utf-8",              # Module 인코딩
    "base"   :0                     # File image base to carve

"""

from moduleInterface.interface import ModuleComponentInterface
from defines import *

from ctypes  import *
import os,sys,platform

if(platform.system()=='Linux'):
    try:
        LIB_PATH = ModuleConstant.LIB_DEFAULT_PATH+ModuleConstant.Dependency.pecarve+".so"
        pelib_parser = cdll.LoadLibrary(LIB_PATH)
    except:
        LIB_PATH = ModuleConstant.DEFINE_PATH + ModuleConstant.Dependency.pecarve+".so"
        pelib_parser = cdll.LoadLibrary(LIB_PATH)
else:
    try:
        LIB_PATH = ModuleConstant.Dependency.pecarve+".dll"
        pelib_parser = cdll.LoadLibrary(LIB_PATH)
    except:
        LIB_PATH = ModuleConstant.DEFINE_PATH + ModuleConstant.Dependency.pecarve+".dll"
        pelib_parser = cdll.LoadLibrary(LIB_PATH)

class PE_CARVE_MODULE_DATA(Structure):pass

PE_CARVE_MODULE_DATA._fields_ = [
    ("sections"  ,c_int32),                # Number of Sections
    ("fileSize"  ,c_uint64),               # Expected Total File Size
]

pelib_parser.pe_carve.argtypes    = [POINTER(PE_CARVE_MODULE_DATA),c_char_p,c_uint64]
pelib_parser.pe_estimate.argtypes = [POINTER(PE_CARVE_MODULE_DATA),c_char_p,c_uint64]
pelib_parser.hexPrint.argtypes    = [c_void_p,c_uint32]


class CHELPER(object):
    CTYPE_SIZE = {
        c_char:1,c_byte:1,c_ubyte:1,
        c_short:2,c_ushort:2,
        c_int:4,c_uint:4,
        c_long:8,c_ulong:8
    }
    @staticmethod
    def hexPrint(arr,size):
        pelib_parser.hexPrint(byref(arr),size)

    @staticmethod
    def getCtypeSize(_ctype):
        return CHELPER.CTYPE_SIZE.get(_ctype)


class ModulePEParser(ModuleComponentInterface):

    def __init__(self):
        super().__init__()                  # Initialize Module Interface
        self.data  = None
        self.flag  = None

        self.set_attrib(ModuleConstant.NAME,"pe")
        self.set_attrib(ModuleConstant.VERSION,"0.1")
        self.set_attrib(ModuleConstant.AUTHOR,"HK")
        self.set_attrib("detailed_type",True)

    def __del__(self):
        self.cleanup()

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
        self.cleanup()
        self.data = PE_CARVE_MODULE_DATA()
        __enc     = self.attrib.get(ModuleConstant.ENCODE)
        pelib_parser.pe_carve(
                        self.data,
                        self.attrib.get(ModuleConstant.FILE_ATTRIBUTE).encode(__enc),
                        self.attrib.get(ModuleConstant.IMAGE_BASE)
                        )

    def estimate(self):
        self.cleanup()
        self.data = PE_CARVE_MODULE_DATA()
        __enc     = self.attrib.get(ModuleConstant.ENCODE)
        pelib_parser.pe_estimate(
                        self.data,
                        self.attrib.get(ModuleConstant.FILE_ATTRIBUTE).encode(__enc),
                        self.attrib.get(ModuleConstant.IMAGE_BASE)
                        )

    def cleanup(self):
        if(self.data!=None):
            self.data = None

    def get_module_info(self):
        return (self.attrib)

    def execute_in_main(self,cmd=None,option=None):
        ret = self.__evaluate()
        if(ret!=ModuleConstant.Return.SUCCESS):
            return ret
        self.estimate()
        return self.data

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
            self.flag = "exe"
            return [(self.attrib.get(ModuleConstant.IMAGE_BASE),self.data.fileSize,ModuleConstant.FILE_ONESHOT)] 
        # return <= 0 means error while collecting information

# Usage Example :
if __name__ == '__main__':
    base = 0
    mpe = ModulePEParser()
    try:
        mpe.set_attrib(ModuleConstant.FILE_ATTRIBUTE,sys.argv[1])   # insert file path to investigate
    except:
        print("This moudule needs exactly one parameter.")
        sys.exit(1)

    mpe.set_attrib(ModuleConstant.IMAGE_BASE,base)                   # Set offset of the file base
    cret = mpe.execute_in_main()
    if(cret==ModuleConstant.Return.EINVAL_FILE):
        print("Invalid File.")
        sys.exit(1)

    print("The Number of Sections : {0}".format(cret.sections))
    print("File Size : ",hex(cret.fileSize))
    print("Maximum Offset : {0} with Base : {1}".format(hex(cret.fileSize+base),base))
    
    cret = mpe.execute()
    if(cret==ModuleConstant.Return.EINVAL_FILE):
        print("Invalid File.")
        sys.exit(1)
    print(cret)    
    sys.exit(0)
