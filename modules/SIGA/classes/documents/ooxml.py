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


class OOXML(Common):
    WORD_NAMESPACE = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
    WORD_PARA = WORD_NAMESPACE + 'p'
    WORD_TEXT = WORD_NAMESPACE + 't'

    EXCEL_NAMESPACE = '{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
    EXCEL_SI = EXCEL_NAMESPACE + 'si'
    EXCEL_TEXT = EXCEL_NAMESPACE + 't'

    POWERPOINT_NAMESPACE = '{http://schemas.openxmlformats.org/presentationml/2006/main}'
    POWERPOINT_TXBODY = POWERPOINT_NAMESPACE + 'txBody'
    POWERPOINT_TEXT = '{http://schemas.openxmlformats.org/drawingml/2006/main}t'

    UNIT_SECTOR_HALF = 256
    UNIT_SECTOR = 512
    SIG_ZIP = 'PK'

    def __init__(self, input=None):
        super(OOXML, self).__init__(input)
        self.input = input
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
            for file in zf.filelist:
                if file.filename == 'word/document.xml':
                    self._ext = '.docx'
                if file.filename == 'xl/sharedStrings.xml':
                    self._ext = '.xlsx'
                if file.filename == 'ppt/slides/slide1.xml':
                    self._ext = '.pptx'
            zf.close()

        if self._ext == None:
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
            for file in zf.filelist:
                if file.filename == 'word/document.xml':
                    self._ext = '.docx'
                if file.filename == 'xl/sharedStrings.xml':
                    self._ext = '.xlsx'
                if file.filename == 'ppt/slides/slide1.xml':
                    self._ext = '.pptx'
            zf.close()

        if self._ext == None:
            return False

        if self._ext != None:
            return self._ext
        else:
            return False

    def get_metadata(self):
        if self._ext == '.docx':
            pass
        elif self._ext == '.xlsx':
            pass
        elif self._ext == '.pptx':
            pass
        else:
            return False

        zf = zipfile.ZipFile(self.input)
        data = zf.read('docProps/core.xml')
        zf.close()
        xmlroot = elemTree.fromstring(data)
        metadata = []
        for xmltag in xmlroot:
            offset = xmltag.tag.find('}')
            type = xmltag.tag[offset + 1:]
            if (xmltag.text == None):
                #metadata.append(type + " : None")
                self._metadata[type] = "None"
            else:
                #metadata.append(type + " : " + xmltag.text)
                self._metadata[type] = xmltag.text

        #self._metadata = metadata
        #print(self._metadata)
        return self._metadata

    def get_text(self):
        if self._ext == '.docx':
            self._text = self.parse_content_docx()
        elif self._ext == '.xlsx':
            self._text = self.parse_content_xlsx()
        elif self._ext == '.pptx':
            self._text = self.parse_content_pptx()
        else:
            return False

        print(self._text)
        # xlsx print example
        #tree = json.loads(self._text)
        #dat = json.loads(tree["xl/worksheets/sheet1.xml"]["data"])
        #print(dat[6][4])
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

        # self._structure['ZIP Format Internals'] = self

        self.get_metadata()
        self._structure['OOXMLDocInfo'] = self._metadata

        return self._structure

    def validate(self):
        if self._ext == '.docx':
            pass
        elif self._ext == '.xlsx':
            pass
        elif self._ext == '.pptx':
            pass
        else:
            return False

        if self.parse() is False:
            return False

        if not self._validate_local_file_signature():
            return False

        if not self._validate_central_directory_signature():
            return False

        if not self._validate_end_of_central_directory_signature():
            return False

        self._validate_document_type()

        if self._ext == '.docx':
            self._validate_docx()
        elif self._ext == '.pptx':
            self._validate_pptx()
        elif self._ext == '.xlsx':
            self._validate_xlsx()

        return definitions.VALID_SUCCESS

    def _validate_docx(self):
        pass
    def _validate_pptx(self):
        pass
    def _validate_xlsx(self):
        pass

    def _validate_document_type(self):
        SIG_ZIP = b'\x50\x4B'

        fp = open(self.input, 'rb')
        header = fp.read(len(SIG_ZIP))
        fp.close()

        if header == SIG_ZIP:
            zf = zipfile.ZipFile(self.input)
            for file in zf.filelist:
                if file.filename == 'word/document.xml':
                    self._structure['type'] = 'Microsoft Word'
                if file.filename == 'ppt/slides/slide1.xml':
                    self._structure['type'] = 'Microsoft Presentation'
                if file.filename == 'xl/sharedStrings.xml':
                    self._structure['type'] = 'Microsoft Spreadsheet'
                else:
                    self._set_vuln_info(definitions.HC_STR_VTYPE_INCONSISTENCY, 0, 0, '올바르지 않은 type', 'type')

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
                self._structure['LocalFile'].append(temp)("sections[%d].signature 값이 정상이 아닙니다." % counter)
                return False
            counter += 1
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

    def parse_content_docx(self, path=None):
        if not path:
            path = self.input

        zf = zipfile.ZipFile(path)
        data = zf.read('word/document.xml')
        zf.close()
        xmlroot = elemTree.fromstring(data)

        paragraphs = []
        for paragraph in xmlroot.iter(OOXML.WORD_PARA):
            texts = [node.text for node in paragraph.iter(OOXML.WORD_TEXT) if node.text]

            if texts: paragraphs.append(''.join(texts))
            else: paragraphs.append('')

        return '\n'.join(paragraphs)

    def parse_content_xlsx(self, path=None):
        if not path:
            path = self.input

        sst = self._parse_xlsx_shared_string(path)
        zf = zipfile.ZipFile(path)
        sheetlists = [node.filename for node in zf.filelist if 'xl/worksheets/sheet' in node.filename]
        sheetinfo = dict()
        for sheet in sheetlists:
            current = dict()
            maxrow = 0
            maxcol = 0
            data = zf.read(sheet)
            xmlroot = elemTree.fromstring(data)
            for worksheet in xmlroot.iter(OOXML.EXCEL_NAMESPACE+'row'):
                if worksheet.tag == OOXML.EXCEL_NAMESPACE + 'row':
                    tmprow = worksheet.attrib['r']
                    if maxrow < int(tmprow): maxrow = int(tmprow)
                for row in worksheet.iter(OOXML.EXCEL_NAMESPACE+'c'):
                    if 'r' in row.attrib:
                        tmpcol = self._xlsx_col2num(row.attrib['r'].replace(tmprow, ''))
                        if maxcol < int(tmpcol): maxcol = int(tmpcol)
            current['max_row'] = maxrow
            current['max_col'] = maxcol
            sheetinfo[str(sheet)] = current

        for sheet in sheetlists:
            rows = [''] * int(sheetinfo[str(sheet)]['max_row'])
            data = zf.read(sheet)
            xmlroot = elemTree.fromstring(data)
            for worksheet in xmlroot.iter(OOXML.EXCEL_NAMESPACE+'row'):
                if worksheet.tag == OOXML.EXCEL_NAMESPACE + 'row':
                    rownum = worksheet.attrib['r']

                cols = [''] * int(sheetinfo[str(sheet)]['max_col'])
                for row in worksheet.iter(OOXML.EXCEL_NAMESPACE + 'c'):
                    is_sst = False
                    if 'r' in row.attrib:
                        colnum = self._xlsx_col2num(row.attrib['r'].replace(rownum, ''))

                    if 't' in row.attrib:
                        if row.attrib['t'] == 's':
                            is_sst = True
                            cols[colnum-1] = sst[int(row.findtext(OOXML.EXCEL_NAMESPACE + 'v'))]
                    if not is_sst:
                        cols[colnum-1] = row.findtext(OOXML.EXCEL_NAMESPACE + 'v')

                rows[int(rownum)-1] = cols
            sheetinfo[str(sheet)]['data'] = json.dumps(rows)
        zf.close()


        return json.dumps(sheetinfo)

    def parse_content_pptx(self, path=None):
        if not path:
            path = self.input

        content = ''
        zf = zipfile.ZipFile(path)
        slidelists = [node.filename for node in zf.filelist if 'ppt/slides/slide' in node.filename]

        for slide in slidelists:
            data = zf.read(slide)
            xmlroot = elemTree.fromstring(data)
            for txbody in xmlroot.iter(OOXML.POWERPOINT_TXBODY):
                for text in txbody.iter(OOXML.POWERPOINT_TEXT):
                    content = content + text.text
                content = content + '\n'
        zf.close()

        return content

    def _parse_xlsx_shared_string(self, path):
        if not path:
            return False

        zf = zipfile.ZipFile(path)
        data = zf.read('xl/sharedStrings.xml')
        zf.close()
        xmlroot = elemTree.fromstring(data)

        sharedstrings = []
        for si in xmlroot.iter(OOXML.EXCEL_SI):
            texts = [node.text for node in si.iter(OOXML.EXCEL_TEXT) if node.text]

            sharedstrings.append(texts)

        return sharedstrings

    def _xlsx_col2num(self, col):

        num = 0
        for c in col:
            if c in string.ascii_letters:
                num = num * 26 + (ord(c.upper()) - ord('A')) + 1
        return num

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