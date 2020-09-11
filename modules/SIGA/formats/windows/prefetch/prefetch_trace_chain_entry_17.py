# This is a generated file! Please edit source .ksy file and use kaitai-struct-compiler to rebuild

from pkg_resources import parse_version
from modules.SIGA.kaitaistruct import __version__ as ks_version, KaitaiStruct, KaitaiStream, BytesIO


if parse_version(ks_version) < parse_version('0.7'):
    raise Exception("Incompatible Kaitai Struct Python API: 0.7 or later is required, but you have %s" % (ks_version))

class PrefetchTraceChainEntry17(KaitaiStruct):
    def __init__(self, _io, _parent=None, _root=None):
        self._io = _io
        self._parent = _parent
        self._root = _root if _root else self
        self._read()

    def _read(self):
        self.index_next_entry = self._io.read_u4le()
        self.count_loaded_blocks = self._io.read_u4le()
        self.unknows1 = self._io.read_bytes(1)
        self.unknows2 = self._io.read_bytes(1)
        self.unknows3 = self._io.read_bytes(2)


