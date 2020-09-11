# This is a generated file! Please edit source .ksy file and use kaitai-struct-compiler to rebuild

from pkg_resources import parse_version
from modules.SIGA.kaitaistruct import __version__ as ks_version, KaitaiStruct, KaitaiStream, BytesIO


if parse_version(ks_version) < parse_version('0.7'):
    raise Exception("Incompatible Kaitai Struct Python API: 0.7 or later is required, but you have %s" % (ks_version))

class CfbfHeader(KaitaiStruct):
    def __init__(self, _io, _parent=None, _root=None):
        self._io = _io
        self._parent = _parent
        self._root = _root if _root else self
        self._read()

    def _read(self):
        self.signature = self._io.read_bytes(8)
        self.clsid = self._io.read_bytes(16)
        self.version_minor = self._io.read_u2le()
        self.version_major = self._io.read_u2le()
        self.byte_order = self._io.read_u2le()
        self.sector_shift = self._io.read_u2le()
        self.mini_sector_shift = self._io.read_u2le()
        self.reserved1 = self._io.read_bytes(6)
        self.size_dir = self._io.read_s4le()
        self.size_fat = self._io.read_s4le()
        self.ofs_dir = self._io.read_s4le()
        self.transaction_seq = self._io.read_s4le()
        self.mini_stream_cutoff_size = self._io.read_s4le()
        self.ofs_mini_fat = self._io.read_s4le()
        self.size_mini_fat = self._io.read_s4le()
        self.ofs_difat = self._io.read_s4le()
        self.size_difat = self._io.read_s4le()
        self.difat = [None] * (109)
        for i in range(109):
            self.difat[i] = self._io.read_s4le()


    @property
    def sector_size(self):
        if hasattr(self, '_m_sector_size'):
            return self._m_sector_size if hasattr(self, '_m_sector_size') else None

        self._m_sector_size = (1 << self.sector_shift)
        return self._m_sector_size if hasattr(self, '_m_sector_size') else None

    @property
    def mini_sector_size(self):
        if hasattr(self, '_m_mini_sector_size'):
            return self._m_mini_sector_size if hasattr(self, '_m_mini_sector_size') else None

        self._m_mini_sector_size = (1 << self.mini_sector_shift)
        return self._m_mini_sector_size if hasattr(self, '_m_mini_sector_size') else None


