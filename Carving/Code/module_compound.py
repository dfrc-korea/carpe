#-*- coding: utf-8 -*-
import os, sys, struct

from defines import ModuleConstant
from interface       import ModuleComponentInterface


class ModuleCOMPOUND(ModuleComponentInterface):
    CONST_KILOBYTE = 1024
    CONST_MEGABYTE = 1048576
    CONST_GIGABYTE = 1073741824

    CONST_RAMSLACK_COMP_UNIT = 2
    CONST_COMPOUND_MAX = 50*CONST_MEGABYTE
    CONST_SEARCH_SIZE = 200*CONST_MEGABYTE
    CONST_BIG_SEARCH_SIZE = 200*CONST_MEGABYTE

    uClusterSize = 0x1000

    def __init__(self):
        super().__init__()                  # Initialize Module Interface
        self.fileSize   = 0
        self.offset     = list()

        self.set_attrib(ModuleConstant.NAME,"COMPOUND")
        self.set_attrib(ModuleConstant.VERSION,"0.1")
        self.set_attrib(ModuleConstant.AUTHOR,"JH")

        self.fp = None


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

        i = 0
        j = 0
        k = 0
        nRead = b''
        pvBuffer = 0
        bVerified = False
        bNameAlloc = False
        uMaxBat = 0
        propCount = 0
        propOffset = 0
        idxTitle = 0
        szTitle = 0
        lenTemp = 0
        strTemp = ""
        strTemp2 = ""
        lpszFileName = ""
        temp = 0
        uFirstXBatID = 0
        puBatTable = b''
        puRootEntry = 0
        puBat = b''
        puSBat = 0
        pSummaryInformation = 0
        uDirEntrySize = 0
        pPropSbat = 0
        pPropSum = 0
        pOleHeader = {}
        qwDataSize = 0

        sigSummary = b'\x05\x53\x75\x6D\x6D\x61\x72\x79' # |Summary
        sigDOC = b'\x57\x6F\x72\x64\x44\x6F\x63\x75'     # WordDocu
        sigPPT = b'\x50\x6F\x77\x65\x72\x50\x6F\x69'     # PowerPoi
        sigXLS = b'\x57\x6F\x72\x6B\x62\x6F\x6F\x6B'     # Workbook
        sigXLS2 = b'\x42\x6F\x6F\x6B'                    # Book

        pvBuffer = self.fp.read(0x1000)


        pOleHeader['uFileType'] = pvBuffer[0x00:0x08]
        pOleHeader['uMinorVersion'] = pvBuffer[0x18:0x1A]
        pOleHeader['uDllVersion'] = pvBuffer[0x1A:0x1C]
        pOleHeader['uByteOrder'] = pvBuffer[0x1C:0x1E]
        pOleHeader['uLogToBigBlockSize'] = struct.unpack('<h', pvBuffer[0x1E:0x20])[0]
        pOleHeader['uLogToSmallBlockSize'] = struct.unpack('<h', pvBuffer[0x20:0x22])[0]
        pOleHeader['uBatCount'] = struct.unpack('<I', pvBuffer[0x2C:0x30])[0]
        pOleHeader['idxPropertyTable'] = pvBuffer[0x30:0x34]
        pOleHeader['uSmallBlockCutOff'] = pvBuffer[0x38:0x3C]
        pOleHeader['idxSbat'] = struct.unpack('<I', pvBuffer[0x3C:0x40])[0]
        pOleHeader['uSbatBlockCount'] = pvBuffer[0x40:0x44]
        pOleHeader['idxXbat'] = struct.unpack('<I', pvBuffer[0x44:0x48])[0]
        pOleHeader['uXbatCount'] = struct.unpack('<I', pvBuffer[0x48:0x4C])[0]

        if pOleHeader['uByteOrder'] != b'\xFE\xFF' or pOleHeader['uLogToBigBlockSize'] != 9 or pOleHeader['uLogToSmallBlockSize'] != 6 or pOleHeader['uBatCount'] > 0xFFFFFF00:
            self.offset = (False, 0, -1, ModuleConstant.INVALID)
            return False


        # puBat =
        if pOleHeader['uXbatCount'] == 0:  # XBAT을 안쓰는 경우(작은 크기의 파일)
            puBatTable = pvBuffer[0x4C:0x4C + pOleHeader['uBatCount'] * 4]
        elif pOleHeader['uXbatCount'] > 0:

            # 1. Header에 있는 XBAT 복사
            puBatTable = pvBuffer[0x4C:0x4C + 109 * 4]

            # 2. XBAT의 수 만큼 loop
            uFirstXBatID = pOleHeader['idxXbat']

            i = 0
            j = 0
            while (i < pOleHeader['uXbatCount']):

                self.fp.seek((uFirstXBatID + 1) * 512)
                puBatTable += bytearray(self.fp.read(0x200))

                if puBatTable[109 * 4 + (i * 128) * 4 + 127 * 4: 109 + (i * 128) + 127 * 4 + 4] == b'\xFF\xFF\xFF\xFF' or puBatTable[109 * 4 + (i * 128) * 4 + 127 * 4: 109 + (i * 128) + 127 * 4 + 4] == b'\xFE\xFF\xFF\xFF':
                    break
                else:
                    uFirstXBatID = struct.unpack('<I', puBatTable[109 * 4 + (i * 128) * 4 - (j) * 4 + 127 * 4: 109 * 4 + (i * 128) * 4 - (j) * 4 + 127 * 4 + 4])[0]

                i += 1
                j += 1

        if puBatTable == b'' :
            self.offset = (False, 0, -1, ModuleConstant.INVALID)
            return False


        # MaxBat 계산산
        i = 0
        while i < pOleHeader['uBatCount']:
            temp = struct.unpack('<I', puBatTable[i * 4: (i + 1) * 4])[0]
            if uMaxBat < temp:
                uMaxBat = temp
            i += 1

        qwDataSize = uMaxBat  # 데이터의 크기 예측

        i = 0
        while i < pOleHeader['uBatCount']:
            temp = struct.unpack('<I', puBatTable[i * 4: (i + 1) * 4])[0]
            # 에러 처리
            if (temp > 0xFFFF0000):
                self.offset = (False, 0, -1, ModuleConstant.INVALID)
                return False

            self.fp.seek((temp + 1) * 512)
            nRead = bytearray(self.fp.read(512))
            puBat += nRead

            if len(nRead) != 512:
                self.offset = (False, 0, -1, ModuleConstant.INVALID)
                return False

            j = 0
            while j < 128:
                temp = struct.unpack('<I', puBat[i * 128 * 4 + j * 4: i * 128 * 4 + j * 4 + 4])[0]
                if temp == 0xFFFFFFFC or temp == 0xFFFFFFFD or temp == 0xFFFFFFFE or temp == 0xFFFFFFFF:
                    j += 1
                    continue
                if pOleHeader['uBatCount'] * 128 <= temp:
                    if(uMaxBat < 2048):
                        uMaxBat += 2048
                    else :
                        uMaxBat += 4096

                    qwDataSize = uMaxBat
                    break

                if qwDataSize < temp:
                    # qwDataSize = struct.unpac k('<Q', puBat[i*128*4 + j*4 : i*128*4 + j*4 + 8])[0]
                    qwDataSize = temp

                j += 1
            i += 1

        qwDataSize += 2
        qwDataSize *= 512

        if qwDataSize > self.CONST_COMPOUND_MAX:
            self.offset = (False, 0, -1, ModuleConstant.INVALID)
            return False

        self.offset = (True, self.attrib.get(ModuleConstant.IMAGE_BASE), qwDataSize, ModuleConstant.FILE_ONESHOT)
        return True




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
            return [(False,ret)]
        self.carve()
        if(self.offset==[]):
            return [(False,0,ModuleConstant.INVALID)]
        return self.offset                  # return <= 0 means error while collecting information


if __name__ == '__main__':

    file = ModuleCOMPOUND()
    try:
        file.set_attrib(ModuleConstant.FILE_ATTRIBUTE,sys.argv[1])   # Insert File
    except:
        print("This moudule needs exactly one parameter.")
        sys.exit(1)

    file.set_attrib(ModuleConstant.IMAGE_BASE,0)  # Set offset of the file base
    file.set_attrib(ModuleConstant.IMAGE_LAST, ModuleCOMPOUND.CONST_SEARCH_SIZE)  # Set offset of the file last
    cret = file.execute()
    print(cret)

    sys.exit(0)