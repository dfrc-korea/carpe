# -*- coding: utf-8 -*-

import os

from modules.SIGA import definitions
from modules.SIGA.classes.interface import Common

class RAR(Common):
    UNIT_SECTOR_HALF = 256
    UNIT_SECTOR = 512
    SIG_RAR = b'Rar!'

    def __init__(self, input=None):
        self.input = input
        if input:
            self.size = os.path.getsize(input)
        else:
            self.size = 0
        self.file = None
        self.data = None

        # Parsing results

        # For external functions
        self._sig = None
        self._ext = None
        self._metadata = None
        self._text = None
        self._structure = None

    def identifyFormatFromFile(self):
        fp = open(self.input, 'rb')
        header = fp.read(len(self.SIG_RAR))
        fp.close()

        if header == self.SIG_RAR:
            self._ext = '.rar'
        else:
            return False
        return self._ext

    def identifyFormatFromMemory(self, file_object):

        header = file_object[0:len(self.SIG_RAR)]

        if header == self.SIG_RAR:
            self._ext = '.rar'
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

        if not self._validate_rar_signature():
            return False

        return definitions.VALID_SUCCESS

    def _validate_rar_signature(self):

        if self.data[0:8] == b'\x52\x61\x72\x21\x1A\x07\x01\x00':
            pass
        elif self.data[0:7] == b'\x52\x61\x72\x21\x1A\x07\x00':
            pass
        else:
            return False

        return True


    def get_metadata(self):
        return self._metadata

    def get_text(self):
        return self._text

    def get_structure(self):
        return self._structure

    def parse(self):
        self.data = self._read_bytes()
        return True