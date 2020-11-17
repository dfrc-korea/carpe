# -*- coding:utf-8 -*-
# carpe_hwp.py
import os
import compoundfiles
import struct
import datetime
import zlib
import warnings
import time
import shutil
import zipfile


class HWP:
    CONST_FILEHEADER_SIG = b'HWP Document File'
    CONST_SUMMARY_SIG = b'\xFE\xFF\x00\x00'
    CONST_SUMMARY_CLSID = b'\x60\xB6\xA2\x9F\x61\x10\xD4\x11\xB4\xC6\x00\x60\x97\xC0\x9D\x8C'
    CONST_HWP_SBLOCK_SIZE = 64

    def __init__(self, filePath):
        warnings.filterwarnings("ignore")

        #if os.path.exists(filePath):
        try:
            self.fp = compoundfiles.CompoundFileReader(filePath)
            self.parseFileHeader()
            self.isDamaged = False
        except:
            self.fp = open(filePath, 'rb')
            self.isDamaged = True
        #else:
        #    self.fp = None

        if self.fp is not None:
            self.fileName = os.path.basename(filePath)
            self.filePath = filePath
            self.fileSize = os.path.getsize(filePath)
            self.fileType = os.path.splitext(filePath)[1][1:]

            self.has_metadata = False
            self.metaList = {'Title': "", 'Subject': "", 'Author': "", 'Tags':"", 'Explanation': "", 'LastSavedBy': "",'Version': "", 'Date': "",\
        'LastPrintedTime': "", 'CreatedTime': "",'LastSavedTime': "", 'Comment': "", 'RevisionNumber': "", 'Category': "", 'Manager': "",\
        'Company': "", 'ProgramName': "", 'TotalTime': "", 'Creator': "", 'Trapped': ""}

            self.has_content = False
            self.content = ""

            self.has_multimedia = False

            if self.isDamaged:
                self.isCompressed = None
                self.isEncrypted = None

    def parseFileHeader(self):
        fileHeader = self.fp.open('FileHeader').read()
        file_signature = fileHeader[0:0x20]

        search_result = file_signature.find(self.CONST_FILEHEADER_SIG)

        if search_result != -1:
            uOption = struct.unpack('<i', fileHeader[0x24:0x28])[0]

            if uOption & 0x00000001:
                self.isCompressed = True
            else:
                self.isCompressed = False

            if uOption & 0x00000002 or uOption & 0x00000004:
                self.isEncrypted = True
            else:
                self.isEncrypted = False
        else:
            self.isDamaged = True
            self.isEncrypted = None
            self.isCompressed = None

    def parse(self, ole_path):

        if self.fp is None:
            return False

        # Normal File
        if not self.isDamaged:
            # Parsing the meta
            self.parseMetadata()

            # Parsing the contents
            if not self.isEncrypted:
                #self.parseDocInfo()
                self.parseContents()
                self.ole_path = ole_path
                if not os.path.exists(self.ole_path):
                    os.mkdir(self.ole_path)
                self.parseMultimedia()

                # Null 처리 해야함
                if len(self.content) > 0:
                    self.has_content = True

        # Damaged File
        else:
            #Parsing the meta
            self.parseDamagedMetadta()

            #Parsing the contents
            self.parseDamagedContents()

    def verifySummaryinfo(self, block):
        sig = block[0x00:0x04]
        CLSID = block[0x08:0x18]
        propertySet = block[0x1C:0x2C]

        if sig == self.CONST_SUMMARY_SIG and CLSID == self.CONST_SUMMARY_CLSID and propertySet == self.CONST_SUMMARY_CLSID:
            return True
        else:
            return False

    def parseMetadata(self):
        try:
            fpSummary = self.fp.open('HwpSummaryInformation').read()
            self.parseSummaryInfo(fpSummary)
            return True
        except:
            return False

    def parseSummaryInfo(self, fpSummary):
        records = []
		
        metaNum = 0
        startOffset = struct.unpack('<i', fpSummary[0x2C: 0x30])[0]
        tempOffset = startOffset
        recordCount = struct.unpack('<i', fpSummary[tempOffset + 0x04: tempOffset + 0x08])[0]
        tempOffset += 0x08

        for i in range(0, recordCount):
            recordType = struct.unpack('<i', fpSummary[tempOffset: tempOffset + 0x04])[0]
            recordOffset = struct.unpack('<i', fpSummary[tempOffset + 0x04: tempOffset + 0x08])[0]
            records.append({'type': recordType, 'offset': recordOffset})
            tempOffset += 0x08

        # Parse Records
        for record in records:
            # 1. Title
            if record['type'] is 0x02:
                recordStartOffset = startOffset + record['offset']
                entryType = struct.unpack('<I', fpSummary[recordStartOffset: recordStartOffset + 4])[0]
                entryLength = struct.unpack('<i', fpSummary[recordStartOffset + 4: recordStartOffset + 8])[0]
                if entryLength > 1:
                    try:
                        if entryType == 0x1E:
                            entryData = fpSummary[recordStartOffset + 8: recordStartOffset + 8 + (entryLength)]
                            tempData = entryData.decode('euc-kr')[0:-1]
                            tempData = tempData.replace('\r\n', "")
                        elif entryType == 0x1F:
                            entryData = fpSummary[recordStartOffset + 8: recordStartOffset + 8 + (entryLength * 2)]
                            tempData = entryData.decode('utf-16')[0:-1]
                            tempData = tempData.replace('\r\n', "")
                        self.metaList['Title'] = tempData
                        metaNum += 1
                    except:
                        self.metaList['Title'] = ''

            # 2. Subject
            elif record['type'] is 0x03:
                recordStartOffset = startOffset + record['offset']
                entryType = struct.unpack('<I', fpSummary[recordStartOffset: recordStartOffset + 4])[0]
                entryLength = struct.unpack('<i', fpSummary[recordStartOffset + 4: recordStartOffset + 8])[0]
                if entryLength > 1:
                    try:
                        if entryType == 0x1E:
                            entryData = fpSummary[recordStartOffset + 8: recordStartOffset + 8 + (entryLength)]
                            tempData = entryData.decode('euc-kr')[0:-1]
                            tempData = tempData.replace('\r\n', "")
                        elif entryType == 0x1F:
                            entryData = fpSummary[recordStartOffset + 8: recordStartOffset + 8 + (entryLength * 2)]
                            tempData = entryData.decode('utf-16')[0:-1]
                            tempData = tempData.replace('\r\n', "")
                        self.metaList['Subject'] = tempData
                        metaNum += 1
                    except:
                        self.metaList['Subject'] = ''

            # 3. Author
            elif record['type'] is 0x04:
                recordStartOffset = startOffset + record['offset']
                entryType = struct.unpack('<I', fpSummary[recordStartOffset: recordStartOffset + 4])[0]
                entryLength = struct.unpack('<i', fpSummary[recordStartOffset + 4: recordStartOffset + 8])[0]
                if entryLength > 1:
                    try:
                        if entryType == 0x1E:
                            entryData = fpSummary[recordStartOffset + 8: recordStartOffset + 8 + (entryLength)]
                            tempData = entryData.decode('euc-kr')[0:-1]
                            tempData = tempData.replace('\r\n', "")
                        elif entryType == 0x1F:
                            entryData = fpSummary[recordStartOffset + 8: recordStartOffset + 8 + (entryLength * 2)]
                            tempData = entryData.decode('utf-16')[0:-1]
                            tempData = tempData.replace('\r\n', "")
                        self.metaList['Author'] = tempData
                        metaNum += 1
                    except:
                        self.metaList['Author'] = ''

            # 4. Keyword
            elif record['type'] is 0x05:
                recordStartOffset = startOffset + record['offset']
                entryType = struct.unpack('<I', fpSummary[recordStartOffset: recordStartOffset + 4])[0]
                entryLength = struct.unpack('<i', fpSummary[recordStartOffset + 4: recordStartOffset + 8])[0]
                if entryLength > 1:
                    try:
                        if entryType == 0x1E:
                            entryData = fpSummary[recordStartOffset + 8: recordStartOffset + 8 + (entryLength)]
                            tempData = entryData.decode('euc-kr')[0:-1]
                            tempData = tempData.replace('\r\n', "")
                        elif entryType == 0x1F:
                            entryData = fpSummary[recordStartOffset + 8: recordStartOffset + 8 + (entryLength * 2)]
                            tempData = entryData.decode('utf-16')[0:-1]
                            tempData = tempData.replace('\r\n', "")
                        self.metaList['Tags'] = tempData
                        metaNum += 1
                    except:
                        self.metaList['Tags'] = ''

            # 5. explanation
            elif record['type'] is 0x06:
                recordStartOffset = startOffset + record['offset']
                entryType = struct.unpack('<I', fpSummary[recordStartOffset: recordStartOffset + 4])[0]
                entryLength = struct.unpack('<i', fpSummary[recordStartOffset + 4: recordStartOffset + 8])[0]
                if entryLength > 1:
                    try:
                        if entryType == 0x1E:
                            entryData = fpSummary[recordStartOffset + 8: recordStartOffset + 8 + (entryLength)]
                            tempData = entryData.decode('euc-kr')[0:-1]
                            tempData = tempData.replace('\r\n', "")
                        elif entryType == 0x1F:
                            entryData = fpSummary[recordStartOffset + 8: recordStartOffset + 8 + (entryLength * 2)]
                            tempData = entryData.decode('utf-16')[0:-1]
                            tempData = tempData.replace('\r\n', "")
                        self.metaList['Explanation'] = tempData
                        metaNum += 1
                    except:
                        self.metaList['Explanation'] = ''

            # 6. LastSaveBy
            elif record['type'] is 0x08:
                recordStartOffset = startOffset + record['offset']
                entryType = struct.unpack('<I', fpSummary[recordStartOffset: recordStartOffset + 4])[0]
                entryLength = struct.unpack('<i', fpSummary[recordStartOffset + 4: recordStartOffset + 8])[0]
                if entryLength > 1:
                    try:
                        if entryType == 0x1E:
                            entryData = fpSummary[recordStartOffset + 8: recordStartOffset + 8 + (entryLength)]
                            tempData = entryData.decode('euc-kr')[0:-1]
                            tempData = tempData.replace('\r\n', "")
                        elif entryType == 0x1F:
                            entryData = fpSummary[recordStartOffset + 8: recordStartOffset + 8 + (entryLength * 2)]
                            tempData = entryData.decode('utf-16')[0:-1]
                            tempData = tempData.replace('\r\n', "")
                        self.metaList['LastSavedBy'] = tempData
                        metaNum += 1
                    except:
                        self.metaList['LastSavedBy'] = ''

            # 7. Version
            elif record['type'] is 0x09:
                recordStartOffset = startOffset + record['offset']
                entryType = struct.unpack('<I', fpSummary[recordStartOffset: recordStartOffset + 4])[0]
                entryLength = struct.unpack('<i', fpSummary[recordStartOffset + 4: recordStartOffset + 8])[0]
                if entryLength > 1:
                    try:
                        if entryType == 0x1E:
                            entryData = fpSummary[recordStartOffset + 8: recordStartOffset + 8 + (entryLength)]
                            tempData = entryData.decode('euc-kr')[0:-1]
                            tempData = tempData.replace('\r\n', "")
                        elif entryType == 0x1F:
                            entryData = fpSummary[recordStartOffset + 8: recordStartOffset + 8 + (entryLength * 2)]
                            tempData = entryData.decode('utf-16')[0:-1]
                            tempData = tempData.replace('\r\n', "")
                        self.metaList['Version'] = tempData
                        metaNum += 1
                    except:
                        self.metaList['Version'] = ''

            # 8. Date
            elif record['type'] is 0x14:
                recordStartOffset = startOffset + record['offset']
                entryType = struct.unpack('<I', fpSummary[recordStartOffset: recordStartOffset + 4])[0]
                entryLength = struct.unpack('<i', fpSummary[recordStartOffset + 4: recordStartOffset + 8])[0]
                if entryLength > 1:
                    try:
                        if entryType == 0x1E:
                            entryData = fpSummary[recordStartOffset + 8: recordStartOffset + 8 + (entryLength)]
                            tempData = entryData.decode('euc-kr')[0:-1]
                            tempData = tempData.replace('\r\n', "")
                        elif entryType == 0x1F:
                            entryData = fpSummary[recordStartOffset + 8: recordStartOffset + 8 + (entryLength * 2)]
                            tempData = entryData.decode('utf-16')[0:-1]
                            tempData = tempData.replace('\r\n', "")
                        self.metaList['Date'] = tempData
                        metaNum += 1
                    except:
                        self.metaList['Date'] = ''

            # 9. LastPrintedTime
            elif record['type'] is 0x0B:
                recordStartOffset = startOffset + record['offset']
                entryTimeData = struct.unpack('<q', fpSummary[recordStartOffset + 4: recordStartOffset + 12])[0]
                if entryTimeData > 0.0:
                    try:
                        tempTime = datetime.datetime.utcfromtimestamp((entryTimeData - 116444736000000000) / 10000000) + datetime.timedelta(hours=9)
                        self.metaList['LastPrintedTime'] = tempTime.strftime('%Y-%m-%d %H:%M:%S.%f')
                        metaNum += 1
                    except:
                        self.metaList['LastPrintedTime'] = ''

            # 10. CreateTime
            elif record['type'] is 0x0C:
                recordStartOffset = startOffset + record['offset']
                entryTimeData = struct.unpack('<q', fpSummary[recordStartOffset + 4: recordStartOffset + 12])[0]
                if entryTimeData > 0.0:
                    try:
                        tempTime = datetime.datetime.utcfromtimestamp((entryTimeData - 116444736000000000) / 10000000) + datetime.timedelta(hours=9)
                        self.metaList['CreatedTime'] = tempTime.strftime('%Y-%m-%d %H:%M:%S.%f')
                        metaNum += 1
                    except:
                        self.metaList['CreatedTime'] = ''

            # 11. LastSaveTime
            elif record['type'] is 0x0D:
                recordStartOffset = startOffset + record['offset']
                entryTimeData = struct.unpack('<q', fpSummary[recordStartOffset + 4: recordStartOffset + 12])[0]
                if entryTimeData > 0.0:
                    try:
                        tempTime = datetime.datetime.utcfromtimestamp((entryTimeData - 116444736000000000) / 10000000) + datetime.timedelta(hours=9)
                        self.metaList['LastSavedTime'] = tempTime.strftime('%Y-%m-%d %H:%M:%S.%f')
                        metaNum += 1
                    except:
                        self.metaList['LastSavedTime'] = ''


        if metaNum > 0:
            self.has_metadata = True
            
        return True


    def parseContents(self):
        records = []

        for entry in self.fp.root:
            if entry.name == 'BodyText':
                for i in range(0, len(entry._children)):
                    stream_name = 'BodyText/' + entry._children[i].name
                    records.append(stream_name)
            else:
                continue

        for record in records:
            section: bytearray = bytearray(self.fp.open(record).read())
            msg = self.inflateBodytext(section, self.isCompressed)
            if msg is not False:
                self.content += msg

    def parseMultimedia(self):
        records = []

        for entry in self.fp.root:
            if entry.name == 'BinData':
                for i in range(0, len(entry._children)):
                    stream_name = 'BinData/' + entry._children[i].name
                    records.append(stream_name)
            else:
                continue

        olefilenames = []
        for record in records:
            bindata: bytearray = bytearray(self.fp.open(record).read())
            decompress = zlib.decompressobj(-zlib.MAX_WBITS)
            name = record.split('/')
            ext = name[1][-4:].lower()
            name = name[1]
            #global path로 변경하면 된다.
            path = self.ole_path+"/"+name


            if ext == '.jpg' or ext == '.png' or ext == '.gif' or ext == '.bmp':
                try:
                    stream = decompress.decompress(bindata)
                    stream += decompress.flush()
                except:
                    continue
            elif ext == '.ole':
                try:
                    stream = decompress.decompress(bindata)
                    stream += decompress.flush()
                    stream = stream[4:]
                    olefilenames.append(path)
                except:
                    continue
            else:
                continue

            f = open(path, mode='wb')
            f.write(stream)
            f.close()
        self.getOLEFile(olefilenames)

    def getOLEFile(self, files):
        for file in files:
            try:
                ole = compoundfiles.CompoundFileReader(file)
                for entry in ole.root:
                    if entry.name == 'Package': # ooxml
                        bindata: bytearray = bytearray(ole.open('Package').read())
                        f = open(file+'.zip', mode='wb')
                        f.write(bindata)
                        f.close()
                        with zipfile.ZipFile(file+'.zip') as z:
                            for filename in z.namelist():
                                if filename == 'word/document.xml':
                                    savefilename = file+'.docx'
                                elif filename == 'ppt/presentation.xml':
                                    savefilename = file+'.pptx'
                                elif filename == 'xl/workbook.xml':
                                    savefilename = file+'.xlsx'

                        f = open(savefilename, mode='wb')
                        f.write(bindata)
                        f.close()
                        os.remove(file + '.zip')

                    elif entry.name == 'WordDocument':
                        shutil.copy(file, file+'.doc')
                    elif entry.name == 'PowerPoint Document':
                        shutil.copy(file, file+'.ppt')
                    elif entry.name == 'Workbook':
                        shutil.copy(file, file+'.xls')
                    elif entry.name == 'CONTENTS':
                        bindata: bytearray = bytearray(ole.open('CONTENTS').read())
                        f = open(file + '.pdf', mode='wb')
                        f.write(bindata)
                        f.close()
                    elif entry.name == 'Ole10Native':
                        bindata: bytearray = bytearray(ole.open('Ole10Native').read())
                        name_len = 6
                        for i in bindata[name_len:]:
                            if i == 0:
                                break
                            name_len += 1
                        cnt = 0
                        while cnt<1000:
                            if bindata[cnt:cnt+12] == b'RIFFf\xb63\x02AVI ':
                                f = open(file + '.avi', mode='wb')
                                f.write(bindata[cnt:])
                                f.close()
                                break
                            if bindata[cnt:cnt+12] == b'RIFF\xe8\xdd\x05\x00WAVE':
                                f = open(file + '.wav', mode='wb')
                                f.write(bindata[cnt:])
                                f.close()
                                break
                            if bindata[cnt:cnt+12] == b'\x00\x00\x00 ftypisom':
                                f = open(file + '.mp4', mode='wb')
                                f.write(bindata[cnt:])
                                f.close()
                                break
                            cnt += 1
                    else:
                        continue
            except:
                return False

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

    def parseDamagedMetadta(self):
        blockNum = self.fileSize / self.CONST_HWP_SBLOCK_SIZE
        index = 0

        while index < blockNum:
            block = self.fp.read(64)
            ret = self.verifySummaryinfo(block)

            if ret:
                startOffset = struct.unpack('<i', block[0x2C: 0x30])[0]
                length = struct.unpack('<i', block[startOffset: startOffset + 0x04])[0]
                size = startOffset + length - 64
                if size % 64 == 0:
                    size = (int)(size / 64)
                else:
                    size = (int)(size / 64) + 1
                block += self.fp.read(size * 64)
                self.parseSummaryInfo(block)
                continue
            index += 1

    def parseDamagedContents(self):
        blockNum = self.fileSize / self.CONST_HWP_SBLOCK_SIZE

        self.fp.seek(0)
        blockNum = self.fileSize / 64

        index = 0
        headerArray = []

        # 1. Find inflate Header
        while index < blockNum:
            block = self.fp.read(64)

            blockHeader = block[0] & 0x06
            if blockHeader == 0x00 or blockHeader == 0x11:
                index += 1
                continue

            if block.count(0x00) == 64 or block.count(0xFF) == 64:
                index += 1
                continue

            decompress = zlib.decompressobj(-zlib.MAX_WBITS)
            try:
                inflated = decompress.decompress(block)

                if decompress.eof is False and len(decompress.unconsumed_tail) is 0 and len(decompress.unused_data) is 0:
                #if len(inflated) > 0 and decompress.eof is False and len(decompress.unconsumed_tail) is 0 and len(decompress.unused_data) is 0:
                    headerArray.append(index)
                index += 1
            except:
                index += 1
                continue

        # 2. Concatenate and parsing
        for headerIndex in headerArray:
            validation = False
            self.fp.seek(64 * headerIndex)
            block = self.fp.read(64)
            index = headerIndex + 1

            while index < blockNum:
                temp = self.fp.read(64)
                block += temp

                try:
                    decompress = zlib.decompressobj(-zlib.MAX_WBITS)
                    inflated = decompress.decompress(block)
                    index += 1
                except:
                    block = block[0:-64]
                    index += 1
                    continue

                if len(decompress.unconsumed_tail) > 0:
                    block = block[0:-64]
                    continue

                if validation is False and len(inflated) > 2:
                    if inflated[0] == 0x42 and inflated[1] == 0x00:
                        validation = True
                        continue
                    else:
                        break

                if decompress.eof is True and len(decompress.unconsumed_tail) is 0:
                    break

            if validation is True:
                tempBodyText = self.inflateBodytext(block, True)
                if tempBodyText is not False:
                    self.content = self.content + tempBodyText

        if len(self.content) > 0:
            self.has_content = True