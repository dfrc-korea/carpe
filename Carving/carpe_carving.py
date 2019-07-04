import os
import struct


class Carving:
    CONST_KILOBYTE = 1024
    CONST_MEGABYTE = 1048576
    CONST_GIGABYTE = 1073741824

    CONST_RAMSLACK_COMP_UNIT = 2
    CONST_COMPOUND_MAX = 50*CONST_MEGABYTE
    CONST_SEARCH_SIZE = 20*CONST_MEGABYTE
    CONST_BIG_SEARCH_SIZE = 200*CONST_MEGABYTE

    CONST_BM_MAXCHAR = 256
    CONST_BM_MAXPATLEN = 8
    CONST_ELEC_WRITE_UNIT = 512
    CONST_ELEC_READ_UNIT = 512

    uClusterSize = 4096
    fp = None

    def __init__(self, filePath):
        if (os.path.exists(filePath)):
            self.fp = open(filePath, 'rb')
        else:
            print("Not exist file.")
            exit(0)

    def signature(self, current_offset, sig_FOOTER):
        search_range = int(self.CONST_SEARCH_SIZE / (self.uClusterSize * 1))  # 1 => sizeof(UCHAR)

        for i in range(0, search_range):
            self.fp.seek(current_offset + i * self.uClusterSize)
            temp = self.fp.read(self.uClusterSize)

            sOffset = temp.find(sig_FOOTER)

            if sOffset > 0:
                qwDataSize = i * self.uClusterSize + sOffset
                return qwDataSize

        if sOffset == -1 :
            return -1

    def carve_jfif(self, current_offset, next_offset):
        sigJFIF_FOOTER = b'\xFF\xD9'
        fileSize = self.signature(current_offset, sigJFIF_FOOTER)

        if fileSize > 0 :
            print("Find!!", hex(fileSize))  # 시작부터 self.uClusterSize + sOffset 여기까지 긁어와서 저장. 그러면 정상.
        else:
            print("not Found")  # 현재 offset에서 next_offset까지.

    def carve_exif(self, current_offset, next_offset):
        sigEXIF_FOOTER = b'\xFF\xD9'
        fileSize = self.signature(current_offset, sigEXIF_FOOTER)

        if fileSize > 0 :
            print("Find!!", hex(fileSize))  # 시작부터 self.uClusterSize + sOffset 여기까지 긁어와서 저장. 그러면 정상.
        else:
            print("not Found")  # 현재 offset에서 next_offset까지.

    def carve_gif(self, current_offset, next_offset):
        sigGIF_FOOTER = b'\x00\x3B'
        fileSize = self.signature(current_offset, sigGIF_FOOTER)

        if fileSize > 0 :
            print("Find!!", hex(fileSize))  # 시작부터 self.uClusterSize + sOffset 여기까지 긁어와서 저장. 그러면 정상.
        else:
            print("not Found")  # 현재 offset에서 next_offset까지.

    def carve_png(self, current_offset, next_offset):
        sigPNG_FOOTER = b'\x49\x45\x4E\x44\xAE\x42\x60\x82'
        fileSize = self.signature(current_offset, sigPNG_FOOTER)

        if fileSize > 0 :
            print("Find!!", hex(fileSize))  # 시작부터 self.uClusterSize + sOffset 여기까지 긁어와서 저장. 그러면 정상.
        else:
            print("not Found")  # 현재 offset에서 next_offset까지.

    def carve_pdf(self, current_offset, next_offset):
        sigPDF_FOOTER = b'\x25\x25\x45\x4F\x46'
        fileSize = self.signature(current_offset, sigPDF_FOOTER)

        if fileSize > 0 :
            print("Find!!", hex(fileSize))  # 시작부터 self.uClusterSize + sOffset 여기까지 긁어와서 저장. 그러면 정상.
        else:
            print("not Found")  # 현재 offset에서 next_offset까지.

    def carve_zip(self, current_offset, next_offset):
        i = 0
        totalfilesize = 0

        while( i <= 0x6400000 ) :                # 100MB
            self.fp.seek(i)
            temp = self.fp.read(0x40)
            self.fp.seek(i)
            if(temp[0:2] != b'\x50\x4B'):
                return False
            # 사이즈 나눠야함, 시그니처 별로.
            # 파일 사이즈 다음에 0x04034b50이 있으면 압축된 파일 더 있음
            if(temp[0:2] == b'\x50\x4B' and temp[2:4] == b'\x03\x04'):
                temp = self.fp.read(0x1E)
                zipheader_comsize = struct.unpack('<I', temp[0x12:0x16])[0]
                zipheader_namelength = struct.unpack('<H', temp[0x1A:0x1C])[0]
                zipheader_extralength = struct.unpack('<H', temp[0x1C:0x1E])[0]

                filesize = 0x1E + zipheader_namelength + zipheader_extralength + zipheader_comsize    # 0x1D is header size
                totalfilesize += filesize
                i = totalfilesize
                continue
            #중심 디렉토리인 경우
            elif (temp[0:2] == b'\x50\x4B' and temp[2:4] == b'\x01\x02'):
                temp = self.fp.read(0x2E)
                zipcentral_namelength = struct.unpack('<H', temp[0x1C:0x1E])[0]
                zipcentral_extralength = struct.unpack('<H', temp[0x1E:0x20])[0]
                zipcentral_commentlength = struct.unpack('<H', temp[0x20:0x22])[0]

                filesize = 0x2E + zipcentral_namelength + zipcentral_extralength + zipcentral_commentlength  # 0x2E is header size
                totalfilesize += filesize
                i = totalfilesize
                continue
            #Digital signature인 경우
            elif (temp[0:2] == b'\x50\x4B' and temp[2:4] == b'\x05\x05'):
                temp = self.fp.read(0x06)
                zipdigitalsignature_datasize = struct.unpack('<H', temp[0x04:0x06])[0]

                filesize = 0x06 + zipdigitalsignature_datasize
                totalfilesize += filesize
                i = totalfilesize
                continue
            #Zip64 end of Central directory record인 경우0x06064b50
            elif (temp[0:2] == b'\x50\x4B' and temp[2:4] == b'\x06\x06'):
                temp = self.fp.read(0x38)
                zip64cdr_sizezip64 = struct.unpack('<Q', temp[0x04:0x0C])[0]

                filesize = 0x38 + zip64cdr_sizezip64
                totalfilesize += filesize
                i = totalfilesize
                continue
            #Zip64 end of Central directory locator인 경우0x07064b50
            elif (temp[0:2] == b'\x50\x4B' and temp[2:4] == b'\x06\x07'):
                filesize = 0x14                 # 0x14 is header size
                totalfilesize += filesize
                i = totalfilesize
                continue
            # End of central directory record인 경우 0x06054b50
            elif (temp[0:2] == b'\x50\x4B' and temp[2:4] == b'\x05\x06'):
                filesize = 0x16
                totalfilesize += filesize
                i = totalfilesize
                print(totalfilesize, hex(totalfilesize))
                return True
            else:
                print(totalfilesize, hex(totalfilesize))
                return True

            return False









        #zipheader size = 30bytes

    def carve_alz(self, current_offset, next_offset):
        sigALZ_FOOTER = b'\x43\x4C\x5A\x02'
        fileSize = self.signature(current_offset, sigALZ_FOOTER)

        if fileSize > 0 :
            print("Find!!", hex(fileSize))  # 시작부터 self.uClusterSize + sOffset 여기까지 긁어와서 저장. 그러면 정상.
        else:
            print("not Found")  # 현재 offset에서 next_offset까지.

        print("not Found", hex(i))

    def carve_avi(self, current_offset, next_offset):
        self.fp.seek(0)
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

        self.fp.seek(0)
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
        print(hex(uDecSize))

    def carve_eml(self, current_offset, next_offset):
        bSuccced = False
        search_range = int(self.CONST_SEARCH_SIZE / (self.uClusterSize * 1))  # 1 => sizeof(UCHAR)
        sector_per_cluster = int(self.uClusterSize / 512)
        for i in range(0, search_range):
            self.fp.seek(current_offset + i * self.uClusterSize)
            temp = self.fp.read(self.uClusterSize)

            sOffset = 1
            while (sOffset <= sector_per_cluster):     # sector per cluster
                footer = temp[512 * sOffset - 8: 512 * sOffset]

                if footer == b'\x00\x00\x00\x00\x00\x00\x00\x00':
                    bSuccced = True
                else:
                    sOffset += 1
                    continue

                if bSuccced == True:
                    filesize = i*self.uClusterSize + sOffset*512
                    print(hex(filesize))
                    return True

        return False

    def carve_wav(self, current_offset, next_offset):
        self.fp.seek(0)
        riff = self.fp.read(0x0C)
        riff_filesize = struct.unpack('<I', riff[4:8])[0]  # 전체 사이즈를 확인하기 위한 헤더
        uFileSize = riff_filesize + 0x08  # RIFF 헤더를 포함한 전체 크기
        uDecSize = uFileSize

        uAddRead = 0
        uMove = 0
        uRealSize = 0
        pReader = 0
        puChunkSize = 0
        bFMT = False
        bDATA = False
        bEND = False

        self.fp.seek(0)
        while uDecSize > 0:
            temp = self.fp.read(self.uClusterSize)
            uCluSize = self.uClusterSize
            pReader += uAddRead  # 버퍼 내 시작 Offset 설정
            uMove += uAddRead  # 움직인 Offset 저장

            if uDecSize == uFileSize:
                pReader += 0x0C  # RIFFHEADER 크기만큼 점프
                uMove += 0x0C  # RIFFHEADER 크기 만큼 이동한 Offset 저장
                uRealSize += 0x0C  # 추출할 실제 사이즈

            while uCluSize > 0:  # 버퍼가 남아있을 때 까지

                if temp[pReader:pReader + 4] == b'\x66\x6D\x74\x20':     # "fmt "
                    bFMT = True
                    puChunkSize = pReader + 4  # 이동할 Chunk size 저장
                    pReader += 8  # read 포인터 이동
                    uMove = puChunkSize + 2 * 4  # 이동한 Offset 저장
                    uRealSize += puChunkSize + 2 * 4  # 추출할 실제 사이즈
                elif temp[pReader:pReader + 4] == b'\x64\x61\x74\x61':      # "data"
                    bDATA = True
                    bEND = True
                    puChunkSize = pReader + 4  # 이동할 Chunk size 저장
                    uRealSize = puChunkSize + 2 * 4  # 추출할 실제 사이즈
                elif temp[pReader:pReader + 4] == b'\x4A\x55\x4E\x4B':      # "JUNK"
                    puChunkSize = pReader + 4  # 이동할 Chunk size 저장
                    pReader += 8  # read 포인터 이동
                    uMove = puChunkSize + 2 * 4  # 이동한 Offset 저장
                    uRealSize += puChunkSize + 2 * 4  # 추출할 실제 사이즈
                elif temp[pReader:pReader + 4] == b'\x4C\x49\x53\x54':      # "LIST"
                    puChunkSize = pReader + 4  # 이동할 Chunk size 저장
                    pReader += 8  # read 포인터 이동
                    uMove = puChunkSize + 2 * 4  # 이동한 Offset 저장
                    uRealSize += puChunkSize + 2 * 4  # 추출할 실제 사이즈
                elif temp[pReader:pReader + 4] == b'\x66\x61\x63\x74':      # "fact"
                    puChunkSize = pReader + 4  # 이동할 Chunk size 저장
                    pReader += 8  # read 포인터 이동
                    uMove = puChunkSize + 2 * 4  # 이동한 Offset 저장
                    uRealSize += puChunkSize + 2 * 4  # 추출할 실제 사이즈
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




            if bEND == True:
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

        if bDATA == True:
            print(hex(uDecSize))

    def carve_pst(self, current_offset, next_offset):
        self.fp.seek(0)
        temp = self.fp.read(512)
        filesize = struct.unpack('<Q', temp[0xB8:0xB8 + 8])[0]

        if filesize == None:
            return False

        print(hex(filesize))
        return True

    def carve_dbx(self, current_offset, next_offset):
        self.fp.seek(0)
        temp = self.fp.read(512)
        filesize = struct.unpack('<I', temp[0x7C:0x7C + 4])[0]

        if filesize == None:
            return False

        print(hex(filesize))
        return True

    def carve_compound(self, current_offset, next_offset):
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
                return False

            self.fp.seek((temp + 1) * 512)
            nRead = bytearray(self.fp.read(512))
            puBat += nRead

            if len(nRead) != 512:
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
                    # qwDataSize = struct.unpack('<Q', puBat[i*128*4 + j*4 : i*128*4 + j*4 + 8])[0]
                    qwDataSize = temp

                j += 1
            i += 1

        qwDataSize += 2
        qwDataSize *= 512

        if qwDataSize > self.CONST_COMPOUND_MAX:
            return False

        #return qwDataSize

        self.fp.seek(0)
        temp = bytearray(self.fp.read(self.CONST_COMPOUND_MAX))
        print(temp.find(b'\x60\xB6\xA2\x9F\x61\x10\xD4\x11'))
        print(qwDataSize)

    def carve_hwp(self, current_offset, next_offset):
        # 3.0은 잠시 제외 5.0부터
        pvBuffer = b''
        strTmpFn = b''
        nRead = b''
        i = 0
        j = 0
        uMaxBat = 0
        bFirst = True
        propCount = 0
        propOffset = 0
        filetime = 0
        idxTitle = 0
        szTitle = 0
        lenTemp = 0
        strTemp  = 0
        lpszFileName = ""
        temp = 0
        uFirstXBatID = 0
        puBatTable = 0
        puRootEntry = 0
        puBat = b''
        puSBat = 0
        pHwpSummaryInformation = 0
        sigHwpSummary = b'\x05\x48\x77\x70\x53\x75\x6D\x6D'
        pPropSbat = 0
        pPropHWPSum = 0
        pOleHeader = {}

        self.fp.seek(0)
        pvBuffer = bytearray(self.fp.read(4096))

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
            return False

        qwDataSize = 0

        # puBat =
        if pOleHeader['uXbatCount'] == 0:       # XBAT을 안쓰는 경우(작은 크기의 파일)
            puBatTable = pvBuffer[0x4C:0x4C + pOleHeader['uBatCount'] * 4]
        elif pOleHeader['uXbatCount'] > 0:

            # 1. Header에 있는 XBAT 복사
            puBatTable = pvBuffer[0x4C:0x4C + 109 * 4]

            # 2. XBAT의 수 만큼 loop
            uFirstXBatID = pOleHeader['idxXbat']

            i = 0
            j = 0
            while( i < pOleHeader['uXbatCount'] ):

                self.fp.seek((uFirstXBatID + 1) * 512)
                puBatTable += bytearray(self.fp.read(0x200))

                if puBatTable[109 * 4 + (i*128)*4 + 127*4 : 109 + (i*128) + 127*4 + 4] == b'\xFF\xFF\xFF\xFF' or puBatTable[109 * 4 + (i*128)*4 + 127*4 : 109 + (i*128) + 127*4 + 4] == b'\xFE\xFF\xFF\xFF':
                    break
                else:
                    uFirstXBatID = struct.unpack('<I', puBatTable[109*4 + (i * 128)*4 - (j)*4 + 127*4 : 109*4 + (i * 128)*4 - (j)*4 + 127*4 + 4])[0]

                i += 1
                j += 1

        if puBatTable == b'' :
            return False

        i = 0
        while i < pOleHeader['uBatCount']:
            temp = struct.unpack('<I',puBatTable[i*4 : (i+1)*4])[0]
            if uMaxBat < temp:
                uMaxBat = temp
            i += 1

        qwDataSize = uMaxBat        # 데이터의 크기 예측

        if uMaxBat < 2048:
            uMaxBat += 2048
        else:
            uMaxBat += 4096

        i = 0
        while i < pOleHeader['uBatCount']:
            temp = struct.unpack('<I', puBatTable[i * 4: (i + 1) * 4])[0]
            # 에러 처리
            if(temp > 0xFFFF0000):
                return False

            self.fp.seek((temp + 1)*512)
            nRead = bytearray(self.fp.read(512))
            puBat += nRead

            if len(nRead) != 512:
                return False

            j = 0
            while j < 128:
                temp = struct.unpack('<I', puBat[i*128*4 + j*4 : i*128*4 + j*4 + 4])[0]
                if temp == 0xFFFFFFFC or temp == 0xFFFFFFFD or temp == 0xFFFFFFFE or temp == 0xFFFFFFFF:
                    j += 1
                    continue

                if uMaxBat < temp:
                    qwDataSize = uMaxBat
                    break

                if qwDataSize < temp:
                    #qwDataSize = struct.unpack('<Q', puBat[i*128*4 + j*4 : i*128*4 + j*4 + 8])[0]
                    qwDataSize = temp

                j += 1
            i += 1

        qwDataSize += 2
        qwDataSize *= 512

        if qwDataSize > self.CONST_COMPOUND_MAX:
            return False

        self.fp.seek(0)
        temp = bytearray(self.fp.read(self.CONST_COMPOUND_MAX))
        print(temp.find(b'\x60\xB6\xA2\x9F\x61\x10\xD4\x11'))
        print(qwDataSize)
        return qwDataSize

    def carve_bmp(self, current_offset, next_offset):
        self.fp.seek(0)
        # Get BITMAP Header
        temp = self.fp.read(512)
        bfSize = struct.unpack('<I', temp[0x02:0x06])[0]
        # bfReserved1, bfReserved1 value is \x00\x00
        bfReserved1 = temp[0x06:0x08]
        bfReserved2 = temp[0x08:0x0A]

        if bfReserved1 != b'\x00\x00' or bfReserved2 != b'\x00\x00':
            return False

        biSize = temp[0x0E:0x12]
        biPlanes = temp[0x1A:0x1C]
        biCompression = struct.unpack('<I', temp[0x1E:0x22])[0]

        if biSize != b'\x28\x00\x00\x00' or biPlanes != b'\x01\x00' or biCompression > 0x05:
            return False

        print(hex(bfSize))
        return bfSize












































