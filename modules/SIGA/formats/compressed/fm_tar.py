# -*- coding: utf-8 -*-

from pkg_resources import parse_version
from modules.SIGA.kaitaistruct import __version__ as ks_version, KaitaiStruct

if parse_version(ks_version) < parse_version('0.7'):
    raise Exception("Incompatible Kaitai Struct Python API: 0.7 or later is required, but you have %s" % (ks_version))

class fm_TAR(KaitaiStruct):
    def __init__(self, _io, _parent=None, _root=None):
        self._io = _io
        self._parent = _parent
        self._root = _root if _root else self
        self._read()

    def _read(self):
        self.name = self._io.read_bytes(100)
        self.mode = self._io.read_bytes(8)
        self.uid = self._io.read_bytes(8)
        self.gid = self._io.read_bytes(8)
        self.size = (self._io.read_bytes(12)).decode(u"ASCII")
        self.mtime = self._io.read_bytes(12)
        self.chksum = self._io.read_bytes(8)
        self.typeflag = self._io.read_bytes(1)
        self.linkname = self._io.read_bytes(100)
        self.magic = self._io.read_bytes(6)
        self.version = self._io.read_bytes(2)
        self.uname = self._io.read_bytes(32)
        self.gname = self._io.read_bytes(32)
        self.devmajor = self._io.read_bytes(8)
        self.devminor = self._io.read_bytes(8)
        self.prefix = self._io.read_bytes(167)

