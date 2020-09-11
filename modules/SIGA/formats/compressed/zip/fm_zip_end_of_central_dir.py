# -*- coding: utf-8 -*-

# This is a generated file! Please edit source .ksy file and use kaitai-struct-compiler to rebuild

from pkg_resources import parse_version
from modules.SIGA.kaitaistruct import __version__ as ks_version, KaitaiStruct

if parse_version(ks_version) < parse_version('0.7'):
    raise Exception("Incompatible Kaitai Struct Python API: 0.7 or later is required, but you have %s" % (ks_version))

class ZipEndOfCentralDir(KaitaiStruct):
    def __init__(self, _io, _parent=None, _root=None):
        self._io = _io
        self._parent = _parent
        self._root = _root if _root else self
        self._read()

    def _read(self):
        self.magic = self._io.read_u2le()
        self.section_type = self._io.read_u2le()
        self.disk_of_end_of_central_dir = self._io.read_u2le()
        self.disk_of_central_dir = self._io.read_u2le()
        self.qty_central_dir_entries_on_disk = self._io.read_u2le()
        self.qty_central_dir_entries_total = self._io.read_u2le()
        self.central_dir_size = self._io.read_u4le()
        self.central_dir_offset = self._io.read_u4le()
        self.comment_len = self._io.read_u2le()
        self.comment = (self._io.read_bytes(self.comment_len)).decode(u"UTF-8")


