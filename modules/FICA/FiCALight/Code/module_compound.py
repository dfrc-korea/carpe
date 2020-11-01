#-*- coding: utf-8 -*-
import os, sys, struct

from moduleInterface.defines   import *
from moduleInterface.interface import ModuleComponentInterface

doc     = b'\x57\x00\x6F\x00\x72\x00\x64\x00\x44\x00\x6F\x00\x63\x00\x75\x00\x6D\x00\x65\x00\x6E\x00\x74\x00'
ppt     = b'\x50\x00\x6F\x00\x77\x00\x65\x00\x72\x00\x50\x00\x6F\x00\x69\x00\x6E\x00\x74\x00\x20\x00\x44\x00\x6F\x00\x63\x00\x75\x00\x6D\x00\x65\x00\x6E\x00\x74\x00'
xls     = b'\x57\x00\x6F\x00\x72\x00\x6B\x00\x62\x00\x6F\x00\x6F\x00\x6B\x00'
hwp     = b'\x48\x00\x77\x00\x70\x00\x53\x00\x75\x00\x6D\x00\x6D\x00\x61\x00\x72\x00\x79\x00\x49\x00\x6E\x00\x66\x00\x6F\x00\x72\x00\x6D\x00\x61\x00\x74\x00\x69\x00\x6F\x00\x6E\x00'
rootentry = b'\x52\x00\x6F\x00\x6F\x00\x74\x00\x20\x00\x45\x00\x6E\x00\x74\x00\x72\x00\x79\x00'

compound = {'doc':doc,'ppt':ppt,'xls':xls,'hwp':hwp}

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
        self.flag     = None

        self.set_attrib(ModuleConstant.NAME,"COMPOUND")
        self.set_attrib(ModuleConstant.VERSION,"0.2.1")
        self.set_attrib(ModuleConstant.AUTHOR,"JH,GM,HK")
        self.set_attrib("detailed_type",True)

        self.fp = None

        self.off_t           = Offset_Info()
        self.off_t.name      = "compound"    # alias
        self.off_t.signature = "compound"    # signature in C_defy.SIGNATURE
        
    """ Module Methods """
    def __reinit__(self):
        self.fileSize   = 0
        self.offset     = list()
        self.missing    = 0
        self.off_t.clear()
        self.RootEntryPos = 0

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
        self.fp = open(self.get_attrib(ModuleConstant.FILE_ATTRIBUTE), 'rb')
        self.fp.seek(self.get_attrib(ModuleConstant.IMAGE_BASE),os.SEEK_SET)
        base    = self.get_attrib(ModuleConstant.IMAGE_BASE)
        
        i = 0
        j = 0
        nRead = b''
        pvBuffer = 0
        uMaxBat = 0
        temp = 0
        uFirstXBatID = 0
        puBatTable = b''
        puBat = b''
        pOleHeader = {}
        qwDataSize = 0
        pvBuffer = self.fp.read(0x1000)

        pOleHeader['uFileType'] = pvBuffer[0x00:0x08]
        pOleHeader['uMinorVersion'] = pvBuffer[0x18:0x1A]
        pOleHeader['uDllVersion'] = pvBuffer[0x1A:0x1C]
        pOleHeader['uByteOrder'] = pvBuffer[0x1C:0x1E]
        pOleHeader['uLogToBigBlockSize'] = struct.unpack('<h', pvBuffer[0x1E:0x20])[0]
        pOleHeader['uLogToSmallBlockSize'] = struct.unpack('<h', pvBuffer[0x20:0x22])[0]
        pOleHeader['uBatCount'] = struct.unpack('<I', pvBuffer[0x2C:0x30])[0]
        pOleHeader['idxPropertyTable'] = struct.unpack('<I', pvBuffer[0x30:0x34])[0]
        pOleHeader['uSmallBlockCutOff'] = pvBuffer[0x38:0x3C]
        pOleHeader['idxSbat'] = struct.unpack('<I', pvBuffer[0x3C:0x40])[0]
        pOleHeader['uSbatBlockCount'] = pvBuffer[0x40:0x44]
        pOleHeader['idxXbat'] = struct.unpack('<I', pvBuffer[0x44:0x48])[0]
        pOleHeader['uXbatCount'] = struct.unpack('<I', pvBuffer[0x48:0x4C])[0]

        if pOleHeader['uByteOrder'] != b'\xFE\xFF' or pOleHeader['uLogToBigBlockSize'] != 9 or pOleHeader['uLogToSmallBlockSize'] != 6 or pOleHeader['uBatCount'] > 0xFFFFFF00:
            self.offset = (False, 0, -1, Offset_Info.NONE)
            return False

        # RootEntry&idxPropertyTable Check
        self.fp.seek(self.attrib.get(ModuleConstant.IMAGE_BASE)+pOleHeader['idxPropertyTable']*0x200+0x200,os.SEEK_SET)
        self.RootEntryPos = self.fp.tell()
        RootEntrybuf = bytearray(self.fp.read(512))
        if RootEntrybuf[0:0x14] != rootentry :
            self.offset = (False, 0, -1, Offset_Info.NONE)
            return False
        __RootEntryPos = struct.unpack('<I', RootEntrybuf[0x74:0x78])[0]

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
            self.offset = (False, 0, -1, Offset_Info.NONE)
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
                self.offset = (False, 0, -1, Offset_Info.NONE)
                return False

            self.fp.seek(base+((temp + 1) * 512),os.SEEK_SET)
            nRead = bytearray(self.fp.read(512))
            puBat += nRead
            #puBat += nRead

            if len(nRead) != 512:
                self.offset = (False, 0, -1, Offset_Info.NONE)
                return False

            j = 0
            while j < 128:
                temp = struct.unpack('<I', puBat[i * 128 * 4 + j * 4: i * 128 * 4 + j * 4 + 4])[0]
                if temp == 0xFFFFFFFC or temp == 0xFFFFFFFD or temp == 0xFFFFFFFE or temp == 0xFFFFFFFF:
                    j += 1
                    continue
                if qwDataSize < temp:
                    # qwDataSize = struct.unpac k('<Q', puBat[i*128*4 + j*4 : i*128*4 + j*4 + 8])[0]
                    qwDataSize = temp
                j += 1
            i += 1

        # Rootentry FAT number check
        if __RootEntryPos not in (0xFFFFFFFC,0xFFFFFFFD,0xFFFFFFFE,0xFFFFFFFF):
            if qwDataSize < __RootEntryPos:
                qwDataSize = __RootEntryPos
        if qwDataSize < pOleHeader['idxPropertyTable']:
            qwDataSize = pOleHeader['idxPropertyTable']
        qwDataSize += 2
        qwDataSize *= 512

        if qwDataSize > self.CONST_COMPOUND_MAX:
            self.offset = (False, 0, -1, Offset_Info.NONE)
            return False

        self.offset = (True, self.attrib.get(ModuleConstant.IMAGE_BASE), qwDataSize, Offset_Info.VALID|Offset_Info.UNIT)
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
        if(cmd=='inspect'):
            return self.flag
        else:
            self.flag = None
            ret = self.__evaluate()
            if(ret!=ModuleConstant.Return.SUCCESS):
                return None

            self.carve()

            if(self.offset==[]):
                self.fp.close()
                return None

            lastPtr = self.offset[2]

            if (lastPtr<=0):
                self.fp.close()
                return None
          
            self.fp.seek(self.RootEntryPos, os.SEEK_SET)
            bcursor = 0
            flag    = False

            if(flag==False):
                self.fp.seek(self.get_attrib(ModuleConstant.IMAGE_BASE), os.SEEK_SET)
                bcursor = 0
                flag    = False
                while(bcursor<lastPtr):
                    buffer = self.fp.read(1024)
                    if(buffer==None or buffer==b''):
                        break
                    for k,v in compound.items():
                        if v in buffer:
                            self.flag = k
                            flag = True
                            break
                    if(flag):break
                    bcursor+=1024
                if(flag==False):
                    self.off_t.flag = "etc"
                    self.flag = "compound"
            self.off_t.name = self.flag
            self.off_t.append(self.offset[1],self.offset[1]+self.offset[2],self.offset[3])
            self.fp.close()
            return self.off_t

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