# This is a generated file! Please edit source .ksy file and use kaitai-struct-compiler to rebuild

from pkg_resources import parse_version
from modules.SIGA.kaitaistruct import __version__ as ks_version, KaitaiStruct, KaitaiStream, BytesIO
from enum import Enum


if parse_version(ks_version) < parse_version('0.7'):
    raise Exception("Incompatible Kaitai Struct Python API: 0.7 or later is required, but you have %s" % (ks_version))

from prefetch_file_info_30 import PrefetchFileInfo30
from prefetch_trace_chain_entry_17 import PrefetchTraceChainEntry17
from prefetch_file_info_23 import PrefetchFileInfo23
from prefetch_header_scca import PrefetchHeaderScca
from prefetch_file_references_23 import PrefetchFileReferences23
from prefetch_metric_entry_23 import PrefetchMetricEntry23
from prefetch_directory_string_entry import PrefetchDirectoryStringEntry
from prefetch_volume_info_entry_23 import PrefetchVolumeInfoEntry23
class PrefetchScca(KaitaiStruct):

    class Formats(Enum):
        win_xp = 17
        win_vista = 23
        win_8 = 26
        win_10 = 30
    def __init__(self, _io, _parent=None, _root=None):
        self._io = _io
        self._parent = _parent
        self._root = _root if _root else self
        self._read()

    def _read(self):
        self.header = PrefetchHeaderScca(self._io)
        if self.header.version == self._root.Formats.WIN_VISTA:
            self.file_info_23 = PrefetchFileInfo23(self._io)

        if self.header.version == self._root.Formats.WIN_10:
            self.file_info_30 = PrefetchFileInfo30(self._io)

        if self.header.version == self._root.Formats.WIN_VISTA:
            self.array_metric_23 = [None] * (self.file_info_23.number_metric_entries)
            for i in range(self.file_info_23.number_metric_entries):
                self.array_metric_23[i] = PrefetchMetricEntry23(self._io)


        if self.header.version.value < self._root.Formats.WIN_10.value:
            self.array_trace_chain_17 = [None] * (self.file_info_23.number_trace_chain_entries)
            for i in range(self.file_info_23.number_trace_chain_entries):
                self.array_trace_chain_17[i] = PrefetchTraceChainEntry17(self._io)


        if self.header.version == self._root.Formats.WIN_VISTA:
            self.array_filepath_string_23 = self._io.read_bytes((self.file_info_23.size_filepath_strings + 6))

        if self.header.version.value < self._root.Formats.WIN_10.value:
            self.array_volume_info_23 = [None] * (self.file_info_23.number_volume_info_entries)
            for i in range(self.file_info_23.number_volume_info_entries):
                self.array_volume_info_23[i] = PrefetchVolumeInfoEntry23(self._io)



    @property
    def volume_device_path(self):
        if hasattr(self, '_m_volume_device_path'):
            return self._m_volume_device_path if hasattr(self, '_m_volume_device_path') else None

        _pos = self._io.pos()
        self._io.seek((self.file_info_23.offset_volume_info_array + self.array_volume_info_23[0].offset_volume_device_path))
        self._m_volume_device_path = (self._io.read_bytes((self.array_volume_info_23[0].number_volume_device_path_characters * 2))).decode(u"UTF-16LE")
        self._io.seek(_pos)
        return self._m_volume_device_path if hasattr(self, '_m_volume_device_path') else None

    @property
    def array_file_reference_23(self):
        if hasattr(self, '_m_array_file_reference_23'):
            return self._m_array_file_reference_23 if hasattr(self, '_m_array_file_reference_23') else None

        _pos = self._io.pos()
        self._io.seek((self.file_info_23.offset_volume_info_array + self.array_volume_info_23[0].offset_file_references))
        self._m_array_file_reference_23 = PrefetchFileReferences23(self._io)
        self._io.seek(_pos)
        return self._m_array_file_reference_23 if hasattr(self, '_m_array_file_reference_23') else None

    @property
    def array_directory_string_23(self):
        if hasattr(self, '_m_array_directory_string_23'):
            return self._m_array_directory_string_23 if hasattr(self, '_m_array_directory_string_23') else None

        _pos = self._io.pos()
        self._io.seek((self.file_info_23.offset_volume_info_array + self.array_volume_info_23[0].offset_directory_strings))
        self._m_array_directory_string_23 = [None] * (self.array_volume_info_23[0].number_directory_strings)
        for i in range(self.array_volume_info_23[0].number_directory_strings):
            self._m_array_directory_string_23[i] = PrefetchDirectoryStringEntry(self._io)

        self._io.seek(_pos)
        return self._m_array_directory_string_23 if hasattr(self, '_m_array_directory_string_23') else None


