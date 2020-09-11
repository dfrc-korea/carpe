# -*- coding: utf-8 -*-

# This is a generated file! Please edit source .ksy file and use kaitai-struct-compiler to rebuild

from pkg_resources import parse_version
from modules.SIGA.kaitaistruct import __version__ as ks_version, KaitaiStruct

if parse_version(ks_version) < parse_version('0.7'):
    raise Exception("Incompatible Kaitai Struct Python API: 0.7 or later is required, but you have %s" % (ks_version))

from lego.formats.compressed.sevenzip.fm_sevenzip_signature_header import SevenzipSignatureHeader
from lego.formats.compressed.sevenzip.fm_sevenzip_start_header import SevenzipStartHeader
from lego.formats.compressed.sevenzip.fm_sevenzip_encoded_header import SevenzipEncodedHeader
class fm_Sevenzip(KaitaiStruct):
    def __init__(self, _io, _parent=None, _root=None):
        self._io = _io
        self._parent = _parent
        self._root = _root if _root else self
        self._read()

    def _read(self):
        self.signature_header = SevenzipSignatureHeader(self._io)
        self.start_header = SevenzipStartHeader(self._io)

    @property
    def encoded_header(self):
        if hasattr(self, '_m_encoded_header'):
            return self._m_encoded_header if hasattr(self, '_m_encoded_header') else None

        _pos = self._io.pos()
        self._io.seek((self.start_header.next_header_offset + 32))
        self._m_encoded_header = SevenzipEncodedHeader(self._io)
        self._io.seek(_pos)
        return self._m_encoded_header if hasattr(self, '_m_encoded_header') else None


