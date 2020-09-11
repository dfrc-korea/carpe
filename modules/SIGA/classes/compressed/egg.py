# -*- coding: utf-8 -*-

import io
import os
import struct

from modules.SIGA import definitions
from modules.SIGA.classes.interface import Common

from modules.SIGA.formats.compressed.egg.egg_header import fm_EggHeader
from modules.SIGA.formats.compressed.egg.egg_file_header import fm_EggFileHeader
from modules.SIGA.formats.compressed.egg.egg_block_header import fm_EggBlockHeader
from modules.SIGA.formats.compressed.egg.egg_file_name_header import  fm_EggFileNameHeader
from modules.SIGA.formats.compressed.egg.egg_windows_file_information import fm_EggWindowsFileInformation


class EGG(Common):
    UNIT_SECTOR_HALF = 256
    UNIT_SECTOR = 512
    SIG_EGG = b'EGGA'

    def __init__(self, input=None):
        self.input = input
        if input:
            self.size = os.path.getsize(input)
        else:
            self.size = 0
        self.file = None
        self.data = None

        # Parsing results
        self.egg_header = None
        self.array_file_header = []  # File Header ~ Windows File Information
        self.array_block_header = []  # Block Header ~ Compressed Data

        # For external functions
        self._sig = None
        self._ext = None
        self._metadata = None
        self._text = None
        self._structure = None

    def identifyFormatFromFile(self):
        fp = open(self.input, 'rb')
        header = fp.read(len(self.SIG_EGG))
        fp.close()

        if header == self.SIG_EGG:
            self._ext = '.egg'
        else:
            return False
        return self._ext

    def identifyFormatFromMemory(self, file_object):

        header = file_object[0:len(self.SIG_EGG)]
        if header == self.SIG_EGG:
            self._ext = '.egg'
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

        if not self._validate_egg_header():
            return False

        if not self._validate_file_header():
            return False

        if not self._validate_block_header():
            return False

        return definitions.VALID_SUCCESS

    def _validate_egg_header(self):

        if not self.egg_header.signature == 0x41474745:
            return False

        if not self.egg_header.version == 0x100:
            return False

        if not self.egg_header.reserved == 0:
            return False

        return True

    def _validate_file_header(self):

        for entry in self.array_file_header:
            if not entry['file_header'].signature == 0x0A8590E3:
                return False

            if not entry['file_name_header'].signature == 0x0A8591AC:
                return False

            if not entry['windows_file_information'].signature == 0x2C86950B:
                return False

        return True

    def _validate_block_header(self):

        for entry in self.array_block_header:
            if not entry.signature == 0x02B50C13:
                return False

        return True

    def get_metadata(self):
        return self._metadata

    def get_text(self):
        return self._text

    def get_structure(self):
        return self._structure

    def parse(self):

        d = self._read_bytes()
        f = io.BytesIO(d)  # 순차적 파싱할 때 사용하면 좋음

        # --------------------------------------------------------
        # Get EGG Header

        try:
            self.egg_header = fm_EggHeader.from_io(f)
        except Exception as e:
            pass

        if self.egg_header is None:
            return False

        # --------------------------------------------------------
        # Get File Header ~ Compressed Data


        while True:
            tmp = f.read(4)
            f.seek(-4, os.SEEK_CUR)
            if tmp == b'\xE3\x90\x85\x0A':
                file = {'file_header':None, 'file_name_header':None, 'windows_file_information':None}

                try:
                    file['file_header'] = fm_EggFileHeader.from_io(f)
                except Exception as e:
                    pass

                if file['file_header'] is None:
                    return False

                try:
                    file['file_name_header'] = fm_EggFileNameHeader.from_io(f)
                except Exception as e:
                    pass

                if file['file_name_header'] is None:
                    return False

                try:
                    file['windows_file_information'] = fm_EggWindowsFileInformation.from_io(f)
                except Exception as e:
                    pass

                if file['windows_file_information'] is None:
                    return False

                tmp = f.read(4)
                if tmp == b'\x22\x82\xe2\x08':
                    pass

                self.array_file_header.append(file)

            elif tmp == b'\x13\x0C\xB5\x02':
                block_header = None
                try:
                    block_header = fm_EggBlockHeader.from_io(f)
                except Exception as e:
                    pass

                if block_header is None:
                    return False

                self.array_block_header.append(block_header)

            elif tmp == b'\x22\x82\xe2\x08':
                break
            else:
                return False

        return True