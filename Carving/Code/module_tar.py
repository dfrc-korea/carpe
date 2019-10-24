#-*- coding: utf-8 -*-
#!/usr/bin/python3

#!/Author : Gibartes

from moduleInterface.defines   import *
from moduleInterface.interface import ModuleComponentInterface
from structureReader import structureReader as sr
from collections     import OrderedDict
import os,sys,platform

class TARStructure(object):
    SIGNATURE = b'ustar '
    SPARSES_IN_SPARSE_HEADER = 21

    def __init__(self):

        self.PosixHeader      = OrderedDict({
            "name"      : [ 0 ,100,None],  # 
            "mode"      : [100,  8,None],  # 
            "uid"       : [108,  8,None],  # 
            "gid"       : [116,  8,None],  # 
            "size"      : [124, 12,None],  # 
            "mtime"     : [136, 12,None],  # 
            "checksum"  : [148,  8,None],  # 
            "typeflag"  : [156,  1,None],  #
            "linkname"  : [157,100,None],  #
            "magic"     : [257,  6,None],  #
            "version"   : [263,  2,None],  #
            "uname"     : [265, 32,None],  #
            "gname"     : [297, 32,None],  #
            "devmajor"  : [329,  8,None],  #
            "devminor"  : [337,  8,None],  #
            "prefix"    : [345,155,None],  #
        })

        self.OldGNUHeader    = OrderedDict({
            "padd"      : [ 0 ,345,None],  # 
            "atime"     : [345, 12,None],  #
            "ctime"     : [357, 12,None],  # 
            "offset"    : [369, 12,None],  #
            "longnames" : [381,  4,None],  # Not used
            "padd2"     : [385,  1,None],  #
            "sparse_sp" : [356, 96,None],  # 
            "extended"  : [482,  1,None],  #
            "realsize"  : [483, 12,None],  # 
        })

        self.StarHeader      = OrderedDict({
            "name"      : [ 0 ,100,None],  # 
            "mode"      : [100,  8,None],  # 
            "uid"       : [108,  8,None],  # 
            "gid"       : [116,  8,None],  # 
            "size"      : [124, 12,None],  # 
            "mtime"     : [136, 12,None],  # 
            "checksum"  : [148,  8,None],  # 
            "typeflag"  : [156,  1,None],  #
            "linkname"  : [157,100,None],  #
            "magic"     : [257,  6,None],  #
            "version"   : [263,  2,None],  #
            "uname"     : [265, 32,None],  #
            "gname"     : [297, 32,None],  #
            "devmajor"  : [329,  8,None],  #
            "devminor"  : [337,  8,None],  #
            "prefix"    : [345,131,None],  #
            "atime"     : [476, 12,None],  #
            "ctime"     : [500, 12,None]
        })

        self.StarInHeader     = OrderedDict({
            "fill"      : [ 0 ,345,None],  # 
            "prefix"    : [345,  1,None],  # 
            "fill2"     : [346,  1,None],  # 
            "fill3"     : [347,  8,None],  # 
            "extended"  : [355,  1,None],  # 
            "sparse_sp" : [356, 96,None],  # 
            "realsize"  : [452, 12,None],  # 
            "offset"    : [464, 12,None],  #
            "atime"     : [476, 12,None],  #
            "ctime"     : [488, 12,None],  #
            "mfill"     : [500,  8,None],  #
            "xmagic"    : [508,  4,None],  # tar
        })

        self.Sparse           = OrderedDict({
            "offset"    : [  0, 12,None],
            "numbytes"  : [ 12, 12,None],
        })

        self.SparseExtHeader     = OrderedDict({
            "sparse_sp" : [  0,TARStructure.SPARSES_IN_SPARSE_HEADER,None],
            "extended"  : [TARStructure.SPARSES_IN_SPARSE_HEADER,  1,None],
        })

        self.Headers = sr.Union()
        self.Headers.add({
            "posix":self.PosixHeader,
            "oldgnu":self.OldGNUHeader,
            "star":self.StarHeader,
        })

    @staticmethod
    def ascii2int(ascii,base=8):
        _str = ''
        for i in ascii:
            if(int(i)==0):
                break
            _str+=chr(i)
        return int(_str,base)

class ModuleTAR(ModuleComponentInterface):

    def __init__(self):
        super().__init__()                  # Initialize Module Interface
        self.fileSize   = 0
        self.offset     = list()
        self.missing    = 0
        self.parser     = sr.StructureReader()
        self.structure  = TARStructure()

        self.set_attrib(ModuleConstant.NAME,"TAR")
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

    def carve(self):
        self.__reinit__()
        self.parser.get_file_handle(
            self.get_attrib(ModuleConstant.FILE_ATTRIBUTE),
            self.get_attrib(ModuleConstant.IMAGE_BASE),1
        )

        offset  = self.get_attrib(ModuleConstant.IMAGE_BASE)
        last    = self.get_attrib(ModuleConstant.IMAGE_LAST)
        sector  = self.get_attrib(ModuleConstant.SECTOR_SIZE)
        if(last==0):
            last= self.parser.bgoto(0,os.SEEK_END)       

        if(sector==None or sector<0x200):
            sector=0x200

        header_padding = self.parser.align(self.structure.Headers.max,sector)

        self.parser.bgoto(offset,os.SEEK_SET)
        self.structure.Headers.data = self.parser.bread_raw(0,self.structure.Headers.max)

        # First Header
        if(self.structure.Headers.get_field("star","magic")!=TARStructure.SIGNATURE):
            self.parser.cleanup()
            return
        
        self.parser.bgoto(header_padding,os.SEEK_CUR)

        oldHeader = TARStructure() 
        _current  = 0
       
        while(_current<last):
            oldHeader.Headers.data      = self.structure.Headers.data
            self.structure.Headers.data = self.parser.bread_raw(0,self.structure.Headers.max)
            if(self.structure.Headers.get_field("star","magic")!=TARStructure.SIGNATURE):
                try:
                    jump  = oldHeader.ascii2int(oldHeader.Headers.get_field("star","size"))
                    jump += self.parser.align(jump,sector)
                    if(jump<1):
                        break
                    self.parser.bgoto(-self.structure.Headers.max+header_padding+jump,os.SEEK_CUR)
                except:
                    break
            _current = self.parser.btell()
               
        _length = self.parser.btell()-offset

        self.offset.append((self.get_attrib(ModuleConstant.IMAGE_BASE),_length,ModuleConstant.FILE_RECORD))
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

    TAR = ModuleTAR()
    try:
        TAR.set_attrib(ModuleConstant.FILE_ATTRIBUTE,sys.argv[1])   # Insert MFT File
    except:
        print("This moudule needs exactly one parameter.")
        sys.exit(1)

    TAR.set_attrib(ModuleConstant.IMAGE_BASE,0)  # Set offset of the file base
    cret = TAR.execute()
    print(cret)
    print(len(cret))
    sys.exit(0)
