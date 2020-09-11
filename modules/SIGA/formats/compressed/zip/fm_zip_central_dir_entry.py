# -*- coding: utf-8 -*-

# This is a generated file! Please edit source .ksy file and use kaitai-struct-compiler to rebuild

from pkg_resources import parse_version
from modules.SIGA.kaitaistruct import __version__ as ks_version, KaitaiStruct, KaitaiStream, BytesIO
from enum import Enum


if parse_version(ks_version) < parse_version('0.7'):
    raise Exception("Incompatible Kaitai Struct Python API: 0.7 or later is required, but you have %s" % (ks_version))

class ZipCentralDirEntry(KaitaiStruct):

    class Compression(Enum):
        none = 0
        shrunk = 1
        reduced_1 = 2
        reduced_2 = 3
        reduced_3 = 4
        reduced_4 = 5
        imploded = 6
        deflated = 8
        enhanced_deflated = 9
        pkware_dcl_imploded = 10
        bzip2 = 12
        lzma = 14
        ibm_terse = 18
        ibm_lz77_z = 19
        ppmd = 98

    class ExtraCodes(Enum):
        zip64 = 1
        av_info = 7
        os2 = 9
        ntfs = 10
        openvms = 12
        pkware_unix = 13
        file_stream_and_fork_descriptors = 14
        patch_descriptor = 15
        pkcs7 = 20
        x509_cert_id_and_signature_for_file = 21
        x509_cert_id_for_central_dir = 22
        strong_encryption_header = 23
        record_management_controls = 24
        pkcs7_enc_recip_cert_list = 25
        ibm_s390_uncomp = 101
        ibm_s390_comp = 102
        poszip_4690 = 18064
        extended_timestamp = 21589
        infozip_unix = 30805
        infozip_unix_var_size = 30837
    def __init__(self, _io, _parent=None, _root=None):
        self._io = _io
        self._parent = _parent
        self._root = _root if _root else self
        self._read()

    def _read(self):
        self.magic = self._io.read_u2le()
        self.section_type = self._io.read_u2le()
        self.version_made_by = self._io.read_u2le()
        self.version_needed_to_extract = self._io.read_u2le()
        self.flags = self._io.read_u2le()
        self.compression_method = self._root.Compression(self._io.read_u2le())
        self.last_mod_file_time = self._io.read_u2le()
        self.last_mod_file_date = self._io.read_u2le()
        self.crc32 = self._io.read_u4le()
        self.compressed_size = self._io.read_u4le()
        self.uncompressed_size = self._io.read_u4le()
        self.file_name_len = self._io.read_u2le()
        self.extra_len = self._io.read_u2le()
        self.comment_len = self._io.read_u2le()
        self.disk_number_start = self._io.read_u2le()
        self.int_file_attr = self._io.read_u2le()
        self.ext_file_attr = self._io.read_u4le()
        self.local_header_offset = self._io.read_s4le()
        self.file_name = (self._io.read_bytes(self.file_name_len)).decode(u"UTF-8")
        self._raw_extra = self._io.read_bytes(self.extra_len)
        io = KaitaiStream(BytesIO(self._raw_extra))
        self.extra = self._root.Extras(io, self, self._root)
        self.comment = (self._io.read_bytes(self.comment_len)).decode(u"UTF-8")

    class Extras(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.entries = []
            i = 0
            while not self._io.is_eof():
                self.entries.append(self._root.ExtraField(self._io, self, self._root))
                i += 1



    class ExtraField(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.code = self._root.ExtraCodes(self._io.read_u2le())
            self.size = self._io.read_u2le()
            _on = self.code
            if _on == self._root.ExtraCodes.ntfs:
                self._raw_body = self._io.read_bytes(self.size)
                io = KaitaiStream(BytesIO(self._raw_body))
                self.body = self._root.ExtraField.Ntfs(io, self, self._root)
            elif _on == self._root.ExtraCodes.extended_timestamp:
                self._raw_body = self._io.read_bytes(self.size)
                io = KaitaiStream(BytesIO(self._raw_body))
                self.body = self._root.ExtraField.ExtendedTimestamp(io, self, self._root)
            elif _on == self._root.ExtraCodes.infozip_unix_var_size:
                self._raw_body = self._io.read_bytes(self.size)
                io = KaitaiStream(BytesIO(self._raw_body))
                self.body = self._root.ExtraField.InfozipUnixVarSize(io, self, self._root)
            else:
                self.body = self._io.read_bytes(self.size)

        class Ntfs(KaitaiStruct):
            """
            .. seealso::
               Source - https://github.com/LuaDist/zip/blob/master/proginfo/extrafld.txt#L191
            """
            def __init__(self, _io, _parent=None, _root=None):
                self._io = _io
                self._parent = _parent
                self._root = _root if _root else self
                self._read()

            def _read(self):
                self.reserved = self._io.read_u4le()
                self.attributes = []
                i = 0
                while not self._io.is_eof():
                    self.attributes.append(self._root.ExtraField.Ntfs.Attribute(self._io, self, self._root))
                    i += 1


            class Attribute(KaitaiStruct):
                def __init__(self, _io, _parent=None, _root=None):
                    self._io = _io
                    self._parent = _parent
                    self._root = _root if _root else self
                    self._read()

                def _read(self):
                    self.tag = self._io.read_u2le()
                    self.size = self._io.read_u2le()
                    _on = self.tag
                    if _on == 1:
                        self._raw_body = self._io.read_bytes(self.size)
                        io = KaitaiStream(BytesIO(self._raw_body))
                        self.body = self._root.ExtraField.Ntfs.Attribute1(io, self, self._root)
                    else:
                        self.body = self._io.read_bytes(self.size)


            class Attribute1(KaitaiStruct):
                def __init__(self, _io, _parent=None, _root=None):
                    self._io = _io
                    self._parent = _parent
                    self._root = _root if _root else self
                    self._read()

                def _read(self):
                    self.last_mod_time = self._io.read_u8le()
                    self.last_access_time = self._io.read_u8le()
                    self.creation_time = self._io.read_u8le()



        class ExtendedTimestamp(KaitaiStruct):
            """
            .. seealso::
               Source - https://github.com/LuaDist/zip/blob/master/proginfo/extrafld.txt#L817
            """
            def __init__(self, _io, _parent=None, _root=None):
                self._io = _io
                self._parent = _parent
                self._root = _root if _root else self
                self._read()

            def _read(self):
                self.flags = self._io.read_u1()
                self.mod_time = self._io.read_u4le()
                if not (self._io.is_eof()):
                    self.access_time = self._io.read_u4le()

                if not (self._io.is_eof()):
                    self.create_time = self._io.read_u4le()



        class InfozipUnixVarSize(KaitaiStruct):
            """
            .. seealso::
               Source - https://github.com/LuaDist/zip/blob/master/proginfo/extrafld.txt#L1339
            """
            def __init__(self, _io, _parent=None, _root=None):
                self._io = _io
                self._parent = _parent
                self._root = _root if _root else self
                self._read()

            def _read(self):
                self.version = self._io.read_u1()
                self.uid_size = self._io.read_u1()
                self.uid = self._io.read_bytes(self.uid_size)
                self.gid_size = self._io.read_u1()
                self.gid = self._io.read_bytes(self.gid_size)




