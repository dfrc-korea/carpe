# carpe_xls.py
import os
import struct
import sys
import zlib

import olefile

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
            dic['type'] = struct.unpack('<H', f[tempOffset: tempOffset + 0x02])[0]
            dic['length'] = struct.unpack('<H', f[tempOffset + 0x02: tempOffset + 0x04])[0]
            dic['data'] = f[tempOffset + RECORD_HEADER_SIZE: tempOffset + RECORD_HEADER_SIZE + dic['length']]
            tempOffset = tempOffset + RECORD_HEADER_SIZE + dic['length']
            records.append(dic)

        arrStXFType = []
        b_drawing = False
        drawing_data = b''
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
            if record['type'] == 0x3C:      # Continue markerz
                # SST
                f[record['offset']:record['offset']+4] = bytearray(b'\xAA\xAA\xAA\xAA')

                # Drawing
                if b_drawing == True:
                    drawing_data += record['data']
                else:
                    b_drawing = False

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
            if record['type'] == 0xEB:
                b_drawing = True
                drawing_data += record['data']


        # SST
        content += "\n"

        cntStream = sstOffset + 4
        cstTotal = struct.unpack('<I', f[cntStream : cntStream + 4])[0]
        cstUnique = struct.unpack('<I', f[cntStream + 4: cntStream + 8])[0]
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

        if b_drawing == True:
            # Drawing
            #print(drawing_data)
            drawing_offset = 0
            rh_recType = struct.unpack('<H', drawing_data[drawing_offset + 2 : drawing_offset + 4])[0]
            rh_recLen = struct.unpack('<I', drawing_data[drawing_offset + 4: drawing_offset + 8])[0]
            drawing_offset += 0x08

            drawingGroup_rh_recType = struct.unpack('<H', drawing_data[drawing_offset + 2: drawing_offset + 4])[0]
            drawingGroup_rh_recLen = struct.unpack('<I', drawing_data[drawing_offset + 4: drawing_offset + 8])[0]
            drawing_offset += 0x08

            drawingGroup_head_spidMax = struct.unpack('<I', drawing_data[drawing_offset : drawing_offset + 4])[0]
            drawing_offset += 0x04
            drawingGroup_head_cidcl = struct.unpack('<I', drawing_data[drawing_offset: drawing_offset + 4])[0]
            drawing_offset += 0x04
            drawingGroup_head_cspSaved = struct.unpack('<I', drawing_data[drawing_offset: drawing_offset + 4])[0]
            drawing_offset += 0x04
            drawingGroup_head_cdgSaved = struct.unpack('<I', drawing_data[drawing_offset: drawing_offset + 4])[0]
            drawing_offset += 0x04

            ### 몇 번 반복해야하지? ###
            drawingGroup_rgidcl_dgid = drawing_data[drawing_offset: drawing_offset + 4]
            drawing_offset += 0x04
            drawingGroup_rgidcl_cspidCur = drawing_data[drawing_offset: drawing_offset + 4]
            drawing_offset += 0x04

            container_rh_recType = struct.unpack('<H', drawing_data[drawing_offset + 2: drawing_offset + 4])[0]
            container_rh_recLen = struct.unpack('<I', drawing_data[drawing_offset + 4: drawing_offset + 8])[0]      # size of rgfb
            drawing_offset += 0x08

            img_num = 0

            while drawing_offset < len(drawing_data):
                blip_rh_Type = struct.unpack('<H', drawing_data[drawing_offset + 2: drawing_offset + 4])[0]
                blip_rh_recLen = struct.unpack('<I', drawing_data[drawing_offset + 4: drawing_offset + 8])[0]      # size of rgfb
                drawing_offset += 0x08

                if blip_rh_Type == 0xF00B:
                    break

                blip_btWin32 = drawing_data[drawing_offset : drawing_offset + 0x01]
                drawing_offset += 0x01
                blip_btMacOS = drawing_data[drawing_offset : drawing_offset + 0x01]
                drawing_offset += 0x01
                blip_rgbUid = drawing_data[drawing_offset : drawing_offset + 0x10]
                drawing_offset += 0x10
                blip_tag = drawing_data[drawing_offset: drawing_offset + 0x02]
                drawing_offset += 0x02
                blip_size = drawing_data[drawing_offset: drawing_offset + 0x04]
                drawing_offset += 0x04
                blip_cRef = drawing_data[drawing_offset: drawing_offset + 0x04]
                drawing_offset += 0x04
                blip_foDelay = drawing_data[drawing_offset: drawing_offset + 0x04]
                drawing_offset += 0x04
                blip_unused1 = drawing_data[drawing_offset : drawing_offset + 0x01]
                drawing_offset += 0x01
                blip_cbName = struct.unpack('<B', drawing_data[drawing_offset: drawing_offset + 0x01])[0]
                drawing_offset += 0x01
                blip_unused2 = drawing_data[drawing_offset: drawing_offset + 0x01]
                drawing_offset += 0x01
                blip_unused3 = drawing_data[drawing_offset: drawing_offset + 0x01]
                drawing_offset += 0x01
                blip_nameData = None
                if blip_cbName != 0:
                    blip_nameData = drawing_data[drawing_offset: drawing_offset + blip_cbName]
                    drawing_offset += blip_cbName

                if drawing_offset + 8 > len(drawing_data):
                    break

                embedded_blip_rh_ver_instance = struct.unpack('<H', drawing_data[drawing_offset: drawing_offset + 2])[0]
                embedded_blip_rh_Type = struct.unpack('<H', drawing_data[drawing_offset + 2: drawing_offset + 4])[0]
                embedded_blip_rh_recLen = struct.unpack('<I', drawing_data[drawing_offset + 4: drawing_offset + 8])[0]
                drawing_offset += 0x08
                embedded_size = embedded_blip_rh_recLen

                # JPEG 발견! 이후 작성..
                embedded_blip_rgbUid1 = drawing_data[drawing_offset : drawing_offset + 0x10]
                drawing_offset += 0x10
                embedded_size -= 0x10
                embedded_blip_rgbUid2 = None

                if int(embedded_blip_rh_ver_instance / 0x10) == 0x46B or int(embedded_blip_rh_ver_instance / 0x10) == 0x6E3:
                    embedded_blip_rgbUid2 = drawing_data[drawing_offset: drawing_offset + 0x10]
                    drawing_offset += 0x10
                    embedded_size -= 0x10


                if embedded_blip_rh_Type != 0xF01A and embedded_blip_rh_Type != 0xF01B and embedded_blip_rh_Type != 0xF01C and \
                        embedded_blip_rh_Type != 0xF01D and embedded_blip_rh_Type != 0xF01E and embedded_blip_rh_Type != 0xF01F and \
                        embedded_blip_rh_Type != 0xF029:
                    break


                extension = ""
                if embedded_blip_rh_Type == 0xF01A:
                    extension = ".emf"
                    embedded_blip_metafileheader = drawing_data[drawing_offset: drawing_offset + 0x22]
                    drawing_offset += 0x22
                    embedded_size -= 0x22
                elif embedded_blip_rh_Type == 0xF01B:
                    extension = ".wmf"
                    embedded_blip_metafileheader = drawing_data[drawing_offset: drawing_offset + 0x22]
                    drawing_offset += 0x22
                    embedded_size -= 0x22
                elif embedded_blip_rh_Type == 0xF01C:
                    extension = ".pict"
                    embedded_blip_metafileheader = drawing_data[drawing_offset: drawing_offset + 0x22]
                    drawing_offset += 0x22
                    embedded_size -= 0x22
                elif embedded_blip_rh_Type == 0xF01D:
                    extension = ".jpg"
                    embedded_blip_tag = drawing_data[drawing_offset: drawing_offset + 0x01]
                    drawing_offset += 0x01
                    embedded_size -= 0x01
                elif embedded_blip_rh_Type == 0xF01E:
                    extension = ".png"
                    embedded_blip_tag = drawing_data[drawing_offset: drawing_offset + 0x01]
                    drawing_offset += 0x01
                    embedded_size -= 0x01
                elif embedded_blip_rh_Type == 0xF01F:
                    extension = ".dib"
                    embedded_blip_tag = drawing_data[drawing_offset: drawing_offset + 0x01]
                    drawing_offset += 0x01
                    embedded_size -= 0x01
                elif embedded_blip_rh_Type == 0xF029:
                    extension = ".tiff"
                    embedded_blip_tag = drawing_data[drawing_offset: drawing_offset + 0x01]
                    drawing_offset += 0x01
                    embedded_size -= 0x01

                if extension == "":
                    break

                if not (os.path.isdir(self.compound.tmp_path + self.compound.fileName + "_extracted")):
                    os.makedirs(os.path.join(self.compound.tmp_path + self.compound.fileName + "_extracted"))

                embedded_data = drawing_data[drawing_offset : drawing_offset + embedded_size]
                drawing_offset += embedded_size

                # 제대로 다 가져와 지는지 확인하기.
                self.compound.ole_path.append(self.compound.tmp_path + self.compound.fileName + "_extracted/" + self.compound.fileName + "_" + str(img_num) + extension)
                embedded_fp = open(self.compound.tmp_path + self.compound.fileName + "_extracted/" + self.compound.fileName + "_" + str(img_num) + extension, 'wb')
                img_num += 1
                embedded_fp.write(embedded_data)
                embedded_fp.close()


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


        """ OLE 주석 처리 
        ### OLE
        ole = olefile.OleFileIO(self.compound.filePath)
        ole_fp = open(self.compound.filePath, 'rb')
        img_num = 0
        for i in range(0, len(ole.direntries)):
            try:
                if ole.direntries[i].name == '\x01Ole10Native':             # Multimedia
                    self.compound.has_ole = True
                    ole_fp.seek((ole.direntries[i].isectStart + 1) * 0x200)
                    ole_data = ole_fp.read(ole.direntries[i].size)

                    ole_data_offset = 6     # Header
                    ole_data_offset = ole_data.find(b'\x00', ole_data_offset + 1) # Label
                    data_name = ole_data[6 : ole_data_offset].decode('ASCII')
                    ole_data_offset = ole_data.find(b'\x00', ole_data_offset + 1) # OrgPath
                    ole_data_offset += 8    # UType
                    ole_data_offset = ole_data.find(b'\x00', ole_data_offset + 1)       # DataPath
                    ole_data_offset += 1
                    data_size = struct.unpack('<I', ole_data[ole_data_offset : ole_data_offset + 4])[0]
                    ole_data_offset += 4
                    data = ole_data[ole_data_offset : ole_data_offset + data_size]

                    if not (os.path.isdir(self.compound.tmp_path + self.compound.fileName + "_extracted")):
                        os.makedirs(os.path.join(self.compound.tmp_path + self.compound.fileName + "_extracted"))

                    self.compound.ole_path.append(self.compound.tmp_path + self.compound.fileName + "_extracted/" + data_name)
                    temp = open(self.compound.tmp_path + self.compound.fileName + "_extracted/" + data_name, 'wb')
                    temp.write(data)
                    temp.close()

                elif ole.direntries[i].name == 'Package':                   # OOXML 처리
                    self.compound.has_ole = True
                    ole_fp.seek((ole.direntries[i].isectStart + 1) * 0x200)
                    ole_data = ole_fp.read(ole.direntries[i].size)
                    if ole_data.find(b'\x78\x6C\x2F\x77\x6F\x72\x6B\x62\x6F\x6F\x6B\x2E\x78\x6D\x6C') > 0:  # XLSX
                        extension = ".xlsx"
                    elif ole_data.find(b'\x77\x6F\x72\x64\x2F\x64\x6F\x63\x75\x6D\x65\x6E\x74\x2E\x78\x6D\x6C') > 0:  # DOCX
                        extension = ".docx"
                    elif ole_data.find(b'\x70\x70\x74\x2F\x70\x72\x65\x73\x65\x6E\x74\x61\x74\x69\x6F\x6E\x2E\x78\x6D\x6C') > 0:  # PPTX
                        extension = ".pptx"
                    else:
                        extension = ".zip"

                    if not (os.path.isdir(self.compound.tmp_path + self.compound.fileName + "_extracted")):
                        os.makedirs(os.path.join(self.compound.tmp_path + self.compound.fileName + "_extracted"))

                    self.compound.ole_path.append(
                        self.compound.tmp_path + self.compound.fileName + "_extracted/" + self.compound.fileName + "_" + str(
                            img_num) + extension)
                    temp = open(self.compound.tmp_path + self.compound.fileName + "_extracted/" + self.compound.fileName + "_" + str(img_num) + extension, 'wb')
                    temp.write(ole_data)
                    temp.close()
                    img_num += 1
                elif ole.direntries[i].name == 'CONTENTS':                   # PDF
                    self.compound.has_ole = True
                    ole_fp.seek((ole.direntries[i].isectStart + 1) * 0x200)
                    ole_data = ole_fp.read(ole.direntries[i].size)

                    if not (os.path.isdir(self.compound.tmp_path + self.compound.fileName + "_extracted")):
                        os.makedirs(os.path.join(self.compound.tmp_path + self.compound.fileName + "_extracted"))

                    self.compound.ole_path.append(self.compound.tmp_path + self.compound.fileName + "_extracted/" + self.compound.fileName + "_" + str(img_num) + ".pdf")
                    temp = open(self.compound.tmp_path + self.compound.fileName + "_extracted/" + self.compound.fileName + "_" + str(img_num) + ".pdf", 'wb')
                    temp.write(ole_data)
                    temp.close()
                    img_num += 1
                elif ole.direntries[i].name[0:3] == 'MBD':
                    self.compound.has_ole = True
                    word_document = None
                    table = None
                    powerpoint_document = None
                    current_user = None
                    workbook = None
                    section_data = ""
                    for j in range(0, len(ole.direntries[i].kids)):
                        if ole.direntries[i].kids[j].name == "WordDocument":
                            ole_fp.seek((ole.direntries[i].kids[j].isectStart + 1) * 0x200)
                            word_document = ole_fp.read(ole.direntries[i].kids[j].size)
                        elif ole.direntries[i].kids[j].name == "1Table":
                            ole_fp.seek((ole.direntries[i].kids[j].isectStart + 1) * 0x200)
                            table = ole_fp.read(ole.direntries[i].kids[j].size)
                        elif ole.direntries[i].kids[j].name == "0Table":
                            ole_fp.seek((ole.direntries[i].kids[j].isectStart + 1) * 0x200)
                            table = ole_fp.read(ole.direntries[i].kids[j].size)
                        elif ole.direntries[i].kids[j].name == "PowerPoint Document":
                            ole_fp.seek((ole.direntries[i].kids[j].isectStart + 1) * 0x200)
                            powerpoint_document = ole_fp.read(ole.direntries[i].kids[j].size)
                        elif ole.direntries[i].kids[j].name == "Current User":
                            idx = ole.root.isectStart
                            chain = [idx]
                            while True:
                                idx = ole.fat[idx]
                                if idx == 4294967294:
                                    break
                                chain.append(idx)
                            out = bytearray(b'')

                            for idx in chain:
                                pos = (idx + 1) * 512
                                ole_fp.seek(pos)
                                d = ole_fp.read(512)
                                out += d
                            current_user = out[64 * (ole.direntries[i].kids[j].isectStart):64 * (
                                ole.direntries[i].kids[j].isectStart) + ole.direntries[i].kids[j].size]
                        elif ole.direntries[i].kids[j].name == "Workbook":
                            ole_fp.seek((ole.direntries[i].kids[j].isectStart + 1) * 0x200)
                            workbook = ole_fp.read(ole.direntries[i].kids[j].size)
                        elif ole.direntries[i].kids[j].name == "BodyText":
                            section_data = ""
                            for k in range(0, len(ole.direntries[i].kids[j].kids)):
                                ole_fp.seek((ole.direntries[i].kids[j].kids[k].isectStart + 1) * 0x200)
                                temp_section_data = ole_fp.read(ole.direntries[i].kids[j].kids[k].size)
                                if temp_section_data[0:2] == b'\x42\x00':
                                    is_compressed = False
                                else:
                                    is_compressed = True
                                msg = self.inflateBodytext(temp_section_data, is_compressed)
                                if msg is not False:
                                    section_data += msg


                    # DOC
                    from carpe_doc import DOC
                    result = None
                    if word_document != None and table != None:
                        temp_doc = DOC(Compound(self.compound.filePath))
                        result = temp_doc.__parse_doc_normal_for_ole__(word_document, table)
                    if result != None:
                        if not (os.path.isdir(self.compound.tmp_path + self.compound.fileName + "_extracted")):
                            os.makedirs(os.path.join(self.compound.tmp_path + self.compound.fileName + "_extracted"))
                        self.compound.ole_path.append(self.compound.tmp_path + self.compound.fileName + "_extracted/" + self.compound.fileName + "_" + str(img_num) + ".txt")
                        temp = open(self.compound.tmp_path + self.compound.fileName + "_extracted/" + self.compound.fileName + "_" + str(img_num) + ".txt", 'w', encoding='utf-16')
                        temp.write(result)
                        temp.close()
                        img_num += 1

                    # XLS
                    result = None
                    if workbook != None:
                        result = self.__parse_xls_normal_for_ole__(workbook)
                    if result != None:
                        if not (os.path.isdir(self.compound.tmp_path + self.compound.fileName + "_extracted")):
                            os.makedirs(os.path.join(self.compound.tmp_path + self.compound.fileName + "_extracted"))
                        self.compound.ole_path.append(self.compound.tmp_path + self.compound.fileName + "_extracted/" + self.compound.fileName + "_" + str(img_num) + ".txt")
                        temp = open(self.compound.tmp_path + self.compound.fileName + "_extracted/" + self.compound.fileName + "_" + str(img_num) + ".txt", 'w', encoding='utf-16')
                        temp.write(result)
                        temp.close()
                        img_num += 1

                    # PPT
                    from carpe_ppt import PPT
                    from carpe_compound import Compound
                    result = None
                    if powerpoint_document != None and current_user != None:
                        temp_ppt = PPT(Compound(self.compound.filePath))
                        result = temp_ppt.__parse_ppt_normal_for_ole__(powerpoint_document, current_user)
                    if result != None:
                        if not (os.path.isdir(self.compound.tmp_path + self.compound.fileName + "_extracted")):
                            os.makedirs(os.path.join(self.compound.tmp_path + self.compound.fileName + "_extracted"))
                        self.compound.ole_path.append(self.compound.tmp_path + self.compound.fileName + "_extracted/" + self.compound.fileName + "_" + str(img_num) + ".txt")
                        temp = open(self.compound.tmp_path + self.compound.fileName + "_extracted/" + self.compound.fileName + "_" + str(img_num) + ".txt", 'w', encoding='utf-16')
                        temp.write(result)
                        temp.close()
                        img_num += 1

                    # HWP
                    if section_data != "":
                        if not (os.path.isdir(self.compound.tmp_path + self.compound.fileName + "_extracted")):
                            os.makedirs(os.path.join(self.compound.tmp_path + self.compound.fileName + "_extracted"))
                        self.compound.ole_path.append(self.compound.tmp_path + self.compound.fileName + "_extracted/" + self.compound.fileName + "_" + str(img_num) + ".txt")
                        temp = open(self.compound.tmp_path + self.compound.fileName + "_extracted/" + self.compound.fileName + "_" + str(img_num) + ".txt", 'w', encoding='utf-16')
                        temp.write(section_data)
                        temp.close()
                        img_num += 1

            except Exception:
                continue
        

        data = len(ole.direntries)
        #print(data)
    
        ole_fp.close()
        """

    def __parse_xls_normal_for_ole__(self, workbook):
        RECORD_HEADER_SIZE = 4
        records = []

        # 원하는 스트림 f에 모두 읽어오기
        temp = workbook
        f = bytearray(temp)
        # 스트림 내부 모두 파싱해서 데이터 출력
        tempOffset = 0
        content = ""  # 최종 저장될 스트링
        substream = 0
        while tempOffset < len(f):
            dic = {}
            dic['offset'] = tempOffset
            dic['type'] = struct.unpack('<H', f[tempOffset: tempOffset + 0x02])[0]
            dic['length'] = struct.unpack('<H', f[tempOffset + 0x02: tempOffset + 0x04])[0]
            dic['data'] = f[tempOffset + RECORD_HEADER_SIZE: tempOffset + RECORD_HEADER_SIZE + dic['length']]
            tempOffset = tempOffset + RECORD_HEADER_SIZE + dic['length']
            records.append(dic)

        arrStXFType = []
        b_drawing = False
        drawing_data = b''
        for record in records:
            if record['type'] == 0xE0:  # GlobalStream XF Type
                stGlobalStreamXF = {}
                stGlobalStreamXF['ifnt'] = record['data'][0:2]
                stGlobalStreamXF['ifmt'] = record['data'][2:4]
                stGlobalStreamXF['Flags'] = record['data'][4:6]
                arrStXFType.append(stGlobalStreamXF)
            if record['type'] == 0xFC:
                sstNum = records.index(record)
                sstOffset = record['offset']
                sstLen = record['length']
            if record['type'] == 0x3C:  # Continue markerz
                # SST
                f[record['offset']:record['offset'] + 4] = bytearray(b'\xAA\xAA\xAA\xAA')

                # Drawing
                if b_drawing == True:
                    drawing_data += record['data']
                else:
                    b_drawing = False

            if record['type'] == 0x85:  # BundleSheet Name
                tempOffset = 6  # GLOBALSTREAM_BUNDLESHEET size
                cch = struct.unpack('<b', record['data'][tempOffset: tempOffset + 1])[0]
                reserved = record['data'][tempOffset + 1: tempOffset + 2]
                tempOffset += 2

                # reserved 0 is single-byte characters
                if reserved == b'\x00':
                    content += record['data'][tempOffset: tempOffset + cch].decode("ascii")
                # reserved 1 is single-byte characters
                if reserved == b'\x01':
                    content += record['data'][tempOffset: tempOffset + cch * 2].decode("utf-16")

        # SST
        content += "\n"

        cntStream = sstOffset + 4
        cstTotal = struct.unpack('<I', f[cntStream: cntStream + 4])[0]
        cstUnique = struct.unpack('<I', f[cntStream + 4: cntStream + 8])[0]
        cntStream += 8

        for i in range(0, cstUnique):
            string = ""
            if (cntStream > len(f)):
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
                    if f[cntStream: cntStream + 4] == b'\xAA\xAA\xAA\xAA':
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

                    if f[cntStream: cntStream + 4] == b'\xAA\xAA\xAA\xAA':
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
            content += string + '\n'
            # print(str(i) + " : " + string)

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
            if bSubstream == True and record['type'] == 0x3C:  # 도형 내 텍스트
                if record['data'][0] == 1:  # Ascii Data
                    for i in range(0, len(record['data']) - 1, 2):
                        content += str(record['data'][1 + i: 1 + i + 2].decode("utf-16"))

            if bSubstream == True and record['type'] == 0x27E:  # 숫자 RK
                row = record['data'][0:2]
                col = record['data'][2:4]
                idxToXF = struct.unpack('<H', record['data'][4:6])[0]
                value = b'\x00\x00\x00\x00' + record['data'][6:10]

                strRKValue = self.__translate_RK_value__(value)
                strRKValue = self.__convert_to_XF_type__(strRKValue, idxToXF, arrStXFType)

        return content

    def inflateBodytext(self, section, isCompressed):
        msg = bytearray()

        if isCompressed:
            decompress = zlib.decompressobj(-zlib.MAX_WBITS)
            try:
                stream = decompress.decompress(section)
                stream += decompress.flush()
            except:
                return False
        else:
            stream = section

        streamLen = len(stream)

        nPos = 0
        RecordHeader = stream[0:4]

        while (RecordHeader[0] >= 0x40) and (RecordHeader[0] <= 0x60):
            try:
                nRecordLength = (RecordHeader[3] << 4) | (RecordHeader[2] >> 4)
                nRecordPos = 4

                if RecordHeader[0] == 0x43:
                    temp = stream[nPos + 4:nPos + 4 + 2]
                    uWord = struct.unpack('<H', temp)

                    while True:
                        if 0x0001 <= uWord[0] <= 0x0017:
                            if uWord[0] != 0x00A and uWord[0] != 0x000D:
                                nRecordPos += 16
                            else:
                                break
                        else:
                            break

                        if nRecordLength < nRecordPos + 2:
                            break

                        temp = stream[nPos + nRecordPos:nPos + nRecordPos + 2]
                        uWord = struct.unpack('<H', temp)

                    if (nRecordLength - nRecordPos + 4) / 2 >= 1:
                        index = (nRecordLength - nRecordPos + 4) / 2

                        i = 0
                        while i < int(index):
                            temp = stream[nPos + nRecordPos + i * 2:nPos + nRecordPos + i * 2 + 2]
                            uWord = struct.unpack('<H', temp)
                            if 0x0001 <= uWord[0] <= 0x0017:
                                if uWord[0] != 0x00A and uWord[0] != 0x000D:
                                    if uWord[0] == 0x0009:
                                        msg.append(0x20)
                                        msg.append(0x00)
                                    i += 7
                                    continue
                            if uWord[0] == 0x000D:
                                msg.append(0x0A)
                                msg.append(0x00)
                            msg.append(stream[nPos + nRecordPos + i * 2])
                            msg.append(stream[nPos + nRecordPos + i * 2 + 1])
                            i += 1

                nPos += nRecordLength + 4
                if streamLen <= nPos:
                    break
                else:
                    RecordHeader = stream[nPos:nPos + 4]
            except:
                break

        # 필터링
        if len(msg) > 0:
            try:
                msg = msg.decode("utf-16", 'ignore')
            except:
                msg = ""

            return msg
        else:
            return False

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
        content = ""  # 최종 저장될 스트링
        substream = 0
        while tempOffset < len(f):
            dic = {}
            dic['offset'] = tempOffset
            dic['type'] = struct.unpack('<H', f[tempOffset: tempOffset + 0x02])[0]
            dic['length'] = struct.unpack('<H', f[tempOffset + 0x02: tempOffset + 0x04])[0]
            dic['data'] = f[tempOffset + RECORD_HEADER_SIZE: tempOffset + RECORD_HEADER_SIZE + dic['length']]
            tempOffset = tempOffset + RECORD_HEADER_SIZE + dic['length']
            records.append(dic)

        arrStXFType = []
        b_drawing = False
        drawing_data = b''
        for record in records:
            if record['type'] == 0xE0:  # GlobalStream XF Type
                stGlobalStreamXF = {}
                stGlobalStreamXF['ifnt'] = record['data'][0:2]
                stGlobalStreamXF['ifmt'] = record['data'][2:4]
                stGlobalStreamXF['Flags'] = record['data'][4:6]
                arrStXFType.append(stGlobalStreamXF)
            if record['type'] == 0xFC:
                sstNum = records.index(record)
                sstOffset = record['offset']
                sstLen = record['length']
            if record['type'] == 0x3C:  # Continue markerz
                # SST
                f[record['offset']:record['offset'] + 4] = bytearray(b'\xAA\xAA\xAA\xAA')

                # Drawing
                if b_drawing == True:
                    drawing_data += record['data']
                else:
                    b_drawing = False

            if record['type'] == 0x85:  # BundleSheet Name
                tempOffset = 6  # GLOBALSTREAM_BUNDLESHEET size
                cch = struct.unpack('<b', record['data'][tempOffset: tempOffset + 1])[0]
                reserved = record['data'][tempOffset + 1: tempOffset + 2]
                tempOffset += 2

                # reserved 0 is single-byte characters
                if reserved == b'\x00':
                    content += record['data'][tempOffset: tempOffset + cch].decode("ascii")
                # reserved 1 is single-byte characters
                if reserved == b'\x01':
                    content += record['data'][tempOffset: tempOffset + cch * 2].decode("utf-16")
            if record['type'] == 0xEB:
                b_drawing = True
                drawing_data += record['data']

        # SST
        content += "\n"

        cntStream = sstOffset + 4
        cstTotal = struct.unpack('<I', f[cntStream: cntStream + 4])[0]
        cstUnique = struct.unpack('<I', f[cntStream + 4: cntStream + 8])[0]
        cntStream += 8

        for i in range(0, cstUnique):
            string = ""
            if (cntStream > len(f)):
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
                    if f[cntStream: cntStream + 4] == b'\xAA\xAA\xAA\xAA':
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

                    if f[cntStream: cntStream + 4] == b'\xAA\xAA\xAA\xAA':
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
            content += string + '\n'
            # print(str(i) + " : " + string)

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

        if b_drawing == True:
            # Drawing
            #print(drawing_data)
            drawing_offset = 0
            rh_recType = struct.unpack('<H', drawing_data[drawing_offset + 2 : drawing_offset + 4])[0]
            rh_recLen = struct.unpack('<I', drawing_data[drawing_offset + 4: drawing_offset + 8])[0]
            drawing_offset += 0x08

            drawingGroup_rh_recType = struct.unpack('<H', drawing_data[drawing_offset + 2: drawing_offset + 4])[0]
            drawingGroup_rh_recLen = struct.unpack('<I', drawing_data[drawing_offset + 4: drawing_offset + 8])[0]
            drawing_offset += 0x08

            drawingGroup_head_spidMax = struct.unpack('<I', drawing_data[drawing_offset : drawing_offset + 4])[0]
            drawing_offset += 0x04
            drawingGroup_head_cidcl = struct.unpack('<I', drawing_data[drawing_offset: drawing_offset + 4])[0]
            drawing_offset += 0x04
            drawingGroup_head_cspSaved = struct.unpack('<I', drawing_data[drawing_offset: drawing_offset + 4])[0]
            drawing_offset += 0x04
            drawingGroup_head_cdgSaved = struct.unpack('<I', drawing_data[drawing_offset: drawing_offset + 4])[0]
            drawing_offset += 0x04

            ### 몇 번 반복해야하지? ###
            drawingGroup_rgidcl_dgid = drawing_data[drawing_offset: drawing_offset + 4]
            drawing_offset += 0x04
            drawingGroup_rgidcl_cspidCur = drawing_data[drawing_offset: drawing_offset + 4]
            drawing_offset += 0x04

            container_rh_recType = struct.unpack('<H', drawing_data[drawing_offset + 2: drawing_offset + 4])[0]
            container_rh_recLen = struct.unpack('<I', drawing_data[drawing_offset + 4: drawing_offset + 8])[0]      # size of rgfb
            drawing_offset += 0x08

            img_num = 0

            while drawing_offset < len(drawing_data):
                blip_rh_Type = struct.unpack('<H', drawing_data[drawing_offset + 2: drawing_offset + 4])[0]
                blip_rh_recLen = struct.unpack('<I', drawing_data[drawing_offset + 4: drawing_offset + 8])[0]      # size of rgfb
                drawing_offset += 0x08

                if blip_rh_Type == 0xF00B:
                    break

                blip_btWin32 = drawing_data[drawing_offset : drawing_offset + 0x01]
                drawing_offset += 0x01
                blip_btMacOS = drawing_data[drawing_offset : drawing_offset + 0x01]
                drawing_offset += 0x01
                blip_rgbUid = drawing_data[drawing_offset : drawing_offset + 0x10]
                drawing_offset += 0x10
                blip_tag = drawing_data[drawing_offset: drawing_offset + 0x02]
                drawing_offset += 0x02
                blip_size = drawing_data[drawing_offset: drawing_offset + 0x04]
                drawing_offset += 0x04
                blip_cRef = drawing_data[drawing_offset: drawing_offset + 0x04]
                drawing_offset += 0x04
                blip_foDelay = drawing_data[drawing_offset: drawing_offset + 0x04]
                drawing_offset += 0x04
                blip_unused1 = drawing_data[drawing_offset : drawing_offset + 0x01]
                drawing_offset += 0x01
                blip_cbName = struct.unpack('<B', drawing_data[drawing_offset: drawing_offset + 0x01])[0]
                drawing_offset += 0x01
                blip_unused2 = drawing_data[drawing_offset: drawing_offset + 0x01]
                drawing_offset += 0x01
                blip_unused3 = drawing_data[drawing_offset: drawing_offset + 0x01]
                drawing_offset += 0x01
                blip_nameData = None
                if blip_cbName != 0:
                    blip_nameData = drawing_data[drawing_offset: drawing_offset + blip_cbName]
                    drawing_offset += blip_cbName

                if drawing_offset + 8 > len(drawing_data):
                    break

                embedded_blip_rh_ver_instance = struct.unpack('<H', drawing_data[drawing_offset: drawing_offset + 2])[0]
                embedded_blip_rh_Type = struct.unpack('<H', drawing_data[drawing_offset + 2: drawing_offset + 4])[0]
                embedded_blip_rh_recLen = struct.unpack('<I', drawing_data[drawing_offset + 4: drawing_offset + 8])[0]
                drawing_offset += 0x08
                embedded_size = embedded_blip_rh_recLen

                # JPEG 발견! 이후 작성..
                embedded_blip_rgbUid1 = drawing_data[drawing_offset : drawing_offset + 0x10]
                drawing_offset += 0x10
                embedded_size -= 0x10
                embedded_blip_rgbUid2 = None

                if int(embedded_blip_rh_ver_instance / 0x10) == 0x46B or int(embedded_blip_rh_ver_instance / 0x10) == 0x6E3:
                    embedded_blip_rgbUid2 = drawing_data[drawing_offset: drawing_offset + 0x10]
                    drawing_offset += 0x10
                    embedded_size -= 0x10


                if embedded_blip_rh_Type != 0xF01A and embedded_blip_rh_Type != 0xF01B and embedded_blip_rh_Type != 0xF01C and \
                        embedded_blip_rh_Type != 0xF01D and embedded_blip_rh_Type != 0xF01E and embedded_blip_rh_Type != 0xF01F and \
                        embedded_blip_rh_Type != 0xF029:
                    break


                extension = ""
                if embedded_blip_rh_Type == 0xF01A:
                    extension = ".emf"
                    embedded_blip_metafileheader = drawing_data[drawing_offset: drawing_offset + 0x22]
                    drawing_offset += 0x22
                    embedded_size -= 0x22
                elif embedded_blip_rh_Type == 0xF01B:
                    extension = ".wmf"
                    embedded_blip_metafileheader = drawing_data[drawing_offset: drawing_offset + 0x22]
                    drawing_offset += 0x22
                    embedded_size -= 0x22
                elif embedded_blip_rh_Type == 0xF01C:
                    extension = ".pict"
                    embedded_blip_metafileheader = drawing_data[drawing_offset: drawing_offset + 0x22]
                    drawing_offset += 0x22
                    embedded_size -= 0x22
                elif embedded_blip_rh_Type == 0xF01D:
                    extension = ".jpg"
                    embedded_blip_tag = drawing_data[drawing_offset: drawing_offset + 0x01]
                    drawing_offset += 0x01
                    embedded_size -= 0x01
                elif embedded_blip_rh_Type == 0xF01E:
                    extension = ".png"
                    embedded_blip_tag = drawing_data[drawing_offset: drawing_offset + 0x01]
                    drawing_offset += 0x01
                    embedded_size -= 0x01
                elif embedded_blip_rh_Type == 0xF01F:
                    extension = ".dib"
                    embedded_blip_tag = drawing_data[drawing_offset: drawing_offset + 0x01]
                    drawing_offset += 0x01
                    embedded_size -= 0x01
                elif embedded_blip_rh_Type == 0xF029:
                    extension = ".tiff"
                    embedded_blip_tag = drawing_data[drawing_offset: drawing_offset + 0x01]
                    drawing_offset += 0x01
                    embedded_size -= 0x01

                if extension == "":
                    break

                if not (os.path.isdir(self.compound.tmp_path + self.compound.fileName + "_extracted")):
                    os.makedirs(os.path.join(self.compound.tmp_path + self.compound.fileName + "_extracted"))

                embedded_data = drawing_data[drawing_offset : drawing_offset + embedded_size]
                drawing_offset += embedded_size

                # 제대로 다 가져와 지는지 확인하기.
                self.compound.ole_path.append(self.compound.tmp_path + self.compound.fileName + "_extracted/" + self.compound.fileName + "_" + str(img_num) + extension)
                embedded_fp = open(self.compound.tmp_path + self.compound.fileName + "_extracted/" + self.compound.fileName + "_" + str(img_num) + extension, 'wb')
                img_num += 1
                embedded_fp.write(embedded_data)
                embedded_fp.close()

        # SubStream
        bSubstream = False

        for record in records:
            if record['type'] == 0x809 and record['data'][0:3] == b'\x00\x06\x10':
                bSubstream = True
            if bSubstream == True and record['type'] == 0x3C:  # 도형 내 텍스트
                if record['data'][0] == 1:  # Ascii Data
                    for i in range(0, len(record['data']) - 1, 2):
                        content += str(record['data'][1 + i: 1 + i + 2].decode("utf-16"))

            if bSubstream == True and record['type'] == 0x27E:  # 숫자 RK
                row = record['data'][0:2]
                col = record['data'][2:4]
                idxToXF = struct.unpack('<H', record['data'][4:6])[0]
                value = b'\x00\x00\x00\x00' + record['data'][6:10]

                strRKValue = self.__translate_RK_value__(value)
                strRKValue = self.__convert_to_XF_type__(strRKValue, idxToXF, arrStXFType)
        self.compound.content = content

        """
        ### OLE
        ole = olefile.OleFileIO(self.compound.filePath)
        ole_fp = open(self.compound.filePath, 'rb')
        img_num = 0
        for i in range(0, len(ole.direntries)):
            try:
                if ole.direntries[i].name == '\x01Ole10Native':  # Multimedia
                    self.compound.has_ole = True
                    ole_fp.seek((ole.direntries[i].isectStart + 1) * 0x200)
                    ole_data = ole_fp.read(ole.direntries[i].size)

                    ole_data_offset = 6  # Header
                    ole_data_offset = ole_data.find(b'\x00', ole_data_offset + 1)  # Label
                    data_name = ole_data[6: ole_data_offset].decode('ASCII')
                    ole_data_offset = ole_data.find(b'\x00', ole_data_offset + 1)  # OrgPath
                    ole_data_offset += 8  # UType
                    ole_data_offset = ole_data.find(b'\x00', ole_data_offset + 1)  # DataPath
                    ole_data_offset += 1
                    data_size = struct.unpack('<I', ole_data[ole_data_offset: ole_data_offset + 4])[0]
                    ole_data_offset += 4
                    data = ole_data[ole_data_offset: ole_data_offset + data_size]

                    if not (os.path.isdir(self.compound.tmp_path + self.compound.fileName + "_extracted")):
                        os.makedirs(os.path.join(self.compound.tmp_path + self.compound.fileName + "_extracted"))

                    self.compound.ole_path.append(
                        self.compound.tmp_path + self.compound.fileName + "_extracted/" + data_name)
                    temp = open(self.compound.tmp_path + self.compound.fileName + "_extracted/" + data_name, 'wb')
                    temp.write(data)
                    temp.close()

                elif ole.direntries[i].name == 'Package':  # OOXML 처리
                    self.compound.has_ole = True
                    ole_fp.seek((ole.direntries[i].isectStart + 1) * 0x200)
                    ole_data = ole_fp.read(ole.direntries[i].size)
                    if ole_data.find(b'\x78\x6C\x2F\x77\x6F\x72\x6B\x62\x6F\x6F\x6B\x2E\x78\x6D\x6C') > 0:  # XLSX
                        extension = ".xlsx"
                    elif ole_data.find(
                            b'\x77\x6F\x72\x64\x2F\x64\x6F\x63\x75\x6D\x65\x6E\x74\x2E\x78\x6D\x6C') > 0:  # DOCX
                        extension = ".docx"
                    elif ole_data.find(
                            b'\x70\x70\x74\x2F\x70\x72\x65\x73\x65\x6E\x74\x61\x74\x69\x6F\x6E\x2E\x78\x6D\x6C') > 0:  # PPTX
                        extension = ".pptx"
                    else:
                        extension = ".zip"

                    if not (os.path.isdir(self.compound.tmp_path + self.compound.fileName + "_extracted")):
                        os.makedirs(os.path.join(self.compound.tmp_path + self.compound.fileName + "_extracted"))

                    self.compound.ole_path.append(
                        self.compound.tmp_path + self.compound.fileName + "_extracted/" + self.compound.fileName + "_" + str(
                            img_num) + extension)
                    temp = open(self.compound.tmp_path + self.compound.fileName + "_extracted/" + self.compound.fileName + "_" + str(
                        img_num) + extension, 'wb')
                    temp.write(ole_data)
                    temp.close()
                    img_num += 1
                elif ole.direntries[i].name == 'CONTENTS':  # PDF
                    self.compound.has_ole = True
                    ole_fp.seek((ole.direntries[i].isectStart + 1) * 0x200)
                    ole_data = ole_fp.read(ole.direntries[i].size)

                    if not (os.path.isdir(self.compound.tmp_path + self.compound.fileName + "_extracted")):
                        os.makedirs(os.path.join(self.compound.tmp_path + self.compound.fileName + "_extracted"))

                    self.compound.ole_path.append(
                        self.compound.tmp_path + self.compound.fileName + "_extracted/" + self.compound.fileName + "_" + str(
                            img_num) + ".pdf")
                    temp = open(
                        self.compound.tmp_path + self.compound.fileName + "_extracted/" + self.compound.fileName + "_" + str(
                            img_num) + ".pdf", 'wb')
                    temp.write(ole_data)
                    temp.close()
                    img_num += 1
                elif ole.direntries[i].name[0:3] == 'MBD':
                    self.compound.has_ole = True
                    word_document = None
                    table = None
                    powerpoint_document = None
                    current_user = None
                    workbook = None
                    section_data = ""
                    for j in range(0, len(ole.direntries[i].kids)):
                        if ole.direntries[i].kids[j].name == "WordDocument":
                            ole_fp.seek((ole.direntries[i].kids[j].isectStart + 1) * 0x200)
                            word_document = ole_fp.read(ole.direntries[i].kids[j].size)
                        elif ole.direntries[i].kids[j].name == "1Table":
                            ole_fp.seek((ole.direntries[i].kids[j].isectStart + 1) * 0x200)
                            table = ole_fp.read(ole.direntries[i].kids[j].size)
                        elif ole.direntries[i].kids[j].name == "0Table":
                            ole_fp.seek((ole.direntries[i].kids[j].isectStart + 1) * 0x200)
                            table = ole_fp.read(ole.direntries[i].kids[j].size)
                        elif ole.direntries[i].kids[j].name == "PowerPoint Document":
                            ole_fp.seek((ole.direntries[i].kids[j].isectStart + 1) * 0x200)
                            powerpoint_document = ole_fp.read(ole.direntries[i].kids[j].size)
                        elif ole.direntries[i].kids[j].name == "Current User":
                            idx = ole.root.isectStart
                            chain = [idx]
                            while True:
                                idx = ole.fat[idx]
                                if idx == 4294967294:
                                    break
                                chain.append(idx)
                            out = bytearray(b'')

                            for idx in chain:
                                pos = (idx + 1) * 512
                                ole_fp.seek(pos)
                                d = ole_fp.read(512)
                                out += d
                            current_user = out[64 * (ole.direntries[i].kids[j].isectStart):64 * (
                                ole.direntries[i].kids[j].isectStart) + ole.direntries[i].kids[j].size]
                        elif ole.direntries[i].kids[j].name == "Workbook":
                            ole_fp.seek((ole.direntries[i].kids[j].isectStart + 1) * 0x200)
                            workbook = ole_fp.read(ole.direntries[i].kids[j].size)
                        elif ole.direntries[i].kids[j].name == "BodyText":
                            section_data = ""
                            for k in range(0, len(ole.direntries[i].kids[j].kids)):
                                ole_fp.seek((ole.direntries[i].kids[j].kids[k].isectStart + 1) * 0x200)
                                temp_section_data = ole_fp.read(ole.direntries[i].kids[j].kids[k].size)
                                if temp_section_data[0:2] == b'\x42\x00':
                                    is_compressed = False
                                else:
                                    is_compressed = True
                                msg = self.inflateBodytext(temp_section_data, is_compressed)
                                if msg is not False:
                                    section_data += msg

                    # DOC
                    from carpe_doc import DOC
                    result = None
                    if word_document != None and table != None:
                        temp_doc = DOC(Compound(self.compound.filePath))
                        result = temp_doc.__parse_doc_normal_for_ole__(word_document, table)
                    if result != None:
                        if not (os.path.isdir(self.compound.tmp_path + self.compound.fileName + "_extracted")):
                            os.makedirs(os.path.join(self.compound.tmp_path + self.compound.fileName + "_extracted"))
                        self.compound.ole_path.append(
                            self.compound.tmp_path + self.compound.fileName + "_extracted/" + self.compound.fileName + "_" + str(
                                img_num) + ".txt")
                        temp = open(
                            self.compound.tmp_path + self.compound.fileName + "_extracted/" + self.compound.fileName + "_" + str(
                                img_num) + ".txt", 'w', encoding='utf-16')
                        temp.write(result)
                        temp.close()
                        img_num += 1

                    # XLS
                    result = None
                    if workbook != None:
                        result = self.__parse_xls_normal_for_ole__(workbook)
                    if result != None:
                        if not (os.path.isdir(self.compound.tmp_path + self.compound.fileName + "_extracted")):
                            os.makedirs(os.path.join(self.compound.tmp_path + self.compound.fileName + "_extracted"))
                        self.compound.ole_path.append(
                            self.compound.tmp_path + self.compound.fileName + "_extracted/" + self.compound.fileName + "_" + str(
                                img_num) + ".txt")
                        temp = open(
                            self.compound.tmp_path + self.compound.fileName + "_extracted/" + self.compound.fileName + "_" + str(
                                img_num) + ".txt", 'w', encoding='utf-16')
                        temp.write(result)
                        temp.close()
                        img_num += 1

                    # PPT
                    from carpe_ppt import PPT
                    from carpe_compound import Compound
                    result = None
                    if powerpoint_document != None and current_user != None:
                        temp_ppt = PPT(Compound(self.compound.filePath))
                        result = temp_ppt.__parse_ppt_normal_for_ole__(powerpoint_document, current_user)
                    if result != None:
                        if not (os.path.isdir(self.compound.tmp_path + self.compound.fileName + "_extracted")):
                            os.makedirs(os.path.join(self.compound.tmp_path + self.compound.fileName + "_extracted"))
                        self.compound.ole_path.append(
                            self.compound.tmp_path + self.compound.fileName + "_extracted/" + self.compound.fileName + "_" + str(
                                img_num) + ".txt")
                        temp = open(
                            self.compound.tmp_path + self.compound.fileName + "_extracted/" + self.compound.fileName + "_" + str(
                                img_num) + ".txt", 'w', encoding='utf-16')
                        temp.write(result)
                        temp.close()
                        img_num += 1

                    # HWP
                    if section_data != "":
                        if not (os.path.isdir(self.compound.tmp_path + self.compound.fileName + "_extracted")):
                            os.makedirs(os.path.join(self.compound.tmp_path + self.compound.fileName + "_extracted"))
                        self.compound.ole_path.append(
                            self.compound.tmp_path + self.compound.fileName + "_extracted/" + self.compound.fileName + "_" + str(
                                img_num) + ".txt")
                        temp = open(
                            self.compound.tmp_path + self.compound.fileName + "_extracted/" + self.compound.fileName + "_" + str(
                                img_num) + ".txt", 'w', encoding='utf-16')
                        temp.write(section_data)
                        temp.close()
                        img_num += 1

            except Exception:
                continue

        data = len(ole.direntries)
        # print(data)

        ole_fp.close()
        """

