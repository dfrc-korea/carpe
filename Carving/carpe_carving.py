import os
import struct


class Carving:
    CONST_KILOBYTE = 1024
    CONST_MEGABYTE = 1048576
    CONST_GIGABYTE = 1073741824

    CONST_RAMSLACK_COMP_UNIT = 2
    CONST_COMPOUND_MAX = 20*CONST_MEGABYTE
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



    def carve_jfif(self, current_offset, next_offset):
        sigJFIF_FOOTER = b'\xFF\xD9'
        search_range = int(self.CONST_SEARCH_SIZE / (self.uClusterSize * 1))   #  1 => sizeof(UCHAR)

        for i in range(0, search_range):
            self.fp.seek(current_offset + i * self.uClusterSize)
            temp = self.fp.read(self.uClusterSize)

            sOffset = 0
            while(True):
                sTempOffset = temp.find(sigJFIF_FOOTER)

                if sTempOffset >= 0:
                    bSucceed = True
                    sOffset = sOffset + sTempOffset + 2         # 헤더 크기 만큼 offset 추가

                    # 쓰기 단위인 섹터(512바이트)의 RAM Slack 계산
                    ramSlack = sOffset
                    ramSlack = ramSlack % self.CONST_ELEC_WRITE_UNIT
                    ramSlack -= self.CONST_ELEC_WRITE_UNIT
                    ramSlack = 0 - ramSlack

                    # RAM Slack의 값이 0x00인지 검사

                    if(ramSlack <= 10):
                        compUnit = 1
                    else:
                        compUnit = self.CONST_RAMSLACK_COMP_UNIT

                    for j in range(sOffset, sOffset + ramSlack, compUnit):
                        if temp[j] == 0x0D or temp[j] == 0x0A:
                            continue

                        if temp[j] != 0x00:
                            bSucceed = False
                            break

                    if (bSucceed):
                        qwDataSize = i * self.uClusterSize + sOffset
                        print("Find!!")
                        return True
                else:
                    sOffset = -1

                if(sOffset < 0):
                    break
                if next_offset - current_offset > i * self.uClusterSize:
                    break

        print("not Found")

    def carve_exif(self, current_offset, next_offset):
        sigEXIF_FOOTER = b'\xFF\xD9'
        search_range = int(self.CONST_SEARCH_SIZE / (self.uClusterSize * 1))   #  1 => sizeof(UCHAR)

        for i in range(0, search_range):
            self.fp.seek(current_offset + i * self.uClusterSize)
            temp = self.fp.read(self.uClusterSize)

            sOffset = 0
            while(True):
                sTempOffset = temp.find(sigEXIF_FOOTER)

                if sTempOffset >= 0:
                    bSucceed = True
                    sOffset = sOffset + sTempOffset + 2         # 헤더 크기 만큼 offset 추가

                    # 쓰기 단위인 섹터(512바이트)의 RAM Slack 계산
                    ramSlack = sOffset
                    ramSlack = ramSlack % self.CONST_ELEC_WRITE_UNIT
                    ramSlack -= self.CONST_ELEC_WRITE_UNIT
                    ramSlack = 0 - ramSlack

                    # RAM Slack의 값이 0x00인지 검사

                    if(ramSlack <= 10):
                        compUnit = 1
                    else:
                        compUnit = self.CONST_RAMSLACK_COMP_UNIT

                    for j in range(sOffset, sOffset + ramSlack, compUnit):
                        if temp[j] == 0x0D or temp[j] == 0x0A:
                            continue

                        if temp[j] != 0x00:
                            bSucceed = False
                            break

                    if (bSucceed):
                        qwDataSize = i * self.uClusterSize + sOffset

                        print("Find!!")
                        return True
                else:
                    sOffset = -1

                if(sOffset < 0):
                    break
                if next_offset - current_offset > i * self.uClusterSize:
                    break


        print("not Found")

    def carve_gif(self, current_offset, next_offset):
        sigGIF_FOOTER = b'\x00\x3B'
        search_range = int(self.CONST_SEARCH_SIZE / (self.uClusterSize * 1))  # 1 => sizeof(UCHAR)

        for i in range(0, search_range):
            self.fp.seek(current_offset + i * self.uClusterSize)
            temp = self.fp.read(self.uClusterSize)

            sOffset = 0
            while (True):
                sTempOffset = temp.find(sigGIF_FOOTER)

                if sTempOffset >= 0:
                    bSucceed = True
                    sOffset = sOffset + sTempOffset + 2  # 헤더 크기 만큼 offset 추가

                    # 쓰기 단위인 섹터(512바이트)의 RAM Slack 계산
                    ramSlack = sOffset
                    ramSlack = ramSlack % self.CONST_ELEC_WRITE_UNIT
                    ramSlack -= self.CONST_ELEC_WRITE_UNIT
                    ramSlack = 0 - ramSlack

                    # RAM Slack의 값이 0x00인지 검사

                    if (ramSlack <= 10):
                        compUnit = 1
                    else:
                        compUnit = self.CONST_RAMSLACK_COMP_UNIT

                    for j in range(sOffset, sOffset + ramSlack, compUnit):
                        if temp[j] == 0x0D or temp[j] == 0x0A:
                            continue

                        if temp[j] != 0x00:
                            bSucceed = False
                            break

                    if (bSucceed):
                        qwDataSize = i * self.uClusterSize + sOffset

                        print("Find!!")
                        return True
                else:
                    sOffset = -1

                if (sOffset < 0):
                    break
                if next_offset - current_offset > i * self.uClusterSize:
                    break

        print("not Found")

    def carve_png(self, current_offset, next_offset):
        sigPNG_FOOTER = b'\x49\x45\x4E\x44\xAE\x42\x60\x82'
        search_range = int(self.CONST_SEARCH_SIZE / (self.uClusterSize * 1))  # 1 => sizeof(UCHAR)

        for i in range(0, search_range):
            self.fp.seek(current_offset + i * self.uClusterSize)
            temp = self.fp.read(self.uClusterSize)

            sOffset = temp.find(sigPNG_FOOTER)

            if sOffset > 0:
                qwDataSize = i * self.uClusterSize + sOffset
                print("Find!!", hex(qwDataSize))               # 시작부터 self.uClusterSize + sOffset 여기까지 긁어와서 저장. 그러면 정상.
                return True

        print("not Found")

    def carve_pdf(self, current_offset, next_offset):
        sigPDF_FOOTER = b'\x25\x25\x45\x4F\x46'
        search_range = int(self.CONST_SEARCH_SIZE / (self.uClusterSize * 1))  # 1 => sizeof(UCHAR)

        for i in range(0, search_range):
            self.fp.seek(current_offset + i * self.uClusterSize)
            temp = self.fp.read(self.uClusterSize)

            sOffset = 0
            while (True):
                sTempOffset = temp.find(sigPDF_FOOTER)

                if sTempOffset >= 0:
                    bSucceed = True
                    sOffset = sOffset + sTempOffset + 5  # 헤더 크기 만큼 offset 추가 (이전 코드에 적혀있음)

                    # 쓰기 단위인 섹터(512바이트)의 RAM Slack 계산
                    ramSlack = sOffset
                    ramSlack = ramSlack % self.CONST_ELEC_WRITE_UNIT
                    ramSlack -= self.CONST_ELEC_WRITE_UNIT
                    ramSlack = 0 - ramSlack

                    # RAM Slack의 값이 0x00인지 검사

                    if (ramSlack <= 10):
                        compUnit = 1
                    else:
                        compUnit = self.CONST_RAMSLACK_COMP_UNIT

                    for j in range(sOffset, sOffset + ramSlack, compUnit):
                        if temp[j] == 0x0D or temp[j] == 0x0A:
                            continue

                        if temp[j] != 0x00:
                            bSucceed = False
                            break

                    if (bSucceed):
                        qwDataSize = i * self.uClusterSize + sOffset
                        print("Find!!", hex(qwDataSize))  # 시작부터 self.uClusterSize + sOffset 여기까지 긁어와서 저장. 그러면 정상.
                        return True
                else:
                    sOffset = -1

                if (sOffset < 0):
                    break
                if next_offset - current_offset > i * self.uClusterSize:
                    break

        print("not Found")

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
        search_range = int(self.CONST_SEARCH_SIZE / (self.uClusterSize * 1)) * 10 # 1 => sizeof(UCHAR) / 크기를 정해야함.

        for i in range(0, search_range):
            self.fp.seek(current_offset + i * self.uClusterSize)
            temp = self.fp.read(self.uClusterSize)

            sOffset = 0
            while(True):
                sTempOffset = temp.find(sigALZ_FOOTER)

                if sTempOffset >= 0:
                    bSucceed = True
                    sOffset = sOffset + sTempOffset + 2         # 헤더 크기 만큼 offset 추가

                    # 쓰기 단위인 섹터(512바이트)의 RAM Slack 계산
                    ramSlack = sOffset
                    ramSlack = ramSlack % self.CONST_ELEC_WRITE_UNIT
                    ramSlack -= self.CONST_ELEC_WRITE_UNIT
                    ramSlack = 0 - ramSlack

                    # RAM Slack의 값이 0x00인지 검사

                    if(ramSlack <= 10):
                        compUnit = 1
                    else:
                        compUnit = self.CONST_RAMSLACK_COMP_UNIT

                    for j in range(sOffset, sOffset + ramSlack, compUnit):
                        if temp[j] == 0x0D or temp[j] == 0x0A:
                            continue

                        if temp[j] != 0x00:
                            # bSucceed = False                              # 왜 여기에 걸리는지 확인해보기
                            break

                    if (bSucceed):
                        qwDataSize = i * self.uClusterSize + sOffset + 2    # +2 는 현재 사이즈가 안맞음. 왜인지 파악
                        print("Find!! ", hex(qwDataSize), qwDataSize)
                        return True
                else:
                    sOffset = -1

                if(sOffset < 0):
                    break
                if next_offset - current_offset > i * self.uClusterSize:
                    break


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
                    pReader += 4                            # read 포인터 이동
                    uMove = puChunkSize + 2 * 4             # 이동한 Offset 저장
                    uRealSize += puChunkSize + 2 * 4        # 추출할 실제 사이즈

                elif temp[pReader:pReader+4] == b'\x4A\x55\x4E\x4B' :     # "JUNK"
                    puChunkSize = pReader + 4               # 이동할 Chunk size 저장
                    pReader += 4                            # read 포인터 이동
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









































