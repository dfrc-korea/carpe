# This is a generated file! Please edit source .ksy file and use kaitai-struct-compiler to rebuild

from pkg_resources import parse_version
from modules.SIGA.kaitaistruct import __version__ as ks_version, KaitaiStruct, KaitaiStream, BytesIO


if parse_version(ks_version) < parse_version('0.7'):
    raise Exception("Incompatible Kaitai Struct Python API: 0.7 or later is required, but you have %s" % (ks_version))

class PrefetchFileInfo30(KaitaiStruct):
    def __init__(self, _io, _parent=None, _root=None):
        self._io = _io
        self._parent = _parent
        self._root = _root if _root else self
        self._read()

    def _read(self):
        self.offset_metric_array = self._io.read_u4le()
        self.number_metric_entries = self._io.read_u4le()
        self.offset_trace_chain_array = self._io.read_u4le()
        self.number_trace_chain_entries = self._io.read_u4le()
        self.offset_filepath_strings = self._io.read_u4le()
        self.size_filepath_strings = self._io.read_u4le()
        self.offset_volume_info_array = self._io.read_u4le()
        self.number_volume_info_entries = self._io.read_u4le()
        self.size_volume_info = self._io.read_u4le()
        self.unknown1 = self._io.read_bytes(8)
        self.time_last_run = [None] * (8)
        for i in range(8):
            self.time_last_run[i] = self._io.read_u8le()

        self.unknown2 = self._io.read_bytes(8)
        self.count_run = self._io.read_u4le()
        self.unknown3 = self._io.read_bytes(4)
        self.unknown4 = self._io.read_bytes(4)
        self.unknown5 = self._io.read_bytes(88)


