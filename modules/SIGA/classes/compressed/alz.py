# -*- coding: utf-8 -*-
import io
import os


from modules.SIGA import definitions
from modules.SIGA.classes.interface import Common

from modules.SIGA.formats.compressed.alz.alz_alz_file_header import fm_AlzAlzFileHeader
from modules.SIGA.formats.compressed.alz.alz_local_file_header import fm_AlzLocalFileHeader
from modules.SIGA.formats.compressed.alz.alz_central_directory_structure import fm_AlzCentralDirectoryStructure
from modules.SIGA.formats.compressed.alz.alz_endof_central_directory_record import fm_AlzEndofCentralDirectoryRecord

class Alz(Common):
    UNIT_SECTOR_HALF = 256
    UNIT_SECTOR = 512
    SIG_Alz = b'\x41\x4C\x5A\x01'

    def __init__(self, input=None):
        self.input = input
        if input:
            self.size = os.path.getsize(input)
        else:
            self.size = 0
        self.file = None
        self.data = None

        # Parsing results
        self.alz_file_header = None
        self.alz_array_local_file_header = None
        self.alz_array_central_directory_structure = None
        self.alz_end_of_central_directory_structure = None

        # For external functions
        self._sig = None
        self._ext = None
        self._metadata = None
        self._text = None
        self._structure = None

    def identifyFormatFromFile(self):
        # Signature를 판단하기 위한 fp
        fp = open(self.input, 'rb')
        header = fp.read(len(self.SIG_Alz))
        fp.close()

        if header == self.SIG_Alz:
            self._ext = '.alz'
        else:
            return False
        return self._ext

    def identifyFormatFromMemory(self, file_object):

        header = file_object[0:len(self.SIG_Alz)]

        if header == self.SIG_Alz:
            self._ext = '.alz'
        else:
            return False

        if self._ext == None:
            return False

        return self._ext

    def validate(self):
        #임시
        #self.data = fm_Alz.from_file(self.input)

        if self.parse() is False:
            return False

        if not self._validate_file_header():
            return False

        if not self._validate_local_file_header():
            return False

        if not self._validate_central_directory_structure():
            return False

        if self._validate_end_of_central_directory_structure():
            return False

        return definitions.VALID_SUCCESS

    def _validate_file_header(self):
        if not self.alz_file_header.signature == 0x015A4C41:  # b'ALZ\x01'
            return False
        return True

    def _validate_local_file_header(self):
        for entry in self.alz_array_local_file_header:
            if not entry.signature == 0x015A4C42:  # b'BLZ\x01'
                return False

            if entry.file_descriptor & 0x10 == 0x10 or entry.file_descriptor & 0x20 == 0x20 or \
                    entry.file_descriptor & 0x40 == 0x40 or entry.file_descriptor & 0x80 == 0x80 or \
                    entry.file_descriptor == 0x00:
                print("local_file_header.file_descriptor 값이 정상입니다.")
            else:
                return False

            if entry.file_descriptor & 0x01 == 0x01:
                print("local_file_header 가 암호화 되어있습니다.")
            else:
                print("local_file_header 가 암호화 되어있지 않습니다.")

        return True

    def _validate_central_directory_structure(self):

        for entry in self.alz_array_central_directory_structure:
            if not entry.signature == 0x015A4C43:  # b'CLZ\x01'
                return False
        return True

    def _validate_end_of_central_directory_structure(self):

        if not self.alz_end_of_central_directory_structure.signature == 0x025A4C43:  # b'CLZ\x02'
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

    def get_metadata(self):

        return self._metadata

    def get_text(self):

        return self._text

    def get_structure(self):

        return self._structure

    def parse(self):
        ''' 작업 해야함 '''



        d = self._read_bytes()

        f = io.BytesIO(d)

        # --------------------------------------------------------
        # Get ALZ File Header

        try:
            self.alz_file_header = fm_AlzAlzFileHeader.from_io(f)
        except Exception as e:
            pass

        if self.alz_file_header is None:
            return False

        # --------------------------------------------------------
        # Get Next Data

        self.alz_array_local_file_header = []
        self.alz_array_central_directory_structure = []

        while True:
            tmp = f.read(4)
            f.seek(-4, os.SEEK_CUR)
            entry = None
            if tmp == b'BLZ\x01' :  # Local File Header
                try:
                    entry = fm_AlzLocalFileHeader.from_io(f)
                except Exception as e:
                    pass

                if entry is None:
                    return False
                self.alz_array_local_file_header.append(entry)

            elif tmp == b'CLZ\x01' :  # Central
                try:
                    entry = fm_AlzCentralDirectoryStructure.from_io(f)
                except Exception as e:
                    pass

                if entry is None:
                    return False

                self.alz_array_central_directory_structure.append(entry)

            elif tmp == b'CLZ\x02' :  # End of Central Directory
                try:
                    self.alz_end_of_central_directory_structure = fm_AlzEndofCentralDirectoryRecord.from_io(f)
                except Exception as e:
                    pass

                if self.alz_end_of_central_directory_structure is None:
                    return False
                break
            else:
                return False

        return True