# This is a generated file! Please edit source .ksy file and use kaitai-struct-compiler to rebuild

from pkg_resources import parse_version
from modules.SIGA.kaitaistruct import __version__ as ks_version, KaitaiStruct, KaitaiStream, BytesIO


if parse_version(ks_version) < parse_version('0.7'):
    raise Exception("Incompatible Kaitai Struct Python API: 0.7 or later is required, but you have %s" % (ks_version))

class PrefetchVolumeInfoEntry23(KaitaiStruct):
    def __init__(self, _io, _parent=None, _root=None):
        self._io = _io
        self._parent = _parent
        self._root = _root if _root else self
        self._read()

    def _read(self):
        self.offset_volume_device_path = self._io.read_u4le()
        self.number_volume_device_path_characters = self._io.read_u4le()
        self.time_volume_creation = self._io.read_u8le()
        self.volume_serial = self._io.read_u4le()
        self.offset_file_references = self._io.read_u4le()
        self.size_file_references = self._io.read_u4le()
        self.offset_directory_strings = self._io.read_u4le()
        self.number_directory_strings = self._io.read_u4le()
        self.unknows1 = self._io.read_bytes(4)
        self.unknows2 = self._io.read_bytes(28)
        self.unknows3 = self._io.read_bytes(4)
        self.unknows4 = self._io.read_bytes(28)
        self.unknows5 = self._io.read_bytes(4)


