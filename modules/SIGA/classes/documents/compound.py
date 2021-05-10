# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import os

from modules.SIGA.classes.interface import Common
from modules.SIGA import definitions
from modules.SIGA import utility

from modules.SIGA.formats.documents.cfbf.fm_cfbf_header import CfbfHeader as Lego_Kaitai_Cfbf_Header
from modules.SIGA.formats.documents.cfbf.fm_cfbf_difat_sector import CfbfDifatSector as Lego_Kaitai_Cfbf_Difat_Sector
from modules.SIGA.formats.documents.cfbf.fm_cfbf_fat_sector import CfbfFatSector as Lego_Kaitai_Cfbf_Fat_Sector
from modules.SIGA.formats.documents.cfbf.fm_cfbf_dir_entry import CfbfDirEntry as Lego_Kaitai_Cfbf_Dir_Entry

class Compound(Common):

    def __init__(self, input=None):

        super(Compound, self).__init__(input)
        self.input = input
        #self.data = fm_Cfbf.from_file(self.input)
        self.data = None
        self._ext = None
        self._metadata = None
        self._text = None
        self._structure = dict()

        self._filesize = 0
        self._SECTOR_SIZE = 0
        self._MINI_SECTOR_SIZE = 0
        self._header = None
        self._difat_entries = None
        self._fat_entries = None
        self._minifat_entries = None
        self._dir_entries = None
        self._mini_stream = None

        # file validation
        if input:
            try:
                self._fp = open(self.input, 'rb')
                self._filesize = os.path.getsize(input)
            except FileNotFoundError:
                print('file not found')
        else:
            self._fp = None
            self._filesize = 0


    def identifyFormatFromFile(self):
        # self._ext = os.path.splitext(self.input)[1]
        # temp
        #self._ext = ['doc', 'xls', 'ppt', 'hwp']
        #self._ext = '.compound'
        #return self._ext
        if self.input[-4:] != ".xls" or self.input[-4:] != ".doc" or self.input[-4:] != ".ppt" or self.input[-4:] != ".hwp":
            return False

        return True

    def identifyFormatFromMemory(self, file_object):

        return False

    def validate(self):
        # validate, parse 부르긴 해야함
        self.get_header()

        if not self._validate_header():
            return definitions.INVALID_SIGNATURE

        # 각 단계별 컴파운드 검증 코드는 들어가야함 : 나중에 하자
        self.load_compound()

        if not self._validate_root_entry():
            return definitions.INVALID_ROOT_ENTRY

        return definitions.VALID_SUCCESS
    '''
    def get_metadata(self):
        logger.info('CFBF Metadata')
        return self._metadata

    def get_text(self):
        logger.error('CFBF Content')
        return self._text
    '''
    def get_structure(self):

        cp_header = dict()
        dir_entires = dict()



        cp_header['Signature'] = "0xD0CF11E0A1B11AE1"
        cp_header['Guid'] = "0-0-0-00000000"
        cp_header['Minor Version'] = str(self._header.version_minor)
        cp_header['Major Version'] = str(self._header.version_major)
        cp_header['Byte Order'] = str(self._header.byte_order)
        cp_header['Sector Size'] = str(self._header.sector_size)
        cp_header['Mini Stream Sector Size'] = str(self._header.mini_sector_size)
        cp_header['Reserved'] = "0"
        cp_header['Total Directory Sectors'] = str(self._header.size_dir)
        cp_header['Total FAT Sectors'] = str(self._header.size_fat)
        cp_header['Start of Directory Sectors'] = str(self._header.ofs_dir)
        cp_header['Transaction Signature'] = str(self._header.transaction_seq)
        cp_header['Mini Stream Cutoff'] = str(self._header.mini_stream_cutoff_size)
        cp_header['Start of Mini FAT Sectors'] = str(self._header.ofs_mini_fat)
        cp_header['Total Mini FAT Sectors'] = str(self._header.size_mini_fat)
        cp_header['Start of DIFAT Sectors'] = str(self._header.ofs_difat)
        cp_header['Total DIFAT Sectors'] = str(self._header.size_difat)


        self._structure['Compound Header'] = cp_header
        return self._structure

    def parse(self):
        ''' 작업 해야함 '''
        return self.data

    """ Compound 내부 함수 """
    def get_header(self):
        ''' Read HEADER (512) '''
        d = self._read_bytes(512)

        self._header = Lego_Kaitai_Cfbf_Header.from_bytes(d)
        self._SECTOR_SIZE = self._header.sector_size
        self._MINI_SECTOR_SIZE = self._header.mini_sector_size

    def load_compound(self):

        if self._SECTOR_SIZE < 512:
            return False

        if self._SECTOR_SIZE < self._MINI_SECTOR_SIZE:
            return False

        # Build Double-Indirect FAT
        self._difat_entries = \
            self._build_difat()

        # temporarily changed - jbc
        if not self._difat_entries:
            return False

        # Build FAT
        self._fat_entries = \
            self._build_fat()

        # Build mini-FAT
        self._minifat_entries = \
            self._build_minifat()

        # temporarily changed - jbc
        if not self._minifat_entries:
            return False

        # Get directory entries
        self._dir_entries = \
            self._get_dir_entries()

        # Get data stream of Root Entry (for mini streams)
        self._mini_stream = \
            self._get_root_stream()


        # Traverse each directory entry and its data stream
        for entry in self._dir_entries:
            if entry.name_len > 64 or entry.object_type == Lego_Kaitai_Cfbf_Dir_Entry.ObjType.unknown:
                continue

        if self._header.mini_stream_cutoff_size <= entry.size:
            d = self._get_stream(entry)
        else:
            d = self._get_mini_stream(entry)

            #print("[ {0} ]".format(entry.name_trancated))
            #print('\t', entry.object_type)
            #print('\t', entry.size)
            #self._print_hex_dump(d[:64])

    def _print_hex_dump(self, buf, start_offset=0):
        print('-' * 78)

        offset = 0
        while offset < len(buf):
            # Offset
            print(' %08X : ' % (offset + start_offset), end='')

            if ((len(buf) - offset) < 0x10) is True:
                data = buf[offset:]
            else:
                data = buf[offset:offset + 0x10]

            # Hex Dump
            for hex_dump in data:
                print("%02X" % hex_dump, end=' ')

            if ((len(buf) - offset) < 0x10) is True:
                print(' ' * (3 * (0x10 - len(data))), end='')

            print('  ', end='')

            # Ascii
            for ascii_dump in data:
                if ((ascii_dump >= 0x20) is True) and ((ascii_dump <= 0x7E) is True):
                    print(chr(ascii_dump), end='')
                else:
                    print('.', end='')

            offset = offset + len(data)
            print('')

        print('-' * 78)

    def _read_bytes(self, size, pos=0):
        if pos > 0:
            self._fp.seek(pos)
        d = self._fp.read(size)
        return d

    def _calc_offset(self, sec_num, base_size):
        return (sec_num + 1) * base_size

    def _build_difat(self):
        out = []

        if self._header.size_difat == 0:
            return self._header.difat[:self._header.size_fat]

        # Set default 109 entries
        out.extend(self._header.difat)

        # Get entries from DIFAT Sectors
        ofs_next = self._header.ofs_difat
        while ofs_next >= 0:
            pos = self._calc_offset(ofs_next, self._SECTOR_SIZE)
            d = self._read_bytes(self._SECTOR_SIZE, pos)
            lk = Lego_Kaitai_Cfbf_Difat_Sector.from_bytes(d)
            out.extend(lk.difat_entries)
            ofs_next = lk.ofs_difat_next
            if ofs_next == Lego_Kaitai_Cfbf_Difat_Sector.FatType.end_of_chain.value:
                break
            # temporarily changed - jbc
            if len(out) >= 1000:
                return False

        return out

    def _build_fat(self):
        out = []

        for entry in self._difat_entries:
            pos = self._calc_offset(entry, self._SECTOR_SIZE)
            d = self._read_bytes(self._SECTOR_SIZE, pos)
            lk = Lego_Kaitai_Cfbf_Fat_Sector.from_bytes(d)
            out.extend(lk.fat_entries)

        return out

    def _get_chain(self, fat, idx):
        chain = [idx]

        while True:
            idx = fat[idx]
            # temporarily changed - jbc
            if idx == 0 or len(chain) > 1000000:
                return False
            if idx == Lego_Kaitai_Cfbf_Difat_Sector.FatType.end_of_chain.value:
                break
            chain.append(idx)

        return chain

    def _build_minifat(self):
        out = []
        idx = self._header.ofs_mini_fat
        if idx < 0:
            return out

        chain = self._get_chain(self._fat_entries, idx)

        # temporarily changed - jbc
        if not chain:
            return False

        for idx in chain:
            pos = self._calc_offset(idx, self._SECTOR_SIZE)
            d = self._read_bytes(self._SECTOR_SIZE, pos)
            lk = Lego_Kaitai_Cfbf_Fat_Sector.from_bytes(d)
            out.extend(lk.fat_entries)

        return out

    def _get_dir_entries(self):
        out = []
        chain = self._get_chain(self._fat_entries, self._header.ofs_dir)

        for idx in chain:
            pos = self._calc_offset(idx, self._SECTOR_SIZE)
            d = self._read_bytes(self._SECTOR_SIZE, pos)

            for x in range(4):
                lk = Lego_Kaitai_Cfbf_Dir_Entry.from_bytes(d[x * 128:(x + 1) * 128])
                out.append(lk)

        return out

    def _get_root_stream(self):
        out = bytearray(b'')
        if self._dir_entries[0].ofs != -2:
            chain = self._get_chain(self._fat_entries, self._dir_entries[0].ofs)

            for idx in chain:
                pos = self._calc_offset(idx, self._SECTOR_SIZE)
                d = self._read_bytes(self._SECTOR_SIZE, pos)
                out += d

        return out

    def _get_stream(self, dir_entry):
        out = bytearray(b'')
        if dir_entry.object_type != Lego_Kaitai_Cfbf_Dir_Entry.ObjType.stream:
            return out

        chain = self._get_chain(self._fat_entries, dir_entry.ofs)

        for idx in chain:
            pos = self._calc_offset(idx, self._SECTOR_SIZE)
            d = self._read_bytes(self._SECTOR_SIZE, pos)
            out += d

        return out

    def _get_mini_stream(self, dir_entry):
        out = bytearray(b'')
        if dir_entry.object_type != Lego_Kaitai_Cfbf_Dir_Entry.ObjType.stream:
            return out

        if dir_entry.ofs == -2:
            return out

        chain = self._get_chain(self._minifat_entries, dir_entry.ofs)

        for idx in chain:
            pos = idx * self._MINI_SECTOR_SIZE
            d = self._mini_stream[pos:pos + self._MINI_SECTOR_SIZE]
            out += d

        return out[:dir_entry.size]

    def _get_siblings(self, child_id, elements):
        if child_id < 0 or child_id > len(self._dir_entries) - 1:
            return False

        idx = child_id

        st = utility.Stack()
        st.push(idx)

        while not st.is_empty():
            if st.size() > 10000:
                break

            idx = st.top()
            st.pop()

            if idx != -1 or idx < len(self._dir_entries):
                elements.append(idx)

                if self._dir_entries[idx].child_id == 0 or self._dir_entries[idx].name_len == 0 or self._dir_entries[idx].name_len > 64 \
                    or self._dir_entries[idx].object_type.value == 0 or self._dir_entries[idx].object_type.value > 5:
                    continue

                if self._dir_entries[idx].right_sibling_id != -1 and self._dir_entries[idx].right_sibling_id < len(self._dir_entries):
                    st.push(self._dir_entries[idx].right_sibling_id)

                if self._dir_entries[idx].left_sibling_id != -1 and self._dir_entries[idx].left_sibling_id < len(self._dir_entries):
                    st.push(self._dir_entries[idx].left_sibling_id)

        if len(elements) > 0: return True
        else: return False



    # validation code
    def _validate_header(self):
        if self._header.signature != definitions.COMPOUND_SIGNATURE:
            return False

        if self._header.byte_order != definitions.COMPOUND_BYTE_ORDER:
            return False

        return True

    def _validate_root_entry(self):
        if self._dir_entries[0].name_trancated != 'Root Entry':
            return False

        return True

