# -*- coding: utf-8 -*-

# This is a generated file! Please edit source .ksy file and use kaitai-struct-compiler to rebuild

from pkg_resources import parse_version
from modules.SIGA.kaitaistruct import __version__ as ks_version, KaitaiStruct

if parse_version(ks_version) < parse_version('0.7'):
    raise Exception("Incompatible Kaitai Struct Python API: 0.7 or later is required, but you have %s" % (ks_version))

from modules.SIGA.formats.compressed.zip.fm_zip_local_file import ZipLocalFile
from modules.SIGA.formats.compressed.zip.fm_zip_end_of_central_dir import ZipEndOfCentralDir
from modules.SIGA.formats.compressed.zip.fm_zip_central_dir_entry import ZipCentralDirEntry
from modules.SIGA.formats.compressed.zip.fm_zip_data_descriptor import ZipDataDescriptor
class fm_Zip(KaitaiStruct):
    """
    .. seealso::
       Source - https://pkware.cachefly.net/webdocs/casestudies/APPNOTE.TXT
    """
    def __init__(self, _io, _parent=None, _root=None):
        self._io = _io
        self._parent = _parent
        self._root = _root if _root else self
        self._read()

    def _read(self):
        self.sections = []
        i = 0
        while not self._io.is_eof():
            self.sections.append(self._root.PkSection(self._io, self, self._root))
            i += 1


    class PkSection(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.magic = self._io.read_u2le()
            self.section_type = self._io.read_u2le()
            _on = self.section_type
            if _on == 513:
                self.body = ZipCentralDirEntry(self._io)
            elif _on == 1027:
                self.body = ZipLocalFile(self._io)
            elif _on == 1541:
                self.body = ZipEndOfCentralDir(self._io)
            elif _on == 2055:
                self.body = ZipDataDescriptor(self._io)



