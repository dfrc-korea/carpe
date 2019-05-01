# carpe_compound.py
import datetime

import compoundfiles
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
    CONST_DOCUMENT_NORMAL = 0x0000
    CONST_DOCUMENT_DAMAGED = 0x0001
    CONST_DOCUMENT_UNKNOWN_DAMAGED = 0x0002

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
                self.fp = compoundfiles.CompoundFileReader(filePath)
                self.is_damaged = self.CONST_DOCUMENT_NORMAL
                temp1 = bytearray(self.fp.open('WordDocument').read())         # read test

                #print("Normal File exist!!")
            except compoundfiles.errors.CompoundFileInvalidBomError:
                self.fp = open(filePath, 'rb')
                self.is_damaged = self.CONST_DOCUMENT_DAMAGED
                #print("Damaged File exist!!")
            except BaseException:
                self.fp = open(filePath, 'rb')
                self.is_damaged = self.CONST_DOCUMENT_DAMAGED
                #print("Damaged File exist!! [else]")

            self.has_content = False
            self.has_metadata = False
            self.content = ""
            self.metadata = {}
            self.metadata['author'] = ""
            self.metadata['title'] = ""
            self.metadata['create_time'] = ""
            self.metadata['modified_time'] = ""



        else:
            self.fp = None
            print("File doesn't exist.")

        self.fileSize = os.path.getsize(filePath)
        self.fileName = os.path.basename(filePath)
        self.filePath = filePath
        self.fileType = os.path.splitext(filePath)[1][1:]   # delete '.' in '.xls' r

        


    def __enter__(self):
        raise NotImplementedError

    def __exit__(self):
        raise NotImplementedError


    def parse(self):
        if self.fileType == "xls" :
            #result = self.parse_xls()
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
            print(self.content)

        self.parse_summaryinfo()
        if( self.metadata['author'] != None or self.metadata['title'] != None or self.metadata['create_time'] != None or self.metadata['modified_time'] != None):
            self.has_metadata = True
            print(self.metadata['author'])
            print(self.metadata['title'])
            print(self.metadata['create_time'])
            print(self.metadata['modified_time'])




    def parse_summaryinfo(self):
        records = []
        # Open SummaryInformation Stream
        f = self.fp.open('\x05SummaryInformation').read()

        startOffset = struct.unpack('<i', f[0x2C: 0x30])[0]
        tempOffset = startOffset

        # Store Records
        length = struct.unpack('<i', f[tempOffset: tempOffset + 0x04])[0]
        recordCount = struct.unpack('<i', f[tempOffset + 0x04: tempOffset + 0x08])[0]
        tempOffset += 0x08
        for i in range(0, recordCount):
            dict = {}
            dict['type'] = struct.unpack('<i', f[tempOffset: tempOffset + 0x04])[0]
            dict['offset'] = struct.unpack('<i', f[tempOffset + 0x04: tempOffset + 0x08])[0]
            records.append(dict)
            tempOffset += 0x08

        # Print Records
        for record in records:

            # Title
            if record['type'] == 0x02:
                entryLength = \
                struct.unpack('<i', f[record['offset'] + startOffset + 4: record['offset'] + startOffset + 8])[0]
                entryData = f[record['offset'] + startOffset + 8: record['offset'] + startOffset + 8 + entryLength]
                #print(entryData.decode('euc-kr'))
                self.metadata['title'] = entryData.decode('euc-kr')


            # Subject
            elif record['type'] == 0x03:
                entryLength = \
                struct.unpack('<i', f[record['offset'] + startOffset + 4: record['offset'] + startOffset + 8])[0]
                entryData = f[record['offset'] + startOffset + 8: record['offset'] + startOffset + 8 + entryLength]
                #print(entryData.decode('euc-kr'))

            # Author
            elif record['type'] == 0x04:
                entryLength = \
                struct.unpack('<i', f[record['offset'] + startOffset + 4: record['offset'] + startOffset + 8])[0]
                entryData = f[record['offset'] + startOffset + 8: record['offset'] + startOffset + 8 + entryLength]
                self.metadata['author'] = entryData.decode('euc-kr')
                #print(entryData.decode('euc-kr'))


            # LastAuthor
            elif record['type'] == 0x08:
                entryLength = \
                struct.unpack('<i', f[record['offset'] + startOffset + 4: record['offset'] + startOffset + 8])[0]
                entryData = f[record['offset'] + startOffset + 8: record['offset'] + startOffset + 8 + entryLength]
                #print(entryData.decode('euc-kr'))


            # AppName
            elif record['type'] == 0x12:
                entryLength = \
                struct.unpack('<i', f[record['offset'] + startOffset + 4: record['offset'] + startOffset + 8])[0]
                entryData = f[record['offset'] + startOffset + 8: record['offset'] + startOffset + 8 + entryLength]
                #print(entryData.decode('euc-kr'))

            # LastPrintedtime
            elif record['type'] == 0x0B:
                # entryTimeData = struct.unpack('<q', f[record['offset'] + startOffset + 4: record['offset'] + startOffset + 12])[0] / 1e8
                # print(datetime.datetime.fromtimestamp(entryTimeData).strftime('%Y-%m-%d %H:%M:%S.%f'))
                pass


            # Createtime
            elif record['type'] == 0x0C:
                #entryTimeData = struct.unpack('<q', f[record['offset'] + startOffset + 4: record['offset'] + startOffset + 12])[0] / 1e8
                #print(datetime.datetime.fromtimestamp(entryTimeData).strftime('%Y-%m-%d %H:%M:%S.%f'))
                self.metadata['create_time'] = struct.unpack('<q', f[record['offset'] + startOffset + 4: record['offset'] + startOffset + 12])[0]


            # LastSavetime
            elif record['type'] == 0x0D:
                #entryTimeData = struct.unpack('<q', f[record['offset'] + startOffset + 4: record['offset'] + startOffset + 12])[0] / 1e8
                #print(datetime.datetime.fromtimestamp(entryTimeData).strftime('%Y-%m-%d %H:%M:%S.%f'))
                self.metadata['modified_time'] = struct.unpack('<q', f[record['offset'] + startOffset + 4: record['offset'] + startOffset + 12])[0]
