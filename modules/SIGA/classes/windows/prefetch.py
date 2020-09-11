# -*- coding: utf-8 -*-

import os
import io
from modules.SIGA import definitions
from modules.SIGA.classes.interface import Common

from modules.SIGA.formats.windows.prefetch.prefetch_header_mam import PrefetchHeaderMam
from modules.SIGA.formats.windows.prefetch.prefetch_header_scca import PrefetchHeaderScca
from modules.SIGA.formats.windows.prefetch.prefetch_file_info_23 import PrefetchFileInfo23
from modules.SIGA.formats.windows.prefetch.prefetch_file_info_30 import PrefetchFileInfo30
from modules.SIGA.formats.windows.prefetch.prefetch_metric_entry_23 import PrefetchMetricEntry23
from modules.SIGA.formats.windows.prefetch.prefetch_trace_chain_entry_17 import PrefetchTraceChainEntry17
from modules.SIGA.formats.windows.prefetch.prefetch_trace_chain_entry_30 import PrefetchTraceChainEntry30
from modules.SIGA.formats.windows.prefetch.prefetch_volume_info_entry_23 import PrefetchVolumeInfoEntry23
from modules.SIGA.formats.windows.prefetch.prefetch_volume_info_entry_30 import PrefetchVolumeInfoEntry30
from modules.SIGA.formats.windows.prefetch.prefetch_file_references_23 import PrefetchFileReferences23
from modules.SIGA.formats.windows.prefetch.prefetch_directory_string_entry import PrefetchDirectoryStringEntry

#from pyfwnt import *


class Prefetch(Common):
    UNIT_SECTOR_HALF = 256
    UNIT_SECTOR = 512
    SIG_MAM  = 'MAM\x04'
    SIG_SCCA = 'SCCA'

    def __init__(self, input=None):
        self.input = input
        if input:
            self.size = os.path.getsize(input)
        else:
            self.size = 0
        self.file = None
        self.data = None

        # Parsing results
        self.pf_header = None
        self.pf_file_info = None
        self.pf_array_metric = None
        self.pf_array_trace_chain = None
        self.pf_array_filepath_string = None
        self.pf_array_volume_info = None
        self.pf_array_volume_device_path = None
        self.pf_array_file_reference = None
        self.pf_array_directory_string = None

        # For external functions
        self._sig = None
        self._ext = None
        self._metadata = None
        self._text = None
        self._structure = None

    def identifyFormatFromFile(self):
        d = self._read_bytes(Prefetch.UNIT_SECTOR_HALF)

        if self._identify_fixed(d) is not None:
            self._ext = '.pf'

        return self._ext

    def identifyFormatFromMemory(self, file_object):
        
        if self._ext == None:
            return False
        
        return self._ext

    def _identify_fixed(self, d):
        header = None

        try:
            header = PrefetchHeaderMam.from_bytes(d)
            self._sig = Prefetch.SIG_MAM
        except Exception as e:
            if str(e).find("unexpected fixed contents") > 0:
                pass

        if header is None:
            try:
                header = PrefetchHeaderScca.from_bytes(d)
                self._sig = Prefetch.SIG_SCCA
            except Exception as e:
                if str(e).find("unexpected fixed contents") > 0:
                    pass

        return header

    def _identify_scanning(self, length):
        return

    def _read_bytes(self, size=0, pos=0):
        if self.file is None:
            self.file = open(self.input, 'rb')

        if size <= 0:
            size = self.size

        if pos > 0:
            self.file.seek(pos)
        d = self.file.read(size)

        self._close_file()
        return d

    def _close_file(self):
        if self.file is not None:
            self.file.close()
            self.file = None

    def _read_bytes_2(self, f, size, pos=0):
        if pos > 0:
            f.seek(pos)
        d = f.read(size)
        return d

    def validate(self):

        if self.parse() is False:
            return False

        if not self._validate_pf_header():
            return False

        # if self._validate_file_information():
        #     logger.info("validate_file_information(): 검증이 완료되었습니다.")
        # else:
        #     logger.error("validate_file_information(): 정상적인 Prefetch 파일 포맷이 아닙니다.")
        #     return False

        return definitions.VALID_SUCCESS

    def _validate_pf_header(self):

        if not self.pf_header.signature == b"SCCA":
            return False

        if self.pf_header.version == PrefetchHeaderScca.Formats.win_8 or \
                self.pf_header.version == PrefetchHeaderScca.Formats.win_10 or \
                self.pf_header.version == PrefetchHeaderScca.Formats.win_vista or \
                self.pf_header.version == PrefetchHeaderScca.Formats.win_xp:
            pass
        else:
            return False

        return True

    # def _validate_file_information(self):
    #     # TODO
    #     return True

    def get_metadata(self):
        return self._metadata

    def get_text(self):
        return self._text

    def get_structure(self):
        return self._structure

    def parse(self):

        if self._sig == Prefetch.SIG_MAM:
            h = self._read_bytes(8)
            d = self._read_bytes(self.size-8, 8)

            dw = DecompressWindows()
            d = dw.decompress(h, d)
        else:
            d = self._read_bytes()

        # Make a temp file
        tmp = open('tmp.dat', 'wb')
        tmp.write(d)
        tmp.close()

        f = io.BytesIO(d)

        # --------------------------------------------------------
        # Get the header of a SCCA file

        # t = self._read_bytes_2(f, Prefetch.UNIT_SECTOR, 0)
        # header = PrefetchHeaderScca.from_bytes(t)

        try:
            self.pf_header = PrefetchHeaderScca.from_io(f)
        except Exception as e:
            pass

        if self.pf_header is None:
            return False

        # --------------------------------------------------------
        # Get the 'file information' structure

        #logger.warning("OFFSET of file info: {}".format(f.tell()))

        if self.pf_header.version.value >= PrefetchHeaderScca.Formats.win_10.value:
            PrefetchFileInfo = PrefetchFileInfo30
        else:
            PrefetchFileInfo = PrefetchFileInfo23

        try:
            self.pf_file_info = PrefetchFileInfo.from_io(f)
        except Exception as e:
            pass

        if self.pf_file_info is None:
            return False

        # --------------------------------------------------------
        # Get the 'metric' entries (= metric array)

        #logger.warning("OFFSET of metric: {}".format(f.tell()))

        if self.pf_header.version.value >= PrefetchHeaderScca.Formats.win_vista.value:
            PrefetchMetricEntry = PrefetchMetricEntry23
        else:
            PrefetchMetricEntry = PrefetchMetricEntry23

        try:
            array = []
            f.seek(self.pf_file_info.offset_metric_array+4)  # why + 4 ? unclear
            #logger.warning("OFFSET of metric: {}".format(f.tell()))

            for idx in range(self.pf_file_info.number_metric_entries):

                array.append(PrefetchMetricEntry.from_io(f))
            self.pf_array_metric = array
        except Exception as e:
            pass

        if self.pf_array_metric is None:
            return False

        # --------------------------------------------------------
        # Get the 'trace chain' entries (= trace chain array)

        #logger.warning("OFFSET of trace chain: {}".format(f.tell()))

        if self.pf_header.version.value >= PrefetchHeaderScca.Formats.win_10.value:
            PrefetchTraceChainEntry = PrefetchTraceChainEntry30
        else:
            PrefetchTraceChainEntry = PrefetchTraceChainEntry17

        try:
            array = []
            f.seek(self.pf_file_info.offset_trace_chain_array)
            #logger.warning("OFFSET of trace chain: {}".format(f.tell()))

            for idx in range(self.pf_file_info.number_trace_chain_entries):
                array.append(PrefetchTraceChainEntry.from_io(f))
            self.pf_array_trace_chain = array
        except Exception as e:
            pass

        if self.pf_array_trace_chain is None:
            return False

        # --------------------------------------------------------
        # Get the 'filepath' strings

        #logger.warning("OFFSET of filepath: {}".format(f.tell()))

        length = self.pf_file_info.size_filepath_strings
        if f.tell() + self.pf_file_info.size_filepath_strings < \
                self.pf_file_info.offset_volume_info_array:
            length = self.pf_file_info.offset_volume_info_array - f.tell()

        try:
            array = []
            f.seek(self.pf_file_info.offset_filepath_strings)
            #logger.warning("OFFSET of filepath: {}".format(f.tell()))

            fs = f.read(length)

            path = b''
            for idx in range(0, len(fs), 2):
                two = fs[idx:idx+2]
                if two == b'\x00\x00':
                    if path != b'':
                        array.append(path.decode('utf-16le', 'ignore'))
                        path = b''
                else:
                    path += two

            self.pf_array_filepath_string = array
        except Exception as e:
            pass

        if self.pf_array_filepath_string is None:
            return False

        # --------------------------------------------------------
        # Get the 'volume information' entries (= volume information array)

        #logger.warning("OFFSET of volume info: {}".format(f.tell()))

        if self.pf_header.version.value >= PrefetchHeaderScca.Formats.win_10.value:
            PrefetchVolumeInfoEntry = PrefetchVolumeInfoEntry30
        else:
            PrefetchVolumeInfoEntry = PrefetchVolumeInfoEntry23

        try:
            array = []
            f.seek(self.pf_file_info.offset_volume_info_array)
            #logger.warning("OFFSET of volume info: {}".format(f.tell()))

            for idx in range(self.pf_file_info.number_volume_info_entries):
                array.append(PrefetchVolumeInfoEntry.from_io(f))
            self.pf_array_volume_info = array
        except Exception as e:
            pass

        if self.pf_array_volume_info is None:
            return False

        # --------------------------------------------------------
        # Get the 'volume device path' array

        #logger.warning("OFFSET: {}".format(f.tell()))

        try:
            array = []
            for vi in self.pf_array_volume_info:
                f.seek(self.pf_file_info.offset_volume_info_array + vi.offset_volume_device_path)
                #logger.warning("OFFSET of volume device path: {}".format(f.tell()))
                d = f.read(vi.number_volume_device_path_characters * 2)
                array.append(d.decode('utf-16le', 'ignore'))
            self.pf_array_volume_device_path = array
        except Exception as e:
            pass

        if self.pf_array_volume_device_path is None:
            return False

        # --------------------------------------------------------
        # Get the 'file reference' array

        #logger.warning("OFFSET: {}".format(f.tell()))
        try:
            array = []
            for vi in self.pf_array_volume_info:
                f.seek(self.pf_file_info.offset_volume_info_array + vi.offset_file_references)
                #logger.warning("OFFSET of file references: {}".format(f.tell()))
                array.append(PrefetchFileReferences23.from_io(f))
            self.pf_array_file_reference = array
        except Exception as e:
            pass

        if self.pf_array_file_reference is None:
            return False

        # --------------------------------------------------------
        # Get the 'directory string' array

        #logger.warning("OFFSET: {}".format(f.tell()))
        try:
            array = []
            for vi in self.pf_array_volume_info:
                f.seek(self.pf_file_info.offset_volume_info_array + vi.offset_directory_strings)
                #logger.warning("OFFSET of directory string: {}".format(f.tell()))
                array.append(PrefetchDirectoryStringEntry.from_io(f))
            self.pf_array_directory_string = array
        except Exception as e:
            pass

        if self.pf_array_directory_string is None:
            return False

        return True


class DecompressWindows:
    #
    # ref: https://github.com/RealityNet/hotoloti/blob/master/sas/w10pfdecomp.py
    # ref: https://docs.microsoft.com/en-us/windows-hardware/drivers/ddi/ntifs/nf-ntifs-rtlgetcompressionworkspacesize
    #

    def __init__(self):
        return

    def decompress(self, header, data):
        import ctypes
        import struct
        import binascii

        NULL = ctypes.POINTER(ctypes.c_uint)()
        SIZE_T = ctypes.c_uint
        DWORD = ctypes.c_uint32
        USHORT = ctypes.c_uint16
        UCHAR = ctypes.c_ubyte
        ULONG = ctypes.c_uint32

        # You must have at least Windows 8, or it should fail.
        try:
            RtlDecompressBufferEx = ctypes.windll.ntdll.RtlDecompressBufferEx
        except AttributeError:
            return

        try:
            RtlGetCompressionWorkSpaceSize = ctypes.windll.ntdll.RtlGetCompressionWorkSpaceSize
        except AttributeError:
            return

        signature, decompressed_size = struct.unpack('<LL', header)
        calgo = (signature & 0x0F000000) >> 24
        crcck = (signature & 0xF0000000) >> 28
        magic = signature & 0x00FFFFFF
        if magic != 0x004d414d :
            return

        if crcck:
            file_crc = struct.unpack('<L', data[:4])[0]
            crc = binascii.crc32(header)
            crc = binascii.crc32(struct.pack('<L', 0), crc)
            data = data[4:]
            crc = binascii.crc32(data, crc)
            if crc != file_crc:
                return

        compressed_size = len(data)
        ntCompressBufferWorkSpaceSize = ULONG()
        ntCompressFragmentWorkSpaceSize = ULONG()

        ntstatus = RtlGetCompressionWorkSpaceSize(
            USHORT(calgo), ctypes.byref(ntCompressBufferWorkSpaceSize),
            ctypes.byref(ntCompressFragmentWorkSpaceSize)
        )

        if ntstatus:
            return

        ntCompressed = (UCHAR * compressed_size).from_buffer_copy(data)
        ntDecompressed = (UCHAR * decompressed_size)()
        ntFinalUncompressedSize = ULONG()
        ntWorkspace = (UCHAR * ntCompressFragmentWorkSpaceSize.value)()

        ntstatus = RtlDecompressBufferEx(
            USHORT(calgo),
            ctypes.byref(ntDecompressed),
            ULONG(decompressed_size),
            ctypes.byref(ntCompressed),
            ULONG(compressed_size),
            ctypes.byref(ntFinalUncompressedSize),
            ctypes.byref(ntWorkspace)
        )

        if ntstatus:
            return

        if ntFinalUncompressedSize.value != decompressed_size:
            pass

        return bytes(ntDecompressed)
