# carpe_xls.py
import struct

class XLS :

    def __init__(self, compound):
        self.compound = compound

    def __enter__(self):
        raise NotImplementedError

    def __exit__(self):
        raise NotImplementedError

    def parse_xls(self):
        if self.compound.is_damaged == self.compound.CONST_DOCUMENT_NORMAL:
            self.__parse_xls_normal__()
        elif self.compound.is_damaged == self.compound.CONST_DOCUMENT_DAMAGED:
            self.__parse_xls_damaged__()

    def __parse_xls_normal__(self):

        RECORD_HEADER_SIZE = 4
        records = []
        # 원하는 스트림 f에 모두 읽어오기
        temp = self.compound.fp.open('Workbook').read()
        f = bytearray(temp)
        # 스트림 내부 모두 파싱해서 데이터 출력
        tempOffset = 0
        content = ""       # 최종 저장될 스트링
        substream = 0
        while tempOffset < len(f):
            dic = {}
            dic['offset'] = tempOffset
            dic['type'] = struct.unpack('<h', f[tempOffset: tempOffset + 0x02])[0]
            dic['length'] = struct.unpack('<h', f[tempOffset + 0x02: tempOffset + 0x04])[0]
            dic['data'] = f[tempOffset + RECORD_HEADER_SIZE: tempOffset + RECORD_HEADER_SIZE + dic['length']]
            tempOffset = tempOffset + RECORD_HEADER_SIZE + dic['length']
            records.append(dic)


        # Continue marker
        for record in records:
            if record['type'] == 0xFC:
                sstNum = records.index(record)
                sstOffset = record['offset']
                sstLen = record['length']
            if record['type'] == 0x3C:
                f[record['offset']:record['offset']+4] = bytearray(b'\xAA\xAA\xAA\xAA')



        cntStream = sstOffset + 4
        cstTotal = struct.unpack('<i', f[cntStream : cntStream + 4])[0]
        cstUnique = struct.unpack('<i', f[cntStream + 4: cntStream + 8])[0]
        cntStream += 8


        for i in range(0, cstUnique):
            string = ""
            if(cntStream > len(f)):
                break
            # if start is Continue
            if f[cntStream: cntStream + 4] == b'\xAA\xAA\xAA\xAA':
                cntStream += 4

            cch = struct.unpack('<H', f[cntStream: cntStream + 2])[0]  ### 문자열 길이
            cntStream += 2
            flags = f[cntStream]  ### 플래그를 이용해서 추가적 정보 확인
            cntStream += 1

            if cch == 0x00 and flags == 0x00:
                continue

            if cch == 0x00:
                break

            if flags & 0x02 or flags >= 0x10:
                break


            if (flags & 0b00000001 == 0b00000001):
                fHighByte = 0x01
            else:
                fHighByte = 0x00

            if (flags & 0b00000100 == 0b00000100):
                fExtSt = 0x01
            else:
                fExtSt = 0x00

            if (flags & 0b00001000 == 0b00001000):
                fRichSt = 0x01
            else:
                fRichSt = 0x00

            if fRichSt == 0x01:
                cRun = struct.unpack('<H', f[cntStream: cntStream + 2])[0]
                cntStream += 2

            if fExtSt == 0x01:
                cbExtRst = struct.unpack('<I', f[cntStream: cntStream + 4])[0]
                cntStream += 4

            if fHighByte == 0x00:  ### Ascii
                bAscii = True
                for j in range(0, cch):
                    if f[cntStream : cntStream + 4] == b'\xAA\xAA\xAA\xAA':
                        if f[cntStream + 4] == 0x00 or f[cntStream + 4] == 0x01:
                            cntStream += 4

                            if f[cntStream] == 0x00:
                                bAscii = True
                            elif f[cntStream] == 0x01:
                                bAscii = False

                            cntStream += 1

                    if bAscii == True:
                        try:
                            string += str(bytes([f[cntStream]]).decode("ascii"))
                            cntStream += 1
                        except UnicodeDecodeError:
                            cntStream += 1
                            continue

                    elif bAscii == False:
                        try:
                            string += str(f[cntStream: cntStream + 2].decode("utf-16"))
                            cntStream += 2
                        except UnicodeDecodeError:
                            cntStream += 2
                            continue

            elif fHighByte == 0x01:  ### Unicode
                bAscii = False
                for j in range(0, cch):

                    if f[cntStream : cntStream + 4] == b'\xAA\xAA\xAA\xAA':
                        if f[cntStream + 4] == 0x00 or f[cntStream + 4] == 0x01:
                            cntStream += 4

                            if f[cntStream] == 0x00:
                                bAscii = True
                            elif f[cntStream] == 0x01:
                                bAscii = False

                            cntStream += 1


                    if bAscii == True:
                        try :
                            string += str(bytes([f[cntStream]]).decode("ascii"))
                            cntStream += 1
                        except UnicodeDecodeError:
                            cntStream += 1
                            continue

                    elif bAscii == False:
                        try :
                            string += str(f[cntStream: cntStream + 2].decode("utf-16"))
                            cntStream += 2
                        except UnicodeDecodeError:
                            cntStream += 2
                            continue
            content += string + '\n'
            #print(str(i) + " : " + string)

            if fRichSt == 0x01:
                if f[cntStream: cntStream + 4] == b'\xAA\xAA\xAA\xAA':
                    cntStream += 4
                cntStream += int(cRun) * 4

            if fExtSt == 0x01:
                for i in range(0, cbExtRst):
                    if cntStream > len(f):
                        break

                    if f[cntStream: cntStream + 4] == b'\xAA\xAA\xAA\xAA':
                        if i + 4 <= cbExtRst:
                            cntStream += 4

                    cntStream += 1

        # SubStream
        bSubstream = False

        for record in records:
            if record['type'] == 0x809 and record['data'][0:3] == b'\x00\x06\x10':
                bSubstream = True
            if bSubstream == True and record['type'] == 0x3C:
                if record['data'][0] == 1:    # Ascii Data
                    for i in range(0, len(record['data'])-1, 2) :
                        content += str(record['data'][1 + i: 1 + i + 2].decode("utf-16"))

        self.compound.content = content

    def __parse_xls_damaged__(self):
        content = ""
        test = bytearray(self.compound.fp.read())
        tempOffset = 0
        globalStreamOffset = 0
        while tempOffset < len(test):
            if test[tempOffset:tempOffset+8] == b'\x09\x08\x10\x00\x00\x06\x05\x00':
                globalStreamOffset = tempOffset
                break
            tempOffset += 0x80

        f = test[globalStreamOffset:]

        RECORD_HEADER_SIZE = 4
        records = []
        # 스트림 내부 모두 파싱해서 데이터 출력
        tempOffset = 0

        while tempOffset < len(f):
            dic = {}
            dic['offset'] = tempOffset
            dic['type'] = struct.unpack('<h', f[tempOffset: tempOffset + 0x02])[0]
            if dic['type'] >= 4200 or dic['type'] <= 6:
                break
            dic['length'] = struct.unpack('<h', f[tempOffset + 0x02: tempOffset + 0x04])[0]
            if dic['length'] >= 8225:
                break
            dic['data'] = f[tempOffset + RECORD_HEADER_SIZE: tempOffset + RECORD_HEADER_SIZE + dic['length']]
            tempOffset = tempOffset + RECORD_HEADER_SIZE + dic['length']
            records.append(dic)

        bSST = False
        # Continue marker
        for record in records:
            if record['type'] == 0xFC:
                sstOffset = record['offset']
                bSST = True
            if record['type'] == 0x3C:
                f[record['offset']:record['offset']+4] = bytearray(b'\xAA\xAA\xAA\xAA')

        if bSST == False:
            return self.compound.CONST_ERROR


        cntStream = sstOffset + 4
        cstTotal = struct.unpack('<i', f[cntStream : cntStream + 4])[0]
        cstUnique = struct.unpack('<i', f[cntStream + 4: cntStream + 8])[0]
        cntStream += 8


        for i in range(0, cstUnique):
            string = ""
            if(cntStream > len(f)):
                break
            # if start is Continue
            if f[cntStream: cntStream + 4] == b'\xAA\xAA\xAA\xAA':
                cntStream += 4

            cch = struct.unpack('<H', f[cntStream: cntStream + 2])[0]  ### 문자열 길이
            cntStream += 2
            flags = f[cntStream]  ### 플래그를 이용해서 추가적 정보 확인
            cntStream += 1

            if cch == 0x00 and flags == 0x00:
                continue

            if cch == 0x00:
                break

            if flags & 0x02 or flags >= 0x10:
                break


            if (flags & 0b00000001 == 0b00000001):
                fHighByte = 0x01
            else:
                fHighByte = 0x00

            if (flags & 0b00000100 == 0b00000100):
                fExtSt = 0x01
            else:
                fExtSt = 0x00

            if (flags & 0b00001000 == 0b00001000):
                fRichSt = 0x01
            else:
                fRichSt = 0x00

            if fRichSt == 0x01:
                cRun = struct.unpack('<H', f[cntStream: cntStream + 2])[0]
                cntStream += 2

            if fExtSt == 0x01:
                cbExtRst = struct.unpack('<I', f[cntStream: cntStream + 4])[0]
                cntStream += 4

            if fHighByte == 0x00:  ### Ascii
                bAscii = True
                for j in range(0, cch):
                    if f[cntStream : cntStream + 4] == b'\xAA\xAA\xAA\xAA':
                        if f[cntStream + 4] == 0x00 or f[cntStream + 4] == 0x01:
                            cntStream += 4

                            if f[cntStream] == 0x00:
                                bAscii = True
                            elif f[cntStream] == 0x01:
                                bAscii = False

                            cntStream += 1

                    if bAscii == True:
                        try:
                            string += str(bytes([f[cntStream]]).decode("ascii"))
                            cntStream += 1
                        except UnicodeDecodeError:
                            cntStream += 1
                            continue

                    elif bAscii == False:
                        try:
                            string += str(f[cntStream: cntStream + 2].decode("utf-16"))
                            cntStream += 2
                        except UnicodeDecodeError:
                            cntStream += 2
                            continue

            elif fHighByte == 0x01:  ### Unicode
                bAscii = False
                for j in range(0, cch):

                    if f[cntStream : cntStream + 4] == b'\xAA\xAA\xAA\xAA':
                        if f[cntStream + 4] == 0x00 or f[cntStream + 4] == 0x01:
                            cntStream += 4

                            if f[cntStream] == 0x00:
                                bAscii = True
                            elif f[cntStream] == 0x01:
                                bAscii = False

                            cntStream += 1


                    if bAscii == True:
                        try :
                            string += str(bytes([f[cntStream]]).decode("ascii"))
                            cntStream += 1
                        except UnicodeDecodeError:
                            cntStream += 1
                            continue

                    elif bAscii == False:
                        try :
                            string += str(f[cntStream: cntStream + 2].decode("utf-16"))
                            cntStream += 2
                        except UnicodeDecodeError:
                            cntStream += 2
                            continue
            content += string + '\n'
            #print(str(i) + " : " + string)


            if fRichSt == 0x01:
                if f[cntStream: cntStream + 4] == b'\xAA\xAA\xAA\xAA':
                    cntStream += 4
                cntStream += int(cRun) * 4

            if fExtSt == 0x01:
                for i in range(0, cbExtRst):
                    if cntStream > len(f):
                        break

                    if f[cntStream: cntStream + 4] == b'\xAA\xAA\xAA\xAA':
                        if i + 4 <= cbExtRst:
                            cntStream += 4

                    cntStream += 1

        # SubStream
        bSubstream = False

        for record in records:
            if record['type'] == 0x809 and record['data'][0:3] == b'\x00\x06\x10':
                bSubstream = True
            if bSubstream == True and record['type'] == 0x3C:
                if record['data'][0] == 1:    # Ascii Data
                    for i in range(0, len(record['data'])-1, 2) :
                        content += str(record['data'][1 + i: 1 + i + 2].decode("utf-16"))

        self.compound.content = content