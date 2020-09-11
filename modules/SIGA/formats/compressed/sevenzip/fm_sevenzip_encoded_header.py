# -*- coding: utf-8 -*-

# This is a generated file! Please edit source .ksy file and use kaitai-struct-compiler to rebuild

from pkg_resources import parse_version
from modules.SIGA.kaitaistruct  import __version__ as ks_version, KaitaiStruct
from enum import Enum


if parse_version(ks_version) < parse_version('0.7'):
    raise Exception("Incompatible Kaitai Struct Python API: 0.7 or later is required, but you have %s" % (ks_version))

class SevenzipEncodedHeader(KaitaiStruct):

    class Nid(Enum):
        k_end = 0
        k_header = 1
        k_archive_properties = 2
        k_additional_streams_info = 3
        k_main_streams_info = 4
        k_files_info = 5
        k_pack_info = 6
        k_unpack_info = 7
        k_substreams_info = 8
        k_size = 9
        k_crc = 10
        k_folder = 11
        k_coders_unpack_size = 12
        k_num_unpack_stream = 13
        k_empty_stream = 14
        k_empty_file = 15
        k_anti = 16
        k_name = 17
        k_ctime = 18
        k_atime = 19
        k_mtime = 20
        k_win_attributes = 21
        k_comment = 22
        k_encoded_header = 23
        k_start_pos = 24
        k_dummy = 25
    def __init__(self, _io, _parent=None, _root=None):
        self._io = _io
        self._parent = _parent
        self._root = _root if _root else self
        self._read()

    def _read(self):
        self.nid = self._root.Nid(self._io.read_u1())
        self.pack_info = self._root.PackInfo(self._io, self, self._root)
        self.unpack_info = self._root.UnpackInfo(self._io, self, self._root)

    class PackInfo(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.nid = self._root.Nid(self._io.read_u1())
            self.pack_pos = self._io.read_bytes(4)
            self.num_pack_streams = self._io.read_u1()
            self.size = self._root.Size(self._io, self, self._root)
            self.end_nid = self._root.Nid(self._io.read_u1())


    class Crc(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.nid = self._root.Nid(self._io.read_u1())
            self.all_are_defined = self._io.read_u1()
            self.crcs = self._io.read_u4le()


    class Folder1(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.num_coders = self._io.read_u1()
            self.codec = self._root.Codec(self._io, self, self._root)


    class Size(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.nid = self._root.Nid(self._io.read_u1())
            self.pack_size = self._io.read_u2le()


    class CodersUnpackSize(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.nid = self._root.Nid(self._io.read_u1())
            self.unpack_size = self._io.read_u2le()
            self.crc = self._root.Crc(self._io, self, self._root)
            self.end_nid = self._root.Nid(self._io.read_u1())


    class Codec(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.codec_info = self._io.read_u1()
            self.codec_id = self._io.read_bytes(3)
            self.properties_size = self._io.read_u1()
            self.properties = self._io.read_bytes(self.properties_size)


    class UnpackInfo(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.nid = self._root.Nid(self._io.read_u1())
            self.folders = self._root.Folder(self._io, self, self._root)
            self.coders_unpack_size = self._root.CodersUnpackSize(self._io, self, self._root)
            self.end_nid = self._root.Nid(self._io.read_u1())


    class Folder(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.nid = self._root.Nid(self._io.read_u1())
            self.num_folders = self._io.read_u1()
            self.external = self._io.read_bytes(1)
            self.folder1s = self._root.Folder1(self._io, self, self._root)


    @property
    def debug(self):
        if hasattr(self, '_m_debug'):
            return self._m_debug if hasattr(self, '_m_debug') else None

        self._m_debug = self._io.pos()
        return self._m_debug if hasattr(self, '_m_debug') else None


