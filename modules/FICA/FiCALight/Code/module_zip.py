# -*- coding: utf-8 -*-
import os, sys, struct

from moduleInterface.defines   import *
from moduleInterface.interface import ModuleComponentInterface

docx    = b'\x77\x6F\x72\x64\x2F\x64\x6F\x63\x75\x6D\x65\x6E\x74\x2E\x78\x6D\x6C'
pptx    = b'\x70\x70\x74\x2F\x70\x72\x65\x73\x65\x6E\x74\x61\x74\x69\x6F\x6E'
xlsx    = b'\x78\x6C\x2F\x77\x6F\x72\x6B\x62\x6F\x6F\x6B\x2E\x78\x6D\x6C'
ooxml   = {'docx':docx,'pptx':pptx,'xlsx':xlsx}

class ModuleZIP(ModuleComponentInterface):
    CONST_KILOBYTE = 1024
    CONST_MEGABYTE = 1048576
    CONST_GIGABYTE = 1073741824

    CONST_RAMSLACK_COMP_UNIT = 2
    CONST_COMPOUND_MAX = 50 * CONST_MEGABYTE
    CONST_SEARCH_SIZE = 200 * CONST_MEGABYTE
    CONST_BIG_SEARCH_SIZE = 200 * CONST_MEGABYTE

    uClusterSize = 0x1000

    def __init__(self):
        super().__init__()  # Initialize Module Interface
        self.fileSize = 0
        self.offset   = list()
        self.flag     = None

        self.set_attrib(ModuleConstant.NAME, "OOXML")
        self.set_attrib(ModuleConstant.VERSION, "0.2")
        self.set_attrib(ModuleConstant.AUTHOR, "JH,GM")
        self.set_attrib("detailed_type",True)
        
        self.fp = None
        self.off_t           = Offset_Info()
        self.off_t.name      = "zip"    # alias
        self.off_t.signature = "zip"    # signature in C_defy.SIGNATURE

    def __reinit__(self):
        self.fileSize   = 0
        self.offset     = list()
        self.missing    = 0
        self.off_t.clear() 

    """ Module Methods """

    def __evaluate(self):
        fn = self.attrib.get(ModuleConstant.FILE_ATTRIBUTE)
        if (fn == None):
            return ModuleConstant.Return.EINVAL_ATTRIBUTE
        try:
            fd = os.open(fn, os.O_RDONLY)
            os.close(fd)
        except:
            return ModuleConstant.Return.EINVAL_FILE
        return ModuleConstant.Return.SUCCESS

    def carve(self):
        self.fp = open(self.get_attrib(ModuleConstant.FILE_ATTRIBUTE), 'rb')
        self.fp.seek(self.get_attrib(ModuleConstant.IMAGE_BASE), os.SEEK_SET)
        i = 0
        totalfilesize = 0

        while (i <= self.get_attrib(ModuleConstant.IMAGE_LAST) - self.get_attrib(ModuleConstant.IMAGE_BASE)):  # 100MB
            self.fp.seek(self.get_attrib(ModuleConstant.IMAGE_BASE) + i, os.SEEK_SET)
            temp = self.fp.read(0x40)
            self.fp.seek(self.get_attrib(ModuleConstant.IMAGE_BASE) + i, os.SEEK_SET)

            if (temp[0:2] != b'PK'):
                # if(temp[0:2] != b'\x50\x4B'):
                self.offset = (False, 0, -1, Offset_Info.NONE)
                return False
            # 사이즈 나눠야함, 시그니처 별로.
            # 파일 사이즈 다음에 0x04034b50이 있으면 압축된 파일 더 있음
            if (temp[0:2] == b'\x50\x4B' and temp[2:4] == b'\x03\x04'):
                temp = self.fp.read(0x1E)
                zipheader_comsize = struct.unpack('<I', temp[0x12:0x16])[0]
                zipheader_namelength = struct.unpack('<H', temp[0x1A:0x1C])[0]
                zipheader_extralength = struct.unpack('<H', temp[0x1C:0x1E])[0]

                filesize = 0x1E + zipheader_namelength + zipheader_extralength + zipheader_comsize  # 0x1D is header size
                totalfilesize += filesize
                i = totalfilesize
                continue
            # 중심 디렉토리인 경우
            elif (temp[0:2] == b'\x50\x4B' and temp[2:4] == b'\x01\x02'):
                temp = self.fp.read(0x2E)
                zipcentral_namelength = struct.unpack('<H', temp[0x1C:0x1E])[0]
                zipcentral_extralength = struct.unpack('<H', temp[0x1E:0x20])[0]
                zipcentral_commentlength = struct.unpack('<H', temp[0x20:0x22])[0]

                filesize = 0x2E + zipcentral_namelength + zipcentral_extralength + zipcentral_commentlength  # 0x2E is header size
                totalfilesize += filesize
                i = totalfilesize
                continue
            # Digital signature인 경우
            elif (temp[0:2] == b'\x50\x4B' and temp[2:4] == b'\x05\x05'):
                temp = self.fp.read(0x06)
                zipdigitalsignature_datasize = struct.unpack('<H', temp[0x04:0x06])[0]

                filesize = 0x06 + zipdigitalsignature_datasize
                totalfilesize += filesize
                i = totalfilesize
                continue
            # Zip64 end of Central directory record인 경우0x06064b50
            elif (temp[0:2] == b'\x50\x4B' and temp[2:4] == b'\x06\x06'):
                temp = self.fp.read(0x38)
                zip64cdr_sizezip64 = struct.unpack('<Q', temp[0x04:0x0C])[0]

                filesize = 0x38 + zip64cdr_sizezip64
                totalfilesize += filesize
                i = totalfilesize
                continue
            # Zip64 end of Central directory locator인 경우0x07064b50
            elif (temp[0:2] == b'\x50\x4B' and temp[2:4] == b'\x06\x07'):
                filesize = 0x14  # 0x14 is header size
                totalfilesize += filesize
                i = totalfilesize
                continue
            # End of central directory record인 경우 0x06054b50
            elif (temp[0:2] == b'\x50\x4B' and temp[2:4] == b'\x05\x06'):
                filesize = 0x16
                totalfilesize += filesize
                i = totalfilesize
                self.offset = (
                True, self.attrib.get(ModuleConstant.IMAGE_BASE), totalfilesize, Offset_Info.VALID|Offset_Info.UNIT)  # Success
                return True
            else:
                self.offset = (
                True, self.attrib.get(ModuleConstant.IMAGE_BASE), totalfilesize, Offset_Info.VALID|Offset_Info.UNIT)  # Success
                return True

            self.offset = (False, 0, -1, Offset_Info.NONE)  # Fail
            return False

    """ Interfaces """

    def module_open(self, id):  # Reserved method for multiprocessing
        super().module_open()

    def module_close(self):  # Reserved method for multiprocessing
        pass

    def set_attrib(self, key, value):  # 모듈 호출자가 모듈 속성 변경/추가하는 method interface
        self.update_attrib(key, value)

    def get_attrib(self, key, value=None):  # 모듈 호출자가 모듈 속성 획득하는 method interface
        return self.attrib.get(key)

    def execute(self, cmd=None, option=None):  # 모듈 호출자가 모듈을 실행하는 method
        self.__reinit__()
        if(cmd=='inspect'):
            return self.flag
        else:
            self.flag = None
            ret = self.__evaluate()
            if (ret != ModuleConstant.Return.SUCCESS):
                self.offset = (False, ret, -1 , Offset_Info.NONE)
                return False
            self.carve()
            
            if (self.offset==[]):
                self.fp.close()
                self.offset = (False, 0, -1, Offset_Info.NONE)
                return False

            lastPtr = self.offset[2]

            if (lastPtr<=0):
                self.fp.close()
                self.offset = (False, 0, -1, Offset_Info.NONE)
                return False
          
            self.fp.seek(self.get_attrib(ModuleConstant.IMAGE_BASE), os.SEEK_SET)
            bcursor = 0
            flag    = False
                        
            while(bcursor<lastPtr):
                buffer = self.fp.read(1024)
                if(buffer==None or buffer==b''):
                    break
                for k,v in ooxml.items():
                    if v in buffer:
                        self.flag = k
                        self.off_t.flag = ".."+os.sep+"document"+os.sep+"OOXML"
                        flag = True
                        break
                if(flag):break
                bcursor+=1024
            if(flag==False):
                self.flag = "zip"
            self.fp.close()
            self.off_t.name = self.flag
            self.off_t.append(self.offset[1],self.offset[1]+self.offset[2],self.offset[3])
            return self.off_t  # return <= 0 means error while collecting information


if __name__ == '__main__':

    file = ModuleZIP()
    try:
        file.set_attrib(ModuleConstant.FILE_ATTRIBUTE, sys.argv[1])  # Insert File
    except:
        print("This moudule needs exactly one parameter.")
        sys.exit(1)

    file.set_attrib(ModuleConstant.IMAGE_BASE, 0)  # Set offset of the file base
    file.set_attrib(ModuleConstant.IMAGE_LAST, ModuleZIP.CONST_SEARCH_SIZE)  # Set offset of the file last
    cret = file.execute()
    print(cret)

    sys.exit(0)