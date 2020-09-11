# -*- coding: utf-8 -*-

import os
import io

from modules.SIGA.formats.compressed.sevenzip.fm_sevenzip_encoded_header import SevenzipEncodedHeader
from modules.SIGA.formats.compressed.sevenzip.fm_sevenzip_signature_header import SevenzipSignatureHeader
from modules.SIGA.formats.compressed.sevenzip.fm_sevenzip_start_header import SevenzipStartHeader

from modules.SIGA import definitions
from modules.SIGA.classes.interface import Common

class SevenZip(Common):
    UNIT_SECTOR_HALF = 256
    UNIT_SECTOR = 512
    SIG_SevenZIP = b'\x37\x7A\xbc\xaf\x27\x1c'

    def __init__(self, input=None):
        self.input = input
        if input:
            self.size = os.path.getsize(input)
        else:
            self.size = 0
        self.file = None
        self.data = None

        # Parsing results
        self.sz_start_header = None
        self.sz_signature_header = None
        self.sz_encoded_header = None

        # For external functions
        self._sig = None
        self._ext = None
        self._metadata = None
        self._text = None
        self._structure = None

    def identifyFormatFromFile(self):
        d = self._read_bytes(len(self.SIG_SevenZIP))

        if self._identify_fixed(d) is True:
            self._ext = '.7z'
            return True

        return False

    def identifyFormatFromMemory(self, file_object):
        header = file_object[0:len(self.SIG_SevenZIP)]

        if self._identify_fixed(header) is True:
            self._ext = '.7z'
        else:
            return False

        if self._ext == None:
            return False

        return self._ext

    def _identify_fixed(self, d):
        try:
            if d == SevenZip.SIG_SevenZIP:
                self._sig = SevenZip.SIG_SevenZIP
            else:
                return False
        except Exception as e:
            if str(e).find("unexpected fixed contents") > 0:
                return False
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

    def validate(self):
        #임시! 새로 구현할 예정
        #
        # self.data = fm_Sevenzip.from_file(self.input)
        #
        # logger.info("validate_signature(): 검증을 시작합니다.")
        # if self._validate_signature():
        #     logger.info("validate_signature(): 검증이 완료되었습니다.")
        # else:
        #     logger.error("validate_signature(): 정상적인 7-ZIP 파일 포맷이 아닙니다.")
        #     return False
        #
        # logger.info("validate_encoded_header(): 검증을 시작합니다.")
        # if self._validate_encoded_header():
        #     logger.info("validate_encoded_header(): 검증이 완료되었습니다.")
        # else:
        #     logger.error("validate_encoded_header(): 정상적인 7-ZIP 파일 포맷이 아닙니다.")
        #     return False

        return definitions.VALID_SUCCESS

    def _validate_signature(self):
        if not self.data.signature_header.signature == b"\x37\x7A\xBC\xAF\x27\x1C":
            return False
        return True

    def _validate_encoded_header(self):
        if not self.data.encoded_header.nid.value == 23:
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

        if self._sig == SevenZip.SIG_SevenZIP:
            h = self._read_bytes(0x0C)  # Fixed Size


        #f = io.BytesIO(d)

        # --------------------------------------------------------
        # Get Signature Header

        try:
            self.sz_signature_header = SevenzipSignatureHeader.from_bytes(h)
        except Exception as e:
            pass

        if self.sz_signature_header is None:
            return False

        # --------------------------------------------------------
        # Get Start Header

        h = self._read_bytes(0x14, 0x0C)  # Fixed Offset

        try:
            self.sz_start_header = SevenzipStartHeader.from_bytes(h)
        except Exception as e:
            pass

        if self.sz_start_header is None:
            return False

        # --------------------------------------------------------
        # Get Encoded Header

        h = self._read_bytes(0x20 + self.sz_start_header.next_header_offset, self.sz_start_header.next_header_size)

        try:
            self.sz_encoded_header = SevenzipEncodedHeader.from_bytes(h)
        except Exception as e:
            pass

        if self.sz_encoded_header is None:
            return False

        return self.data