#-*- coding: utf-8 -*-
#!/usr/bin/python3

#!/Author : Gibartes

from moduleInterface.defines   import *
from moduleInterface.interface import ModuleComponentInterface
from structureReader import structureReader as sr
from collections     import OrderedDict
import os,sys,platform


class EGGStructure(object):
    SIGNATURE     = b'\x45\x47\x47\x41'

    FILEHEADER    = b'\xE3\x90\x85\x0A'
    FILENAMEHEADER= b'\xAC\x91\x85\x0A'
    BLOCKHEADER   = b'\x13\x0C\xB5\x02'

    DUMMYHEADER   = b'\x07\x33\x46\x07'
    COMMENTHEADER = b'\x72\x36\xC6\x04'
    ENCRYPTHEADER = b'\x0F\x47\xD1\x08'
    ENDFILEHEADER = b'\x22\x82\xE2\x08'

    SIGLIST = [
        SIGNATURE,      # Support
        FILEHEADER,     # Support
        BLOCKHEADER,    # Support
        DUMMYHEADER, 
        COMMENTHEADER,
        ENCRYPTHEADER, 
        FILENAMEHEADER, # Support
        ENDFILEHEADER,  # Support
    ]

    def __init__(self):
        self.metaheader     = sr.CStructure()
        self.fileheader     = sr.CStructure()
        self.filenameheader = sr.CStructure()
        self.blockheader    = sr.CStructure()

        self.metaheader.build(['signature','version','id','reserved','end'],[4,2,4,4,4])
        self.fileheader.build(['signature','reserved','length'],[4,4,8])    # Compressed Filesize
        self.filenameheader.build(['signature','flag','length'],[4,1,2])    # Namelength
        self.blockheader.build(['signature','hi_len_1','len_1','len_2','crc','end'],[4,2,4,4,4,4])
        
        self.EGGHDRLIST = {
            EGGStructure.SIGNATURE:self.metaheader,
            EGGStructure.FILEHEADER:self.fileheader,
            EGGStructure.FILENAMEHEADER:self.filenameheader,
            EGGStructure.BLOCKHEADER:self.blockheader
            #EGGStructure.ENCRYPTHEADER:self.encryptheader
        }


class ModuleEGG(ModuleComponentInterface):

    def __init__(self):
        super().__init__()                  # Initialize Module Interface
        self.fileSize   = 0
        self.offset     = list()
        self.missing    = 0
        self.parser     = sr.StructureReader()
        self.structure  = EGGStructure()

        self.set_attrib(ModuleConstant.NAME,"EGG")
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

        self.parser.bexecute(self.structure.metaheader.data,'byte',offset,os.SEEK_SET,'big')
        if(self.parser.get_value('signature')!=EGGStructure.SIGNATURE or 
           self.parser.get_value('end')!=EGGStructure.ENDFILEHEADER):
            self.parser.cleanup()
            return
        
        cursor  = self.parser.btell()
        jump    = 0
        _length = 0

        while(cursor<last):
            sig = self.parser.bread_raw(0,4)

            if(sig==EGGStructure.ENDFILEHEADER):
                _length = self.parser.btell()-offset
                break

            htype = self.structure.EGGHDRLIST.get(sig)
            if htype!=None:
                self.parser.bgoto(-4)
                self.parser.bexecute(htype.data,'byte',0,os.SEEK_CUR,'big')
                if(sig==EGGStructure.FILEHEADER):
                    jump    = self.parser.byte2int(self.parser.get_value('length'))
                    if(jump==0):
                        break
                elif(sig==EGGStructure.FILENAMEHEADER):
                    namelen = self.parser.byte2int(self.parser.get_value('length'))
                    self.parser.bgoto(namelen+0x10)
                    _sig = self.parser.bread_raw(0,4)
                    if(_sig!=EGGStructure.ENDFILEHEADER):
                        self.parser.bgoto(-4)
                        break
                elif(sig==EGGStructure.BLOCKHEADER):
                    self.parser.bgoto(jump)
                    jump = 0

            cursor = self.parser.btell()

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

    EGG = ModuleEGG()
    try:
        EGG.set_attrib(ModuleConstant.FILE_ATTRIBUTE,sys.argv[1])   # Insert MFT File
    except:
        print("This moudule needs exactly one parameter.")
        sys.exit(1)

    EGG.set_attrib(ModuleConstant.IMAGE_BASE,0)  # Set offset of the file base
    cret = EGG.execute()
    print(cret)
    print(len(cret))
    sys.exit(0)
