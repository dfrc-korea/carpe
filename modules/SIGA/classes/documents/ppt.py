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


class PPT(Common):
    RT_CurrentUserAtom = b'\xF6\x0F'
    RT_UserEditAtom = b'\xF5\x0F'
    RT_PersistPtrIncrementalAtom = b'\x72\x17'

    RT_Document = b'\xE8\x03'
    RT_MainMaster = b'\xF8\x03'
    RT_Slide = b'\xEE\x03'
    RT_Notes = b'\xF0\x03'
    RT_NotesAtom = b'\xF1\x03'

    RT_SlideListWithText = b'\xF0\x0F'
    RT_SlidePersistAtom = b'\xF3\x03'
    RT_TextHeader = b'\x9F\x0F'
    RT_TextBytesAtom = b'\xA8\x0F'
    RT_TextCharsAtom = b'\xA0\x0F'
    RT_StyleTextPropAtom = b'\xA1\x0F'
    RT_TextSpecInfoAtom = b'\xAA\x0F'

    RT_SlideAtom = b'\xEF\x03'
    RT_PPDrawing = b'\x0C\x04'
    RT_EscherClientTextbox = b'\x0D\xF0'

    # define RT_Slide							0x03EE	// 1006	 [C]
    RT_ProgTags = b'\x88\x13'
    RT_BinaryTagDataBlob = b'\x8B\x13'
    RT_Comment10 = b'\xE0\x2E'
    RT_CString = b'\xBA\x0F'

    # define RT_CString		0x0FBA	// 4026	 [A]	// UNICODE
    # define RT_Comment10			0x2EE0	// 12000 [C]
    # define RT_CString		0x0FBA	// 4026	 [A]	// UNICODE

    RT_EndDocument = b'\xEA\x03'

    def __init__(self, input=None):
        # self.tar = fm_TAR()

        self.input = input
        #self.data = fm_Cfbf.from_file(self.input)
        self.data = None
        self._ext = None
        self._metadata = None
        self._text = None
        self._structure = dict()

        self.powerpoint_document = bytearray(b'')
        self.current_user = bytearray(b'')
        self.current_offset = 0
        self.arr_user_edit_block = []
        self.arr_persist_ptr_incremental_block = []
        self.arr_edit_block_text = []
        self.text = b''              # tempText
        self.text_bytes = b''
        self.text_chars = b''
        self.filteredText = bytearray(b'')
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
            if entry.name_trancated == 'PowerPoint Document':
                self._ext = '.ppt'

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
                if entry.name_trancated == 'PowerPoint Document':
                    self._ext = '.ppt'
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

            # PowerPoint Document
            if entry.name_trancated == 'PowerPoint Document':
                storage_name = self._get_parent_storage(entry_idx)
                if storage_name == 'Root Entry' or (storage_name[0:3] == "MBD" and len(storage_name) == 11) or \
                        self._is_valid_child(storage_name, "ObjectPool"):
                    self._validate_stream_powerpointdocument(d, len(d), entry.name_trancated)

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
        self.fp = Compound(self.input)
        self.fp.get_header()
        self.fp.load_compound()

        # Traverse each directory entry and its data stream
        for entry in self.fp._dir_entries:
            if entry.name_len > 64 or entry.object_type == CfbfDirEntry.ObjType.unknown:
                continue

            if entry.name[:(entry.name_len >> 1) - 1] == "PowerPoint Document":
                if self.fp._header.mini_stream_cutoff_size <= entry.size:
                    self.powerpoint_document = self.fp._get_stream(entry)
                else:
                    self.powerpoint_document = self.fp._get_mini_stream(entry)

            if entry.name[:(entry.name_len >> 1) - 1] == "Current User":
                if self.fp._header.mini_stream_cutoff_size <= entry.size:
                    self.current_user = self.fp._get_stream(entry)
                else:
                    self.current_user = self.fp._get_mini_stream(entry)



            #print("[ {0} ]".format(entry.name_trancated))
            #print('\t', entry.object_type)
            #print('\t', entry.size)
            #self.fp._print_hex_dump(f[:64])

        ################ entry read 완료 ################

        # Get User Edit Offset
        self.current_offset = struct.unpack('<I', self.current_user[16 : 20])[0]

        # Set Chain
        # Set User Edit Chain
        tmpHeader = {}
        tmpHeader['option'] = struct.unpack('<H', self.powerpoint_document[self.current_offset: self.current_offset + 2])[0]
        tmpHeader['type'] = self.powerpoint_document[self.current_offset + 2 : self.current_offset + 4]
        tmpHeader['length'] = struct.unpack('<I', self.powerpoint_document[self.current_offset + 4: self.current_offset + 8])[0]

        editblock = {}
        editblock['last_user_edit_atom_offset'] = 0
        editblock['persist_ptr_incremental_block_offset'] = 0

        if tmpHeader['type'] == self.RT_UserEditAtom:
            self.current_offset += 8
            self.current_offset += 8

            editblock['last_user_edit_atom_offset'] = struct.unpack('<I', self.powerpoint_document[self.current_offset : self.current_offset + 4])[0]
            self.current_offset += 4
            editblock['persist_ptr_incremental_block_offset']  = struct.unpack('<I', self.powerpoint_document[self.current_offset : self.current_offset + 4])[0]
            self.current_offset += 4
            self.arr_user_edit_block.append(editblock)

        while editblock['last_user_edit_atom_offset'] != 0:
            self.current_offset = editblock['last_user_edit_atom_offset']

            tmpHeader.fromkeys(tmpHeader.keys(), 0)
            editblock.fromkeys(editblock.keys(), 0)

            tmpHeader['option'] = struct.unpack('<H', self.powerpoint_document[self.current_offset: self.current_offset + 2])[0]
            tmpHeader['type'] = self.powerpoint_document[self.current_offset + 2: self.current_offset + 4]
            tmpHeader['length'] = struct.unpack('<I', self.powerpoint_document[self.current_offset + 4: self.current_offset + 8])[0]

            if tmpHeader['type'] == self.RT_UserEditAtom:
                self.current_offset += 8
                self.current_offset += 8

                editblock['last_user_edit_atom_offset'] = struct.unpack('<I', self.powerpoint_document[self.current_offset : self.current_offset + 4])[0]
                self.current_offset += 4
                editblock['persist_ptr_incremental_block_offset'] = struct.unpack('<I', self.powerpoint_document[self.current_offset : self.current_offset + 4])[0]
                self.current_offset += 4
                self.arr_user_edit_block.append(editblock)




        # SetPersistPtrIncrementalBlockChain
        tmpSheet = 0
        tmpLength = 0
        ppl_block = []

        for i in range(0, len(self.arr_user_edit_block)):
            self.current_offset = self.arr_user_edit_block[i]['persist_ptr_incremental_block_offset']

            tmpHeader.fromkeys(tmpHeader.keys(), 0)
            ppl_block.clear()


            tmpLength = 0

            tmpHeader['option'] = struct.unpack('<H', self.powerpoint_document[self.current_offset: self.current_offset + 2])[0]
            tmpHeader['type'] = self.powerpoint_document[self.current_offset + 2: self.current_offset + 4]
            tmpHeader['length'] = struct.unpack('<I', self.powerpoint_document[self.current_offset + 4: self.current_offset + 8])[0]

            if tmpHeader['type'] == self.RT_PersistPtrIncrementalAtom:
                self.current_offset += 8

                while True:
                    sheet_offset = {}
                    sheet_offset['count'] = 0
                    sheet_offset['startnum'] = 0
                    sheet_offset['object'] = b''
                    sheet_offset['slidenum'] = []
                    sheet_offset['slideid'] = []

                    sheet_offset.fromkeys(sheet_offset.keys(), 0)
                    tmpSheet = 0

                    tmpSheet = struct.unpack('<I', self.powerpoint_document[self.current_offset : self.current_offset + 4])[0]
                    self.current_offset += 4

                    sheet_offset['count'] = tmpSheet >> 20
                    sheet_offset['startnum'] = tmpSheet & 0x000FFFFF
                    sheet_offset['object'] = self.powerpoint_document[self.current_offset : self.current_offset + sheet_offset['count'] * 4]
                    self.current_offset += sheet_offset['count'] * 4

                    ppl_block.append(sheet_offset)

                    tmpLength += (sheet_offset['count'] + 1) * 4
                    if tmpHeader['length'] == tmpLength:
                        break

                self.arr_persist_ptr_incremental_block.append(ppl_block)

        ### Extract Body Text
        # arrSlideText에 각 slide의 text 저장
        arrSlideText = []
        for i in range(0, len(self.arr_persist_ptr_incremental_block)):
            self.current_offset = struct.unpack('<I', self.arr_persist_ptr_incremental_block[i][0]['object'][0:4])[0]

            tmpHeader.fromkeys(tmpHeader.keys(), 0)
            tmpHeader['option'] = struct.unpack('<H', self.powerpoint_document[self.current_offset: self.current_offset + 2])[0]
            tmpHeader['type'] = self.powerpoint_document[self.current_offset + 2: self.current_offset + 4]
            tmpHeader['length'] = struct.unpack('<I', self.powerpoint_document[self.current_offset + 4: self.current_offset + 8])[0]
            self.current_offset += 8

            if tmpHeader['type'] != self.RT_Document:
                #print("Not RT_Document.")
                return

            tmpHeader.fromkeys(tmpHeader.keys(), 0)
            tmpHeader['option'] = struct.unpack('<H', self.powerpoint_document[self.current_offset: self.current_offset + 2])[0]
            tmpHeader['type'] = self.powerpoint_document[self.current_offset + 2: self.current_offset + 4]
            tmpHeader['length'] = struct.unpack('<I', self.powerpoint_document[self.current_offset + 4: self.current_offset + 8])[0]
            self.current_offset += 8

            if tmpHeader['type'] != self.RT_SlideListWithText:
                while True:
                    self.current_offset += tmpHeader['length']

                    if self.current_offset > len(self.powerpoint_document):
                        #print("Error!")
                        return

                    tmpHeader.fromkeys(tmpHeader.keys(), 0)
                    tmpHeader['option'] = struct.unpack('<H', self.powerpoint_document[self.current_offset: self.current_offset + 2])[0]
                    tmpHeader['type'] = self.powerpoint_document[self.current_offset + 2: self.current_offset + 4]
                    tmpHeader['length'] = struct.unpack('<I', self.powerpoint_document[self.current_offset + 4: self.current_offset + 8])[0]
                    self.current_offset += 8

                    if tmpHeader['type'] == self.RT_SlideListWithText:
                        break

            slide_text = ""
            in_text = False
            sheet_number = 0
            slide_id = 0
            current_offset_backup = 0
            presize = 0
            editblock_text = []

            while tmpHeader['type'] != self.RT_EndDocument:
                if len(self.powerpoint_document) < self.current_offset + 8:
                    if len(self.text) > 0 :
                        editblock_text.append(self.text)
                        self.text = b''
                    else :
                        slide_text = ""
                    break

                tmpHeader.fromkeys(tmpHeader.keys(), 0)
                tmpHeader['option'] = struct.unpack('<H', self.powerpoint_document[self.current_offset: self.current_offset + 2])[0]
                tmpHeader['type'] = self.powerpoint_document[self.current_offset + 2: self.current_offset + 4]
                tmpHeader['length'] = struct.unpack('<I', self.powerpoint_document[self.current_offset + 4: self.current_offset + 8])[0]
                self.current_offset += 8

                if tmpHeader['type'] == self.RT_SlideListWithText:
                    pass
                elif tmpHeader['type'] == self.RT_SlidePersistAtom:
                    if in_text == True:
                        editblock_text.append(self.text)
                        self.text = b''

                        in_text = False

                        if len(self.powerpoint_document) >= self.current_offset + 16 :
                            sheet_number = struct.unpack('<I', self.powerpoint_document[self.current_offset : self.current_offset + 4])[0]
                            slide_id = struct.unpack('<I', self.powerpoint_document[self.current_offset + 12: self.current_offset + 16])[0]
                            current_offset_backup = self.current_offset
                            self.__extract_text_in_slide__(i, sheet_number, slide_id)
                            self.current_offset = current_offset_backup
                        if self.text == None :
                            pass
                        elif len(self.text) > 0:
                            in_text = True

                    else :
                        # 각 슬라이드 text 추출
                        if len(self.powerpoint_document) >= self.current_offset + 16 :
                            sheet_number = struct.unpack('<I', self.powerpoint_document[self.current_offset : self.current_offset + 4])[0]
                            slide_id = struct.unpack('<I', self.powerpoint_document[self.current_offset + 12: self.current_offset + 16])[0]
                            current_offset_backup = self.current_offset
                            self.__extract_text_in_slide__(i, sheet_number, slide_id)
                            self.current_offset = current_offset_backup
                        if self.text == None :
                            pass
                        elif len(self.text) > 0:
                            in_text = True

                    self.current_offset += tmpHeader['length']

                elif tmpHeader['type'] == self.RT_TextHeader:
                    self.current_offset += tmpHeader['length']

                elif tmpHeader['type'] == self.RT_TextBytesAtom:
                    self.text_bytes = b''
                    self.text_chars = b''
                    self.text_bytes = self.powerpoint_document[self.current_offset: self.current_offset + tmpHeader['length']]
                    for i in range(0, len(self.text_bytes)):
                        self.text_chars += bytes([self.text_bytes[i]])
                        self.text_chars += b'\x00'

                    if self.text == None:
                        self.text = b''

                    presize = len(self.text)
                    self.text += self.text_chars
                    self.text += b'\x0A\x00'

                    self.current_offset += tmpHeader['length']
                    in_text = True

                elif tmpHeader['type'] == self.RT_TextCharsAtom:
                    self.text_chars = b''
                    self.text_chars = self.powerpoint_document[self.current_offset : self.current_offset + tmpHeader['length']]

                    if self.text == None:
                        self.text = b''

                    self.text += self.text_chars
                    self.text += b'\x0A\x00'

                    self.current_offset += tmpHeader['length']
                    in_text = True

                elif tmpHeader['type'] == self.RT_EndDocument:
                    if in_text == True:
                        editblock_text.append(self.text)
                        in_text = False
                else :
                    self.current_offset += tmpHeader['length']

            if len(editblock_text) > 0:
                self.arr_edit_block_text.append(editblock_text)

        j = 0
        uFilteredTextLen = 0

        for i in range(0, 1):
            if len(self.arr_edit_block_text) > 0:
                for j in range(0, len(self.arr_edit_block_text[i])):
                    uTempLen = int(len(self.arr_edit_block_text[i][j]) / 2)
                    self.filteredText += self.arr_edit_block_text[i][j]
                    uFilteredTextLen += uTempLen

        uFilteredTextLen = self.__ppt_extra_filter__(uFilteredTextLen)

        for i in range(0, len(self.filteredText), 2):
            try:
                self.content += self.filteredText[i:i+2].decode('utf-16')
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

    def __extract_text_in_slide__(self, block_number, sheet_number, slide_id):
        slide_total_length = 0
        length = 0

        tmpHeader = {}
        tmpHeader['option'] = 0
        tmpHeader['type'] = b''
        tmpHeader['length'] = 0


        # set the current offset
        self.current_offset = 0

        for i in range(block_number, len(self.arr_persist_ptr_incremental_block)):
            for j in range(0, len(self.arr_persist_ptr_incremental_block[i])):
                for k in range(0, self.arr_persist_ptr_incremental_block[i][j]['count']):
                    if self.arr_persist_ptr_incremental_block[i][j]['startnum'] + k == sheet_number:
                        self.current_offset = struct.unpack('<I', self.arr_persist_ptr_incremental_block[i][j]['object'][4 * k : 4 * (k + 1)])[0]
                if self.current_offset != 0:
                    break
            if self.current_offset != 0:
                break

        # traverse records in a slide record
        if self.__get_header_info__(tmpHeader) == False:
            return

        if tmpHeader['type'] != self.RT_Slide and tmpHeader['type'] != self.RT_Notes:
            return

        slide_total_length = tmpHeader['length']

        while True:
            if length >= slide_total_length:
                return

            if self.__get_header_info__(tmpHeader) == False:
                return

            if tmpHeader['type'] == self.RT_PPDrawing:
                self.__extract_text_in_slide_ppt_drawing__(tmpHeader)
                length += tmpHeader['length']
                continue
            elif tmpHeader['type'] == self.RT_ProgTags:
                self.__extract_text_in_slide_ppt_comment__(tmpHeader)
                length += tmpHeader['length']
                continue

            self.current_offset += tmpHeader['length']
            length += tmpHeader['length']

    def __extract_text_in_slide_ppt_comment__(self, header):
        j = 0
        preSize = 0
        totalLength_tmp = header['length']
        totalLength = 0
        tmpLength = 0
        readLength = 0

        tmpHeader = {}
        tmpHeader['option'] = 0
        tmpHeader['type'] = b''
        tmpHeader['length'] = 0

        while True :
            if totalLength_tmp <= totalLength:
                break

            if ((tmpHeader['option'] & 0x000F) == 0x000F):  # Container
                pass
            else:  # Atom
                self.current_offset += tmpHeader['length']
                totalLength += tmpHeader['length']

            if totalLength_tmp <= totalLength:
                break

            if self.__get_header_info__(tmpHeader) == False:
                break

            totalLength += 8

            if tmpHeader['type'] == self.RT_BinaryTagDataBlob:
                tmpLength = tmpHeader['length']
                readLength = 0

                while True:
                    if tmpLength <= readLength:
                        break

                    if self.__get_header_info__(tmpHeader) == False:
                        break

                    readLength += 8

                    if tmpHeader['type'] == self.RT_CString:
                        if tmpHeader['length'] == 2 and self.powerpoint_document[self.current_offset] == 0x6A and self.powerpoint_document[self.current_offset + 1] == 0x00:
                            self.current_offset += tmpHeader['length']
                            readLength += tmpHeader['length']

                        self.text_chars = b''
                        self.text_chars = self.powerpoint_document[self.current_offset : self.current_offset + tmpHeader['length']]

                        preSize = len(self.text)
                        self.text += self.text_chars
                        self.text += b'\x0A'

                        self.current_offset += tmpHeader['length']
                        readLength += tmpHeader['length']
                    else:
                        if((tmpHeader['option'] & 0x000F) == 0x000F):       # Container
                            pass
                        else:                                               # Atom
                            self.current_offset += tmpHeader['length']
                            readLength += tmpHeader['length']

                totalLength += readLength

                if totalLength_tmp != totalLength :
                    if self.__get_header_info__(tmpHeader) == False:
                        break
                    totalLength += 8

    def __extract_text_in_slide_ppt_drawing__(self, header):

        preSize = 0
        tmpPPDrawingLength = header['length']
        PPDrawingReadLength = 0

        tmpLength = 0
        readLength = 0
        textOK = False

        tmpHeader = {}
        tmpHeader['option'] = 0
        tmpHeader['type'] = b''
        tmpHeader['length'] = 0

        while True:
            if tmpPPDrawingLength <= PPDrawingReadLength:
                break
            if tmpHeader['option'] & 0x000F == 0x000F:
                pass            # Container
            else:               # Atom
                self.current_offset += tmpHeader['length']
                PPDrawingReadLength += tmpHeader['length']


            if tmpPPDrawingLength <= PPDrawingReadLength:
                break

            if self.__get_header_info__(tmpHeader) == False:
                break

            PPDrawingReadLength += 8

            if tmpHeader['type'] == self.RT_EscherClientTextbox:
                tmpLength = tmpHeader['length']
                readLength = 0
                textOK = False

                while True:
                    if tmpLength <= readLength:
                        break

                    if self.__get_header_info__(tmpHeader) == False:
                        break

                    readLength += 8

                    if tmpHeader['type'] == self.RT_SlidePersistAtom:
                        pass
                    elif tmpHeader['type'] == self.RT_TextHeader:
                        self.current_offset += tmpHeader['length']
                        readLength += tmpHeader['length']
                    elif tmpHeader['type'] == self.RT_TextBytesAtom:
                        self.text_bytes = b''
                        self.text_chars = b''
                        self.text_bytes = self.powerpoint_document[self.current_offset : self.current_offset + tmpHeader['length']]
                        for i in range(0, len(self.text_bytes)):
                            self.text_chars += bytes([self.text_bytes[i]])
                            self.text_chars += b'\x00'

                        preSize = len(self.text)
                        self.text += self.text_chars
                        self.text += b'\x0A\x00'

                        self.current_offset += tmpHeader['length']
                        readLength += tmpHeader['length']
                        textOK = True
                    elif tmpHeader['type'] == self.RT_TextCharsAtom:
                        self.text_chars = b''
                        self.text_chars = self.powerpoint_document[self.current_offset : self.current_offset + tmpHeader['length']]

                        self.text += self.text_chars
                        self.text += b'\x0A\x00'

                        self.current_offset += tmpHeader['length']
                        readLength += tmpHeader['length']
                        textOK = True
                    else:
                        if((tmpHeader['option'] & 0x000F) == 0x000F):       # Container
                            pass
                        else:                                               # Atom
                            self.current_offset += tmpHeader['length']
                            readLength += tmpHeader['length']

                PPDrawingReadLength += readLength

                if tmpPPDrawingLength != PPDrawingReadLength:
                    if self.__get_header_info__(tmpHeader) == False:
                        break
                    PPDrawingReadLength += 8

    def __get_header_info__(self, header):
        if self.current_offset + 8 > len(self.powerpoint_document):
            return False

        header['option'] = struct.unpack('<H', self.powerpoint_document[self.current_offset: self.current_offset + 2])[0]
        header['type'] = self.powerpoint_document[self.current_offset + 2: self.current_offset + 4]
        header['length'] = struct.unpack('<I', self.powerpoint_document[self.current_offset + 4: self.current_offset + 8])[0]
        self.current_offset += 8
        return True

    def __ppt_extra_filter__(self, tempLen):
        i = 0
        j = 0
        k = 0

        uBlank = b'\x20\x00'    # ASCII Blank
        uBlank2 = b'\xA0\x00'   # Unicode Blank
        uBlank3 = b'\x0B\x00'
        uNewline = b'\x0A\x00'  # Line Feed
        uTab = b'\x09\x00'      # Horizontal Tab
        uCR = b'\x0D\x00'       # Carriage Return
        uFilteredTextLen = tempLen
        while i < len(self.filteredText):
            if i == 0:
                k = 0
                while self.filteredText[0 : 2] == uBlank or self.filteredText[0 : 2] == uBlank2 or self.filteredText[0 : 2] == uNewline :
                    self.filteredText = self.filteredText[: k] + self.filteredText[k + 2 :]
                    uFilteredTextLen -= 1

                    if len(self.filteredText) <= 0:
                        break

            if len(self.filteredText) <= 0:
                break

            if self.filteredText[i : i + 2] == uNewline:
                j = i
                while True :
                    j += 2
                    if j >= len(self.filteredText):
                        break

                    if self.filteredText[j : j + 2] == uNewline or self.filteredText[j : j + 2] == uBlank or self.filteredText[j : j + 2] == uBlank2:
                        self.filteredText = self.filteredText[: j] + self.filteredText[j + 2:]
                        uFilteredTextLen -= 1
                        j -= 2
                    elif self.filteredText[j : j + 2] == uTab or self.filteredText[j : j + 2] == uBlank3 or self.filteredText[j : j + 2] == uCR :
                        self.filteredText = self.filteredText[: j] + self.filteredText[j + 2:]
                        uFilteredTextLen -= 1
                        j -= 2
                    else :
                        break


            elif self.filteredText[i : i + 2] == uBlank or self.filteredText[i : i + 2] == uBlank2:
                j = i
                while True :
                    j += 2
                    if j >= len(self.filteredText):
                        break

                    if self.filteredText[j: j + 2] == uBlank or self.filteredText[j : j + 2] == uBlank2:
                        self.filteredText = self.filteredText[: j] + self.filteredText[j + 2:]
                        uFilteredTextLen -= 1
                        j -= 2
                    elif self.filteredText[j: j + 2] == uTab:
                        self.filteredText = self.filteredText[: j] + self.filteredText[j + 2:]
                        uFilteredTextLen -= 1
                        j -= 2
                    elif self.filteredText[j: j + 2] == uBlank3:
                        self.filteredText = self.filteredText[: j] + self.filteredText[j + 2:]
                        uFilteredTextLen -= 1
                        j -= 2
                    else:
                        break

            elif self.filteredText[i : i + 2] == uBlank3:
                self.filteredText[i] = 0x20
                i -= 2
            elif self.filteredText[i : i + 2] == uCR:
                self.filteredText[i] = 0x0A
                i -= 2
            elif self.filteredText[i : i + 2] == uTab:
                self.filteredText[i] = 0x20
                i -= 2

            i += 2

        return uFilteredTextLen

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
                        self._doc_info['SumInfoLastSavedTime'] = time.filetime_to_dt(ft)

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