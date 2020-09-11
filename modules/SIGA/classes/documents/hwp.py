# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import io
import os
import struct
import zlib

from modules.SIGA import definitions
from modules.SIGA.utility import filetime_to_dt
from modules.SIGA.classes.interface import Common
from modules.SIGA.classes.documents.compound import Compound
from modules.SIGA.formats.documents.fm_hwp import fm_Tag_Record_Item

class HWP(Common):
    def __init__(self, input=None):
        super(HWP, self).__init__(input)

        self.input = input
        self.data = None
        self._ext = None
        self._metadata = None
        self._text = None
        self._structure = dict()

        # result
        self._hwp_doc_info = dict()
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
            if entry.name_trancated == 'HwpSummaryInformation':
                self._ext = '.hwp'

        if self._ext == None:
            return False

        return self._ext

    def identifyFormatFromMemory(self, file_object):
        file_like_object = io.BytesIO(file_object)
        #self._cp._filesize = len(file_object)
        self._cp._fp = file_like_object
        try:
            self._cp.get_header()
            self._cp.load_compound()
            for entry in self._cp._dir_entries:
                if entry.name[:8] == '\x00\x00\x00\x00\x00\x00\x00\x00':
                    break
                if entry.name_trancated == 'HwpSummaryInformation':
                    self._ext = '.hwp'
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

        self._hwp_doc_info['Filename'] = os.path.basename(self.input)
        self._hwp_doc_info['Filepath'] = os.path.abspath(self.input)
        self._hwp_doc_info['Filesize'] = str(self._cp._filesize/1024) + 'KB'
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

            # FileHeader
            if entry.name_trancated == 'FileHeader':
                if self._is_valid_child(entry_idx, "Root Entry", 0):
                    self._validate_stream_fileheader(d, len(d), entry.name_trancated)

                else:
                    desc = '%s Storage 하위에 포함됨' % self._get_parent_storage(entry_idx)
                    self._set_vuln_info(definitions.HC_STR_VTYPE_UNKWNON_STREAM, 0, 0, desc, entry.name_trancated)
                    self._validate_unknown_data(definitions.HC_STR_VTYPE_ABNORMAL_BINDATA, d, len(d), 0, 0, entry.name_trancated)
                continue

            # DocInfo
            if entry.name_trancated == 'DocInfo':
                if self._is_valid_child(entry_idx, "Root Entry", 0):
                    if not self._is_encrypted:
                        self._validate_stream_docinfo(d,len(d) , entry.name_trancated)
                        self._hwp_doc_info['is_encrypted'] = 'No'
                    else:
                        self._hwp_doc_info['is_encrypted'] = 'Yes'
                else:
                    desc = '%s Storage 하위에 포함됨' % self._get_parent_storage(entry_idx)
                    self._set_vuln_info(definitions.HC_STR_VTYPE_UNKWNON_STREAM, 0, 0, desc, entry.name_trancated)
                    self._validate_unknown_data(definitions.HC_STR_VTYPE_ABNORMAL_BINDATA, d, len(d), 0, 0, entry.name_trancated)

            # HwpSummaryInformation
            if entry.name_trancated == 'HwpSummaryInformation':
                if self._is_valid_child(entry_idx, "Root Entry", 0):
                    self._validate_stream_summaryinfo(d, len(d), entry.name_trancated)
                else:
                    desc = '%s Storage 하위에 포함됨' % self._get_parent_storage(entry_idx)
                    self._set_vuln_info(definitions.HC_STR_VTYPE_UNKWNON_STREAM, 0, 0, desc, entry.name_trancated)
                    self._validate_unknown_data(definitions.HC_STR_VTYPE_ABNORMAL_BINDATA, d, len(d), 0, 0, entry.name_trancated)
                continue

            # PrvText
            if entry.name_trancated == 'PrvText':
                if self._is_valid_child(entry_idx, "Root Entry", 0):
                    self._validate_stream_prvtext(d, len(d), entry.name_trancated)
                else:
                    desc = '%s Storage 하위에 포함됨' % self._get_parent_storage(entry_idx)
                    self._set_vuln_info(definitions.HC_STR_VTYPE_UNKWNON_STREAM, 0, 0, desc, entry.name_trancated)
                    self._validate_unknown_data(definitions.HC_STR_VTYPE_ABNORMAL_BINDATA, d, len(d), 0, 0, entry.name_trancated)
                continue

            # PrvImage
            if entry.name_trancated == 'PrvImage':
                if self._is_valid_child(entry_idx, "Root Entry", 0):
                    self._validate_stream_prvimage(d, len(d), entry.name_trancated)
                else:
                    desc = '%s Storage 하위에 포함됨' % self._get_parent_storage(entry_idx)
                    self._set_vuln_info(definitions.HC_STR_VTYPE_UNKWNON_STREAM, 0, 0, desc, entry.name_trancated)
                    self._validate_unknown_data(definitions.HC_STR_VTYPE_ABNORMAL_BINDATA, d, len(d), 0, 0, entry.name_trancated)
                continue

            # BodyText & ViewText
            if entry.name_trancated[0:7] == 'Section':
                if self._is_encrypted & 0x04:
                    if self._is_valid_child(entry_idx, 'ViewText', 0) or self._is_valid_child(entry_idx, 'BodyText', 0):
                        self._validate_stream_section(d, len(d), entry.name_trancated)
                        self._validate_unknown_data(definitions.HC_STR_VTYPE_ABNORMAL_BINDATA, d, len(d), 0, 0, entry.name_trancated)
                    else:
                        desc = '%s Storage 하위에 포함됨' % self._get_parent_storage(entry_idx)
                        self._set_vuln_info(definitions.HC_STR_VTYPE_UNKWNON_STREAM, 0, 0, desc, entry.name_trancated)
                        self._validate_unknown_data(definitions.HC_STR_VTYPE_ABNORMAL_BINDATA, d, len(d), 0, 0, entry.name_trancated)
                else:
                    if self._is_valid_child(entry_idx, 'BodyText', 0):
                        if not self._is_encrypted:
                            self._validate_stream_section(d, len(d), entry.name_trancated)
                        else:
                            self._validate_unknown_data(definitions.HC_STR_VTYPE_ABNORMAL_BINDATA, d, len(d), 0, 0, entry.name_trancated)
                    elif self._is_valid_child(entry_idx, 'ViewText', 0):
                        self._validate_unknown_data(definitions.HC_STR_VTYPE_ABNORMAL_BINDATA, d, len(d), 0, 0, entry.name_trancated)
                    else:
                        desc = '%s Storage 하위에 포함됨' % self._get_parent_storage(entry_idx)
                        self._set_vuln_info(definitions.HC_STR_VTYPE_UNKWNON_STREAM, 0, 0, desc, entry.name_trancated)
                        self._validate_unknown_data(definitions.HC_STR_VTYPE_ABNORMAL_BINDATA, d, len(d), 0, 0, entry.name_trancated)

                continue

            # BinData
            if entry.name_trancated[0:3] == 'BIN':
                if self._is_valid_child(entry_idx, "BinData", 0):
                    if not self._is_encrypted:
                        self._validate_stream_bindata(d, len(d), entry.name_trancated)
                    else:
                        self._validate_unknown_data(definitions.HC_STR_VTYPE_ABNORMAL_BINDATA, d, len(d), 0, 0, entry.name_trancated)
                else:
                    desc = '%s Storage 하위에 포함됨' % self._get_parent_storage(entry_idx)
                    self._set_vuln_info(definitions.HC_STR_VTYPE_UNKWNON_STREAM, 0, 0, desc, entry.name_trancated)
                    self._validate_unknown_data(definitions.HC_STR_VTYPE_ABNORMAL_BINDATA, d, len(d), 0, 0, entry.name_trancated)
                continue

            # DefaultJScript
            if entry.name_trancated == 'DefaultJScript':
                if self._is_valid_child(entry_idx, "Scripts", 0):
                    if not self._is_encrypted:
                        self._validate_stream_defaultjscript(d, len(d), entry.name_trancated)
                    else:
                        self._validate_unknown_data(definitions.HC_STR_VTYPE_ABNORMAL_BINDATA, d, len(d), 0, 0, entry.name_trancated)
                else:
                    desc = '%s Storage 하위에 포함됨' % self._get_parent_storage(entry_idx)
                    self._set_vuln_info(definitions.HC_STR_VTYPE_UNKWNON_STREAM, 0, 0, desc, entry.name_trancated)
                    self._validate_unknown_data(definitions.HC_STR_VTYPE_ABNORMAL_BINDATA, d, len(d), 0, 0, entry.name_trancated)
                continue

            # JScriptVersion
            if entry.name_trancated == 'JScriptVersion':
                if self._is_valid_child(entry_idx, "Scripts", 0):
                    if not self._is_encrypted:
                        self._validate_stream_jscryptversion(d, len(d), entry.name_trancated)
                    else:
                        self._validate_unknown_data(definitions.HC_STR_VTYPE_ABNORMAL_BINDATA, d, len(d), 0, 0, entry.name_trancated)
                else:
                    desc = '%s Storage 하위에 포함됨' % self._get_parent_storage(entry_idx)
                    self._set_vuln_info(definitions.HC_STR_VTYPE_UNKWNON_STREAM, 0, 0, desc, entry.name_trancated)
                    self._validate_unknown_data(definitions.HC_STR_VTYPE_ABNORMAL_BINDATA, d, len(d), 0, 0, entry.name_trancated)
                continue

            # _LinkDoc
            if entry.name_trancated == '_LinkDoc':
                if self._is_valid_child(entry_idx, "DocOptions", 0):
                    self._validate_stream_linkdoc(d, len(d), entry.name_trancated)
                else:
                    desc = '%s Storage 하위에 포함됨' % self._get_parent_storage(entry_idx)
                    self._set_vuln_info(definitions.HC_STR_VTYPE_UNKWNON_STREAM, 0, 0, desc, entry.name_trancated)
                    self._validate_unknown_data(definitions.HC_STR_VTYPE_ABNORMAL_BINDATA, d, len(d), 0, 0, entry.name_trancated)
                continue

            # DrmLicense, DrmRootSect, CertDrmHeader, CertDrmInfo, DigitalSignature, DSVersion, PublicKeyInfo
            if entry.name_trancated == 'DrmLicense' or entry.name_trancated == 'DrmRootSect' or entry.name_trancated == 'CertDrmHeader' or \
                    entry.name_trancated == 'CertDrmInfo' or entry.name_trancated == 'DigitalSignature' or entry.name_trancated == 'DSVersion' or \
                    entry.name_trancated == 'PublicKeyInfo':
                if self._is_valid_child(entry_idx, "DocOptions", 0):
                    pass
                else:
                    desc = '%s Storage 하위에 포함됨' % self._get_parent_storage(entry_idx)
                    self._set_vuln_info(definitions.HC_STR_VTYPE_UNKWNON_STREAM, 0, 0, desc, entry.name_trancated)
                    self._validate_unknown_data(definitions.HC_STR_VTYPE_ABNORMAL_BINDATA, d, len(d), 0, 0, entry.name_trancated)
                continue

            # _SchemaName, Schema, Instance
            if entry.name_trancated == '_SchemaName' or entry.name_trancated == 'Schema' or entry.name_trancated == 'Instance':
                if self._is_valid_child(entry_idx, "XMLTemplate", 0):
                    pass
                else:
                    desc = '%s Storage 하위에 포함됨' % self._get_parent_storage(entry_idx)
                    self._set_vuln_info(definitions.HC_STR_VTYPE_UNKWNON_STREAM, 0, 0, desc, entry.name_trancated)
                    self._validate_unknown_data(definitions.HC_STR_VTYPE_ABNORMAL_BINDATA, d, len(d), 0, 0, entry.name_trancated)
                continue

            # HistoryLastDoc, VersionLog%d
            if entry.name_trancated == 'HistoryLastDoc' or entry.name_trancated[0:10] == 'VersionLog':
                if self._is_valid_child(entry_idx, "DocHistory", 0):
                    pass
                else:
                    desc = '%s Storage 하위에 포함됨' % self._get_parent_storage(entry_idx)
                    self._set_vuln_info(definitions.HC_STR_VTYPE_UNKWNON_STREAM, 0, 0, desc, entry.name_trancated)
                    self._validate_unknown_data(definitions.HC_STR_VTYPE_ABNORMAL_BINDATA, d, len(d), 0, 0, entry.name_trancated)
                continue

        return definitions.VALID_SUCCESS

    def get_metadata(self):
        return self._metadata

    def get_text(self):
        return self._text

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

        self._structure['HWPDocInfo'] = self._hwp_doc_info
        self._structure['Compound Format Internals'] = self._cp.get_structure()
        self._structure['HWP_Record_Info'] = temp_dict

        return self._structure

    def parse(self):
        ''' 작업 해야함 '''
        return self.data

    # Stream 검증
    def _validate_stream_fileheader(self, data, length, name):

        if not data[:17].decode() == 'HWP Document File':
            self._set_vuln_info(definitions.HC_STR_VTYPE_STREAM_SYNTAX_ERROR, 0, 17, '올바르지 않은 한글 시그니처', name)
            return False

        self._hwp_doc_info['HWPDocVer'] = str(data[35])+'.'+str(data[34])+'.'+str(data[33])+'.'+str(data[32])

        hwp_prop = struct.unpack('<I', data[36:40])[0]


        if hwp_prop & 0x01:
            self._is_compressed = True

        if hwp_prop & 0x02:
            self._is_encrypted = 0x02
        if hwp_prop & 0x04:
            self._is_encrypted = 0x04

        tmpstr = hex(hwp_prop)
        if hwp_prop == 0: tmpstr += '(default)'
        else:
            tmpstr += "("
            if hwp_prop & 0x01: tmpstr +=", 압축"
            if hwp_prop & 0x02: tmpstr += ", 읽기 암호"
            if hwp_prop & 0x04: tmpstr += ", 배포용 문서"
            if hwp_prop & 0x08: tmpstr += ", 스크립트 저장"
            if hwp_prop & 0x10: tmpstr += ", DRM 보안 문서"
            if hwp_prop & 0x20: tmpstr += ", XMLTemplate 스토리지 존재"
            if hwp_prop & 0x40: tmpstr += ", 문서 이력 관리 존재"
            if hwp_prop & 0x80: tmpstr += ", 전자 서명 정보 존재"
            if hwp_prop & 0x100: tmpstr += ", 공인 인증서 암호화"
            if hwp_prop & 0x200: tmpstr += ", 전자 서명 예비 저장"
            if hwp_prop & 0x400: tmpstr += ", 공인 인증서 DRM 보안 문서"
            if hwp_prop & 0x800: tmpstr += ", CCL 문서"
            tmpstr += ")"

        self._hwp_doc_info['HWPDocProp'] = tmpstr.replace('(, ', '(')

        if length != 256:
            self._set_vuln_info(definitions.HC_STR_VTYPE_STREAM_SYNTAX_ERROR, 0, length, '고정 크기 256 bytes가 아닌 %d bytes' % length, name)

        tmpbyte = 0x00
        for idx in range(17, 32):
            tmpbyte | data[idx]

        if(tmpbyte != 0x00):
            self._set_vuln_info(definitions.HC_STR_VTYPE_STREAM_SYNTAX_ERROR,  17, 15, 'NULL 영역에 알 수 없는 데이터 존재', name)

        tmpbyte = 0x00
        for idx in range(48, 256):
            tmpbyte | data[idx]

        if (tmpbyte != 0x00):
            self._set_vuln_info(definitions.HC_STR_VTYPE_STREAM_SYNTAX_ERROR, 48, 208, 'NULL 영역에 알 수 없는 데이터 존재', name)

        return True

    def _validate_stream_docinfo(self, data, length, name):

        if self._is_encrypted:
            return False

        if self._is_compressed:

            avail_in, out_data = self._decompress_stream(data)
            if avail_in < 0:
                desc = '평문 데이터 ; 문서 속성의 \'압축\' 설정과 일치하지 않음'
                self._set_vuln_info(definitions.HC_STR_VTYPE_INCONSISTENCY, 0, length, desc, name)

            else:
                if avail_in > 12:
                    desc = '(압축스트림크기 - 유효데이터크기 = ' + hex(avail_in) + ') > 0'
                    self._set_vuln_info(definitions.HC_STR_VTYPE_UNUSED_AREA, 0, length, desc, name + '(압축스트림)')

                    #수정해야함
                    self._validate_unknown_data(definitions.HC_STR_VTYPE_UNUSED_AREA, data[length - avail_in], avail_in, length - avail_in, avail_in, name)
                data = out_data
                length = len(out_data)

        tempLen = 0
        tempData = data

        ar = []
        while tempLen < length:
            tag_header = struct.unpack('<I', tempData[tempLen:tempLen+4])[0]

            ri = fm_Tag_Record_Item()
            ri.offset = tempLen
            ri.length = (tag_header & 0xfff00000) >> 20
            ri.level  = (tag_header & 0x000ffc00) >> 10
            ri.tag_id = (tag_header & 0x000003ff)

            if ri.length == 0xfff:
                ri.length = struct.unpack('<I', tempData[tempLen+4:tempLen+8])[0]
                ri.header_size = 8
            else:
                ri.header_size = 4

            known = self._set_hwp_record_info(ri)
            if known == False:
                desc = '알 수 없는 레코드 ID = ' + hex(ri.tag_id)
                self._set_vuln_info(definitions.HC_STR_VTYPE_ABNORMAL_RECORD, ri.offset, ri.length, desc, name)

            ar.append(ri)

            #????
            #if ri.tag_id == 18:
            #    print(tempData[ri.offset:ri.offset+ri.length])

            found = 0

            u_len = tempLen + ri.length + ri.header_size

            if u_len > length:
                desc = hex(ri.length) + ' 크기의 비정상 ' + ri.name + ' (' + ri.desc + ') 레코드'
                self._set_vuln_info(definitions.HC_STR_VTYPE_ABNORMAL_RECORD, ri.offset, ri.length, desc, name)

            if ri.length > 0xa00:
                abnormal_d = ''
                if self._check_dummy_data(tempData + ri.header_size, ri.length, abnormal_d):
                    desc = hex(ri.length) + ' 크기의 비정상 ' + ri.name + ' (' + ri.desc + ') 레코드'
                    desc += '비정상 데이터 '+ abnormal_d +'-> 레코드의 70% 이상을 차지함'
                    self._set_vuln_info(definitions.HC_STR_VTYPE_ABNORMAL_RECORD, ri.offset, ri.length, desc, name)
                    found += 1

                desc = hex(ri.length) + ' 크기의 비정상' + ri.name + ' (' + ri.desc + ') 레코드;'
                found += self._validate_unknown_data(definitions.HC_STR_VTYPE_ABNORMAL_RECORD, tempData + ri.header_size, ri.length, ri.offset + ri.header_size, ri.length, name, desc)

            if known == False:
                break

            offset = ri.length + ri.header_size
            tempLen += offset

        self._arr_tag[name] = ar
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
                    self._hwp_doc_info['SumInfoWindowsVer'] = 'Windows 2000'
                elif (OSVersion >> 8) & 0xFF == 1:
                    self._hwp_doc_info['SumInfoWindowsVer'] = 'Windows XP'
                elif (OSVersion >> 8) & 0xFF == 2:
                    self._hwp_doc_info['SumInfoWindowsVer'] = 'Windows XP 64-Bit Edition'
            elif OSVersion & 0xFF == 0x06:
                if (OSVersion >> 8) & 0xFF == 0:
                    self._hwp_doc_info['SumInfoWindowsVer'] = 'Windows Vista'
                elif (OSVersion >> 8) & 0xFF == 1:
                    self._hwp_doc_info['SumInfoWindowsVer'] = 'Windows 7'
                elif (OSVersion >> 8) & 0xFF == 2:
                    self._hwp_doc_info['SumInfoWindowsVer'] = 'Windows 8'
                elif (OSVersion >> 8) & 0xFF == 3:
                    self._hwp_doc_info['SumInfoWindowsVer'] = 'Windows 8.1'

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
                            self._hwp_doc_info['SumInfoTitle'] = wInfo
                        elif struct.unpack('<I', data[52 + i * 4:56 + i * 4])[0] == 0x04:
                            self._hwp_doc_info['SumInfoAuthor'] = wInfo
                        elif struct.unpack('<I', data[52 + i * 4:56 + i * 4])[0] == 0x08:
                            self._hwp_doc_info['SumInfoLastSavedBy'] = wInfo
                        elif struct.unpack('<I', data[52 + i * 4:56 + i * 4])[0] == 0x09:
                            self._hwp_doc_info['SumInfoVersion'] = wInfo
                        elif struct.unpack('<I', data[52 + i * 4:56 + i * 4])[0] == 0x14:
                            self._hwp_doc_info['SumInfoDate'] = wInfo

                elif struct.unpack('<I', data[52 + i * 4:56 + i * 4])[0] == 0x0C:
                    propOffset = struct.unpack('<I', data[52 + (i + 1) * 4:56 + (i + 1) * 4])[0]
                    if struct.unpack('<I', data[48 + propOffset:52 + propOffset])[0] == 0x40:
                        ft = struct.unpack('<q', data[52 + propOffset:60 + propOffset])[0]
                        self._hwp_doc_info['SumInfoCreatedTime'] = filetime_to_dt(ft)

                elif struct.unpack('<I', data[52 + i * 4:56 + i * 4])[0] == 0x0D:
                    propOffset = struct.unpack('<I', data[52 + (i + 1) * 4:56 + (i + 1) * 4])[0]
                    if struct.unpack('<I', data[48 + propOffset:52 + propOffset])[0] == 0x40:
                        ft = struct.unpack('<q', data[52 + propOffset:60 + propOffset])[0]
                        self._hwp_doc_info['SumInfoLastSavedTime'] = filetime_to_dt(ft)

            if length != totalLength:
                self._validate_unknown_data(definitions.HC_STR_VTYPE_UNUSED_AREA, data[totalLength:], length-totalLength, totalLength, length-totalLength, name)

        return True

    def _validate_stream_prvtext(self, data, length, name):
        if length > 2046:
            self._set_vuln_info(definitions.HC_STR_VTYPE_STREAM_SYNTAX_ERROR, 0, length, '최대 크기 2,045 bytes 초과 ; %d bytes' % length, name)
        return True

    def _validate_stream_prvimage(self, data, length, name):
        if length < 16:
            self._set_vuln_info(definitions.HC_STR_VTYPE_STREAM_SYNTAX_ERROR, 0, length, '미리보기 이미지 포맷 검증 실패 (비정상적으로 짧은 데이터)', name)

        if data[0:4] != b'\x89PNG' and data[0:4] != b'GIF87a' and data[0:4] != b'GIF89a' and data[0:2] != b'bm':
            self._set_vuln_info(definitions.HC_STR_VTYPE_ABNORMAL_BINDATA, 0, length, '올바르지 않은 미리보기 이미지 헤더', name)

        if (data[0:4] == b'GIF87a' or data[0:4] == b'GIF89a') and data[length-1] != b';':
            self._set_vuln_info(definitions.HC_STR_VTYPE_ABNORMAL_BINDATA, length-1, 1, '올바르지 않은 미리보기 이미지 푸터', name)

        if data[0:2] == b'bm':
            imgsize = struct.unpack('<I', data[2:6])[0]

            if imgsize != length:
                self._set_vuln_info(definitions.HC_STR_VTYPE_ABNORMAL_BINDATA, 2, 4, '올바르지 않은 미리보기 이미지 크기', name)

        return True

    def _validate_stream_section(self, data, length, name):

        return True

    def _validate_stream_bindata(self, data, length, name):

        return True

    def _validate_stream_defaultjscript(self, data, length, name):

        return True

    def _validate_stream_jscryptversion(self, data, length, name):
        if self._is_encrypted:
            return False

        if self._is_compressed:

            avail_in, out_data = self._decompress_stream(data)
            if avail_in < 0:
                desc = '평문 데이터 ; 문서 속성의 \'압축\' 설정과 일치하지 않음'
                self._set_vuln_info(definitions.HC_STR_VTYPE_INCONSISTENCY, 0, length, desc, name)

            else:
                if avail_in > 12:
                    desc = '(압축스트림크기 - 유효데이터크기 = ' + hex(avail_in) + ') > 0'
                    self._set_vuln_info(definitions.HC_STR_VTYPE_UNUSED_AREA, 0, length, desc, name + '(압축스트림)')

                    # 수정해야함
                    self._validate_unknown_data(definitions.HC_STR_VTYPE_UNUSED_AREA, data[length - avail_in], avail_in,
                                                length - avail_in, avail_in, name)
                data = out_data
                length = len(out_data)

        if length != 8:
            self._set_vuln_info(definitions.HC_STR_VTYPE_STREAM_SYNTAX_ERROR, 0, length, '정상 크기 8 bytes가 아닌 %d bytes'% length, name)
        else:
            js_version = struct.unpack('<q', data[0:8])[0]

            if js_version != 0x01:
                self._set_vuln_info(definitions.HC_STR_VTYPE_STREAM_SYNTAX_ERROR, 0, length, '비정상 데이터 %s'% hex(js_version), name)


        return True

    def _validate_stream_linkdoc(self, data, length, name):

        if length != 524:
            self._set_vuln_info(definitions.HC_STR_VTYPE_STREAM_SYNTAX_ERROR, 0, length, '고정 크기 524 bytes가 아닌 %d bytes' % length, name)
            return False
        if data[520] != 0x00 and data[520] != 0x01 and data[520] != 0x02 and data[520] != 0x03:
            self._set_vuln_info(definitions.HC_STR_VTYPE_STREAM_SYNTAX_ERROR, 129*4, 4, '비정상적인 문서 연결 속성 정보 %s'% hex(struct.unpack('<I', data[504:508])[0]), name)

        return True

    # _is_valid_child, _get_parent_storage는 compound class에서 구현되는게 맞는것같다.....
    def _is_valid_child(self, target_idx, storage_name, storage_idx=-1):

        ret = False
        name = ''
        elements = []

        if storage_idx != -1:
            for entry in self._cp._dir_entries:
                if entry.name_trancated == storage_name:
                    name = entry.name_trancated
                    break

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

    def _check_dummy_data(self, buf, buf_len, abnormal_d):
        raise NotImplementedError

    def _validate_unknown_data(self, type, buf, buf_len, offset, length, name, desc=""):
        raise NotImplementedError

    def _decompress_stream(self, data):

        avail_in = 8  # 임시
        decompress = zlib.decompressobj(-zlib.MAX_WBITS)
        try:
            stream = decompress.decompress(data)
            stream += decompress.flush()
        except:
            # return avail_in
            return (-1, None)

        return (avail_in, stream)

    def _set_hwp_record_info(self, ri):

        HWPTAG_BEGIN = 0x010
        tag_name = ''
        tag_desc = ''

        if ri.tag_id == HWPTAG_BEGIN:
            tag_name = "HWPTAG_DOCUMENT_PROPERTIES"
            tag_desc = "문서 속성"
        elif ri.tag_id == HWPTAG_BEGIN + 1:
            tag_name = "HWPTAG_ID_MAPPINGS"
            tag_desc = "아이디 매핑 헤더"
        elif ri.tag_id == HWPTAG_BEGIN + 2:
            tag_name = "HWPTAG_BIN_DATA"
            tag_desc = "BinData"
        elif ri.tag_id == HWPTAG_BEGIN + 3:
            tag_name = "HWPTAG_FACE_NAME"
            tag_desc = "글꼴"
        elif ri.tag_id == HWPTAG_BEGIN + 4:
            tag_name = "HWPTAG_BORDER_FILL"
            tag_desc = "테두리/배경"
        elif ri.tag_id == HWPTAG_BEGIN + 5:
            tag_name = "HWPTAG_CHAR_SHAPE"
            tag_desc = "글자 모양"
        elif ri.tag_id == HWPTAG_BEGIN + 6:
            tag_name = "HWPTAG_TAB_DEF"
            tag_desc = "탭 정의"
        elif ri.tag_id == HWPTAG_BEGIN + 7:
            tag_name = "HWPTAG_NUMBERING"
            tag_desc = "번호 정의"
        elif ri.tag_id == HWPTAG_BEGIN + 8:
            tag_name = "HWPTAG_BULLET"
            tag_desc = "불릿 정의"
        elif ri.tag_id == HWPTAG_BEGIN + 9:
            tag_name = "HWPTAG_PARA_SHAPE"
            tag_desc = "문단 모양"
        elif ri.tag_id == HWPTAG_BEGIN + 10:
            tag_name = "HWPTAG_STYLE"
            tag_desc = "스타일"
        elif ri.tag_id == HWPTAG_BEGIN + 11:
            tag_name = "HWPTAG_DOC_DATA"
            tag_desc = "문서의 임의의 데이터"
        elif ri.tag_id == HWPTAG_BEGIN + 12:
            tag_name = "HWPTAG_DISTRIBUTE_DOC_DATA"
            tag_desc = "배포용 문서 데이터"
        elif ri.tag_id == HWPTAG_BEGIN + 13:
            tag_name = "RESERVED"
            tag_desc = "예약"
        elif ri.tag_id == HWPTAG_BEGIN + 14:
            tag_name = "HWPTAG_COMPATIBLE_DOCUMENT"
            tag_desc = "호환 문서"
        elif ri.tag_id == HWPTAG_BEGIN + 15:
            tag_name = "HWPTAG_LAYOUT_COMPATIBILITY"
            tag_desc = "레이아웃 호환성"
        elif ri.tag_id == HWPTAG_BEGIN + 16:
            tag_name = "HWPTAG_TRACKCHANGE"
            tag_desc = "변경 추적 정보"
        elif ri.tag_id == HWPTAG_BEGIN + 76:
            tag_name = "HWPTAG_MEMO_SHAPE"
            tag_desc = "메모 모양"
        elif ri.tag_id == HWPTAG_BEGIN + 78:
            tag_name = "HWPTAG_FORBIDDEN_CHAR"
            tag_desc = "금칙처리 문자"
        elif ri.tag_id == HWPTAG_BEGIN + 80:
            tag_name = "HWPTAG_TRACK_CHANGE"
            tag_desc = "변경 추적 내용 및 모양"
        elif ri.tag_id == HWPTAG_BEGIN + 81:
            tag_name = "HWPTAG_TRACK_CHANGE_AUTHOR"
            tag_desc = "변경 추적 작성자"
        # 문서 정보 끝
        # 본문 사용 데이터 레코드 시작
        elif ri.tag_id == HWPTAG_BEGIN + 50:
            tag_name = "HWPTAG_PARA_HEADER"
            tag_desc = "문단 헤더"
        elif ri.tag_id == HWPTAG_BEGIN + 51:
            tag_name = "HWPTAG_PARA_TEXT"
            tag_desc = "문단 텍스트"
        elif ri.tag_id == HWPTAG_BEGIN + 52:
            tag_name = "HWPTAG_PARA_CHAR_SHAPE"
            tag_desc = "문단의 글자 모양"
        elif ri.tag_id == HWPTAG_BEGIN + 53:
            tag_name = "HWPTAG_PARA_LINE_SEG"
            tag_desc = "문단의 레이아웃"
        elif ri.tag_id == HWPTAG_BEGIN + 54:
            tag_name = "HWPTAG_PARA_RANGE_TAG"
            tag_desc = "문단의 영역 태그"
        elif ri.tag_id == HWPTAG_BEGIN + 55:
            tag_name = "HWPTAG_CTRL_HEADER"
            tag_desc = "컨트롤 헤더"
        elif ri.tag_id == HWPTAG_BEGIN + 56:
            tag_name = "HWPTAG_LIST_HEADER"
            tag_desc = "문단 리스트 헤더"
        elif ri.tag_id == HWPTAG_BEGIN + 57:
            tag_name = "HWPTAG_PAGE_DEF"
            tag_desc = "용지 설정"
        elif ri.tag_id == HWPTAG_BEGIN + 58:
            tag_name = "HWPTAG_FOOTNOTE_SHAPE"
            tag_desc = "각주/미주 모양"
        elif ri.tag_id == HWPTAG_BEGIN + 59:
            tag_name = "HWPTAG_PAGE_BORDER_FILL"
            tag_desc = "쪽 테두리/배경"
        elif ri.tag_id == HWPTAG_BEGIN + 60:
            tag_name = "HWPTAG_SHAPE_COMPONENT"
            tag_desc = "개체"
        elif ri.tag_id == HWPTAG_BEGIN + 61:
            tag_name = "HWPTAG_TABLE"
            tag_desc = "표 개체"
        elif ri.tag_id == HWPTAG_BEGIN + 62:
            tag_name = "HWPTAG_SHAPE_COMPONENT_LINE"
            tag_desc = "직선 개체"
        elif ri.tag_id == HWPTAG_BEGIN + 63:
            tag_name = "HWPTAG_SHAPE_COMPONENT_RECTANGLE"
            tag_desc = "사각형 개체"
        elif ri.tag_id == HWPTAG_BEGIN + 64:
            tag_name = "HWPTAG_SHAPE_COMPONENT_ELLIPSE"
            tag_desc = "타원 개체"
        elif ri.tag_id == HWPTAG_BEGIN + 65:
            tag_name = "HWPTAG_SHAPE_COMPONENT_ARC"
            tag_desc = "호 개체"
        elif ri.tag_id == HWPTAG_BEGIN + 66:
            tag_name = "HWPTAG_SHAPE_COMPONENT_POLYGON"
            tag_desc = "다각형 개체"
        elif ri.tag_id == HWPTAG_BEGIN + 67:
            tag_name = "HWPTAG_SHAPE_COMPONENT_CURVE"
            tag_desc = "곡선 개체"
        elif ri.tag_id == HWPTAG_BEGIN + 68:
            tag_name = "HWPTAG_SHAPE_COMPONENT_OLE"
            tag_desc = "OLE 개체"
        elif ri.tag_id == HWPTAG_BEGIN + 69:
            tag_name = "HWPTAG_SHAPE_COMPONENT_PICTURE"
            tag_desc = "그림 개체"
        elif ri.tag_id == HWPTAG_BEGIN + 70:
            tag_name = "HWPTAG_SHAPE_COMPONENT_CONTAINER"
            tag_desc = "컨테이너 개체"
        elif ri.tag_id == HWPTAG_BEGIN + 71:
            tag_name = "HWPTAG_CTRL_DATA"
            tag_desc = "컨트롤 임의의 데이터"
        elif ri.tag_id == HWPTAG_BEGIN + 72:
            tag_name = "HWPTAG_EQEDIT"
            tag_desc = "수식 개체"
        elif ri.tag_id == HWPTAG_BEGIN + 73:
            tag_name = "RESERVED"
            tag_desc = "예약"
        elif ri.tag_id == HWPTAG_BEGIN + 74:
            tag_name = "HWPTAG_SHAPE_COMPONENT_TEXTART"
            tag_desc = "글맵시"
        #
        # elif ri.tag_id == HWPTAG_BEGIN+76:
        #    tag_name = "HWPTAG_MEMO_SHAPE"
        #    tag_desc = "메모 모양"
        #
        elif ri.tag_id == HWPTAG_BEGIN + 75:
            tag_name = "HWPTAG_FORM_OBJECT"
            tag_desc = "양식 개체"
        elif ri.tag_id == HWPTAG_BEGIN + 77:
            tag_name = "HWPTAG_MEMO_LIST"
            tag_desc = "메모 리스트 헤더"
        elif ri.tag_id == HWPTAG_BEGIN + 79:
            tag_name = "HWPTAG_CHART_DATA"
            tag_desc = "차트 데이터"
        elif ri.tag_id == HWPTAG_BEGIN + 82:
            tag_name = "HWPTAG_VIDEO_DATA"
            tag_desc = "비디오 데이터"
        elif ri.tag_id == HWPTAG_BEGIN + 99:
            tag_name = "HWPTAG_SHAPE_COMPONENT_UNKNOWN"
            tag_desc = "Unknown"

        if tag_name != '':
            ri.name = tag_name
            ri.desc = tag_desc
        else:
            ri.name = "unknown"
            ri.desc = "n/a"
            return False

        return True