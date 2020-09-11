# -*- coding: utf-8 -*-

# This is a generated file! Please edit source .ksy file and use kaitai-struct-compiler to rebuild

from pkg_resources import parse_version
from modules.SIGA.kaitaistruct import __version__ as ks_version, KaitaiStruct, KaitaiStream, BytesIO


if parse_version(ks_version) < parse_version('0.7'):
    raise Exception("Incompatible Kaitai Struct Python API: 0.7 or later is required, but you have %s" % (ks_version))

from modules.SIGA.formats.documents.cfbf.fm_cfbf_dir_entry import CfbfDirEntry
from modules.SIGA.formats.documents.cfbf.fm_cfbf_header import CfbfHeader
from modules.SIGA.formats.documents.cfbf.fm_cfbf_difat_sector import CfbfDifatSector
from modules.SIGA.formats.documents.cfbf.fm_cfbf_fat_sector import CfbfFatSector
class fm_Cfbf(KaitaiStruct):
    def __init__(self, _io, _parent=None, _root=None):
        self._io = _io
        self._parent = _parent
        self._root = _root if _root else self
        self._read()

    def _read(self):
        self.header = CfbfHeader(self._io)

    @property
    def difat_1st(self):
        if hasattr(self, '_m_difat_1st'):
            return self._m_difat_1st if hasattr(self, '_m_difat_1st') else None

        if self.header.size_difat > 0:
            _pos = self._io.pos()
            self._io.seek(((self.header.ofs_difat + 1) * self.sector_size))
            self._raw__m_difat_1st = self._io.read_bytes(self.sector_size)
            io = KaitaiStream(BytesIO(self._raw__m_difat_1st))
            self._m_difat_1st = CfbfDifatSector(io)
            self._io.seek(_pos)

        return self._m_difat_1st if hasattr(self, '_m_difat_1st') else None

    @property
    def sector_size(self):
        if hasattr(self, '_m_sector_size'):
            return self._m_sector_size if hasattr(self, '_m_sector_size') else None

        self._m_sector_size = (1 << self.header.sector_shift)
        return self._m_sector_size if hasattr(self, '_m_sector_size') else None

    @property
    def root_entry(self):
        if hasattr(self, '_m_root_entry'):
            return self._m_root_entry if hasattr(self, '_m_root_entry') else None

        _pos = self._io.pos()
        self._io.seek(((self.header.ofs_dir + 1) * self.sector_size))
        self._m_root_entry = CfbfDirEntry(self._io)
        self._io.seek(_pos)
        return self._m_root_entry if hasattr(self, '_m_root_entry') else None

    @property
    def mini_fat_1st(self):
        if hasattr(self, '_m_mini_fat_1st'):
            return self._m_mini_fat_1st if hasattr(self, '_m_mini_fat_1st') else None

        _pos = self._io.pos()
        self._io.seek(((self.header.ofs_mini_fat + 1) * self.sector_size))
        self._raw__m_mini_fat_1st = self._io.read_bytes(self.sector_size)
        io = KaitaiStream(BytesIO(self._raw__m_mini_fat_1st))
        self._m_mini_fat_1st = CfbfFatSector(io)
        self._io.seek(_pos)
        return self._m_mini_fat_1st if hasattr(self, '_m_mini_fat_1st') else None

    @property
    def fat_1st(self):
        if hasattr(self, '_m_fat_1st'):
            return self._m_fat_1st if hasattr(self, '_m_fat_1st') else None

        _pos = self._io.pos()
        self._io.seek(((self.header.difat[0] + 1) * self.sector_size))
        self._raw__m_fat_1st = self._io.read_bytes(self.sector_size)
        io = KaitaiStream(BytesIO(self._raw__m_fat_1st))
        self._m_fat_1st = CfbfFatSector(io)
        self._io.seek(_pos)
        return self._m_fat_1st if hasattr(self, '_m_fat_1st') else None


