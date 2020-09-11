# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import io
import struct

from modules.SIGA import definitions
from modules.SIGA.utility import filetime_to_dt
from modules.SIGA.classes.interface import Common
from modules.SIGA.classes.documents.compound import Compound
from modules.SIGA.formats.documents.cfbf.fm_cfbf_dir_entry import CfbfDirEntry



class DOC(Common):


    def __init__(self, input=None):

        self.input = input
        # self.data = fm_Cfbf.from_file(self.input)
        self.data = None
        self._ext = None
        self._metadata = None
        self._text = None
        self._structure = dict()
        
        self.content = ""

        # result
        self._doc_info = dict()
        self._vuln_info = dict()
        self._vuln_cnt = 0
        self._arr_tag = dict()

        self._is_compressed = False
        self._is_encrypted = 0

        if input:
            self._cp = Compound(self.input)
        else:
            self._cp = Compound()

    def identifyFormatFromFile(self):
        if self.input[-4:] != ".xls" and self.input[-4:] != ".doc" and self.input[-4:] != ".ppt" and self.input[-4:] != ".hwp":
            return False

        # 이걸 어디서 할까?
        self._cp.get_header()
        #self._cp._validate_header()
        self._cp.load_compound()
        for entry in self._cp._dir_entries:
            if entry.name[:8] == '\x00\x00\x00\x00\x00\x00\x00\x00':
                break
            if entry.name_trancated == 'WordDocument':
                self._ext = '.doc'

        if self._ext == None:
            return False

        return self._ext

    def identifyFormatFromMemory(self, file_object):

        file_like_object = io.BytesIO(file_object)
        self._cp._fp = file_like_object
        try:
            self._cp.get_header()
            self._cp.load_compound()
            for entry in self._cp._dir_entries:
                if entry.name[:8] == '\x00\x00\x00\x00\x00\x00\x00\x00':
                    break
                if entry.name_trancated == 'WordDocument':
                    self._ext = '.doc'
        except:
            return False

        if self._ext == None:
            return False

        return self._ext

    def _set_vuln_info(self, type, offset, length, desc, section_name):

        vinfo = dict()
        vinfo['type'] = type
        vinfo['offset'] = offset
        vinfo['length'] = length

        if section_name != '':
            vinfo['desc'] = 'S ; ' + section_name + ' ; '
        else:
            vinfo['desc'] = 'F ;'

        vinfo['desc'] += desc
        self._vuln_info['vuln' + str(self._vuln_cnt + 1)] = vinfo
        self._vuln_cnt += 1

    def validate(self):

        self._cp._validate_header()

        entry_idx = -1
        for entry in self._cp._dir_entries:

            entry_idx += 1
            if not entry.object_type.name == 'stream':
                continue

            if self._cp._header.mini_stream_cutoff_size <= entry.size:
                d = self._cp._get_stream(entry)
            else:
                d = self._cp._get_mini_stream(entry)

            # 상위 16 bytes 체크 안함


            # |SummaryInformation
            if entry.name_trancated == '\x05SummaryInformation':
                if self._is_valid_child(entry_idx, "Root Entry", 0):
                    self._validate_stream_summaryinfo(d, len(d), entry.name_trancated)

                else:
                    desc = '%s Storage 하위에 포함됨' % self._get_parent_storage(entry_idx)
                    self._set_vuln_info(definitions.HC_STR_VTYPE_UNKWNON_STREAM, 0, 0, desc, entry.name_trancated)
                    self._validate_unknown_data(definitions.HC_STR_VTYPE_ABNORMAL_BINDATA, d, len(d), 0, 0, entry.name_trancated)
                continue


            # |DocumentSummaryInformation
            if entry.name_trancated == '\x05DocumentSummaryInformation':
                if self._is_valid_child(entry_idx, "Root Entry", 0):
                    self._validate_stream_docsummaryinfo(d, len(d), entry.name_trancated)

                else:
                    desc = '%s Storage 하위에 포함됨' % self._get_parent_storage(entry_idx)
                    self._set_vuln_info(definitions.HC_STR_VTYPE_UNKWNON_STREAM, 0, 0, desc, entry.name_trancated)
                    self._validate_unknown_data(definitions.HC_STR_VTYPE_ABNORMAL_BINDATA, d, len(d), 0, 0, entry.name_trancated)
                continue

            # \x01CompObj
            if entry.name_trancated == '\x01CompObj':
                if self._is_valid_child(entry_idx, "Root Entry", 0):
                    self._validate_stream_compobj(d, len(d), entry.name_trancated)

                else:
                    desc = '%s Storage 하위에 포함됨' % self._get_parent_storage(entry_idx)
                    self._set_vuln_info(definitions.HC_STR_VTYPE_UNKWNON_STREAM, 0, 0, desc, entry.name_trancated)
                    self._validate_unknown_data(definitions.HC_STR_VTYPE_ABNORMAL_BINDATA, d, len(d), 0, 0, entry.name_trancated)
                continue

            # [Root Entry] - [_VBA_PROJECT_CUR] - [VBA]
            if entry.name_trancated == 'dir':
                if self._is_valid_child(entry_idx, "VBA", 0):
                    self._validate_stream_dir(d, len(d), entry.name_trancated)

                else:
                    desc = '%s Storage 하위에 포함됨' % self._get_parent_storage(entry_idx)
                    self._set_vuln_info(definitions.HC_STR_VTYPE_UNKWNON_STREAM, 0, 0, desc, entry.name_trancated)
                    self._validate_unknown_data(definitions.HC_STR_VTYPE_ABNORMAL_BINDATA, d, len(d), 0, 0,
                                                entry.name_trancated)
                continue

            # WordDocument
            if entry.name_trancated == 'WordDocument':
                if self._is_valid_child(entry_idx, "Root Entry", 0):
                    self._validate_stream_worddocument(d, len(d), entry.name_trancated)

                else:
                    desc = '%s Storage 하위에 포함됨' % self._get_parent_storage(entry_idx)
                    self._set_vuln_info(definitions.HC_STR_VTYPE_UNKWNON_STREAM, 0, 0, desc, entry.name_trancated)
                    self._validate_unknown_data(definitions.HC_STR_VTYPE_ABNORMAL_BINDATA, d, len(d), 0, 0, entry.name_trancated)
                continue

            # Data
            if entry.name_trancated == 'Data':
                if self._is_valid_child(entry_idx, "Root Entry", 0):
                    self._validate_stream_data(d, len(d), entry.name_trancated)

                else:
                    desc = '%s Storage 하위에 포함됨' % self._get_parent_storage(entry_idx)
                    self._set_vuln_info(definitions.HC_STR_VTYPE_UNKWNON_STREAM, 0, 0, desc, entry.name_trancated)
                    self._validate_unknown_data(definitions.HC_STR_VTYPE_ABNORMAL_BINDATA, d, len(d), 0, 0, entry.name_trancated)
                continue

        return definitions.VALID_SUCCESS

    def get_metadata(self):
        """
        #########################################################
        self.fp = Compound(self.input)
        self.fp.get_header()
        self.fp.load_compound()

        # Traverse each directory entry and its data stream
        for entry in self.fp._dir_entries:
            if entry.name_len > 64 or entry.object_type == CfbfDirEntry.ObjType.unknown:
                continue

            if entry.name[:(entry.name_len >> 1) - 1] == "\x05SummaryInformation":
                if self.fp._header.mini_stream_cutoff_size <= entry.size:
                    f = self.fp._get_stream(entry)
                else:
                    f = self.fp._get_mini_stream(entry)

            #print("[ {0} ]".format(entry.name_trancated))
            #print('\t', entry.object_type)
            #print('\t', entry.size)
            #self.fp._print_hex_dump(f[:64])

        ################ workbook read 완료 ################
        #########################################################
        records = []

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
                entryType = struct.unpack('<I', f[record['offset'] + startOffset : record['offset']  + startOffset + 4])[0]
                if entryType == 0x1E:
                    entryLength = struct.unpack('<i', f[record['offset'] + startOffset + 4: record['offset'] + startOffset + 8])[0]
                elif entryType == 0x1F:
                    entryLength = struct.unpack('<i', f[record['offset'] + startOffset + 4: record['offset'] + startOffset + 8])[0] * 2
                else:
                    return False

                entryData = bytearray(f[record['offset'] + startOffset + 8: record['offset'] + startOffset + 8 + entryLength])
                if entryType == 0x1E:
                    #self.metadata['title'] = entryData.decode('euc-kr')
                    try:
                        print("Title : " + entryData.decode('utf-8'))
                    except Exception:
                        print("Title : " + entryData.decode('euc-kr'))
                elif entryType == 0x1F:
                    #self.metadata['title'] = entryData.decode('utf-16')
                    print("Title : " + entryData.decode('utf-16'))
                #self.metadata['title'] = entryData



            # Subject
            elif record['type'] == 0x03:
                entryType = struct.unpack('<I', f[record['offset'] + startOffset: record['offset']  + startOffset + 4])[0]
                if entryType == 0x1E:
                    entryLength = \
                    struct.unpack('<i', f[record['offset'] + startOffset + 4: record['offset'] + startOffset + 8])[0]
                elif entryType == 0x1F:
                    entryLength = \
                    struct.unpack('<i', f[record['offset'] + startOffset + 4: record['offset'] + startOffset + 8])[
                        0] * 2
                else:
                    return False

                entryData = bytearray(
                    f[record['offset'] + startOffset + 8: record['offset'] + startOffset + 8 + entryLength])
                if entryType == 0x1E:
                    #self.metadata['title'] = entryData.decode('euc-kr')
                    try:
                        print("Subject : " + entryData.decode('utf-8'))
                    except Exception:
                        print("Subject : " + entryData.decode('euc-kr'))
                elif entryType == 0x1F:
                    #self.metadata['title'] = entryData.decode('utf-16')
                    print("Subject : " + entryData.decode('utf-16'))



            # Author
            elif record['type'] == 0x04:

                entryType = struct.unpack('<I', f[record['offset'] + startOffset: record['offset']  + startOffset + 4])[0]
                if entryType == 0x1E:
                    entryLength = \
                        struct.unpack('<i', f[record['offset'] + startOffset + 4: record['offset'] + startOffset + 8])[
                            0]
                elif entryType == 0x1F:
                    entryLength = \
                        struct.unpack('<i', f[record['offset'] + startOffset + 4: record['offset'] + startOffset + 8])[
                            0] * 2
                else:
                    return False

                entryData = bytearray(f[record['offset'] + startOffset + 8: record['offset'] + startOffset + 8 + entryLength])
                if entryType == 0x1E:
                    #self.metadata['author'] = entryData.decode('euc-kr')
                    try:
                        print("Author : " + entryData.decode('utf-8'))
                    except Exception:
                        print("Author : " + entryData.decode('euc-kr'))
                elif entryType == 0x1F:
                    #self.metadata['author'] = entryData.decode('utf-16')
                    print("Author : " + entryData.decode('utf-16'))



            # LastAuthor
            elif record['type'] == 0x08:
                entryType = struct.unpack('<I', f[record['offset'] + startOffset: record['offset']  + startOffset + 4])[0]
                if entryType == 0x1E:
                    entryLength = struct.unpack('<i', f[record['offset'] + startOffset + 4: record['offset'] + startOffset + 8])[0]
                elif entryType == 0x1F:
                    entryLength = struct.unpack('<i', f[record['offset'] + startOffset + 4: record['offset'] + startOffset + 8])[0] * 2
                else:
                    return False

                entryData = bytearray(f[record['offset'] + startOffset + 8: record['offset'] + startOffset + 8 + entryLength])
                if entryType == 0x1E:
                    #self.metadata['author'] = entryData.decode('euc-kr')
                    try:
                        print("LastAuthor : " + entryData.decode('utf-8'))
                    except Exception:
                        print("LastAuthor : " + entryData.decode('euc-kr'))
                elif entryType == 0x1F:
                    #self.metadata['author'] = entryData.decode('utf-16')
                    print("LastAuthor : " + entryData.decode('utf-16'))


            # AppName
            elif record['type'] == 0x12:
                entryType = struct.unpack('<I', f[record['offset'] + startOffset: record['offset']  + startOffset + 4])[0]
                if entryType == 0x1E:
                    entryLength = struct.unpack('<i', f[record['offset'] + startOffset + 4: record['offset'] + startOffset + 8])[0]
                elif entryType == 0x1F:
                    entryLength = struct.unpack('<i', f[record['offset'] + startOffset + 4: record['offset'] + startOffset + 8])[0] * 2
                else:
                    return False

                entryData = bytearray(f[record['offset'] + startOffset + 8: record['offset'] + startOffset + 8 + entryLength])
                if entryType == 0x1E:
                    #self.metadata['author'] = entryData.decode('euc-kr')
                    try:
                        print("AppName : " + entryData.decode('utf-8'))
                    except Exception:
                        print("AppName : " + entryData.decode('euc-kr'))
                elif entryType == 0x1F:
                    #self.metadata['author'] = entryData.decode('utf-16')
                    print("AppName : " + entryData.decode('utf-16'))

            # LastPrintedtime
            elif record['type'] == 0x0B:
                entryTimeData = struct.unpack('<q', f[record['offset'] + startOffset + 4: record['offset'] + startOffset + 12])[0] / 1e8
                # print(datetime.datetime.fromtimestamp(entryTimeData).strftime('%Y-%m-%d %H:%M:%S.%f'))
                print("LastPrintedtime : " + datetime.datetime.fromtimestamp(entryTimeData).strftime('%Y-%m-%d %H:%M:%S'))



            # Createtime
            elif record['type'] == 0x0C:
                entryTimeData = struct.unpack('<q', f[record['offset'] + startOffset + 4: record['offset'] + startOffset + 12])[0] / 1e8
                #self.metadata['create_time'] = datetime.datetime.fromtimestamp(entryTimeData).strftime('%Y-%m-%d %H:%M:%S')
                #self.metadata['create_time'] = struct.unpack('<q', f[record['offset'] + startOffset + 4: record['offset'] + startOffset + 12])[0]
                print("Createtime : " + datetime.datetime.fromtimestamp(entryTimeData).strftime('%Y-%m-%d %H:%M:%S'))


            # LastSavetime
            elif record['type'] == 0x0D:
                entryTimeData = struct.unpack('<q', f[record['offset'] + startOffset + 4: record['offset'] + startOffset + 12])[0] / 1e8
                #self.metadata['modified_time'] = datetime.datetime.fromtimestamp(entryTimeData).strftime('%Y-%m-%d %H:%M:%S')
                #self.metadata['modified_time'] = struct.unpack('<q', f[record['offset'] + startOffset + 4: record['offset'] + startOffset + 12])[0]
                print("LastSavetime : " + datetime.datetime.fromtimestamp(entryTimeData).strftime('%Y-%m-%d %H:%M:%S'))


        #########################################################
        return self._metadata
        """

    def get_text(self):
        self.fp = Compound(self.input)
        self.fp.get_header()
        self.fp.load_compound()
        
        word_document = b''
        one_table = b''
        zero_table = b''
        
        # Traverse each directory entry and its data stream
        for entry in self.fp._dir_entries:
            if entry.name_len > 64 or entry.object_type == CfbfDirEntry.ObjType.unknown:
                continue
            if entry.name[:(entry.name_len >> 1) - 1] == "WordDocument":
                if self.fp._header.mini_stream_cutoff_size <= entry.size:
                    word_document = self.fp._get_stream(entry)
                else:
                    word_document = self.fp._get_mini_stream(entry)

            if entry.name[:(entry.name_len >> 1) - 1] == "1Table":
                if self.fp._header.mini_stream_cutoff_size <= entry.size:
                    one_table = self.fp._get_stream(entry)
                else:
                    one_table = self.fp._get_mini_stream(entry)

            if entry.name[:(entry.name_len >> 1) - 1] == "0Table":
                if self.fp._header.mini_stream_cutoff_size <= entry.size:
                    zero_table = self.fp._get_stream(entry)
                else:
                    zero_table = self.fp._get_mini_stream(entry)
                    
            #print("[ {0} ]".format(entry.name_trancated))
            #print('\t', entry.object_type)
            #print('\t', entry.size)
            # self.fp._print_hex_dump(f[:64])

        ################ entry read 완료 ################


        if len(one_table) == 0 and len(zero_table) == 0:
            return False

        # Extract doc Text
        ccpText = b''
        fcClx = b''
        lcbClx = b''
        aCP = b''
        aPcd = b''
        fcCompressed = b''
        Clx = b''
        byteTable = b''
        ccpTextSize = 0
        fcClxSize = 0
        lcbClxSize = 0
        ClxSize = 0
        string = b''
        CONST_FCFLAG = 1073741824  # 0x40000000
        CONST_FCINDEXFLAG = 1073741823  # 0x3FFFFFFF
        i = 0
        j = 0
        k = 0

        # Check Encrypted
        uc_temp = word_document[11]
        uc_temp = uc_temp & 1

        if uc_temp == 1:
            return False

        # 0Table 1Table
        is0Table = word_document[11] & 2

        if is0Table == 0:
            byteTable = zero_table
        else:
            byteTable = one_table

        # Get cppText in FibRgLw
        ccpText = word_document[0x4C:0x50]
        ccpTextSize = struct.unpack('<I', ccpText)[0]

        if (ccpTextSize == 0):
            return False

        # Get fcClx in FibRgFcLcbBlob
        fcClx = word_document[0x1A2:0x1A6]
        fcClxSize = struct.unpack('<I', fcClx)[0]

        if (fcClxSize == 0):
            return False

        # Get lcbClx in FibRgFcLcbBlob
        lcbClx = word_document[0x1A6:0x1AA]
        lcbClxSize = struct.unpack('<I', lcbClx)[0]

        if (lcbClxSize == 0):
            return False

        # Get Clx
        Clx = byteTable[fcClxSize: fcClxSize + lcbClxSize]

        if Clx[0] == 0x01:
            cbGrpprl = struct.unpack("<H", Clx[1:3])[0]
            Clx = byteTable[fcClxSize + cbGrpprl + 3: (fcClxSize + cbGrpprl + 3) + lcbClxSize - cbGrpprl + 3]
        if Clx[0] != 0x02:
            return False

        ClxSize = struct.unpack('<I', Clx[1:5])[0]

        ClxIndex = 5
        PcdCount = 0
        aCPSize = []
        fcFlag = 0
        fcIndex = 0
        fcSize = 0
        encodingFlag = False

        PcdCount = int(((ClxSize / 4) / 3)) + 1

        for i in range(0, PcdCount):
            aCp = Clx[ClxIndex:ClxIndex + 4]
            aCPSize.append(struct.unpack('<I', aCp[0:4])[0])
            ClxIndex += 4

        PcdCount -= 1

        ### Filtering

        uBlank = b'\x20\x00'  # ASCII Blank
        uBlank2 = b'\xA0\x00'  # Unicode Blank
        uNewline = b'\x0A\x00'  # Line Feed
        uNewline2 = b'\x0D\x00'
        uNewline3 = b'\x04\x00'
        uNewline4 = b'\x03\x00'
        uSection = b'\x01\x00'
        uSection2 = b'\x02\x00'
        uSection3 = b'\x05\x00'
        uSection4 = b'\x07\x00'
        uSection5 = b'\x08\x00'
        uSection6 = b'\x15\x00'
        uSection7 = b'\x0C\x00'
        uSection8 = b'\x0B\x00'
        uSection9 = b'\x14\x00'
        uTrash = b'\x00\x00'
        uCaption = b'\x53\x00\x45\x00\x51\x00'
        uCaption2 = b'\x41\x00\x52\x00\x41\x00\x43\x00\x49\x00\x43\x00\x20\x00\x14\x00'
        uHyperlink = b'\x48\x00\x59\x00\x50\x00\x45\x00\x52\x00\x4C\x00\x49\x00\x4E\x00\x4B\x00'
        uToc = b'\x54\x00\x4F\x00'
        uPageref = b'\x50\x00\x41\x00\x47\x00\x45\x00\x52\x00\x45\x00\x46\x00'
        uIndex = b'\x49\x00\x4E\x00\x44\x00\x45\x00\x58\x00'
        uEnd = b'\x20\x00\x01\x00\x14\x00'
        uEnd2 = b'\x20\x00\x14\x00'
        uEnd3 = b'\x20\x00\x15\x00'
        uEnd4 = b'\x14\x00'
        uEnd5 = b'\x01\x00\x14\x00'
        uEnd6 = b'\x15\x00'
        uHeader = b'\x13\x00'
        uChart = b'\x45\x00\x4D\x00\x42\x00\x45\x00\x44\x00'
        uShape = b'\x53\x00\x48\x00\x41\x00\x50\x00\x45\x00'
        uPage = b'\x50\x00\x41\x00\x47\x00\x45\x00'
        uDoc = b'\x44\x00\x4F\x00\x43\x00'
        uStyleref = b'\x53\x00\x54\x00\x59\x00\x4C\x00\x45\x00\x52\x00\x45\x00\x46\x00'
        uTitle = b'\x54\x00\x49\x00\x54\x00\x4C\x00\x45\x00'
        uDate = b'\x49\x00\x46\x00\x20\x00\x44\x00\x41\x00\x54\x00\x45\x00'

        ### Filtering targets: 0x0001 ~ 0x0017(0x000A Line Feed skipped)
        uTab = b'\x09\x00'  # Horizontal Tab
        uSpecial = b'\xF0'
        bFullScanA = False
        bFullScanU = False  # if the size info is invalid, then the entire range will be scanned.
        tempPlus = 0

        for i in range(0, PcdCount):
            aPcd = Clx[ClxIndex:ClxIndex + 8]
            fcCompressed = aPcd[2:6]

            fcFlag = struct.unpack('<I', fcCompressed[0:4])[0]

            if CONST_FCFLAG == (fcFlag & CONST_FCFLAG):
                encodingFlag = True  # 8-bit ANSI
            else:
                encodingFlag = False  # 16-bit Unicode

            fcIndex = fcFlag & CONST_FCINDEXFLAG

            k = 0
            if encodingFlag == True:  # 8-bit ANSI
                fcIndex = int(fcIndex / 2)
                fcSize = aCPSize[i + 1] - aCPSize[i]

                if len(word_document) < fcIndex + fcSize + 1:
                    if bFullScanA == False and len(word_document) > fcIndex:
                        fcSize = len(word_document) - fcIndex - 1
                        bFullScanA = True
                    else:
                        ClxIndex += 8
                        continue

                ASCIIText = word_document[fcIndex:fcIndex + fcSize]
                UNICODEText = b''

                for i in range(0, len(ASCIIText)):
                    UNICODEText += bytes([ASCIIText[i]])
                    UNICODEText += b'\x00'

                while k < len(UNICODEText):

                    if (UNICODEText[k: k + 2] == uSection2 or UNICODEText[k: k + 2] == uSection3 or UNICODEText[
                                                                                                    k: k + 2] == uSection4 or
                            UNICODEText[k: k + 2] == uSection5 or UNICODEText[k: k + 2] == uSection7 or UNICODEText[
                                                                                                        k: k + 2] == uSection8 or
                            UNICODEText[k + 1] == uSpecial or UNICODEText[k: k + 2] == uTrash):
                        k += 2  ### while
                        continue

                    if (UNICODEText[k: k + 2] == uNewline or UNICODEText[k: k + 2] == uNewline2 or UNICODEText[
                                                                                                   k: k + 2] == uNewline3 or UNICODEText[
                                                                                                                             k: k + 2] == uNewline4):
                        string += bytes([UNICODEText[k]])
                        string += bytes([UNICODEText[k + 1]])

                        j = k + 2
                        while j < len(UNICODEText):
                            if (UNICODEText[j:j + 2] == uSection2 or UNICODEText[j:j + 2] == uSection3 or UNICODEText[
                                                                                                          j:j + 2] == uSection4 or
                                    UNICODEText[j:j + 2] == uSection5 or UNICODEText[j:j + 2] == uSection7 or UNICODEText[
                                                                                                              j:j + 2] == uSection8 or
                                    UNICODEText[j:j + 2] == uBlank or UNICODEText[j:j + 2] == uBlank2 or UNICODEText[
                                                                                                         j:j + 2] == uNewline or
                                    UNICODEText[j:j + 2] == uNewline2 or UNICODEText[j:j + 2] == uNewline3 or UNICODEText[
                                                                                                              j:j + 2] == uNewline4 or
                                    UNICODEText[j:j + 2] == uTab or UNICODEText[j + 1] == uSpecial):
                                j += 2
                                continue
                            else:
                                k = j
                                break

                        if j >= len(UNICODEText):
                            break

                    elif (UNICODEText[k:k + 2] == uBlank or UNICODEText[k:k + 2] == uBlank2 or UNICODEText[
                                                                                               k:k + 2] == uTab):

                        string += bytes([UNICODEText[k]])
                        string += bytes([UNICODEText[k + 1]])

                        j = k + 2
                        while j < len(UNICODEText):
                            if (UNICODEText[j:j + 2] == uSection2 or UNICODEText[j:j + 2] == uSection3 or UNICODEText[
                                                                                                          j:j + 2] == uSection4 or
                                    UNICODEText[j:j + 2] == uSection5 or UNICODEText[j:j + 2] == uSection7 or UNICODEText[
                                                                                                              j:j + 2] == uSection8 or
                                    UNICODEText[j:j + 2] == uBlank or UNICODEText[j:j + 2] == uBlank2 or UNICODEText[
                                                                                                         j:j + 2] == uTab or
                                    UNICODEText[j + 1] == uSpecial):
                                j += 2
                                continue
                            else:
                                k = j
                                break

                        if (j >= len(UNICODEText)):
                            break

                    string += bytes([UNICODEText[k]])
                    string += bytes([UNICODEText[k + 1]])
                    k += 2

            elif encodingFlag == False:  ### 16-bit Unicode
                fcSize = 2 * (aCPSize[i + 1] - aCPSize[i])

                if (len(
                        word_document) < fcIndex + fcSize + 1):  # Invalid structure - size info is invalid (large) => scan from fcIndex to last
                    if (bFullScanU == False and len(word_document) > fcIndex):
                        fcSize = len(word_document) - fcIndex - 1
                        bFullScanU = True
                    else:
                        ClxIndex = ClxIndex + 8
                        continue

                while k < fcSize:
                    if (word_document[fcIndex + k: fcIndex + k + 2] == uSection2 or word_document[
                                                                                    fcIndex + k: fcIndex + k + 2] == uSection3 or
                            word_document[fcIndex + k: fcIndex + k + 2] == uSection4 or word_document[
                                                                                        fcIndex + k: fcIndex + k + 2] == uSection5 or
                            word_document[fcIndex + k: fcIndex + k + 2] == uSection7 or word_document[
                                                                                        fcIndex + k: fcIndex + k + 2] == uSection8 or
                            word_document[fcIndex + k + 1] == uSpecial or word_document[
                                                                          fcIndex + k: fcIndex + k + 2] == uTrash):
                        k += 2
                        continue

                    if (word_document[fcIndex + k: fcIndex + k + 2] == uNewline or word_document[
                                                                                   fcIndex + k: fcIndex + k + 2] == uNewline2 or
                            word_document[fcIndex + k: fcIndex + k + 2] == uNewline3 or word_document[
                                                                                        fcIndex + k: fcIndex + k + 2] == uNewline4):

                        if (word_document[fcIndex + k] == 0x0d):
                            string += b'\x0a'
                            string += bytes([word_document[fcIndex + k + 1]])
                        else:
                            string += bytes([word_document[fcIndex + k]])
                            string += bytes([word_document[fcIndex + k + 1]])

                        j = k + 2
                        while j < fcSize:
                            if (word_document[fcIndex + j: fcIndex + j + 2] == uSection2 or word_document[
                                                                                            fcIndex + j: fcIndex + j + 2] == uSection3 or word_document[
                                                                                                                                          fcIndex + j: fcIndex + j + 2] == uSection4 or
                                    word_document[fcIndex + j: fcIndex + j + 2] == uSection5 or word_document[
                                                                                                fcIndex + j: fcIndex + j + 2] == uSection7 or word_document[
                                                                                                                                              fcIndex + j: fcIndex + j + 2] == uSection8 or
                                    word_document[fcIndex + j: fcIndex + j + 2] == uBlank or word_document[
                                                                                             fcIndex + j: fcIndex + j + 2] == uBlank2 or word_document[
                                                                                                                                         fcIndex + j: fcIndex + j + 2] == uNewline or word_document[
                                                                                                                                                                                      fcIndex + j: fcIndex + j + 2] == uNewline2 or
                                    word_document[fcIndex + j: fcIndex + j + 2] == uNewline3 or word_document[
                                                                                                fcIndex + j: fcIndex + j + 2] == uNewline4 or word_document[
                                                                                                                                              fcIndex + j: fcIndex + j + 2] == uTab or
                                    word_document[
                                        fcIndex + j + 1] == uSpecial):
                                j += 2
                                continue
                            else:
                                k = j
                                break

                        if j >= fcSize:
                            break

                    elif word_document[fcIndex + k: fcIndex + k + 2] == uBlank or word_document[
                                                                                  fcIndex + k: fcIndex + k + 2] == uBlank2 or word_document[
                                                                                                                              fcIndex + k: fcIndex + k + 2] == uTab:
                        string += bytes([word_document[fcIndex + k]])
                        string += bytes([word_document[fcIndex + k + 1]])

                        j = k + 2
                        while j < fcSize:
                            if (word_document[fcIndex + j: fcIndex + j + 2] == uSection2 or word_document[
                                                                                            fcIndex + j: fcIndex + j + 2] == uSection3 or word_document[
                                                                                                                                          fcIndex + j: fcIndex + j + 2] == uSection4 or
                                    word_document[fcIndex + j: fcIndex + j + 2] == uSection5 or word_document[
                                                                                                fcIndex + j: fcIndex + j + 2] == uSection7 or word_document[
                                                                                                                                              fcIndex + j: fcIndex + j + 2] == uSection8 or
                                    word_document[fcIndex + j: fcIndex + j + 2] == uBlank or word_document[
                                                                                             fcIndex + j: fcIndex + j + 2] == uBlank2 or word_document[
                                                                                                                                         fcIndex + j: fcIndex + j + 2] == uTab or
                                    word_document[fcIndex + j + 1] == uSpecial):
                                j += 2
                                continue
                            else:
                                k = j
                                break

                        if j >= fcSize:
                            break

                    string += bytes([word_document[fcIndex + k]])
                    string += bytes([word_document[fcIndex + k + 1]])
                    k += 2

            ClxIndex += 8

        dictionary = self.__doc_extra_filter__(string, len(string))

        filteredText = dictionary['string']
        filteredLen = dictionary['length']

        for i in range(0, len(filteredText), 2):
            try:
                self.content += filteredText[i:i+2].decode('utf-16')
            except UnicodeDecodeError:
                continue

        self._text = self.content
        ####################################################
        return self._text

    def get_structure(self):
        return self._structure

    def parse(self):
        ''' 작업 해야함 '''
        return self.data

    def __doc_extra_filter__(self, string, uFilteredTextLen):
        i = 0
        j = 0
        k = 0
        textLen = uFilteredTextLen
        # 1. 첫 부분의        공백        문자        모두        제거
        # 2. 공백        문자가        2        개        이상인        경우에        1        개로        만들자
        # 3.        개행        문자가        2        개        이상인        경우에        1        개로        만들자
        # 4.        Filtering

        uBlank = b'\x20\x00'   # ASCII Blank
        uBlank2 = b'\xA0\x00'   # Unicode Blank
        uNewline = b'\x0A\x00'   # Line Feed
        uNewline2 = b'\x0D\x00'
        uNewline3 = b'\x04\x00'
        uNewline4 = b'\x03\x00'
        uSection = b'\x01\x00'
        uSection2 = b'\x02\x00'
        uSection3 = b'\x05\x00'
        uSection4 = b'\x07\x00'
        uSection5 = b'\x08\x00'
        uSection6 = b'\x15\x00'
        uSection7 = b'\x0C\x00'
        uSection8 = b'\x0B\x00'
        uSection9 = b'\x14\x00'
        uTrash = b'\x00\x00'
        uCaption = b'\x53\x00\x45\x00\x51\x00'
        uCaption2 = b'\x41\x00\x52\x00\x41\x00\x43\x00\x49\x00\x43\x00\x20\x00\x14\x00'
        uHyperlink = b'\x48\x00\x59\x00\x50\x00\x45\x00\x52\x00\x4C\x00\x49\x00\x4E\x00\x4B\x00'
        uToc = b'\x54\x00\x4F\x00'
        uPageref = b'\x50\x00\x41\x00\x47\x00\x45\x00\x52\x00\x45\x00\x46\x00'
        uIndex = b'\x49\x00\x4E\x00\x44\x00\x45\x00\x58\x00'
        uEnd = b'\x20\x00\x01\x00\x14\x00'
        uEnd2 = b'\x20\x00\x14\x00'
        uEnd3 = b'\x20\x00\x15\x00'
        uEnd4 = b'\x14\x00'
        uEnd5 = b'\x01\x00\x14\x00'
        uEnd6 = b'\x15\x00'
        uHeader = b'\x13\x00'
        uChart = b'\x45\x00\x4D\x00\x42\x00\x45\x00\x44\x00'
        uShape = b'\x53\x00\x48\x00\x41\x00\x50\x00\x45\x00'
        uPage = b'\x50\x00\x41\x00\x47\x00\x45\x00'
        uDoc = b'\x44\x00\x4F\x00\x43\x00'
        uStyleref = b'\x53\x00\x54\x00\x59\x00\x4C\x00\x45\x00\x52\x00\x45\x00\x46\x00'
        uTitle = b'\x54\x00\x49\x00\x54\x00\x4C\x00\x45\x00'
        uDate = b'\x49\x00\x46\x00\x20\x00\x44\x00\x41\x00\x54\x00\x45\x00'
        filteredText = string
        while i < textLen :
            if i == 0:
                k = 0
                while (filteredText[0:2] == uBlank or filteredText[0:2] == uBlank2 or filteredText
                                                                                      [0:2] == uNewline or filteredText
                                                                                                          [0:2] == uNewline2 or
                       filteredText[0:2] == uNewline3 or filteredText[0:2] == uNewline4) :
                    filteredText = filteredText[:k] + filteredText[k + 2:]
                    textLen -= 2

                    if (len(filteredText) == 0):
                        break

            if len(filteredText) == 0:
                break


            if (len(filteredText) >= 2 + i) and filteredText[i : i + 2] == uHeader:
                filteredText = filteredText[:i] + filteredText[i + 2:]
                textLen -= 2

                if (len(filteredText) >= 2 + i) and filteredText[i : i + 2] == uBlank:
                    filteredText = filteredText[:i] + filteredText[i + 2:]
                    textLen -= 2

                charSize = 0
                temp = True
                j = i

                if (len(filteredText) >= 16 + i) and \
                        (filteredText[i: i + 6] == uCaption or filteredText[i: i + 18] == uHyperlink or
                        filteredText[i: i + 4] == uToc or filteredText[i: i + 14] == uPageref or filteredText[
                                                                                                 i: i + 10] == uIndex or
                        filteredText[i: i + 10] == uChart or filteredText[i: i + 10] == uShape or filteredText[
                                                                                                  i: i + 8] == uPage or
                        filteredText[i: i + 6] == uDoc or filteredText[i: i + 16] == uStyleref or filteredText[
                                                                                                  i: i + 10] == uTitle or filteredText[
                                                                                                                          i: i + 14] == uDate):
                    pass
                else:
                    temp = False

                while temp == True:
                    if (len(filteredText) >= 6 + j) and (filteredText[j: j + 6] == uEnd):
                        charSize += 6
                        j += 6
                        break

                    elif (len(filteredText) >= 4 + j) and (
                            filteredText[j: j + 4] == uEnd2 or filteredText[j: j + 4] == uEnd3):
                        charSize += 4
                        j += 4
                        break
                    elif (len(filteredText) >= 2 + j) and (filteredText[j: j + 2] == uEnd4):
                        charSize += 2
                        j += 2
                        break

                    charSize += 2
                    j += 2

                    if (len(filteredText) < 6 + j):
                        temp = False
                        break

                if temp == True:
                    filteredText = filteredText[:i] + filteredText[i + charSize:]
                    textLen -= charSize

                i -= 2
                continue

            if (len(filteredText) >= 2 + i) and (
                    filteredText[i: i + 2] == uSection or filteredText[i: i + 2] == uSection6 or
                    filteredText[i: i + 2] == uSection9):
                filteredText = filteredText[:i] + filteredText[i + 2:]
                textLen -= 2

                i -= 2
                continue

            if (len(filteredText) >= 4 + i) and (filteredText[i: i + 4] == uHeader):
                filteredText = filteredText[:i] + filteredText[i + 4:]
                textLen -= 4

                i -= 4
                continue

            i += 2
        dict = {}
        dict['string'] = filteredText
        dict['length'] = textLen
        return dict

    # validation code
    def _validate_header(self):
        if self._header.signature != definitions.COMPOUND_SIGNATURE:
            return False

        if self._header.byte_order != definitions.COMPOUND_BYTE_ORDER:
            return False

        return True

    def _validate_root_entry(self):
        if self._dir_entries[0].name_trancated != 'Root Entry':
            return False

        return True

    def _validate_stream_summaryinfo(self, data, length, name):

        summary_info_sig = struct.unpack('<I', data[0:4])[0]

        if summary_info_sig == 0x0000FFFE:
            OSVersion =  struct.unpack('<I', data[4:8])[0]
            totalLength = struct.unpack('<I', data[44:48])[0]
            totalLength += struct.unpack('<I', data[48:52])[0]

            # print(hex((OSVersion >> 24) & 0xFF)) = [3]
            # print(hex((OSVersion >> 16) & 0xFF)) = [2]
            # print(hex((OSVersion >> 8) & 0xFF))  = [1]
            # print(hex((OSVersion) & 0xFF))       = [0]
            if OSVersion & 0xFF == 0x05:
                if (OSVersion >> 8) & 0xFF == 0:
                    self._doc_info['SumInfoWindowsVer'] = 'Windows 2000'
                elif (OSVersion >> 8) & 0xFF == 1:
                    self._doc_info['SumInfoWindowsVer'] = 'Windows XP'
                elif (OSVersion >> 8) & 0xFF == 2:
                    self._doc_info['SumInfoWindowsVer'] = 'Windows XP 64-Bit Edition'
            elif OSVersion & 0xFF == 0x06:
                if (OSVersion >> 8) & 0xFF == 0:
                    self._doc_info['SumInfoWindowsVer'] = 'Windows Vista'
                elif (OSVersion >> 8) & 0xFF == 1:
                    self._doc_info['SumInfoWindowsVer'] = 'Windows 7'
                elif (OSVersion >> 8) & 0xFF == 2:
                    self._doc_info['SumInfoWindowsVer'] = 'Windows 8'
                elif (OSVersion >> 8) & 0xFF == 3:
                    self._doc_info['SumInfoWindowsVer'] = 'Windows 8.1'

            if length > 14 * 4:
                propCount = struct.unpack('<I', data[52:56])[0]

                if length <14 * 4 + propCount * 8:
                    propCount = 0

            else:
                propCount = 0

            #print(propCount*2)

            for i in range(1, propCount * 2, 2):

                if struct.unpack('<I', data[52 + i * 4:56 + i * 4])[0] == 0x02 or struct.unpack('<I', data[52 + i * 4:56 + i * 4])[0] == 0x03 \
                    or struct.unpack('<I', data[52 + i * 4:56 + i * 4])[0] == 0x04 or struct.unpack('<I', data[52 + i * 4:56 + i * 4])[0] == 0x05 \
                    or struct.unpack('<I', data[52 + i * 4:56 + i * 4])[0] == 0x06 or struct.unpack('<I', data[52 + i * 4:56 + i * 4])[0] == 0x07 \
                    or struct.unpack('<I', data[52 + i * 4:56 + i * 4])[0] == 0x08 or struct.unpack('<I', data[52 + i * 4:56 + i * 4])[0] == 0x09 \
                    or struct.unpack('<I', data[52 + i * 4:56 + i * 4])[0] == 0x12 or struct.unpack('<I', data[52 + i * 4:56 + i * 4])[0] == 0x14:

                    propOffset = struct.unpack('<I', data[52 + (i + 1) * 4:56 + (i + 1) * 4])[0]

                    if struct.unpack('<I', data[48 + propOffset:52 + propOffset])[0] == 0x1F:
                        ulen = struct.unpack('<I', data[52 + propOffset:56 + propOffset])[0]
                        if ulen < 2:
                            continue

                        wInfo = data[56 + propOffset: 56 + propOffset + ((ulen-1) * 2)].decode('utf-16')

                        if struct.unpack('<I', data[52 + i * 4:56 + i * 4])[0] == 0x02:
                            self._doc_info['SumInfoTitle'] = wInfo
                        elif struct.unpack('<I', data[52 + i * 4:56 + i * 4])[0] == 0x04:
                            self._doc_info['SumInfoAuthor'] = wInfo
                        elif struct.unpack('<I', data[52 + i * 4:56 + i * 4])[0] == 0x08:
                            self._doc_info['SumInfoLastSavedBy'] = wInfo
                        elif struct.unpack('<I', data[52 + i * 4:56 + i * 4])[0] == 0x09:
                            self._doc_info['SumInfoVersion'] = wInfo
                        elif struct.unpack('<I', data[52 + i * 4:56 + i * 4])[0] == 0x14:
                            self._doc_info['SumInfoDate'] = wInfo

                elif struct.unpack('<I', data[52 + i * 4:56 + i * 4])[0] == 0x0C:
                    propOffset = struct.unpack('<I', data[52 + (i + 1) * 4:56 + (i + 1) * 4])[0]
                    if struct.unpack('<I', data[48 + propOffset:52 + propOffset])[0] == 0x40:
                        ft = struct.unpack('<q', data[52 + propOffset:60 + propOffset])[0]
                        self._doc_info['SumInfoCreatedTime'] = filetime_to_dt(ft)

                elif struct.unpack('<I', data[52 + i * 4:56 + i * 4])[0] == 0x0D:
                    propOffset = struct.unpack('<I', data[52 + (i + 1) * 4:56 + (i + 1) * 4])[0]
                    if struct.unpack('<I', data[48 + propOffset:52 + propOffset])[0] == 0x40:
                        ft = struct.unpack('<q', data[52 + propOffset:60 + propOffset])[0]
                        #self._doc_info['SumInfoLastSavedTime'] = time.filetime_to_dt(ft)  # 191128_0200 임시 주석

            if length != totalLength:
                self._validate_unknown_data(definitions.HC_STR_VTYPE_UNUSED_AREA, data[totalLength:], length-totalLength, totalLength, length-totalLength, name)

        return True

    def _validate_stream_docsummaryinfo(self, data, length, name):

        summary_info_sig = struct.unpack('<I', data[0:4])[0]

        if summary_info_sig == 0x0000FFFE:
            OSVersion =  struct.unpack('<I', data[4:8])[0]
            totalLength = struct.unpack('<I', data[44:48])[0]
            totalLength += struct.unpack('<I', data[48:52])[0]

            # print(hex((OSVersion >> 24) & 0xFF)) = [3]
            # print(hex((OSVersion >> 16) & 0xFF)) = [2]
            # print(hex((OSVersion >> 8) & 0xFF))  = [1]
            # print(hex((OSVersion) & 0xFF))       = [0]
            if OSVersion & 0xFF == 0x05:
                if (OSVersion >> 8) & 0xFF == 0:
                    self._doc_info['SumInfoWindowsVer'] = 'Windows 2000'
                elif (OSVersion >> 8) & 0xFF == 1:
                    self._doc_info['SumInfoWindowsVer'] = 'Windows XP'
                elif (OSVersion >> 8) & 0xFF == 2:
                    self._doc_info['SumInfoWindowsVer'] = 'Windows XP 64-Bit Edition'
            elif OSVersion & 0xFF == 0x06:
                if (OSVersion >> 8) & 0xFF == 0:
                    self._doc_info['SumInfoWindowsVer'] = 'Windows Vista'
                elif (OSVersion >> 8) & 0xFF == 1:
                    self._doc_info['SumInfoWindowsVer'] = 'Windows 7'
                elif (OSVersion >> 8) & 0xFF == 2:
                    self._doc_info['SumInfoWindowsVer'] = 'Windows 8'
                elif (OSVersion >> 8) & 0xFF == 3:
                    self._doc_info['SumInfoWindowsVer'] = 'Windows 8.1'

            if length > 14 * 4:
                propCount = struct.unpack('<I', data[52:56])[0]

                if length <14 * 4 + propCount * 8:
                    propCount = 0

            else:
                propCount = 0

            #print(propCount*2)

            for i in range(1, propCount * 2, 2):

                if struct.unpack('<I', data[52 + i * 4:56 + i * 4])[0] == 0x02 or struct.unpack('<I', data[52 + i * 4:56 + i * 4])[0] == 0x03 \
                    or struct.unpack('<I', data[52 + i * 4:56 + i * 4])[0] == 0x04 or struct.unpack('<I', data[52 + i * 4:56 + i * 4])[0] == 0x05 \
                    or struct.unpack('<I', data[52 + i * 4:56 + i * 4])[0] == 0x06 or struct.unpack('<I', data[52 + i * 4:56 + i * 4])[0] == 0x07 \
                    or struct.unpack('<I', data[52 + i * 4:56 + i * 4])[0] == 0x08 or struct.unpack('<I', data[52 + i * 4:56 + i * 4])[0] == 0x09 \
                    or struct.unpack('<I', data[52 + i * 4:56 + i * 4])[0] == 0x12 or struct.unpack('<I', data[52 + i * 4:56 + i * 4])[0] == 0x14:

                    propOffset = struct.unpack('<I', data[52 + (i + 1) * 4:56 + (i + 1) * 4])[0]

                    if struct.unpack('<I', data[48 + propOffset:52 + propOffset])[0] == 0x1F:
                        ulen = struct.unpack('<I', data[52 + propOffset:56 + propOffset])[0]
                        if ulen < 2:
                            continue

                        wInfo = data[56 + propOffset: 56 + propOffset + ((ulen-1) * 2)].decode('utf-16')

                        if struct.unpack('<I', data[52 + i * 4:56 + i * 4])[0] == 0x02:
                            self._doc_info['SumInfoTitle'] = wInfo
                        elif struct.unpack('<I', data[52 + i * 4:56 + i * 4])[0] == 0x04:
                            self._doc_info['SumInfoAuthor'] = wInfo
                        elif struct.unpack('<I', data[52 + i * 4:56 + i * 4])[0] == 0x08:
                            self._doc_info['SumInfoLastSavedBy'] = wInfo
                        elif struct.unpack('<I', data[52 + i * 4:56 + i * 4])[0] == 0x09:
                            self._doc_info['SumInfoVersion'] = wInfo
                        elif struct.unpack('<I', data[52 + i * 4:56 + i * 4])[0] == 0x14:
                            self._doc_info['SumInfoDate'] = wInfo

                elif struct.unpack('<I', data[52 + i * 4:56 + i * 4])[0] == 0x0C:
                    propOffset = struct.unpack('<I', data[52 + (i + 1) * 4:56 + (i + 1) * 4])[0]
                    if struct.unpack('<I', data[48 + propOffset:52 + propOffset])[0] == 0x40:
                        ft = struct.unpack('<q', data[52 + propOffset:60 + propOffset])[0]
                        self._doc_info['SumInfoCreatedTime'] = filetime_to_dt(ft)

                elif struct.unpack('<I', data[52 + i * 4:56 + i * 4])[0] == 0x0D:
                    propOffset = struct.unpack('<I', data[52 + (i + 1) * 4:56 + (i + 1) * 4])[0]
                    if struct.unpack('<I', data[48 + propOffset:52 + propOffset])[0] == 0x40:
                        ft = struct.unpack('<q', data[52 + propOffset:60 + propOffset])[0]
                        self._doc_info['SumInfoLastSavedTime'] = filetime_to_dt(ft)

            if length != totalLength:
                self._validate_unknown_data(definitions.HC_STR_VTYPE_UNUSED_AREA, data[totalLength:], length-totalLength, totalLength, length-totalLength, name)

        return True

    def _validate_stream_compobj(self, data, length, name):
        pass

    def _validate_stream_dir(self, data, length, name):
        pass

    def _validate_stream_workbook(self, data, length, name):
        pass

    def _validate_stream_worddocument(self, data, length, name):
        pass

    def _validate_stream_data(self, data, length, name):
        pass

    def _validate_stream_powerpointdocument(self, data, length, name):
        pass

    def _is_in_vba(self, entry_name):
        return True

    def _check_dummy_data(self, buf, buf_len, abnormal_d):
        pass

    def _validate_unknown_data(self, type, buf, buf_len, offset, length, name, desc=""):
        pass

    # _is_valid_child, _get_parent_storage는 compound class에서 구현되는게 맞는것같다.....
    def _is_valid_child(self, target_idx, storage_name, storage_idx=-1):

        ret = False
        name = ''
        elements = []

        if storage_idx != -1:
            for entry in self._cp._dir_entries:
                try:
                    if entry.name_trancated == storage_name:
                        name = entry.name_trancated
                        break
                except Exception:
                    continue

            if(name == ''): return ret

            if self._cp._get_siblings(entry.child_id, elements):
                for idx in range(len(elements)):
                    if target_idx == elements[idx]:
                        ret = True
                        break

        return ret

    def _get_parent_storage(self, target_idx):

        elements = []
        ret = False

        for entry in self._cp._dir_entries:
            if entry.object_type.value != 1 and entry.object_type.value != 5:
                continue

            if self._cp._get_siblings(entry.child_id, elements):
                for idx in range(len(elements)):
                    if target_idx == elements[idx]:
                        ret = True
                        break
            if ret: break


        return entry.name_trancated