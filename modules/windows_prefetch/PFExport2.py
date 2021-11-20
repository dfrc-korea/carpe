import os.path, sys
from datetime import datetime

# from lib2.yjSysUtils import *
# from lib2.yjSQLite3 import TSQLite3
# from lib2.yjDateTime import *
# from lib import compressors as comp  # https://github.com/coderforlife/ms-compress/blob/master/test/compressors.py
from modules.windows_prefetch.lib.yjSysUtils import *
from modules.windows_prefetch.lib.yjSQLite3 import TSQLite3
from modules.windows_prefetch.lib.yjDateTime import *
from modules.windows_prefetch.lib import \
    compressors as comp  # https://github.com/coderforlife/ms-compress/blob/master/test/compressors.py
from modules.app_email.lib.delphi import ExtractFilePath


def exit(exit_code, msg=None):
    if debug_mode: exit_code = 0
    if msg: print(msg)
    sys.exit(exit_code)


def get_files(path, w='*'):
    """ 지정 경로의 파일목록을 구한다. """
    if os.path.isdir(path):
        import glob
        try:
            path = IncludeTrailingBackslash(path)
            return [v for v in glob.glob(path + w) if os.path.isfile(v)]
        finally:
            del glob
    else:
        return []


def _cast(buf, fmt):
    if debug_mode: assert type(buf) is bytes
    return cast(c_char_p(buf), POINTER(fmt)).contents

class TPFHeader(LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ('Version', c_uint32),
        ('Signature', c_char * 4),
        ('_Unknown1', c_uint32),
        ('FileSize', c_uint32),
        ('FileName', c_byte * 60),
        ('Hash', c_uint32),
        ('_Unknown2', c_uint32)
    ]

## Windwos 7
class TFileInfo23(LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ('FileMetricsArrayOffset', c_uint32),
        ('MetricsEntryCount', c_uint32),
        ('OffsetTraceChainsArray', c_uint32),
        ('TraceChainsArrayEntryCount', c_uint32),
        ('FilenameStringsOffset', c_uint32),
        ('FileNameStringSize', c_uint32),
        ('VolumeInfoOffset', c_uint32),
        ('VolumeNumber', c_uint32),
        ('VolumeInfoSize', c_uint32),
        ('_Unknown1', c_char * 8),
        ('LastExecutionTime', FILETIME * 1),
        ('_Unknown2', c_char * 16),
        ('ExecutionCounter', c_uint32),
        ('_Unknown3', c_uint32),
        ('_Unknown4', c_uint32),
        ('_Unknown5', c_char * 80)
    ]


class TVolumeInfo23(LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ('VolumeDevicePathOffset', c_uint32),
        ('VolumeDevicePathLen', c_uint32),
        ('VolumeCreationTime', FILETIME),
        ('VolumeSerialNumber', c_uint32),
        ('FileRefOffset', c_uint32),
        ('FileRefDataSize', c_uint32),
        ('DirStrsOffset', c_uint32),
        ('DirStrsCount', c_uint32),
        ('_Unknown1', c_uint32),
        ('_Unknown2', c_byte * 28),
        ('_Unknown3', c_uint32),
        ('_Unknown4', c_byte * 28),
        ('_Unknown5', c_uint32),
    ]


## Windows 8.1
class TFileInfo26(LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ('FileMetricsArrayOffset', c_uint32),
        ('MetricsEntryCount', c_uint32),
        ('OffsetTraceChainsArray', c_uint32),
        ('TraceChainsArrayEntryCount', c_uint32),
        ('FilenameStringsOffset', c_uint32),
        ('FileNameStringSize', c_uint32),
        ('VolumeInfoOffset', c_uint32),
        ('VolumeNumber', c_uint32),
        ('VolumeInfoSize', c_uint32),
        ('_Unknown1', c_char * 8),
        ('LastExecutionTime', FILETIME * 8),
        ('_Unknown2', c_char * 16),
        ('ExecutionCounter', c_uint32),
        ('_Unknown4', c_uint32 * 8),
        ('_Unknown5', c_char * 88)
    ]


class TVolumeInfo26(LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ('VolumeDevicePathOffset', c_uint32),
        ('VolumeDevicePathLen', c_uint32),
        ('VolumeCreationTime', FILETIME),
        ('VolumeSerialNumber', c_uint32),
        ('FileRefOffset', c_uint32),
        ('FileRefDataSize', c_uint32),
        ('DirStrsOffset', c_uint32),
        ('DirStrsCount', c_uint32),
        ('_Unknown1', c_uint32),
        ('_Unknown2', c_byte * 28),
        ('_Unknown3', c_uint32),
        ('_Unknown4', c_byte * 28),
        ('_Unknown5', c_uint32),
    ]



## Windows 10
class TFileInfo30(LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ('FileMetricsArrayOffset', c_uint32),
        ('MetricsEntryCount', c_uint32),
        ('OffsetTraceChainsArray', c_uint32),
        ('TraceChainsArrayEntryCount', c_uint32),
        ('FilenameStringsOffset', c_uint32),
        ('FileNameStringSize', c_uint32),
        ('VolumeInfoOffset', c_uint32),
        ('VolumeNumber', c_uint32),
        ('VolumeInfoSize', c_uint32),
        ('_Unknown1', c_char * 8),
        ('LastExecutionTime', FILETIME * 8),
        ('_Unknown2', c_char * 8),
        ('ExecutionCounter', c_uint32),
        ('Temp', c_uint32),
        ('Old_ExcutionCounter', c_uint32),
        ('_Unknown4', c_uint32),
        ('_Unknown5', c_char * 88)
    ]


class TVolumeInfo30(LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ('VolumeDevicePathOffset', c_uint32),
        ('VolumeDevicePathLen', c_uint32),
        ('VolumeCreationTime', FILETIME),
        ('VolumeSerialNumber', c_uint32),
        ('FileRefOffset', c_uint32),
        ('FileRefDataSize', c_uint32),
        ('DirStrsOffset', c_uint32),
        ('DirStrsCount', c_uint32),
        ('_Unknown1', c_uint32),
        ('_Unknown2', c_byte * 24),
        ('_Unknown3', c_uint32),
        ('_Unknown4', c_byte * 24),
        ('_Unknown5', c_uint32),
    ]


class TPFDecompressor:
    def __init__(self, srcfile):
        self.is_src_fileobj = type(srcfile) is not str
        self.data = self.__read_file(srcfile)

    def __decomp_MAMFile(self, file_obj):
        """ Superfetch file이나 Prefetch file의 MAM 포맷의 압축을 푼다. """
        file_obj.seek(0)
        data = file_obj.read()

        # 압축된 파일인지 확인한다.
        """
      MAM\x84 : Windows 8 이상 수퍼패치 파일
      MAM\x04 : Windows 10 프리패치 파일
        """
        try:
            id = data[0:3].decode('utf8')  # MAM
        except Exception:
            id = ''
        b1 = ord(data[3:4])  # b'\x84' , b'\x04'
        if (id != 'MAM') or (not b1 in [0x84, 0x04]):
            return None

        decomp_size = struct.unpack('<i', data[4:8])[0]
        compdata_stpos = 8
        if b1 == 0x84:
            compdata_stpos += 4

        data = data[compdata_stpos:]
        dest_data = bytearray(decomp_size)
        dest_data = comp.XpressHuffman['OpenSrc'].Decompress(data, dest_data)
        return bytes(dest_data)

    def __iscompfile(self, file_obj):
        try:
            file_obj.seek(0)
            h = file_obj.read(3).decode('utf8')
        except UnicodeDecodeError:
            h = ''
        return h == 'MAM'

    def __read_file(self, srcfile):
        file_obj = srcfile if self.is_src_fileobj else open(srcfile, 'rb')
        if self.__iscompfile(file_obj):
            data = self.__decomp_MAMFile(file_obj)
        else:
            file_obj.seek(0)
            data = file_obj.read()
        if not self.is_src_fileobj: file_obj.close()
        return data


# https://github.com/libyal/libscca/blob/master/documentation/Windows%20Prefetch%20File%20(PF)%20format.asciidoc
class TPrefetchFileParser:
    def __init__(self, srcfile, src_id, pfCTime='', pfMTime='', pfATime=''):

        is_src_fileobj = type(srcfile) is not str
        self.sid = src_id
        self.data = TDataAccess(TPFDecompressor(srcfile).data)

        if self.data.size > sizeof(TFileInfo30) + sizeof(TPFHeader):
            self.header = _cast(self.data.read(sizeof(TPFHeader)), TPFHeader)
            self.isPrefetchFile = self.header.Signature == b'SCCA'
            # if debug_mode:
            #     assert self.header.Version == 0x1e

            if self.header.Version == 0x17:
                self.fileinfo = _cast(self.data.read(sizeof(TFileInfo23)), TFileInfo23)
                self.fileName = srcfile.name if is_src_fileobj else srcfile
                if is_src_fileobj:
                    self.pfCTime = pfCTime
                    self.pfMTime = pfMTime
                    self.pfATime = pfATime
                else:
                    self.pfCTime = datetime.datetime.fromtimestamp(os.path.getctime(srcfile))
                    self.pfMTime = datetime.datetime.fromtimestamp(os.path.getmtime(srcfile))
                    self.pfATime = datetime.datetime.fromtimestamp(os.path.getatime(srcfile))
                v = ''
                for time in self.fileinfo.LastExecutionTime:
                    if time.LowDateTime and time.HighDateTime:
                        try:
                            v += ',%s' % filetime_to_datetime(FileTime(time), 0)
                        except ValueError:
                            v += ','
                self.lastExecutionTime = v.lstrip(',')

            elif self.header.Version == 0x1A:
                self.fileinfo = _cast(self.data.read(sizeof(TFileInfo26)), TFileInfo26)
                self.fileName = srcfile.name if is_src_fileobj else srcfile
                if is_src_fileobj:
                    self.pfCTime = pfCTime
                    self.pfMTime = pfMTime
                    self.pfATime = pfATime
                else:
                    self.pfCTime = datetime.datetime.fromtimestamp(os.path.getctime(srcfile))
                    self.pfMTime = datetime.datetime.fromtimestamp(os.path.getmtime(srcfile))
                    self.pfATime = datetime.datetime.fromtimestamp(os.path.getatime(srcfile))
                v = ''
                for time in self.fileinfo.LastExecutionTime:
                    if time.LowDateTime and time.HighDateTime:
                        try:
                            v += ',%s' % filetime_to_datetime(FileTime(time), 0)
                        except ValueError:
                            v += ','
                self.lastExecutionTime = v.lstrip(',')

            elif self.header.Version == 0x1e:
               self.fileinfo = _cast(self.data.read(sizeof(TFileInfo30)), TFileInfo30)
               self.fileName = srcfile.name if is_src_fileobj else srcfile
               if is_src_fileobj:
                   self.pfCTime = pfCTime
                   self.pfMTime = pfMTime
                   self.pfATime = pfATime
               else:
                   self.pfCTime = datetime.datetime.fromtimestamp(os.path.getctime(srcfile))
                   self.pfMTime = datetime.datetime.fromtimestamp(os.path.getmtime(srcfile))
                   self.pfATime = datetime.datetime.fromtimestamp(os.path.getatime(srcfile))
               v = ''
               for time in self.fileinfo.LastExecutionTime:
                   if time.LowDateTime and time.HighDateTime:
                       try:
                           v += ',%s' % filetime_to_datetime(FileTime(time), 0)
                       except ValueError:
                           v += ','
               self.lastExecutionTime = v.lstrip(',')

        else:
            self.header = None
            self.isPrefetchFile = False

    def parse(self):
        data = self.data
        fileinfo = self.fileinfo
        # AccessTime is LastExecutionTime
        result = {'PrefetchInfo': [
            ['sid', 'Name', 'CreationTime', 'ModifiedTime', 'Size', 'ProcessName', 'ProcessPath', 'RunCount',
             'AccessTime']],
                  'RunInfo': [['sid', 'FileExt', 'FileName', 'LogicalPath', 'DevicePath']],
                  'VolInfo': [['sid', 'DevicePath', 'CreationTime', 'SerialNumber', 'Directories']]
                  }
        sid = self.sid
        try:
            processName = bytes(self.header.FileName).decode('utf-16').rstrip('\x00')
        except Exception:
            processName = ''

        processPath = ''

        class TFileMetricsArrayEntry(LittleEndianStructure):
            _fields_ = [
                ('StartTime', c_uint32),
                ('Duration', c_uint32),
                ('AverageDuration', c_uint32),
                ('FileNameOffset', c_uint32),
                ('FileNameChacterCount', c_uint32),
                ('Unknown1', c_uint32),
                ('NTFSReference', c_char * 8)
            ]

        rec_set = []
        rec = []
        p = fileinfo.FileMetricsArrayOffset
        for i in range(0, fileinfo.MetricsEntryCount):
            if p > data.size: continue
            data.position = p
            fmaEntry = _cast(data.read(sizeof(TFileMetricsArrayEntry)), TFileMetricsArrayEntry)
            p = data.position
            if fileinfo.FilenameStringsOffset + fmaEntry.FileNameOffset + fmaEntry.FileNameChacterCount * 2 < data.size:
                data.position = fileinfo.FilenameStringsOffset + fmaEntry.FileNameOffset
                try:
                    fileName = data.read(fmaEntry.FileNameChacterCount * 2).decode('utf-16')
                except Exception:
                    fileName = ''

                rec.append(sid)  # sid
                rec.append(ExtractFileExt(fileName))  # FileExt
                fn = ExtractFileName(fileName)
                rec.append(fn)  # FileName
                rec.append('')  # LogicalPath
                rec.append(fileName)  # DevicePath

                if not processPath and (fn == processName):
                    processPath = ExtractFilePath(fileName)

                if debug_mode: assert len(result['RunInfo'][0]) == len(rec)
                rec_set.append(rec)

        # Volume information
        if self.header.Version == 0x17:
            volinfo = _cast(data.read(sizeof(TVolumeInfo23), offset=fileinfo.VolumeInfoOffset), TVolumeInfo23)
            data.position = fileinfo.VolumeInfoOffset + volinfo.VolumeDevicePathOffset
            try:
                volumeDevicePath = data.read(volinfo.VolumeDevicePathLen * 2).decode('utf-16').rstrip('\x00')
            except Exception:
                volumeDevicePath = ''
            # Volume information - Directory strings
            data.position = fileinfo.VolumeInfoOffset + volinfo.DirStrsOffset
            dirlist = []

        elif self.header.Version == 0x1A:
            volinfo = _cast(data.read(sizeof(TVolumeInfo26), offset=fileinfo.VolumeInfoOffset), TVolumeInfo26)
            data.position = fileinfo.VolumeInfoOffset + volinfo.VolumeDevicePathOffset
            try:
                volumeDevicePath = data.read(volinfo.VolumeDevicePathLen * 2).decode('utf-16').rstrip('\x00')
            except Exception:
                volumeDevicePath = ''
            # Volume information - Directory strings
            data.position = fileinfo.VolumeInfoOffset + volinfo.DirStrsOffset
            dirlist = []

        elif self.header.Version == 0x1e:
            volinfo = _cast(data.read(sizeof(TVolumeInfo30), offset=fileinfo.VolumeInfoOffset), TVolumeInfo30)
            data.position = fileinfo.VolumeInfoOffset + volinfo.VolumeDevicePathOffset
            try:
                volumeDevicePath = data.read(volinfo.VolumeDevicePathLen * 2).decode('utf-16').rstrip('\x00')
            except Exception:
                volumeDevicePath = ''

            # Volume information - Directory strings
            data.position = fileinfo.VolumeInfoOffset + volinfo.DirStrsOffset
            dirlist = []

        for i in range(0, volinfo.DirStrsCount):
            size = data.read(2, 'H') * 2 + 2
            try:
                dirlist.append(data.read(size).decode('utf-16').rstrip('\x00'))
            except Exception:
                continue

        result['VolInfo'].append(
            [sid, volumeDevicePath,
             filetime_to_datetime(FileTime(volinfo.VolumeCreationTime), 0),
             volinfo.VolumeSerialNumber,
             ','.join(dirlist)
             ]
        )


        # Windows 10 set Runcount
        if self.header.Version == 0x1e:
            if fileinfo.Temp == 0x00 :
                Runcount = fileinfo.Old_ExcutionCounter
            elif fileinfo.Temp != 0x00:
                Runcount = fileinfo.ExecutionCounter
        elif self.header.Version == 0x17:
            Runcount = fileinfo.ExecutionCounter
        elif self.header.Version == 0x1A:
            Runcount = fileinfo.ExecutionCounter

        result['RunInfo'].extend(rec_set)
        pfinfo = [sid, self.fileName, self.pfCTime, self.pfMTime, data.size, processName, processPath, Runcount, self.lastExecutionTime]

        #if debug_mode: assert len(result['PrefetchInfo'][0]) == len(pfinfo)
        result['PrefetchInfo'].append(pfinfo)

        return result


def printHelp():
    print(
        """
    Usage:
        >PFExport2.py <Prefetch Filename> <Output .db Filename>
        >PFExport2.py <Prefetch Path> <Output .db Filename>
        >PFExport2.py <Prefetch Filename> [/decomp]
        >python PFExport2.py
        >python PFExport2.py OUTLOOK.EXE-F1C71227.pf re.db
        >python PFExport2.py c:\samples re.db
        >python PFExport2.py OUTLOOK.EXE-F1C71227.pf /decomp
    """)


def main(fn, app_path):
    if type(fn) is str:
        src_files = []
        if os.path.isfile(fn):
            if ExtractFilePath(fn) == '':
                fn = app_path + fn
            if FileExists(fn):
                src_files.append(fn)
            else:
                exit(1, 'Error: File not found - "%s"' % fn)
        else:
            if not DirectoryExists(fn):
                exit(1, 'Error: Directory not found - "%s"' % fn)
            src_files = get_files(fn, '*.pf')
    else:
        src_files = [fn]

    i = 0
    for fn in src_files:
        prefetchParser = TPrefetchFileParser(fn, i)

        i += 1
        result = prefetchParser.parse()
        if debug_mode:
            assert (len(result.keys()) == 3) and (len(result['PrefetchInfo'][0]) == 9) and (
                        len(result['RunInfo'][0]) == 5) and (len(result['VolInfo'][0]) == 5)

        return result

if __name__ == "__main__":
    app_path = IncludeTrailingBackslash(os.path.dirname(os.path.abspath(__file__)))
    main(sys.argv, len(sys.argv))
