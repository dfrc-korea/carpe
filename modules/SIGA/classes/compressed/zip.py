# -*- coding: utf-8 -*-

import os
import struct

from modules.SIGA import definitions
from modules.SIGA.classes.interface import Common

from modules.SIGA.formats.compressed.zip.fm_zip_local_file import ZipLocalFile
from modules.SIGA.formats.compressed.zip.fm_zip_end_of_central_dir import ZipEndOfCentralDir
from modules.SIGA.formats.compressed.zip.fm_zip_central_dir_entry import ZipCentralDirEntry


class Zip(Common):
    UNIT_SECTOR_HALF = 256
    UNIT_SECTOR = 512
    SIGNATURE_ZIP = b'\x50\x4B'
    7
    def __init__(self, input=None):
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
        self._metadata = None
        self._text = None
        self._structure = dict()

        self._structure['LocalFile'] = list()
        self._structure['CentralDirectory'] = list()
        self._structure['EndofCentralDirecotry'] = list()
        self._vuln_cnt = 0

    def identifyFormatFromFile(self):
        SIG_ZIP = b'\x50\x4B'

        fp = open(self.input, 'rb')
        header = fp.read(len(SIG_ZIP))
        fp.close()

        if header == SIG_ZIP:
            self._ext = '.zip'
        else:
            return False
        return self._ext

    def identifyFormatFromMemory(self, file_object):

        header = file_object[0:len(self.SIGNATURE_ZIP)]
        if header == self.SIGNATURE_ZIP:
            self._ext = '.zip'
        else:
            return False

        if self._ext == None:
            return False

        return self._ext

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

    def validate(self):

        if self.parse() is False:
            return False

        if not self._validate_local_file_signature():
            return False

        if not self._validate_central_directory_signature():
            return False

        if not self._validate_end_of_central_directory_signature():
            return False

        return definitions.VALID_SUCCESS

    def _validate_local_file_signature(self):
        counter = 0

        for entry in self.zip_array_local_file:
            temp = {}
            temp['name'] = entry.header.file_name
            if entry.header.magic == 19280 and (entry.header.section_type == 0x0403 or entry.header.section_type == 0x0807 or \
                                                entry.header.section_type == 0x0806 or entry.header.section_type == 0x0201 or \
                                                entry.header.section_type == 0x0505 or entry.header.section_type == 0x0606 or \
                                                entry.header.section_type == 0x0706 or entry.header.section_type == 0x3030):
                temp['signature'] =  "정상"
            elif  entry.header.magic == 19280 and entry.header.section_type == 0x0605:
                temp['signature'] = "정상"
            else:
                temp['signature'] = "비정상"
                self._vuln_cnt += 1
                self._structure['LocalFile'].append(temp)
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

    def get_metadata(self):
        return self._metadata

    def get_text(self):
        return self._text

    def get_structure(self):
        return self._structure

    def parse(self):
        ''' 작업 해야함 '''

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