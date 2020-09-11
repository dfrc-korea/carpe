# -*- coding: utf-8 -*-

import io
import os

from modules.SIGA import definitions
from modules.SIGA.classes.interface import Common

class PDF(Common):
    UNIT_SECTOR_HALF = 256
    UNIT_SECTOR = 512
    SIG_PDF = b'%PDF-1'

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
        header = fp.read(len(self.SIG_PDF))
        fp.close()

        if header == self.SIG_PDF:
            self._ext = '.pdf'
        else:
            return False
        return self._ext

    def identifyFormatFromMemory(self, file_object):

        header = file_object[0:len(self.SIG_PDF)]

        if header == self.SIG_PDF:
            self._ext = '.pdf'
        else:
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


        return definitions.VALID_SUCCESS

    def get_metadata(self):
        return self._metadata

    def get_text(self):
        return self._text

    def get_structure(self):
        return self._structure

    def parse(self):

        d = self._read_bytes()
        f = io.BytesIO(d)

        return True