# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import io
import struct
import datetime

from modules.SIGA import definitions
from modules.SIGA.utility import filetime_to_dt
from modules.SIGA.classes.interface import Common
from modules.SIGA.classes.documents.compound import Compound
from modules.SIGA.formats.documents.cfbf.fm_cfbf_dir_entry import CfbfDirEntry


class XLS(Common):

    def __init__(self, input=None):
        # self.tar = fm_TAR()

        self.input = input
        #self.data = fm_Cfbf.from_file(self.input)
        self.data = None
        self._ext = None
        self._metadata = None
        self._text = None
        self._structure = dict()

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
            if entry.name_trancated == 'Workbook':
                self._ext = '.xls'

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
                if entry.name_trancated == 'Workbook':
                    self._ext = '.xls'
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

            # Workbook
            if entry.name_trancated == 'Workbook':
                storage_name = self._get_parent_storage(entry_idx)
                if storage_name == 'Root Entry' or self._is_valid_child(entry_idx, "ObejctPool", 0):
                    self._validate_stream_workbook(d, len(d), entry.name_trancated)
                else:
                    desc = f'{storage_name} Storage 하위에 포함됨'
                    self._set_vuln_info(definitions.HC_STR_VTYPE_UNKWNON_STREAM, 0, 0, desc, entry.name_trancated)
                    self._validate_unknown_data(definitions.HC_STR_VTYPE_ABNORMAL_BINDATA, d, len(d), 0, 0,
                                                entry.name_trancated)
                continue

            # |SummaryInformation
            if entry.name_trancated == '\x05SummaryInformation':
                storage_name = self._get_parent_storage(entry_idx)

                if storage_name == "Root Entry" or (storage_name[0:3] == "MBD" and len(storage_name) == 11) or \
                    self._is_valid_child(entry_idx, "ObjectPool"):
                    self._validate_stream_summaryinfo(d, len(d), entry.name_trancated)
                else:
                    # 부모 Storage가 Root Entry나 MBD(embedded object)가 아닐 경우 오류
                    desc = f'{storage_name} Storage 하위에 포함됨'
                    self._set_vuln_info(definitions.HC_STR_VTYPE_UNKWNON_STREAM, 0, 0, desc, entry.name_trancated)
                    self._validate_unknown_data(definitions.HC_STR_VTYPE_ABNORMAL_BINDATA, d, len(d), 0, 0,entry.name_trancated)
                continue

            # |DocumentSummaryInformation
            if entry.name_trancated == '\x05DocumentSummaryInformation':
                storage_name = self._get_parent_storage(entry_idx)

                if storage_name == "Root Entry" or (storage_name[0:3] == "MBD" and len(storage_name) == 11) or \
                    self._is_valid_child(entry_idx, "ObjectPool"):
                    self._validate_stream_docsummaryinfo(d, len(d), entry.name_trancated)
                else:
                    # 부모 Storage가 Root Entry나 MBD(embedded object)가 아닐 경우 오류
                    desc = f'{storage_name} Storage 하위에 포함됨'
                    self._set_vuln_info(definitions.HC_STR_VTYPE_UNKWNON_STREAM, 0, 0, desc, entry.name_trancated)
                    self._validate_unknown_data(definitions.HC_STR_VTYPE_ABNORMAL_BINDATA, d, len(d), 0, 0,
                                                entry.name_trancated)
                continue

            # \x01CompObj
            if entry.name_trancated == '\x01CompObj':
                self._validate_stream_compobj(d, len(d), entry.name_trancated)
                continue

            # [Root Entry] - [_VBA_PROJECT_CUR] - [VBA]
            if entry.name_trancated == 'dir':
                if self._is_valid_child(entry_idx, "VBA"):
                    self._validate_stream_dir(d, len(d), entry.name_trancated)
                else:
                    storage_name = self._get_parent_storage(entry_idx)
                    desc = f'{storage_name} Storage 하위에 포함됨'
                    self._set_vuln_info(definitions.HC_STR_VTYPE_UNKWNON_STREAM, 0, 0, desc, entry.name_trancated)
                    self._validate_unknown_data(definitions.HC_STR_VTYPE_ABNORMAL_BINDATA, d, len(d), 0, 0,
                                                entry.name_trancated)
                continue

            # else
            if entry.name_trancated == 'Ctls' or entry.name_trancated[1:11] == 'DataSpaces' or \
                    entry.name_trancated == 'encryption' or entry.name_trancated == 'List Data' or \
                    entry.name_trancated == 'XCB' or entry.name_trancated[1:4] == 'Ole' or \
                    entry.name_trancated[1:11] == 'DRMContent' or entry.name_trancated[1:7] == 'EPRINT' or \
                    entry.name_trancated == 'Revision Log' or entry.name_trancated == '_signatures' or \
                    entry.name_trancated == 'User Names' or entry.name_trancated[1:17] == 'DRMViewerContent' or \
                    entry.name_trancated == '_xmlsignatures' or entry.name_trancated == 'XML' or \
                    entry.name_trancated[1:8] == 'ObjInfo' or entry.name_trancated[1:8] == 'OlePres' or \
                    entry.name_trancated == '0Table' or entry.name_trancated == '1Table':
                storage_name = self._get_parent_storage(entry_idx)

                if storage_name != "Root Entry" and storage_name[0:3] == "MBD" and not self._is_valid_child(storage_name, "ObjectPool"):
                    desc = '%s Storage 하위에 포함됨' % self._get_parent_storage(entry_idx)
                    self._set_vuln_info(definitions.HC_STR_VTYPE_UNKWNON_STREAM, 0, 0, desc, entry.name_trancated)

                self._validate_unknown_data(definitions.HC_STR_VTYPE_ABNORMAL_BINDATA, d, len(d), 0, 0, entry.name_trancated)

            # PROJECT
            if entry.name_trancated == 'PROJECT' or entry.name_trancated == 'PROJECTwm':
                if not self._is_valid_child(entry_idx, "_VBA_PROJECT_CUR"):
                    desc = '%s Storage 하위에 포함됨' % self._get_parent_storage(entry_idx)
                    self._set_vuln_info(definitions.HC_STR_VTYPE_UNKWNON_STREAM, 0, 0, desc, entry.name_trancated)
                self._validate_unknown_data(definitions.HC_STR_VTYPE_ABNORMAL_BINDATA, d, len(d), 0, 0, entry.name_trancated)

            # Item / Properties
            if entry.name_trancated == 'Item' or entry.name_trancated == 'Properties':
                storage_name = self._get_parent_storage(entry_idx)

                if not self._is_valid_child(storage_name, "MsoDataStore"):
                    desc = '%s Storage 하위에 포함됨' % self._get_parent_storage(entry_idx)
                    self._set_vuln_info(definitions.HC_STR_VTYPE_UNKWNON_STREAM, 0, 0, desc, entry.name_trancated)

                self._validate_unknown_data(definitions.HC_STR_VTYPE_ABNORMAL_BINDATA, d, len(d), 0, 0,entry.name_trancated)

            elif self._is_valid_child(entry_idx, "_SX_DB_CUR") or self._is_valid_child(entry_idx, "VBA") or \
                entry.name_trancated == "o" or entry.name_trancated == "x" or entry.name_trancated == "f" or \
                entry.name_trancated[1:8] == "VBFrame":

                if self._is_in_vba(entry.name_trancated):
                    continue

                self._validate_unknown_data(definitions.HC_STR_VTYPE_ABNORMAL_BINDATA, d, len(d), 0, 0,entry.name_trancated)

            else:
                storage_name = self._get_parent_storage(entry_idx)

                if not self._is_valid_child(entry_idx, "ObjectPool") and storage_name[0:3] == "MBD":
                    desc = '%s Storage 하위에 포함됨' % self._get_parent_storage(entry_idx)
                    self._set_vuln_info(definitions.HC_STR_VTYPE_UNKWNON_STREAM, 0, 0, desc, entry.name_trancated)

                self._validate_unknown_data(definitions.HC_STR_VTYPE_ABNORMAL_BINDATA, d, len(d), 0, 0, entry.name_trancated)

            desc = 'Unknown Stream'
            self._set_vuln_info(definitions.HC_STR_VTYPE_UNKWNON_STREAM, 0, 0, desc, entry.name_trancated)

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
        """
        self.fp = Compound(self.input)
        self.fp.get_header()
        self.fp.load_compound()

        # Traverse each directory entry and its data stream
        for entry in self.fp._dir_entries:
            if entry.name_len > 64 or entry.object_type == CfbfDirEntry.ObjType.unknown:
                continue

            if entry.name[:(entry.name_len >> 1) - 1] == "Workbook":
                if self.fp._header.mini_stream_cutoff_size <= entry.size:
                    f = self.fp._get_stream(entry)
                else:
                    f = self.fp._get_mini_stream(entry)



            #print("[ {0} ]".format(entry.name_trancated))
            #print('\t', entry.object_type)
            #print('\t', entry.size)
#            self.fp._print_hex_dump(f[:64])

        ################ workbook read 완료 ################

        RECORD_HEADER_SIZE = 4
        records = []
        # 스트림 내부 모두 파싱해서 데이터 출력
        tempOffset = 0
        content = ""       # 최종 저장될 스트링
        substream = 0

        #test = open('E:\\01. Project\\10. I-AI\\LEGO\\LEGO-0901-1616\\test.txt', 'w')
        while tempOffset < len(f):
            dic = {}
            dic['offset'] = tempOffset
            dic['type'] = struct.unpack('<h', f[tempOffset: tempOffset + 0x02])[0]

            if dic['type'] == 0:        # EOF 이후 값
                break

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
                            string += str(d[cntStream: cntStream + 2].decode("utf-16"))
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
                            string += str(bytes([d[cntStream]]).decode("ascii"))
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

                strRKValue = self._translate_RK_value(value)
                strRKValue = self._convert_to_XF_type(strRKValue, idxToXF, arrStXFType)

        self._text = content


        ####################################################
        return self._text
        """
    def get_structure(self):

        if not self._is_encrypted and self._vuln_cnt == 0:
            self._structure['Vuln_Result'] = '정상'
        elif self._is_encrypted and self._vuln_cnt == 0:
            self._structure['Vuln_Result'] = '알 수 없음'
        else:
            self._structure['Vuln_Result'] = '의심'

        if self._vuln_cnt > 0:
            self._structure['Vuln_Info'] = self._vuln_info

        # HWP Record Information - option에서 체크 해야함 일단 TRUE
        temp_list = []
        temp_dict = dict()
        for key in self._arr_tag:
            for idx in range(len(self._arr_tag[key])):
                temp = ['name: '+ self._arr_tag[key][idx].name, 'offset: '+ str(self._arr_tag[key][idx].offset), 'length: '+ str(self._arr_tag[key][idx].length), 'desc: '+ self._arr_tag[key][idx].desc]
                temp_list.append(temp)

            temp_dict[key] = temp_list

        self._structure['DocInfo'] = self._doc_info
        self._structure['Compound Format Internals'] = self._cp.get_structure()
        self._structure['Record_Info'] = temp_dict

        return self._structure

    def parse(self):
        ''' 작업 해야함 '''
        return self.data

    def _translate_RK_value(self, value):
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

    def _convert_to_XF_type(self, strOriginal, idxToXF, arrStXFType):
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
                        self._doc_info['SumInfoLastSavedTime'] = filetime_to_dt(ft)

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