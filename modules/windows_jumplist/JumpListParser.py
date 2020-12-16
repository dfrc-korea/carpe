import os.path, sys

from modules.windows_jumplist.consts import *
from ctypes import *
from modules.windows_jumplist.lib.delphi import *
from modules.windows_jumplist.lib.yjSysUtils import *
from modules.windows_jumplist.lib.yjDateTime import *
from modules.windows_jumplist.LNKFileParser import TLNKFileParser
from modules.windows_jumplist.lib import olefile     # https://pypi.org/project/olefile/
from modules.windows_jumplist.lib.yjSQLite3 import TSQLite3

def exit(exit_code, msg = None):
  if debug_mode: exit_code = 0
  if msg: print(msg)
  sys.exit(exit_code)

def split_filename(fn):
    """ 경로가 포함된 파일명 텍스트를 ['경로', '파일명', '파일확장자'] 로 나눈다. """
    v = os.path.splitext(fn)
    fileext = v[1]
    v = os.path.split(v[0])
    if (fileext == '') and (len(v[1]) > 0) and (v[1][0] == '.'):
        v = list(v)
        fileext = v[1]
        v[1] = ''
    return [v[0], v[1], fileext]

def get_files(path, w = '*'):
    """ 지정 경로의 파일목록을 구한다. """
    if os.path.isdir(path):
        import glob
        try:
            path = IncludeTrailingBackslash(path)
            return  [v for v in glob.glob(path + w) if os.path.isfile(v)]
        finally:
            del glob
    else: return []

fileext_customdestination = '.customdestinations-ms'
fileext_automaticdestinations = '.automaticdestinations-ms'

FILE_ATTRIBUTE_READONLY = 0x00000001
FILE_ATTRIBUTE_HIDDEN = 0x00000002
FILE_ATTRIBUTE_SYSTEM = 0x00000004
FILE_ATTRIBUTE_DIRECTORY = 0x00000010
FILE_ATTRIBUTE_ARCHIVE = 0x00000020

# DestListEntry : https://bonggang.tistory.com/120
class TDestListEntry(LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ('Checksum', c_uint64),
        ('NewVolumeID', c_ubyte * 16),
        ('NewObjectID', c_ubyte * 16),
        ('BirthVolumeID', c_ubyte * 16),
        ('BirthObjectID', c_ubyte * 16),
        ('NetBIOSName', c_char * 16),
        ('EntryID', c_uint32),
        ('_f08', c_ubyte * 8),
        ('last_recorded_aceess_time', c_uint64),   # FILETIME
        ('Enty_pin_status', c_uint32),             # FF FF FF FF
        ('_f11', c_uint32),                        # FF FF FF FF
        ('access_count', c_uint32),
        ('_f13', c_ubyte * 8),                     # 00 00 00 00 00 00 00 00
        ('length_of_unicode', c_uint16)
    ]

class TJumpListParser:
    appids_file = None
    def __init__(self, srcfile, src_id):

        def getProgramName():
            if not hasattr(TJumpListParser.appids_file, 'read'): return ''
            app_dict = {}
            f = TJumpListParser.appids_file
            for line in f.readlines():
                line = line.rstrip().split('\t')
                if len(line) > 1: app_dict[line[0]] = line[1]
            v = app_dict.get(split_filename(self.fileName)[1])    # split_filename : ['경로', '파일명', '파일 확장자']
            return '' if v == None else v

        def filesize(f):
            p = f.tell()
            try:
                f.seek(0, os.SEEK_END)
                return f.tell()
            finally:
                f.seek(p, os.SEEK_SET)

        if not hasattr(TJumpListParser.appids_file, 'read'):
            fn = ExtractFilePath(sys.argv[0]) + 'AppIDs.dat'
            if FileExists(fn): TJumpListParser.appids_file = open(fn, 'rt')
        self.src_id = src_id
        if hasattr(srcfile, 'read'):
            self.fileName = srcfile.name
            self.fileObject = srcfile
            self.fileCTime = ''
        else:
            self.fileName = srcfile
            self.fileObject = open(srcfile, 'rb')
            t = os.path.getctime(srcfile)
            if debug_mode: assert type(t) is float   # TDateTime
            self.fileCTime = datetime.datetime.fromtimestamp(t)
        self.fileExt = ExtractFileExt(self.fileName).lower()
        self.fileSize = filesize(self.fileObject)
        self.programName = getProgramName()

    def parse(self):
        f = self.fileObject
        fn = self.fileName
        fext = self.fileExt
        result = {'RecentFileInfo': [['sid', 'Name', 'Path', 'ProgramName', 'CreationTime', 'ModifiedTime', 'AccessTime', 'Size']],
                  'LnkData' : [['sid', 'EntryId', 'ParentIdx', 'Item', 'ItemInfo']],
                  'DestList': [['sid', 'RecordedTime', 'AccessCount', 'EntryId', 'ComputerName', 'FileName', 'FilePath', 'FileExt']]
                  }
        sid = self.src_id
        finfo = result['RecentFileInfo']
        finfo.append([sid, ExtractFileName(fn), ExtractFilePath(fn), self.programName, self.fileCTime, '', '', self.fileSize])
        if debug_mode: assert len(finfo[0]) == len(finfo[1])

        lnkData = result['LnkData']
        destList = result['DestList']
        if fext == fileext_customdestination:
            # .customdestinations-ms 파일 처리
            data = TDataAccess(f.read())
            if data.size < 30: return False
            sign_end = b'\xAB\xFB\xBF\xBA'
            sign_lnk = b'\x4C\x00\x00\x00\x01\x14\x02\x00\x00\x00\x00\x00'
            pos = 0
            bg_offset = -1
            while data.size > pos:
                data.position = pos
                sign_data = data.read(12)
                if debug_mode and not pos:
                    assert len(sign_data[8:]) == len(sign_end)
                    assert len(sign_data) == len(sign_lnk)
                if sign_data[8:] == sign_end:
                    if bg_offset > 0:
                        l = data.position - 4 - bg_offset
                        LNKFileParser = TLNKFileParser(data.read(l, offset = bg_offset), 0)
                        r = LNKFileParser.parse_data()['LinkHeaderInfo']
                        del r[0]
                        lnkData.extend(r)
                    break
                elif sign_data == sign_lnk:
                    if bg_offset >= 0:
                        data.position -= 12
                        l = data.position - bg_offset
                        LNKFileParser = TLNKFileParser(data.read(l, offset = bg_offset), 0)
                        r = LNKFileParser.parse_data()['LinkHeaderInfo']
                        del r[0]
                        lnkData.extend(r)
                        bg_offset = -1
                        pos = data.position
                    else:
                        bg_offset = data.position - 12
                        pos += 1
                        pass
                    pass
                else: pos += 1
        else:
            # .automaticdestinations-ms 파일 처리
            _tmp = {}
            if debug_mode:
                assert self.fileExt == fileext_automaticdestinations
                assert olefile.isOleFile(f)
            ole = olefile.OleFileIO(f)
            for item in ole.listdir():
                if item == ['DestList']:
                    with ole.openstream(item) as f:
                        data = TDataAccess(f.read())
                    data.position = 32
                    while True:
                        entry = data.read_recdata(TDestListEntry)
                        if not entry: break
                        try:
                            fileName = data.read(entry.length_of_unicode * 2).decode('utf-16')
                            filePath = ExtractFilePath(fileName) if fileName.find('://') == -1 else fileName
                            computerName = entry.NetBIOSName.decode('utf-8')
                            destList.append([sid, filetime_to_datetime(entry.last_recorded_aceess_time, 0),
                                             entry.access_count, entry.EntryID, computerName, ExtractFileName(fileName),
                                             filePath, ExtractFileExt(fileName).lower()])
                        except Exception:
                            pass
                        data.position += 4
                else:
                    entryid = int(item[0], 16)    # entryid는 entry.EntryID 다.
                    f = ole.openstream(item)
                    LNKFileParser = TLNKFileParser(f.read(), entryid)
                    r = LNKFileParser.parse_data()['LinkHeaderInfo']
                    del r[0]
                    lnkData.extend(r)

                    fname = ''
                    ctime = ''
                    atime = ''
                    mtime = ''
                    fattr = ''
                    fsize = ''
                    for v in r:
                        if debug_mode: assert v[0] == entryid
                        name = v[2]
                        val = v[3]
                        if (ctime == '') and (name == RS_TargetFileCreateDT): ctime = val
                        if (atime == '') and (name == RS_TargetFileAccessDT): atime = val
                        if (mtime == '') and (name == RS_TargetFileModifyDT): mtime = val
                        if (fsize == '') and (name == RS_TargetFileSize): fsize = val
                        if (fattr == '') and (name == RS_TargetFileProp): fattr = val
                        if (fname == '') and (name == 'Base Path'): fname = val
                    del r
                    fattr_str = ''
                    fattr = StrToIntDef(fattr, 0)
                    if fattr:
                        if (fattr & FILE_ATTRIBUTE_ARCHIVE): fattr_str += 'A'
                        if (fattr & FILE_ATTRIBUTE_READONLY): fattr_str += 'R'
                        if (fattr & FILE_ATTRIBUTE_DIRECTORY): fattr_str += 'D'
                        if (fattr & FILE_ATTRIBUTE_SYSTEM): fattr_str += 'S'
                        if (fattr & FILE_ATTRIBUTE_HIDDEN): fattr_str += 'H'
                        fattr_str = '%s (%x)' % (fattr_str, fattr)
                    del fattr
                    _tmp[entryid] = {'CreatedTime': ctime,
                                     'ModifiedTime': mtime,
                                     'AccessedTime': atime,
                                     'FileAttr': fattr_str,
                                     'FileSize': fsize,
                                    }
            if len(destList) > 1:
                if debug_mode: assert self.fileExt == fileext_automaticdestinations
                for i, r in enumerate(destList):
                    if i == 0:
                        if debug_mode: assert r[3] == 'EntryId'
                        r.extend(list(_tmp[entryid].keys()))    # 필드 확장
                        continue
                    entryid = r[3]
                    try:
                        v = list(_tmp[entryid].values())
                    except Exception as e:
                        v = ['', '', '', '', '']
                    r.extend(v)
            del _tmp

        if len(lnkData) > 1:
            for i, rec in enumerate(lnkData):
                if i == 0: continue
                rec.insert(0, sid)   # sid

        if debug_mode:
            if len(destList) > 1: assert len(destList[0]) == 8 + 5
            if len(lnkData) > 1: assert (len(lnkData[0]) == 5) and (len(lnkData[1]) == 5)
        return result

def printHelp():
    print(
    r"""
    Usage:
       JumpListParser.py <.automaticDestinations-ms file> <Output .db Filename>
       JumpListParser.py <.customDestination-ms file> <Output .db Filename>
       JumpListParser.py <Path> <Output .db Filename>

       >python JumpListParser.py
       >python JumpListParser.py 9d1f905ce5044aee.automaticDestinations-ms re.db
       >python JumpListParser.py 28c8b86deab549a1.customDestinations-ms re.db       
       >python JumpListParser.py c:\jumplist_samples re.db
    """)


def main(file, app_path):
    fn = file
    # 처리할 소스 파일(src_files)을 구한다.
    src_files = []
    #src_files.append(fn)
    if os.path.isfile(fn):
        if ExtractFilePath(fn) == '': fn = app_path + fn
        if FileExists(fn): src_files.append(fn)
        else: exit(1, 'Error: File not found - "%s"' % fn)
    else:
        if not DirectoryExists(fn): exit(1, 'Error: Directory not found - "%s"' % fn)
        src_files = get_files(fn, '*.customdestination-ms')
        src_files.extend(get_files(fn, '*.automaticdestinations-ms'))

    i = 0
    for fn in src_files:
        # print(i + 1, fn if type(fn) is str else fn.name)
        JumpListParser = TJumpListParser(fn, i)
        i += 1
        result = JumpListParser.parse()
        # if debug_mode:
        #     assert (len(result['RecentFileInfo'][0]) == 8) and (len(result['LnkData'][0]) == 5)
        #     if JumpListParser.fileExt == fileext_automaticdestinations: assert len(result['DestList'][0]) == 8 + 5
        JumpListParser.fileObject.close()
    return result

"""
if sys.version_info < (3, 8):
    print('\'%s\' \r\nError: \'%s\' works on Python v3.8 and above.' % (sys.version, ExtractFileName(__file__)))
    exit(1)
"""
"""
if __name__ == "__main__":
  app_path = IncludeTrailingBackslash(os.path.dirname(os.path.abspath( __file__ )))
  main(sys.argv, len(sys.argv))
"""