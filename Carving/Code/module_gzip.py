#-*- coding: utf-8 -*-
# http://www.multiweb.cz/twoinches/GZIPinside.htm
#!/usr/bin/python3

#!/Author : Gibartes

from moduleInterface.defines   import *
from moduleInterface.interface import ModuleComponentInterface
from structureReader import structureReader as sr
from collections     import OrderedDict
import os,sys,platform,time
import gzip

class GZIPStructure(object):
    Signature   = b'\x1F\x8B'
    FTEXT       = 1
    FHCRC       = 2
    FEXTRA      = 4
    FNAME       = 8
    FCOMMENT    = 16

    def __init__(self):
        # TAG
        self.Header      = OrderedDict({
            "signature" : [ 0, 2,None],  # ID
            "cm"        : [ 2, 1,None],  # Compression Method
            "flag"      : [ 3, 1,None],  # Flags
            "mtime"     : [ 4, 4,None],  # Modified Time
            "xfl"       : [ 8, 1,None],  # Extra Flags
            "os"        : [ 9, 1,None],
        })

        self.Extra       = OrderedDict({
            "xlen"      : [ 0, 2,None],  #
        })

        self.data        = OrderedDict({
            "16crc"     : [ 0, 2,None],
            # Compressed
            # Uncompressed input size modulo 2^32
        })


    @staticmethod
    def get_set(_byte):
        return _byte&1+_byte&2>>1+_byte&4>>2+_byte&8>>3+_byte&16>>4

class ModuleGZIP(ModuleComponentInterface):

    def __init__(self):
        super().__init__()        # Initialize Module Interface
        self.fileSize        = 0
        self.offset          = list()
        self.missing         = 0
        self.parser          = sr.StructureReader()
        self.structure       = GZIPStructure()
        self.decomp          = None
        
        self.set_attrib(ModuleConstant.NAME,"GZIP")
        self.set_attrib(ModuleConstant.VERSION,"0.1")
        self.set_attrib(ModuleConstant.AUTHOR,"HK")
    
    def __reinit__(self):
        self.fileSize     = 0
        self.offset       = list()
        self.missing      = 0
        self._stream_size = 0
        self._crc         = 0

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

    def carve(self,cmd,option):
        self.__reinit__()
        self.parser.get_file_handle(
            self.get_attrib(ModuleConstant.FILE_ATTRIBUTE),
            self.get_attrib(ModuleConstant.IMAGE_BASE),1
        )

        opflag  = False
        offset  = self.get_attrib(ModuleConstant.IMAGE_BASE)
        last    = self.get_attrib(ModuleConstant.IMAGE_LAST)
        flag    = False

        if(option!=None and type(option)==int):
            rbyte = int(option)
        else:
            rbyte = 1
        if(last==0):
            last= self.parser.bgoto(0,os.SEEK_END)

        
        fname  = "temp_gz"+str(time.time())
        try:
            with open(fname,"wb") as _temp:
                buffer = self.parser.bread_raw(offset,last,os.SEEK_SET)
                _temp.write(buffer)
                
            with gzip.open(fname,"rb") as _temp:
                _temp.read()
            flag = True
        except:
            pass
        
        if(flag):
            if(os.path.exists(fname)):
                os.remove(fname)
            self.offset.append((self.get_attrib(ModuleConstant.IMAGE_BASE),last,ModuleConstant.FILE_ONESHOT))
            self.parser.cleanup()
            return
        
        self.parser.bgoto(offset,os.SEEK_SET)
        self.parser.bexecute(self.structure.Header,'byte',offset,os.SEEK_SET)
        if(self.parser.get_value("signature")!=self.structure.Signature):
            self.parser.cleanup()
            return

        flag  = self.parser.byte2int(self.parser.get_value("flag"))&0x1F

        while(flag!=0):
            if(flag&self.structure.FEXTRA):
                flag-=self.structure.FEXTRA
                extra_h = self.parser.byte2int(self.parser.bread_raw(0,self.parser.sizeof(self.parser.Extra)))
                self.parser.bgoto(extra_h)
            if(flag&self.structure.FNAME):
                flag-=self.structure.FNAME
                while(1):
                    blk = self.parser.bread_raw(0,1)
                    if(blk==b'\x00'):
                        break
            if(flag&self.structure.FCOMMENT):
                flag-=self.structure.FCOMMENT
                while(1):
                    blk = self.parser.bread_raw(0,1)
                    if(blk==b'\x00'):
                        break
            if(flag&self.structure.FTEXT):
                flag-=self.structure.FTEXT
                while(1):
                    blk = self.parser.bread_raw(0,1)
                    if(blk==b'\x00'):
                        break
            if(flag&self.structure.FHCRC):
                flag-=self.structure.FHCRC
                self.parser.bread_raw(0,2)

        fname  = "temp_gz"+str(time.time())
        current = self.parser.btell()
        while(current<last):
            current+=rbyte
            try:
                with open(fname,"wb") as _temp:
                    buffer = self.parser.bread_raw(offset,current,os.SEEK_SET)
                    _temp.write(buffer)
                
                with gzip.open(fname,"rb") as _temp:
                    _temp.read()
                flag = True
                break
            except:
                pass
        
        if(os.path.exists(fname)):
            os.remove(fname)

        self.parser.cleanup()
        if(flag):
            self.offset.append((self.get_attrib(ModuleConstant.IMAGE_BASE),current,ModuleConstant.FILE_ONESHOT))


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
        self.carve(cmd,option)
        if(self.offset==[]):
            return [(False,0,ModuleConstant.INVALID)]
        return self.offset                  # return <= 0 means error while collecting information


if __name__ == '__main__':

    GZIP = ModuleGZIP()
    try:
        GZIP.set_attrib(ModuleConstant.FILE_ATTRIBUTE,sys.argv[1])   # Insert MFT File
    except:
        print("This moudule needs exactly one parameter.")
        sys.exit(1)

    GZIP.set_attrib(ModuleConstant.IMAGE_BASE,0)  # Set offset of the file base
    cret = GZIP.execute(None,1)
    print(cret)
    print(len(cret))
    sys.exit(0)
