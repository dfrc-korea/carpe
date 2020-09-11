# This is a generated file! Please edit source .ksy file and use kaitai-struct-compiler to rebuild

from pkg_resources import parse_version
from modules.SIGA.kaitaistruct import __version__ as ks_version, KaitaiStruct, KaitaiStream, BytesIO


if parse_version(ks_version) < parse_version('0.7'):
    raise Exception("Incompatible Kaitai Struct Python API: 0.7 or later is required, but you have %s" % (ks_version))

class PrefetchMetricEntry23(KaitaiStruct):
    def __init__(self, _io, _parent=None, _root=None):
        self._io = _io
        self._parent = _parent
        self._root = _root if _root else self
        self._read()

    def _read(self):
        self.unknown1 = self._io.read_bytes(4)
        self.unknown2 = self._io.read_bytes(4)
        self.unknown3 = self._io.read_bytes(4)
        self.offset_filename = self._io.read_u4le()
        self.size_filename = self._io.read_u4le()
        self.unknown4 = self._io.read_bytes(4)
        self.file_reference = self._root.FileRef(self._io, self, self._root)

    class FileRef(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.value = self._io.read_u8le()

        @property
        def mft_entry_number(self):
            if hasattr(self, '_m_mft_entry_number'):
                return self._m_mft_entry_number if hasattr(self, '_m_mft_entry_number') else None

            self._m_mft_entry_number = (self.value & 281474976710655)
            return self._m_mft_entry_number if hasattr(self, '_m_mft_entry_number') else None

        @property
        def sequence_number(self):
            if hasattr(self, '_m_sequence_number'):
                return self._m_sequence_number if hasattr(self, '_m_sequence_number') else None

            self._m_sequence_number = ((self.value & 18446462598732840960) >> 48)
            return self._m_sequence_number if hasattr(self, '_m_sequence_number') else None



