# -*- coding: utf-8 -*-

import os
import io
import struct
import zipfile
import string
import json
import xml.etree.ElementTree as elemTree

from modules.SIGA.formats.compressed.zip.fm_zip import fm_Zip
from modules.SIGA import definitions
from modules.SIGA.classes.interface import Common
from modules.SIGA.formats.compressed.zip.fm_zip_local_file import ZipLocalFile
from modules.SIGA.formats.compressed.zip.fm_zip_end_of_central_dir import ZipEndOfCentralDir
from modules.SIGA.formats.compressed.zip.fm_zip_central_dir_entry import ZipCentralDirEntry


class ODF(Common):
    UNIT_SECTOR_HALF = 256
    UNIT_SECTOR = 512
    SIG_ZIP = 'PK'

    # Namespace
    ODF_NAMESPACE = '{urn:oasis:names:tc:opendocument:xmlns:meta:1.0}'
    DC_NAMESPACE = '{http://purl.org/dc/elements/1.1/}'
    # Metadata
    ODF_META_TITLE = DC_NAMESPACE + 'title'
    ODF_META_DESCRIPTION = DC_NAMESPACE + 'description'
    ODF_META_SUBJECT = DC_NAMESPACE + 'subject'
    ODF_META_CREATOR = DC_NAMESPACE + 'creator'
    ODF_META_CREATION_DATE = DC_NAMESPACE + 'creation-date'
    ODF_META_DATE = DC_NAMESPACE + 'date'
    ODF_META_LANGUAGE = DC_NAMESPACE + 'language'
    ODF_META_GENERATOR = ODF_NAMESPACE + 'generator'
    ODF_META_KEYWORD = ODF_NAMESPACE + 'keyword'
    ODF_META_INITIAL_CREATOR = ODF_NAMESPACE + 'initial-creator'
    ODF_META_PRINTED_BY = ODF_NAMESPACE + 'printed-by'
    ODF_META_PRINT_DATE = ODF_NAMESPACE + 'print-date'
    ODF_META_TEMPLATE = ODF_NAMESPACE + 'template'
    ODF_META_AUTO_RELOAD = ODF_NAMESPACE + 'auto-reload'
    ODF_META_HYPERLINK_BEHAVIOUR = ODF_NAMESPACE + 'hyperlink-behaviour'
    ODF_META_EDITING_CYCLES = ODF_NAMESPACE + 'editing-cycles'
    ODF_META_EDITING_DURATION = ODF_NAMESPACE + 'editing-duration'
    ODF_META_DOCUMENT_STATISTIC = ODF_NAMESPACE + 'document-statistic'
    ODF_META_USER_DEFINED = ODF_NAMESPACE + 'user-defined'

    # Content
    ODF_TEXT = ODF_NAMESPACE + 'p'
    ODF_TEXT_SPACE = ODF_NAMESPACE + 's'
    ODF_TEXT_SPACE_COUNT = ODF_NAMESPACE + 'c'
    ODF_TEXT_SPAN = ODF_NAMESPACE + 'span'

    def __init__(self, input=None):
        super(ODF, self).__init__(input)
        if input:
            self.size = os.path.getsize(input)
        else:
            self.size = 0
        self.file = None
        self.data = None

        # Parsing results
        self.zip_array_local_file = None
        self.zip_array_central_directory = None
        self.zip_end_of_central_directory = None


        # For external functions
        self._sig = None
        self._ext = None
        self._vuln_info = dict()
        self._vuln_cnt = 0
        self._is_encrypted = 0
        self._metadata = dict()
        self._text = None
        self._structure = dict()

        # temp structure
        self._structure['LocalFile'] = list()
        self._structure['CentralDirectory'] = list()
        self._structure['EndofCentralDirecotry'] = list()

    def identifyFormatFromFile(self):
        SIG_ZIP = b'\x50\x4B'

        fp = open(self.input, 'rb')
        header = fp.read(len(SIG_ZIP))
        fp.close()

        if header == SIG_ZIP:
            zf = zipfile.ZipFile(self.input)

            is_configurations2 = False
            is_mimetype = False

            for file in zf.filelist:
                if file.filename == 'mimetype':
                    is_mimetype = True
                """ 서광, 리브레만 있음
                elif file.filename[:16] == 'Configurations2/':
                    is_configurations2 = True
                    if is_mimetype == True and is_configurations2 == True:
                        break
                """

            if is_mimetype == True:
                data = zf.read('mimetype')

                if data[data.rfind(b'.') + 1:] == b'text':
                    self._ext = '.odt'
                elif data[data.rfind(b'.') + 1:] == b'presentation':
                    self._ext = '.odp'
                elif data[data.rfind(b'.') + 1:] == b'spreadsheet':
                    self._ext = '.ods'
            else:
                return False

        if self._ext != None:
            return self._ext
        else:
            return False

    def identifyFormatFromMemory(self, file_object):
        SIG_ZIP = b'\x50\x4B'

        header = file_object[0:len(SIG_ZIP)]

        if header == SIG_ZIP:
            file_like_object = io.BytesIO(file_object)
            try:
                zf = zipfile.ZipFile(file_like_object)
            except:
                return False

            is_configurations2 = False
            is_mimetype = False

            for file in zf.filelist:
                if file.filename == 'mimetype':
                    is_mimetype = True
                """ 서광, 리브레만 있음
                elif file.filename[:16] == 'Configurations2/':
                    is_configurations2 = True
                    if is_mimetype == True and is_configurations2 == True:
                        break
                """

            if is_mimetype == True:
                data = zf.read('mimetype')

                if data[data.rfind(b'.') + 1:] == b'text':
                    self._ext = '.odt'
                elif data[data.rfind(b'.') + 1:] == b'presentation':
                    self._ext = '.odp'
                elif data[data.rfind(b'.') + 1:] == b'spreadsheet':
                    self._ext = '.ods'
            else:
                return False

        if self._ext != None:
            return self._ext
        else:
            return False

    def get_metadata(self):
        if self._ext == '.odt':
            pass
        elif self._ext == '.odp':
            pass
        elif self._ext == '.ods':
            pass
        else:
            return False


        zf = zipfile.ZipFile(self.input)
        data = zf.read('meta.xml')
        zf.close()
        xmlroot = elemTree.fromstring(data)
        metadata = []

        for meta in xmlroot.iter():
            if meta.tag == ODF.ODF_META_TITLE:
                self._metadata['title'] = meta.text
            elif meta.tag == ODF.ODF_META_DESCRIPTION:
                self._metadata['description'] = meta.text
            elif meta.tag == ODF.ODF_META_SUBJECT:
                self._metadata['subject'] = meta.text
            elif meta.tag == ODF.ODF_META_CREATOR:
                self._metadata['creator'] = meta.text
            elif meta.tag == ODF.ODF_META_CREATION_DATE:
                self._metadata['creation-date'] = meta.text
            elif meta.tag == ODF.ODF_META_DATE:
                self._metadata['date'] = meta.text
            elif meta.tag == ODF.ODF_META_LANGUAGE:
                self._metadata['language'] = meta.text
            elif meta.tag == ODF.ODF_META_GENERATOR:
                self._metadata['generator'] = meta.text
            elif meta.tag == ODF.ODF_META_KEYWORD:
                self._metadata['keyword'] = meta.text
            elif meta.tag == ODF.ODF_META_INITIAL_CREATOR:
                self._metadata['initial-creator'] = meta.text
            elif meta.tag == ODF.ODF_META_PRINTED_BY:
                self._metadata['printed-by'] = meta.text
            elif meta.tag == ODF.ODF_META_PRINT_DATE:
                self._metadata['print-date'] = meta.text
            elif meta.tag == ODF.ODF_META_TEMPLATE:
                self._metadata['template'] = meta.text
            elif meta.tag == ODF.ODF_META_AUTO_RELOAD:
                self._metadata['auto-reload'] = meta.text
            elif meta.tag == ODF.ODF_META_HYPERLINK_BEHAVIOUR:
                self._metadata['hyperlink-behaviour'] = meta.text
            elif meta.tag == ODF.ODF_META_EDITING_CYCLES:
                self._metadata['editing-cycles'] = meta.text
            elif meta.tag == ODF.ODF_META_EDITING_DURATION:
                self._metadata['editing-duration'] = meta.text
            elif meta.tag == ODF.ODF_META_DOCUMENT_STATISTIC:
                self._metadata['document-statistic'] = meta.text
            elif meta.tag == ODF.ODF_META_USER_DEFINED:
                self._metadata['user-defined'] = meta.text

        return self._metadata

    def get_text(self):
        if self._ext == '.odt':
            self._text = self.parse_content_odt()
        elif self._ext == '.odp':
            self._text = self.parse_content_odp()
        elif self._ext == '.ods':
            self._text = self.parse_content_ods()
        else:
            return False

        #print(self._text)
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

        #self._structure['ZIP Format Internals'] = self

        self.get_metadata()
        self._structure['ODFDocInfo'] = self._metadata

        return self._structure

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
        if self._ext == '.odt':
            pass
        elif self._ext == '.odp':
            pass
        elif self._ext == '.ods':
            pass
        else:
            pass
            return False

        if self.parse() is False:
            return False

        if not self._validate_local_file_signature():
            return False

        if not self._validate_central_directory_signature():
            return False

        if not self._validate_end_of_central_directory_signature():
            return False

        self._validate_mimetype()

        if self._ext == '.odt':
            self._validate_odt()
        elif self._ext == '.odp':
            self._validate_odp()
        elif self._ext == '.ods':
            self._validate_ods()

        return definitions.VALID_SUCCESS

    def _validate_mimetype(self):

        SIG_ZIP = b'\x50\x4B'
        fp = open(self.input, 'rb')
        header = fp.read(len(SIG_ZIP))
        fp.close()
        if header == SIG_ZIP:
            zf = zipfile.ZipFile(self.input)

            is_mimetype = False

            for file in zf.filelist:
                if file.filename == 'mimetype':
                    is_mimetype = True

            if is_mimetype == True:
                data = zf.read('mimetype')

                if data[data.rfind(b'.') + 1:] == b'text' or \
                        data[data.rfind(b'.') + 1:] == b'text-template' or\
                        data[data.rfind(b'.') + 1:] == b'text-master':
                    self._structure['mimetype'] = 'OpenDocument Text'
                elif data[data.rfind(b'.') + 1:] == b'presentation' or \
                        data[data.rfind(b'.') + 1:] == b'presentation-template':
                    self._structure['mimetype'] = 'OpenDocument Presentation'
                elif data[data.rfind(b'.') + 1:] == b'spreadsheet' or \
                        data[data.rfind(b'.') + 1:] == b'spreadsheet-template':
                    self._structure['mimetype'] = 'OpenDocument Spreadsheet'
                else:
                    self._set_vuln_info(definitions.HC_STR_VTYPE_INCONSISTENCY, 0, 0, '올바르지 않은 mimetype', 'mimetype')

            zf.close()

    def _validate_local_file_signature(self):

        counter = 0
        for entry in self.zip_array_local_file:
            temp = {}
            temp['name'] = entry.header.file_name
            if entry.header.magic == 19280 and (entry.header.section_type == 0x0403 or entry.header.section_type == 0x0807 or \
                                                entry.header.section_type == 0x0806 or entry.header.section_type == 0x0201 or \
                                                entry.header.section_type == 0x0505 or entry.header.section_type == 0x0606 or \
                                                entry.header.section_type == 0x0706 or entry.header.section_type == 0x3030):
                temp['signature'] = "정상"
            elif  entry.header.magic == 19280 and entry.header.section_type == 0x0605:
                temp['signature'] = "정상"
            else:
                temp['signature'] = "비정상"
                self._vuln_cnt += 1
                self._structure['LocalFile'].append(temp)
                return False
            counter +=1
            self._structure['LocalFile'].append(temp)
        return True

    def _validate_central_directory_signature(self):
        counter = 0
        for entry in self.zip_array_central_directory:
            temp = {}
            temp['name'] = entry.file_name
            if entry.magic == 19280 and (entry.section_type == 0x0403 or entry.section_type == 0x0807 or \
                                                entry.section_type == 0x0806 or entry.section_type == 0x0201 or \
                                                entry.section_type == 0x0505 or entry.section_type == 0x0606 or \
                                                entry.section_type == 0x0706 or entry.section_type == 0x3030):
                temp['signature'] = "정상"
            elif  entry.header.magic == 19280 and entry.header.section_type == 0x0605:
                temp['signature'] = "정상"
            else:
                temp['signature'] = "비정상"
                self._structure['CentralDirectory'].append(temp)
                self._vuln_cnt += 1
                return False
            counter +=1
            self._structure['CentralDirectory'].append(temp)
        return True

    def _validate_end_of_central_directory_signature(self):
        temp = {}
        if self.zip_end_of_central_directory.magic == 19280 and self.zip_end_of_central_directory.section_type == 0x0605:
            temp['signature'] = "정상"
        else:
            temp['signature'] = "비정상"
            self._structure['EndofCentralDirecotry'].append(temp)
            self._vuln_cnt += 1
            return False

        self._structure['EndofCentralDirecotry'].append(temp)
        return True

    def _validate_odt(self):
        pass

    def _validate_odp(self):
        pass

    def _validate_ods(self):
        pass

    def _read_bytes(self, size=0, pos=0):
        if self.file is None:
            self.file = open(self.input, 'rb')

        if size <= 0:
            size = self.size

        if pos > 0:
            self.file.seek(pos)
        d = self.file.read(size)

        self._close_file()
        return d

    def _close_file(self):
        if self.file is not None:
            self.file.close()
            self.file = None

    def parse(self):

        d = self._read_bytes()

        # --------------------------------------------------------
        # Get end of central directory

        try:
            end_of_central_directory = self._read_bytes(self.size - d.rfind(b'PK'), d.rfind(b'PK'))
            self.zip_end_of_central_directory = ZipEndOfCentralDir.from_bytes(end_of_central_directory)
        except Exception as e:
            pass

        if self.zip_end_of_central_directory is None:
            return False

        # --------------------------------------------------------
        # Get central directory entries
        central_dir_offset = self.zip_end_of_central_directory.central_dir_offset
        self.zip_array_central_directory = []
        try:
            for idx in range(0, self.zip_end_of_central_directory.qty_central_dir_entries_total):
                tmp = self._read_bytes(46, central_dir_offset)  # 46 is fixed length
                tmp_file_name_len = struct.unpack('<H', tmp[0x1C:0x1E])[0]
                tmp_extra_field_len = struct.unpack('<H', tmp[0x1E:0x20])[0]
                tmp_file_comment_len = struct.unpack('<H', tmp[0x20:0x22])[0]
                central_directory = self._read_bytes(46 + tmp_file_name_len + tmp_extra_field_len + \
                                                     tmp_file_comment_len, central_dir_offset)
                self.zip_array_central_directory.append(ZipCentralDirEntry.from_bytes(central_directory))
                central_dir_offset += 46 + tmp_file_comment_len + tmp_extra_field_len + tmp_file_name_len

        except Exception as e:
            pass

        if self.zip_array_central_directory is []:
            return False

        # --------------------------------------------------------
        # Get local file
        self.zip_array_local_file = []
        try:
            for entry in self.zip_array_central_directory:
                tmp = self._read_bytes(30, entry.local_header_offset)  # 30 is fixed length
                tmp_compressed_size = struct.unpack('<I', tmp[0x12:0x16])[0]
                tmp_file_name_len = struct.unpack('<H', tmp[0x1A:0x1C])[0]
                tmp_extra_field_len = struct.unpack('<H', tmp[0x1C:0x1E])[0]
                local_file = self._read_bytes(30 + tmp_file_name_len + tmp_extra_field_len + tmp_compressed_size, \
                                              entry.local_header_offset)
                self.zip_array_local_file.append(ZipLocalFile.from_bytes(local_file))

        except Exception as e:
            pass

        if self.zip_array_local_file is []:
            return False

        return True

    def parse_content_odt(self, path=None):

        if not path:
            path = self.input

        zf = zipfile.ZipFile(path)
        data = zf.read('content.xml')
        zf.close()
        xmlroot = elemTree.fromstring(data)

        paragraphs = []

        for paragraph in xmlroot.iter(ODF.ODF_TEXT):
            if paragraph.text:
                text = paragraph.text
            else:
                text = ''

            # space
            for space in paragraph.iter(ODF.ODF_TEXT_SPACE):
                if len(space.attrib):
                    if space.attrib[ODF.ODF_TEXT_SPACE_COUNT]:
                        for i in range(1, int(space.attrib[ODF.ODF_TEXT_SPACE_COUNT])):
                            text += ' '
                    text += space.tail
                else:
                    text += space.tail

            # span
            for span in paragraph.iter(ODF.ODF_TEXT_SPAN):
                if span.text:
                    text += span.text

            if text:
                paragraphs.append(''.join(text))
            else:
                paragraphs.append(text)

        return '\n'.join(paragraphs)


    def parse_content_ods(self, path=None):
        # row, column 정보 파싱해야함

        if not path:
            path = self.input

        zf = zipfile.ZipFile(path)
        data = zf.read('content.xml')
        zf.close()
        xmlroot = elemTree.fromstring(data)

        paragraphs = []

        for paragraph in xmlroot.iter(ODF.ODF_TEXT):
            if paragraph.text:
                text = paragraph.text
            else:
                text = ''

            # space
            for space in paragraph.iter(ODF.ODF_TEXT_SPACE):
                if len(space.attrib):
                    if space.attrib[ODF.ODF_TEXT_SPACE_COUNT]:
                        for i in range(1, int(space.attrib[ODF.ODF_TEXT_SPACE_COUNT])):
                            text += ' '
                    text += space.tail
                else:
                    text += space.tail

            # span
            for span in paragraph.iter(ODF.ODF_TEXT_SPAN):
                if span.text:
                    text += span.text

            if text:
                paragraphs.append(''.join(text))
            else:
                paragraphs.append(text)

        return '\n'.join(paragraphs)



    def parse_content_odp(self, path=None):

        if not path:
            path = self.input

        zf = zipfile.ZipFile(path)
        data = zf.read('content.xml')
        zf.close()
        xmlroot = elemTree.fromstring(data)

        paragraphs = []

        for paragraph in xmlroot.iter(ODF.ODF_TEXT):
            if paragraph.text:
                text = paragraph.text
            else:
                text = ''

            # space
            for space in paragraph.iter(ODF.ODF_TEXT_SPACE):
                if len(space.attrib):
                    if space.attrib[ODF.ODF_TEXT_SPACE_COUNT]:
                        for i in range(1, int(space.attrib[ODF.ODF_TEXT_SPACE_COUNT])):
                            text += ' '
                    text += space.tail
                else:
                    text += space.tail

            # span
            for span in paragraph.iter(ODF.ODF_TEXT_SPAN):
                if span.text:
                    text += span.text

            if text:
                paragraphs.append(''.join(text))
            else:
                paragraphs.append(text)

        return '\n'.join(paragraphs)