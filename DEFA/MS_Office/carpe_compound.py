# carpe_compound.py
import datetime

from compoundfiles import *
import os, sys
import struct
try:
    from carpe_xls import XLS
except ModuleNotFoundError:
    sys.path.append(os.path.dirname(__file__))
    from carpe_xls import XLS
try:
    from carpe_ppt import PPT
except ModuleNotFoundError:
    sys.path.append(os.path.dirname(__file__))
    from carpe_ppt import PPT
try:
    from carpe_doc import DOC
except ModuleNotFoundError:
    sys.path.append(os.path.dirname(__file__))
    from carpe_doc import DOC


class Compound:

    ### Dameged Documents ###
    CONST_DOCUMENT_NORMAL = False
    CONST_DOCUMENT_DAMAGED = True

    ### Encrypted Documents ###
    CONST_DOCUMENT_NO_ENCRYPTED = 0x0000
    CONST_DOCUMENT_ENCRYPTED = 0x0001
    CONST_DOCUMENT_UNKNOWN_ENCRYPTED = 0x0002

    ### Restoreable Documents ###
    CONST_DOCUMENT_RESTORABLE = 0x0000
    CONST_DOCUMENT_UNRESTORABLE = 0x0001
    CONST_DOCUMENT_UNKNOWN_RESTORABLE = 0x0002

    CONST_SUCCESS = True
    CONST_ERROR = False

    def __init__(self, filePath):
        if(os.path.exists(filePath)):
            try:
                self.fp = CompoundFileReader(filePath)
                self.is_damaged = self.CONST_DOCUMENT_NORMAL
                temp1 = bytearray(self.fp.open('\x05SummaryInformation').read())         # read test
                #temp1 = bytearray(self.fp.open('Root Entry').read())                     # read test
                temp1 = bytearray(self.fp.open('\x05DocumentSummaryInformation').read())                     # read test
                #print("Normal File exist!!")
            except errors.CompoundFileInvalidBomError:
                self.fp = open(filePath, 'rb')
                self.is_damaged = self.CONST_DOCUMENT_DAMAGED
                #print("Damaged File exist!!")
            except BaseException:
                self.fp = open(filePath, 'rb')
                self.is_damaged = self.CONST_DOCUMENT_DAMAGED
                #print("Damaged File exist!! [else]")



            self.has_content = False
            self.has_metadata = False
            self.has_ole = False
            self.ole_path = []
            self.content = ""
            self.metadata = {'title': "", 'subject': "", 'author': "", 'keyword': "", 'explanation': "",
                             'last_saved_by': "",
                             'version': "", 'last_printed_time': "", 'create_time': "", 'modified_time': "", 'date': ""}



        else:
            self.fp = None
            # print("File doesn't exist.")

        self.fileSize = os.path.getsize(filePath)
        self.fileName = os.path.basename(filePath)
        self.filePath = filePath
        self.fileType = os.path.splitext(filePath)[1][1:].lower()   # delete '.' in '.xls' r

        


    def __enter__(self):
        raise NotImplementedError

    def __exit__(self):
        raise NotImplementedError


    def parse(self):
        if self.fileType == "xls" :
            object = XLS(self)
            object.parse_xls()

        elif self.fileType == "ppt" :
            object = PPT(self)
            object.parse_ppt()

        elif self.fileType == "doc" :
            object = DOC(self)
            object.parse_doc()

        if len(self.content) > 0:
            self.has_content = True
            #print(self.content)

        if self.is_damaged == self.CONST_DOCUMENT_NORMAL:
            self.parse_summaryinfo()

        if( self.metadata['author'] != None or self.metadata['title'] != None or self.metadata['create_time'] != None or self.metadata['modified_time'] != None):
            self.has_metadata = True
            #print(self.metadata['author'])
            #print(self.metadata['title'])
            #print(self.metadata['create_time'])
            #print(self.metadata['modified_time'])


    def parse_summaryinfo(self):
        records = []
        if self.is_damaged == self.CONST_DOCUMENT_NORMAL:
            # Open SummaryInformation Stream
            fpSummary = self.fp.open('\x05SummaryInformation').read()
        elif self.is_damaged == self.CONST_DOCUMENT_DAMAGED:
            self.fp.seek(0)
            s = bytearray(self.fp.read(self.fileSize))
            summary_offset = s.find(b'\xFE\xFF\x00\x00\x06\x01\x02\x00')
            if summary_offset == -1:  # not found
                return False
            fpSummary = s[summary_offset:summary_offset + 512]

        metaNum = 0
        startOffset = struct.unpack('<I', fpSummary[0x2C: 0x30])[0]
        tempOffset = startOffset
        recordCount = struct.unpack('<I', fpSummary[tempOffset + 0x04: tempOffset + 0x08])[0]
        tempOffset += 0x08

        for i in range(0, recordCount):
            recordType = struct.unpack('<I', fpSummary[tempOffset: tempOffset + 0x04])[0]
            recordOffset = struct.unpack('<I', fpSummary[tempOffset + 0x04: tempOffset + 0x08])[0]
            records.append({'type': recordType, 'offset': recordOffset})
            tempOffset += 0x08

        # Parse Records
        for record in records:
            # 1. Title
            if record['type'] is 0x02:
                recordStartOffset = startOffset + record['offset']
                entryType = struct.unpack('<I', fpSummary[recordStartOffset: recordStartOffset + 4])[0]
                entryLength = struct.unpack('<I', fpSummary[recordStartOffset + 4: recordStartOffset + 8])[0]
                if entryLength > 1:
                    entryData = fpSummary[recordStartOffset + 8: recordStartOffset + 8 + (entryLength * 2)]
                    try:
                        if entryType == 0x1E:
                            tempData = entryData.decode('euc-kr')[0:-1]
                            tempData = tempData.replace('\r\n', "")
                        elif entryType == 0x1F:
                            tempData = entryData.decode('utf-16')[0:-1]
                            tempData = tempData.replace('\r\n', "")
                        self.metadata['title'] = tempData
                        metaNum += 1
                    except:
                        self.metadata['title'] = ''

            # 2. Subject
            elif record['type'] is 0x03:
                recordStartOffset = startOffset + record['offset']
                entryType = struct.unpack('<I', fpSummary[recordStartOffset: recordStartOffset + 4])[0]
                entryLength = struct.unpack('<I', fpSummary[recordStartOffset + 4: recordStartOffset + 8])[0]
                if entryLength > 1:
                    entryData = fpSummary[recordStartOffset + 8: recordStartOffset + 8 + (entryLength * 2)]
                    try:
                        if entryType == 0x1E:
                            tempData = entryData.decode('euc-kr')[0:-1]
                            tempData = tempData.replace('\r\n', "")
                        elif entryType == 0x1F:
                            tempData = entryData.decode('utf-16')[0:-1]
                            tempData = tempData.replace('\r\n', "")
                        self.metadata['subject'] = tempData
                        metaNum += 1
                    except:
                        self.metadata['subject'] = ''

            # 3. Author
            elif record['type'] is 0x04:
                recordStartOffset = startOffset + record['offset']
                entryType = struct.unpack('<I', fpSummary[recordStartOffset: recordStartOffset + 4])[0]
                entryLength = struct.unpack('<I', fpSummary[recordStartOffset + 4: recordStartOffset + 8])[0]
                if entryLength > 1:
                    entryData = fpSummary[recordStartOffset + 8: recordStartOffset + 8 + (entryLength * 2)]
                    try:
                        if entryType == 0x1E:
                            tempData = entryData.decode('euc-kr')[0:-1]
                            tempData = tempData.replace('\r\n', "")
                        elif entryType == 0x1F:
                            tempData = entryData.decode('utf-16')[0:-1]
                            tempData = tempData.replace('\r\n', "")
                        self.metadata['author'] = tempData
                        metaNum += 1
                    except:
                        self.metadata['author'] = ''

            # 4. Keyword
            elif record['type'] is 0x05:
                recordStartOffset = startOffset + record['offset']
                entryType = struct.unpack('<I', fpSummary[recordStartOffset: recordStartOffset + 4])[0]
                entryLength = struct.unpack('<I', fpSummary[recordStartOffset + 4: recordStartOffset + 8])[0]
                if entryLength > 1:
                    entryData = fpSummary[recordStartOffset + 8: recordStartOffset + 8 + (entryLength * 2)]
                    try:
                        if entryType == 0x1E:
                            tempData = entryData.decode('euc-kr')[0:-1]
                            tempData = tempData.replace('\r\n', "")
                        elif entryType == 0x1F:
                            tempData = entryData.decode('utf-16')[0:-1]
                            tempData = tempData.replace('\r\n', "")
                        self.metadata['keyword'] = tempData
                        metaNum += 1
                    except:
                        self.metadata['keyword'] = ''

            # 5. explanation
            elif record['type'] is 0x06:
                recordStartOffset = startOffset + record['offset']
                entryType = struct.unpack('<I', fpSummary[recordStartOffset: recordStartOffset + 4])[0]
                entryLength = struct.unpack('<I', fpSummary[recordStartOffset + 4: recordStartOffset + 8])[0]
                if entryLength > 1:
                    entryData = fpSummary[recordStartOffset + 8: recordStartOffset + 8 + (entryLength * 2)]
                    try:
                        if entryType == 0x1E:
                            tempData = entryData.decode('euc-kr')[0:-1]
                            tempData = tempData.replace('\r\n', "")
                        elif entryType == 0x1F:
                            tempData = entryData.decode('utf-16')[0:-1]
                            tempData = tempData.replace('\r\n', "")
                        self.metadata['explanation'] = tempData
                        metaNum += 1
                    except:
                        self.metadata['explanation'] = ''

            # 6. LastSaveBy
            elif record['type'] is 0x08:
                recordStartOffset = startOffset + record['offset']
                entryType = struct.unpack('<I', fpSummary[recordStartOffset: recordStartOffset + 4])[0]
                entryLength = struct.unpack('<I', fpSummary[recordStartOffset + 4: recordStartOffset + 8])[0]
                if entryLength > 1:
                    entryData = fpSummary[recordStartOffset + 8: recordStartOffset + 8 + (entryLength * 2)]
                    try:
                        if entryType == 0x1E:
                            tempData = entryData.decode('euc-kr')[0:-1]
                            tempData = tempData.replace('\r\n', "")
                        elif entryType == 0x1F:
                            tempData = entryData.decode('utf-16')[0:-1]
                            tempData = tempData.replace('\r\n', "")
                        self.metadata['last_saved_by'] = tempData
                        metaNum += 1
                    except:
                        self.metadata['last_saved_by'] = ''

            # 7. Version
            elif record['type'] is 0x09:
                recordStartOffset = startOffset + record['offset']
                entryType = struct.unpack('<I', fpSummary[recordStartOffset: recordStartOffset + 4])[0]
                entryLength = struct.unpack('<I', fpSummary[recordStartOffset + 4: recordStartOffset + 8])[0]
                if entryLength > 1:
                    entryData = fpSummary[recordStartOffset + 8: recordStartOffset + 8 + (entryLength * 2)]
                    try:
                        if entryType == 0x1E:
                            tempData = entryData.decode('euc-kr')[0:-1]
                            tempData = tempData.replace('\r\n', "")
                        elif entryType == 0x1F:
                            tempData = entryData.decode('utf-16')[0:-1]
                            tempData = tempData.replace('\r\n', "")
                        self.metadata['version'] = tempData
                        metaNum += 1
                    except:
                        self.metadata['version'] = ''

            # 8. Date
            elif record['type'] is 0x14:
                recordStartOffset = startOffset + record['offset']
                entryType = struct.unpack('<I', fpSummary[recordStartOffset: recordStartOffset + 4])[0]
                entryLength = struct.unpack('<I', fpSummary[recordStartOffset + 4: recordStartOffset + 8])[0]
                if entryLength > 1:
                    entryData = fpSummary[recordStartOffset + 8: recordStartOffset + 8 + (entryLength * 2)]
                    try:
                        if entryType == 0x1E:
                            tempData = entryData.decode('euc-kr')[0:-1]
                            tempData = tempData.replace('\r\n', "")
                        elif entryType == 0x1F:
                            tempData = entryData.decode('utf-16')[0:-1]
                            tempData = tempData.replace('\r\n', "")
                        self.metadata['date'] = tempData
                        metaNum += 1
                    except:
                        self.metadata['date'] = ''

            # 9. LastPrintedTime
            elif record['type'] is 0x0B:
                recordStartOffset = startOffset + record['offset']
                entryTimeData = struct.unpack('<q', fpSummary[recordStartOffset + 4: recordStartOffset + 12])[0]
                if entryTimeData > 0.0:
                    try:
                        tempTime = datetime.datetime.utcfromtimestamp(
                            (entryTimeData - 116444736000000000) / 10000000) + datetime.timedelta(hours=9)
                        self.metadata['last_printed_time'] = tempTime.strftime('%Y-%m-%d %H:%M:%S.%f')
                        metaNum += 1
                    except:
                        self.metadata['last_printed_time'] = ''

            # 10. CreateTime
            elif record['type'] is 0x0C:
                recordStartOffset = startOffset + record['offset']
                entryTimeData = struct.unpack('<q', fpSummary[recordStartOffset + 4: recordStartOffset + 12])[0]
                if entryTimeData > 0.0:
                    try:
                        tempTime = datetime.datetime.utcfromtimestamp(
                            (entryTimeData - 116444736000000000) / 10000000) + datetime.timedelta(hours=9)
                        self.metadata['create_time'] = tempTime.strftime('%Y-%m-%d %H:%M:%S.%f')
                        metaNum += 1
                    except:
                        self.metadata['create_time'] = ''

            # 11. LastSaveTime
            elif record['type'] is 0x0D:
                recordStartOffset = startOffset + record['offset']
                entryTimeData = struct.unpack('<q', fpSummary[recordStartOffset + 4: recordStartOffset + 12])[0]
                if entryTimeData > 0.0:
                    try:
                        tempTime = datetime.datetime.utcfromtimestamp(
                            (entryTimeData - 116444736000000000) / 10000000) + datetime.timedelta(hours=9)
                        self.metadata['modified_time'] = tempTime.strftime('%Y-%m-%d %H:%M:%S.%f')
                        metaNum += 1
                    except:
                        self.metadata['modified_time'] = ''

        if metaNum > 0:
            self.has_metadata = True
            return True
