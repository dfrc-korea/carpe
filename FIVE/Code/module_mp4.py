#-*- coding: utf-8 -*-
# http://www.multiweb.cz/twoinches/MP4inside.htm
#!/usr/bin/python3

#!/Author : Gibartes

from moduleInterface.defines   import *
from moduleInterface.interface import ModuleComponentInterface
from structureReader import structureReader as sr
from collections     import OrderedDict
import os,sys,platform

class MP4Structure(object):
    def __init__(self):
        # TAG
        self.Header      = OrderedDict({
            "size"       : [ 0, 4,None],  # HeaderSize
            "type"       : [ 4, 4,None],  # Type
            "subtype"    : [ 8, 4,None],  # Subtype
        })
        self.Chunk      = OrderedDict({
            "size"       : [ 0, 4,None],
            "flag"       : [ 8, 4,None],
            "type"       : [12, 4,None],
        })

        self.Types      = (
            "ftyp","mdat","moov","pnot",
            "udta","uuid","moof","free",
            "skip","jP2 ","wide","load",
            "ctab","imap","matt","kmat",
            "clip","crgn","sync","chap",
            "tmcd","scpt","ssrc","PICT",
            "mvhd"
        )

        self.hxedTypes = self.__convert(self.Types)
        self.hxedTypes.append(0x605ffff)

    def __convert(self,list):
        temp = []
        for i in list:
            temp.append(MP4Structure.str2ascii(i))
        return temp

    @staticmethod
    def str2ascii(string):
        code   = 0
        length = len(string)-1
        for i,v in enumerate(string):
            code+=ord(v)
            if(i<length):code<<=8
        return code

class ModuleMP4(ModuleComponentInterface):

    def __init__(self):
        super().__init__()                  # Initialize Module Interface
        self.fileSize   = 0
        self.offset     = list()
        self.missing    = 0
        self.parser     = sr.StructureReader()
        self.structure  = MP4Structure()

        self.set_attrib(ModuleConstant.NAME,"mp4")
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
        current = offset

        if(last==0):
            last= self.parser.bgoto(0,os.SEEK_END)       

        self.parser.bgoto(offset,os.SEEK_SET)
        self.parser.bexecute(self.structure.Header,'int',0,os.SEEK_CUR)
        if(self.parser.get_value("size")==0):
            self.parser.cleanup()
            return
        self.parser.bgoto(-self.parser.get_size()+self.parser.get_value("size"))
        
        while(current<last):
            self.parser.bexecute(self.structure.Chunk,'int',0,os.SEEK_CUR)
            if(self.parser.get_value("size")==0):
                break

            if(self.parser.get_value("type") not in self.structure.hxedTypes):
                break
            
            self.parser.bgoto(-self.parser.get_size()+self.parser.get_value("size"))
            current = self.parser.btell()
        
        self.offset.append((self.get_attrib(ModuleConstant.IMAGE_BASE),current-offset,ModuleConstant.FILE_RECORD))
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

    MP4 = ModuleMP4()
    try:
        MP4.set_attrib(ModuleConstant.FILE_ATTRIBUTE,sys.argv[1])   # Insert MFT File
    except:
        print("This moudule needs exactly one parameter.")
        sys.exit(1)

    MP4.set_attrib(ModuleConstant.IMAGE_BASE,0)  # Set offset of the file base
    cret = MP4.execute()
    print(cret)
    print(len(cret))
    sys.exit(0)
