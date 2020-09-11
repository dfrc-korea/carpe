# -*- coding: utf-8 -*-

# This is a generated file! Please edit source .ksy file and use kaitai-struct-compiler to rebuild

from pkg_resources import parse_version
from modules.SIGA.kaitaistruct import __version__ as ks_version, KaitaiStruct
from enum import Enum


if parse_version(ks_version) < parse_version('0.7'):
    raise Exception("Incompatible Kaitai Struct Python API: 0.7 or later is required, but you have %s" % (ks_version))

class CfbfDirEntry(KaitaiStruct):

    class ObjType(Enum):
        unknown = 0
        storage = 1
        stream = 2
        root_storage = 5

    class RbColor(Enum):
        red = 0
        black = 1
    def __init__(self, _io, _parent=None, _root=None):
        self._io = _io
        self._parent = _parent
        self._root = _root if _root else self
        self._read()

    def _read(self):
        self.name = (self._io.read_bytes(64)).decode(u"UTF-16LE")
        self.name_len = self._io.read_u2le()
        self.object_type = self._root.ObjType(self._io.read_u1())
        self.color_flag = self._root.RbColor(self._io.read_u1())
        self.left_sibling_id = self._io.read_s4le()
        self.right_sibling_id = self._io.read_s4le()
        self.child_id = self._io.read_s4le()
        self.clsid = self._io.read_bytes(16)
        self.state = self._io.read_u4le()
        self.time_created = self._io.read_u8le()
        self.time_modified = self._io.read_u8le()
        self.ofs = self._io.read_s4le()
        self.size = self._io.read_u8le()

    @property
    def name_trancated(self):
        if hasattr(self, '_m_name_trancated'):
            return self._m_name_trancated if hasattr(self, '_m_name_trancated') else None

        _pos = self._io.pos()
        self._io.seek(0)
        self._m_name_trancated = (self._io.read_bytes((self.name_len - 2))).decode(u"UTF-16LE")
        self._io.seek(_pos)
        return self._m_name_trancated if hasattr(self, '_m_name_trancated') else None


