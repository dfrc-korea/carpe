# This is a generated file! Please edit source .ksy file and use kaitai-struct-compiler to rebuild

from pkg_resources import parse_version
from modules.SIGA.kaitaistruct import __version__ as ks_version, KaitaiStruct, KaitaiStream, BytesIO
from enum import Enum


if parse_version(ks_version) < parse_version('0.7'):
    raise Exception("Incompatible Kaitai Struct Python API: 0.7 or later is required, but you have %s" % (ks_version))

class fm_GZip(KaitaiStruct):

    class EnumCompression(Enum):
        stored = 0
        compressed = 1
        packed = 2
        lzhed = 3
        reserved_4 = 4
        reserved_5 = 5
        reserved_6 = 6
        reserved_7 = 7
        deflate = 8

    class EnumOs(Enum):
        fat_filesystem = 0
        amiga = 1
        vms = 2
        unix = 3
        vm_cms = 4
        atari_tos = 5
        hpfs_filesystem = 6
        macintosh = 7
        z_system = 8
        cpm = 9
        tops_20 = 10
        ntfs_filesystem = 11
        qdos = 12
        acorn_riscos = 13
        unknown = 255
    def __init__(self, _io, _parent=None, _root=None):
        self._io = _io
        self._parent = _parent
        self._root = _root if _root else self
        self._read()

    def _read(self):
        self.header = self._root.GzipHeader(self._io, self, self._root)
        self.compressed = self._io.read_bytes(((self._io.size() - self._io.pos()) - 8))
        self.crc32 = self._io.read_u4le()
        self.uncompressed_sized = self._io.read_u4le()

    class GzipHeader(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.magic = self._io.read_bytes(2)
            self.compression_method = self._root.EnumCompression(self._io.read_u1())
            self.flag_reserved_2bits = self._io.read_bits_int(2)
            self.flag_encrypted = self._io.read_bits_int(1) != 0
            self.flag_comment = self._io.read_bits_int(1) != 0
            self.flag_name = self._io.read_bits_int(1) != 0
            self.flag_extra = self._io.read_bits_int(1) != 0
            self.flag_continuation = self._io.read_bits_int(1) != 0
            self.flag_ascii_text = self._io.read_bits_int(1) != 0
            self._io.align_to_byte()
            self.modification_time = self._io.read_u4le()
            self.extra_flags = self._io.read_u1()
            self.operating_system = self._root.EnumOs(self._io.read_u1())
            if self.flag_continuation == True:
                self.part_number = self._io.read_u2le()

            if self.flag_extra == True:
                self.extra_len = self._io.read_u2le()

            if self.flag_extra == True:
                self.extra_bytes = self._io.read_bytes(self.extra_len)

            if self.flag_name == True:
                self.original_file_name = (self._io.read_bytes_term(0, False, True, True)).decode(u"EUC-KR")

            if self.flag_encrypted == True:
                self.encryption_header = self._io.read_bytes(12)




