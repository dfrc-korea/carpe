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

    def __translate_RK_value__(self, value):
        bInt = False
        bDiv100 = False
        nRkValue = struct.unpack('<I', value[4:8])[0]
        fRkDouble = 0.0
        strRKValue = ""

        ## check 'bit 0' (0 = Value not changed, 1 = Encoded value is multiplied by 100)
        if (nRkValue & 0x00000001):
            bDiv100 = True

        ## check 'bit 1' (0 = Floating-point value, 1 = Signed integer value)
        if (nRkValue & 0x00000002):
            bInt = True

        if bInt == True:
            nRkInt = nRkValue

            nRkInt >>= 2

            if bDiv100 == True:
                fRkDouble *= 0.01
                strRKValue = str(fRkDouble)
            else:
                strRKValue = str(nRkInt)


        else:
            if bytes(struct.unpack('<b', value[4:5])[0] & 0xFC) == b'':
                temp4 = b'\x00'
            else:
                temp4 = struct.unpack('<b', value[4:5])[0] & 0xFC
                temp4 = bytes([temp4])
            tempValue = value[0:4] + temp4 + value[5:8]
            fRkDouble = struct.unpack('<d', tempValue)[0]

            if bDiv100 == True:
                fRkDouble *= 0.01
            strRKValue = str(fRkDouble)

        strRKValue = strRKValue[0:strRKValue.find('.')]
        return strRKValue

    def __convert_to_XF_type__(self, strOriginal, idxToXF, arrStXFType):
        strConverted = strOriginal
        ifmt = 0

        if idxToXF < 0 or idxToXF >= len(arrStXFType):
            return strConverted

        ifmt = arrStXFType[idxToXF]['ifmt']

        GENERAL_FORMAT = 0x00
        NUMBERIC_FORMAT1 = 0x01         # 0
        NUMBERIC_FORMAT2 = 0x02         # 0.00
        NUMBERIC_COMMA_FORMAT1 = 0x03   # # ,##0
        NUMBERIC_COMMA_FORMAT2 = 0x04   # # ,##0.00
        CURRENCY_FORMAT1 = 0x05         # ($  # ,##0_);($#,##0)
        CURRENCY_FORMAT2 = 0x06         # ($  # ,##0_);[Red]($#,##0)
        CURRENCY_FORMAT3 = 0x07         # ($  # ,##0.00_);($#,##0.00)
        CURRENCY_FORMAT4 = 0x08         # ($  # ,##0.00_);[Red]($#,##0.00)
        PERCENT_FORMAT1 = 0x09          # 0 %
        PERCENT_FORMAT2 = 0x0A          # 0.00 %
        EXPONENT_FORMAT1 = 0x0B         # 0.00E+00
        FRACTION_FORMAT1 = 0x0C         # # ?/?
        FRACTION_FORMAT2 = 0x0D         # # ??/??
        DATE_FORMAT1 = 0x0E             # m / d / yy
        DATE_FORMAT2 = 0x0F             # d-mmm-yy
        DATE_FORMAT3 = 0x10             # d-mmm
        DATE_FORMAT4 = 0x11             # mmm-yy
        TIME_FORMAT1 = 0x12             # h:mm AM / PM
        TIME_FORMAT2 = 0x13             # h:mm:ss AM / PM
        TIME_FORMAT3 = 0x14             # h:mm
        TIME_FORMAT4 = 0x15             # h:mm:ss
        DATE_TIME_FORMAT1 = 0x16        # m / d / yy h:mm
        UNKNOWN_FORMAT1 = 0x25          # (  # ,##0_);(#,##0)
        UNKNOWN_FORMAT2 = 0x26          # (  # ,##0_);[Red](#,##0)
        UNKNOWN_FORMAT3 = 0x27          # (  # ,##0.00_);(#,##0.00)
        UNKNOWN_FORMAT4 = 0x28          # (  # ,##0.00_);[Red](#,##0.00)
        UNKNOWN_FORMAT5 = 0x29          # _( *  # ,##0_);_(* (#,##0);_(* "-"_);_(@_)
        UNKNOWN_FORMAT6 = 0x2A          # _($ *   # ,##0_);_($* (#,##0);_($* "-"_);_(@_)
        UNKNOWN_FORMAT7 = 0x2B          # _( *  # ,##0.00_);_(* (#,##0.00);_(* "-"??_);_(@_)
        UNKNOWN_FORMAT8 = 0x2C          # _($ *  # ,##0.00_);_($* (#,##0.00);_($* "-"??_);_(@_)
        TIME_FORMAT5 = 0x2D             # mm:ss
        TIME_FORMAT6 = 0x2E             # [h]:mm:ss
        TIME_FORMAT7 = 0x2F             # mm:ss.0
        EXPONENT_FORMAT2 = 0x30         # ##0.0E+0
        UNKNOWN_FORMAT9 = 0x31          # @

        if ifmt == NUMBERIC_FORMAT1 or ifmt == NUMBERIC_FORMAT2 :
            pass    # not yet
        else:
            # Number Format == NUMBERIC_COMMA_FORMAT
            if ifmt == NUMBERIC_COMMA_FORMAT1 or ifmt ==  NUMBERIC_COMMA_FORMAT2:
                i = len(strConverted - 3)
                while i > 0 :
                    strConverted = strConverted[:i] + "," + strConverted[i:]
                    i -= 3
            else:
                # Number Format == CURRENTY_FORMAT
                if ifmt == CURRENCY_FORMAT1 or ifmt == CURRENCY_FORMAT2 or ifmt == CURRENCY_FORMAT3 or ifmt == CURRENCY_FORMAT4:
                    i = len(strConverted - 3)
                    while i > 0:
                        strConverted = strConverted[:i] + "," + strConverted[i:]
                        i -= 3
                    strConverted = "$" + strConverted
                else:
                    # Number Format == PERCENT_FORMAT
                    if ifmt == PERCENT_FORMAT1 or ifmt == PERCENT_FORMAT2:
                        strTemp = ""
                        iCurNumVal = float(strConverted)
                        iCurNumVal = str(int(iCurNumVal * 100)) + "%"

                        i = len(iCurNumVal - 3)
                        while i > 0:
                            iCurNumVal = iCurNumVal[:i] + "," + iCurNumVal[i:]
                            i -= 3
                        strConverted = iCurNumVal

                    else:
                        # Number Format == FRANCTION_FORMAT
                        if ifmt == FRACTION_FORMAT1 or ifmt == FRACTION_FORMAT2:
                            pass
                        else:
                            # Number Format == DATE_FORMAT
                            if ifmt == DATE_FORMAT1 or ifmt == DATE_FORMAT2 or ifmt == DATE_FORMAT3 or ifmt == DATE_FORMAT4:
                                pass
                            else:
                                # Number Format == TIME_FORMAT
                                if ifmt == TIME_FORMAT1 or ifmt == TIME_FORMAT2 or ifmt == TIME_FORMAT3 or ifmt == TIME_FORMAT4 or ifmt == TIME_FORMAT5 or ifmt == TIME_FORMAT6 or ifmt == TIME_FORMAT7:
                                    pass
                                else:
                                    if ifmt == DATE_TIME_FORMAT1:
                                        pass
        return strConverted













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

        arrStXFType = []
        # Continue marker
        for record in records:
            if record['type'] == 0xE0:      # GlobalStream XF Type
                stGlobalStreamXF = {}
                stGlobalStreamXF['ifnt'] = record['data'][0:2]
                stGlobalStreamXF['ifmt'] = record['data'][2:4]
                stGlobalStreamXF['Flags'] = record['data'][4:6]
                arrStXFType.append(stGlobalStreamXF)
            if record['type'] == 0xFC:
                sstNum = records.index(record)
                sstOffset = record['offset']
                sstLen = record['length']
            if record['type'] == 0x3C:
                f[record['offset']:record['offset']+4] = bytearray(b'\xAA\xAA\xAA\xAA')
            if record['type'] == 0x85:      # BundleSheet Name
                tempOffset = 6          # GLOBALSTREAM_BUNDLESHEET size
                cch = struct.unpack('<b', record['data'][tempOffset : tempOffset + 1])[0]
                reserved = record['data'][tempOffset + 1 : tempOffset + 2]
                tempOffset += 2

                # reserved 0 is single-byte characters
                if reserved == b'\x00':
                    content += record['data'][tempOffset : tempOffset + cch].decode("ascii")
                # reserved 1 is single-byte characters
                if reserved == b'\x01':
                    content += record['data'][tempOffset: tempOffset + cch * 2].decode("utf-16")

        content += "\n"


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
            if bSubstream == True and record['type'] == 0x3C:           # 도형 내 텍스트
                if record['data'][0] == 1:    # Ascii Data
                    for i in range(0, len(record['data'])-1, 2) :
                        content += str(record['data'][1 + i: 1 + i + 2].decode("utf-16"))

            if bSubstream == True and record['type'] == 0x27E:          # 숫자 RK
                row = record['data'][0:2]
                col = record['data'][2:4]
                idxToXF = struct.unpack('<H', record['data'][4:6])[0]
                value = b'\x00\x00\x00\x00' + record['data'][6:10]

                strRKValue = self.__translate_RK_value__(value)
                strRKValue = self.__convert_to_XF_type__(strRKValue, idxToXF, arrStXFType)
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
            if dic['length'] >= 8225 or dic['length'] < 0:
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
                        try:
                            content += str(record['data'][1 + i: 1 + i + 2].decode("utf-16"))
                        except UnicodeDecodeError:
                            continue

        self.compound.content = content

