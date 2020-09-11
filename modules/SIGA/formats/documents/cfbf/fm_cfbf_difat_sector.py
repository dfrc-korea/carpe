# -*- coding: utf-8 -*-

# This is a generated file! Please edit source .ksy file and use kaitai-struct-compiler to rebuild

from pkg_resources import parse_version
from modules.SIGA.kaitaistruct import __version__ as ks_version, KaitaiStruct
from enum import Enum


if parse_version(ks_version) < parse_version('0.7'):
    raise Exception("Incompatible Kaitai Struct Python API: 0.7 or later is required, but you have %s" % (ks_version))

class CfbfDifatSector(KaitaiStruct):

    class FatType(Enum):
        difat = -4
        fat = -3
        end_of_chain = -2
        unallocated = -1
    def __init__(self, _io, _parent=None, _root=None):
        self._io = _io
        self._parent = _parent
        self._root = _root if _root else self
        self._read()

    def _read(self):
        self.difat_entries = [None] * ((self._io.size() // 4 - 1))
        for i in range((self._io.size() // 4 - 1)):
            self.difat_entries[i] = self._io.read_s4le()

        self.ofs_difat_next = self._io.read_s4le()


