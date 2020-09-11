# This is a generated file! Please edit source .ksy file and use kaitai-struct-compiler to rebuild

from pkg_resources import parse_version
from modules.SIGA.kaitaistruct import __version__ as ks_version, KaitaiStruct, KaitaiStream, BytesIO


if parse_version(ks_version) < parse_version('0.7'):
    raise Exception("Incompatible Kaitai Struct Python API: 0.7 or later is required, but you have %s" % (ks_version))

class fm_AlzLocalFileHeader(KaitaiStruct):
    def __init__(self, _io, _parent=None, _root=None):
        self._io = _io
        self._parent = _parent
        self._root = _root if _root else self
        self._read()

    def _read(self):
        self.signature = self._io.read_u4le()
        self.file_name_length = self._io.read_u2le()
        self.file_attribute = self._io.read_u1()
        self.file_time_date = self._io.read_u4le()
        self.file_descriptor = self._io.read_u1()
        self.unknown1 = self._io.read_u1()
        if self.file_descriptor != 0:
            self.compresstion_method = self._io.read_u1()

        if self.file_descriptor != 0:
            self.unknown2 = self._io.read_u1()

        if self.file_descriptor != 0:
            self.file_crc = self._io.read_u4le()

        if self.file_descriptor != 0:
            _on = self.file_descriptor
            if _on == 17:
                self.compressed_size = self._io.read_u1()
            elif _on == 32:
                self.compressed_size = self._io.read_u2le()
            elif _on == 33:
                self.compressed_size = self._io.read_u2le()
            elif _on == 64:
                self.compressed_size = self._io.read_u4le()
            elif _on == 65:
                self.compressed_size = self._io.read_u4le()
            elif _on == 129:
                self.compressed_size = self._io.read_u8le()
            elif _on == 16:
                self.compressed_size = self._io.read_u1()
            elif _on == 128:
                self.compressed_size = self._io.read_u8le()

        if self.file_descriptor != 0:
            _on = self.file_descriptor
            if _on == 17:
                self.uncompressed_size = self._io.read_u1()
            elif _on == 32:
                self.uncompressed_size = self._io.read_u2le()
            elif _on == 33:
                self.uncompressed_size = self._io.read_u2le()
            elif _on == 64:
                self.uncompressed_size = self._io.read_u4le()
            elif _on == 65:
                self.uncompressed_size = self._io.read_u4le()
            elif _on == 129:
                self.uncompressed_size = self._io.read_u8le()
            elif _on == 16:
                self.uncompressed_size = self._io.read_u1()
            elif _on == 128:
                self.uncompressed_size = self._io.read_u8le()

        self.file_name = (self._io.read_bytes(self.file_name_length)).decode(u"euc-kr")
        if self.file_descriptor != 0:
            self.compressed_data = self._io.read_bytes(self.compressed_size)



