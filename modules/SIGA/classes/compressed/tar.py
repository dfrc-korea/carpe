# -*- coding: utf-8 -*-
import io
import os

from modules.SIGA.formats.compressed.fm_tar import fm_TAR
from modules.SIGA import definitions
from modules.SIGA.classes.interface import Common


class Tar(Common):
    UNIT_SECTOR_HALF = 256
    UNIT_SECTOR = 512

    def __init__(self, input=None):
        self.input = input
        if input:
            self.size = os.path.getsize(input)
        else:
            self.size = 0
        self.file = None
        self.data = None

        # Parsing results
        self.tar_array_directory_header = None
        self.tar_array_data_header = None
        self.tar_array_data = None
        self.tar_slack = None


        # For external functions
        self._sig = None
        self._ext = None
        self._metadata = None
        self._text = None
        self._structure = None

    def identifyFormatFromFile(self):

        fp = open(self.input, 'rb')
        header = fp.read(0x90)
        fp.close()

        if header[0x64] >= 0x30 and header[0x64] <= 0x37:
            pass
        else:
            return False

        if header[0x65] >= 0x30 and header[0x65] <= 0x37:
            pass
        else:
            return False

        if header[0x66] >= 0x30 and header[0x66] <= 0x37:
            pass
        else:
            return False

        if header[0x67] >= 0x30 and header[0x67] <= 0x37:
            pass
        else:
            return False

        if header[0x68] >= 0x30 and header[0x68] <= 0x37:
            pass
        else:
            return False

        if header[0x69] >= 0x30 and header[0x69] <= 0x37:
            pass
        else:
            return False

        if header[0x6A] >= 0x30 and header[0x6A] <= 0x37:
            pass
        else:
            return False

        if header[0x6B] == 0x00:
            self._ext = '.tar'
        else:
            return False


        return self._ext

    def identifyFormatFromMemory(self, file_object):

        if len(file_object) < 0x90:
            return False
        header = file_object[0:0x90]

        if header[0x64] >= 0x30 and header[0x64] <= 0x37:
            pass
        else:
            return False

        if header[0x65] >= 0x30 and header[0x65] <= 0x37:
            pass
        else:
            return False

        if header[0x66] >= 0x30 and header[0x66] <= 0x37:
            pass
        else:
            return False

        if header[0x67] >= 0x30 and header[0x67] <= 0x37:
            pass
        else:
            return False

        if header[0x68] >= 0x30 and header[0x68] <= 0x37:
            pass
        else:
            return False

        if header[0x69] >= 0x30 and header[0x69] <= 0x37:
            pass
        else:
            return False

        if header[0x6A] >= 0x30 and header[0x6A] <= 0x37:
            pass
        else:
            return False

        if header[0x6B] == 0x00:
            self._ext = '.tar'
        else:
            return False

        if self._ext == None:
            return False

        return self._ext

    def validate(self):

        if self.parse() is False:
            return False

        if not self._validate_tar_array_directory_header():
            return False

        if not self._validate_tar_array_data_header():
            return False

        return definitions.VALID_SUCCESS

    def _validate_range(self, data):
        for i in range(0, len(data)):
            if int(data[i]) >= 0x30 and int(data[i]) <= 0x37:
                pass
            elif i == len(data) - 1 and int(data[i]) == 0x00:
                break
            else:
                return False
        return True


    def _validate_tar_array_directory_header(self):

        for entry in self.tar_array_directory_header:
            if not self._validate_range(entry.mode):
                return False

            if not self._validate_range(entry.uid):
                return False

            if not self._validate_range(entry.gid):
                return False

            if not self._validate_range(entry.size):
                return False

            if not self._validate_range(entry.mtime):
                return False

            if not self._validate_range(entry.chksum):
                return False

            if not self._validate_range(entry.version):
                return False

        return True

    def _validate_tar_array_data_header(self):

        for entry in self.tar_array_data_header:

            if not self._validate_range(entry.mode):
                return False

            if not self._validate_range(entry.uid):
                return False

            if not self._validate_range(entry.gid):
                return False

            if not self._validate_range(entry.size):
                return False

            if not self._validate_range(entry.mtime):
                return False

            if not self._validate_range(entry.chksum):
                return False

            if not self._validate_range(entry.version):
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

        d = self._read_bytes()
        f = io.BytesIO(d)

        # --------------------------------------------------------
        # Get Tar Entry
        self.tar_array_data = []
        self.tar_array_data_header = []
        self.tar_array_directory_header = []

        while True:
            entry = None
            try:
                entry = fm_TAR.from_io(f)

            except Exception as e:
                pass

            if entry is None:
                return False

            if entry.name == b'\x00' * 100:
                f.seek(-512, os.SEEK_CUR)
                self.tar_slack = f.read()
                break


            if entry.typeflag == b'5':
                self.tar_array_directory_header.append(entry)
            elif entry.typeflag == b'0':
                data_size = int(entry.size[:-1], 8)
                data = self._read_bytes(data_size, f.tell())

                self.tar_array_data_header.append(entry)
                self.tar_array_data.append(data)

                if data_size % 512 == 0:
                    f.seek(data_size, os.SEEK_CUR)
                else:
                    f.seek(data_size + (512 - data_size % 512), os.SEEK_CUR)

            else:
                print("invalid")
                pass

        return self.data
