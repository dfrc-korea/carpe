#-*- coding: utf-8 -*-
import os, sys, struct

from moduleInterface.defines   import *
from moduleInterface.interface import ModuleComponentInterface


class ModuleAVI(ModuleComponentInterface):
    CONST_KILOBYTE = 1024
    CONST_MEGABYTE = 1048576
    CONST_GIGABYTE = 1073741824

    CONST_RAMSLACK_COMP_UNIT = 2
    CONST_COMPOUND_MAX = 50*CONST_MEGABYTE
    CONST_SEARCH_SIZE = 20*CONST_MEGABYTE
    CONST_BIG_SEARCH_SIZE = 200*CONST_MEGABYTE

    uClusterSize = 0x1000

    def __init__(self):
        super().__init__()                  # Initialize Module Interface
        self.fileSize   = 0
        self.offset     = list()

        self.set_attrib(ModuleConstant.NAME,"AVI")
        self.set_attrib(ModuleConstant.VERSION,"0.2")
        self.set_attrib(ModuleConstant.AUTHOR,"JH,GM")

        self.fp = None
        self.off_t           = Offset_Info()
        self.off_t.name      = "avi"    # alias
        self.off_t.signature = "riff"    # signature in C_defy.SIGNATURE

    def __reinit__(self):
        self.fileSize   = 0
        self.offset     = list()
        self.missing    = 0
        self.off_t.clear()

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
        self.fp = open(self.get_attrib(ModuleConstant.FILE_ATTRIBUTE), 'rb')
        self.fp.seek(self.get_attrib(ModuleConstant.IMAGE_BASE),os.SEEK_SET)

        riff = self.fp.read(0x0C)
        riff_filesize = struct.unpack('<I', riff[4:8])[0]       # 전체 사이즈를 확인하기 위한 헤더
        uFileSize = riff_filesize + 0x08                        # RIFF 헤더를 포함한 전체 크기
        uDecSize = uFileSize

        uAddRead = 0
        uMove = 0
        uRealSize = 0
        pReader = 0
        puChunkSize = 0
        bHDRL = False
        bMOVI = False
        bIDX1 = False
        bEND = False

        self.fp.seek(self.get_attrib(ModuleConstant.IMAGE_BASE),os.SEEK_SET)
        while uDecSize > 0 :
            temp = self.fp.read(self.uClusterSize)
            uCluSize = self.uClusterSize
            pReader += uAddRead         # 버퍼 내 시작 Offset 설정
            uMove += uAddRead           # 움직인 Offset 저장

            if uDecSize == uFileSize:
                pReader += 0x0C             # RIFFHEADER 크기만큼 점프
                uMove += 0x0C               # RIFFHEADER 크기 만큼 이동한 Offset 저장
                uRealSize += 0x0C           # 추출할 실제 사이즈

            while uCluSize > 0 :            # 버퍼가 남아있을 때 까지

                if temp[pReader:pReader+4] == b'\x4C\x49\x53\x54' :     # "LIST"
                    if temp[pReader + 2*4 : pReader + 2*4 + 4] == b'\x6D\x6F\x76\x69':      # "movi"
                        bMOVI = True
                    elif temp[pReader + 2*4 : pReader + 2*4 + 4] == b'\x68\x64\x72\x6C':      # "hdrl"
                        bHDRL = True
                    puChunkSize = pReader + 4               # 이동할 Chunk size 저장
                    pReader += 8                            # read 포인터 이동
                    uMove = puChunkSize + 2 * 4             # 이동한 Offset 저장
                    uRealSize += puChunkSize + 2 * 4        # 추출할 실제 사이즈

                elif temp[pReader:pReader+4] == b'\x4A\x55\x4E\x4B' :     # "JUNK"
                    puChunkSize = pReader + 4               # 이동할 Chunk size 저장
                    pReader += 8                            # read 포인터 이동
                    uMove = puChunkSize + 2 * 4             # 이동한 Offset 저장
                    uRealSize += puChunkSize + 2 * 4        # 추출할 실제 사이즈

                elif temp[pReader:pReader+4] == b'\x69\x64\x78\x31':
                    bIDX1 = True
                    bEND = True
                    puChunkSize = pReader + 4               # 이동할 Chunk size 저장
                    uRealSize = puChunkSize + 2 * 4         # 추출할 실제 사이즈
                    break
                else:
                    bEND = True
                    break

                if uCluSize <= uMove:
                    uAddRead = uMove - uCluSize
                    pReader += (uCluSize - (2 * 4))          # 2 * long size
                    uCluSize = 0
                    uMove = 0
                else:
                    uCluSize -= uMove
                    pReader += puChunkSize
                    uMove = 0

            if bEND == True :
                break

            if self.uClusterSize > uDecSize:
                break
            else:
                i = 0
                j = 0

                if uAddRead > self.uClusterSize:
                    i = uAddRead % self.uClusterSize
                    j = (uAddRead - i) / self.uClusterSize
                    uAddRead = i

                if j > 0:
                    uDecSize -= self.uClusterSize * j
                else:
                    uDecSize -= self.uClusterSize

        if uDecSize < self.attrib.get(ModuleConstant.IMAGE_LAST) - self.attrib.get(ModuleConstant.IMAGE_BASE):
            self.offset = (True, self.attrib.get(ModuleConstant.IMAGE_BASE), uDecSize, Offset_Info.VALID|Offset_Info.UNIT)
            self.off_t.append(self.offset[1],self.offset[1]+self.offset[2],self.offset[3])
        else:
            self.offset = (False, 0, -1, Offset_Info.NONE)





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
        self.__reinit__()
        ret = self.__evaluate()
        if(ret!=ModuleConstant.Return.SUCCESS):
            return None
        self.carve()
        return self.off_t                 # return <= 0 means error while collecting information


if __name__ == '__main__':

    file = ModuleAVI()
    try:
        file.set_attrib(ModuleConstant.FILE_ATTRIBUTE,sys.argv[1])   # Insert File
    except:
        print("This moudule needs exactly one parameter.")
        sys.exit(1)

    file.set_attrib(ModuleConstant.IMAGE_BASE,0)  # Set offset of the file base
    file.set_attrib(ModuleConstant.IMAGE_LAST, ModuleAVI.CONST_SEARCH_SIZE)  # Set offset of the file last
    cret = file.execute()
    print(cret)

    sys.exit(0)