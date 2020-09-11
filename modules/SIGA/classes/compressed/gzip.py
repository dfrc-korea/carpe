# -*- coding: utf-8 -*-

import os

from modules.SIGA.formats.compressed.fm_gzip import fm_GZip
from modules.SIGA import definitions
from modules.SIGA.classes.interface import Common

class GZip(Common):
    SIGNATURE_GZIP = b'\x1F\x8B'
    def __init__(self, input=None):
        #self.tar = fm_TAR()

        self.input = input
        #self.data = fm_GZip.from_file(self.input)
        self.data = None

        self._ext = None
        self._metadata = None
        self._text = None
        self._structure = None

    def identifyFormatFromFile(self):

        # Signature를 판단하기 위한 fp
        fp = open(self.input, 'rb')
        header = fp.read(len(self.SIGNATURE_GZIP))
        fp.close()

        if header == self.SIGNATURE_GZIP:
            self._ext = '.gz'
        else:
            return False
        return self._ext

    def identifyFormatFromMemory(self, file_object):

        header = file_object[0:len(self.SIGNATURE_GZIP)]

        if header == self.SIGNATURE_GZIP:
            self._ext = '.gz'
        else:
            return False

        if self._ext == None:
            return False

        return self._ext

    def validate(self):
        #임시
        self.data = fm_GZip.from_file(self.input)

        if not self._validate_signature():
            return False

        return definitions.VALID_SUCCESS

    def _validate_signature(self):
        if not self.data.header.magic == b"\x1F\x8B":
            return False

        return True



    def get_metadata(self):

        return self._metadata

    def get_text(self):

        return self._text

    def get_structure(self):

        return self._structure

    def parse(self):
        ''' 작업 해야함 '''
        return self.data