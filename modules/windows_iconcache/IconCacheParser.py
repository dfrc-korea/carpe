import os.path, sys
from ctypes import *
from modules.windows_iconcache.lib.yjSysUtils import *
#from modules.windows_iconcache.lib.yjSQLite3 import TSQLite3
import base64, hashlib

def exit(exit_code, msg = None):
    if debug_mode: exit_code = 0
    if msg: print(msg)
    sys.exit(exit_code)

def _cast(buf, fmt):
    if debug_mode: assert type(buf) is bytes
    return cast(c_char_p(buf), POINTER(fmt)).contents

signIconCacheFile = 'CMMM'
signJPG = 0xD8FF
signBMP = 0x4D42

class TIconCacheFileHeader(LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ('Signature', c_char * 4),       # CMMM
        ('FormatVer', c_uint32),         # $20 : FirstEntOffset=$10, $15 : FirstEntOffset=$0C
        ('CacheType', c_uint32),
        ('FirEntOffsetVx15', c_uint32),
        ('FirEntOffsetVx20', c_uint32),
        ('Unknown', c_uint32)
    ]

class TIconCacheEntHeaderCommon(LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ('Signature', c_char * 4),       # CMMM
        ('EntLen', c_uint32),
        ('Unknown1', c_byte * 8),
        ('NameLen', c_uint32),
        ('IconOffset', c_uint32),
        ('IconLen', c_uint32)
    ]

class TIconCacheEntHeader15(LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ('HC', TIconCacheEntHeaderCommon),
        ('Unknown2', c_byte * 20)
    ]

class TIconCacheEntHeader20(LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ('HC', TIconCacheEntHeaderCommon),
        ('IconResX', c_uint32),
        ('IconResY', c_uint32),
        ('Unknown2', c_byte * 20)
    ]

class TIconCacheFileParser:
    def __init__(self, srcfile, exportDirName, src_id = None):
        if type(srcfile) is str:
            self.fileName = srcfile
            f = open(srcfile, 'rb')
        else:
            self.fileName = srcfile.name
            f = srcfile
        self.exportDirName = exportDirName
        err = False
        try:
            data = f.read()
            if len(data) < sizeof(TIconCacheFileHeader):
                err = True
                return
            self.data = TDataAccess(data)
            self.header = _cast(self.data.read(sizeof(TIconCacheFileHeader)), TIconCacheFileHeader)
            if self.header.Signature.decode('utf-8') != signIconCacheFile:
                err = True
                return
        finally:
            if err: self.header = None

    def parse(self):
        size_IconCacheEntHeader15 = sizeof(TIconCacheEntHeader15)
        size_IconCacheEntHeader20 = sizeof(TIconCacheEntHeader20)
        if debug_mode: assert size_IconCacheEntHeader15 == 48
        data = self.data
        dirname = self.exportDirName
        fmtver = self.header.FormatVer
        result = {'ThumbsData': [['Name', 'ResXY', 'ImgType', 'Data', 'SHA1']] }
        thumbsData = result['ThumbsData']

        fmtver = self.header.FormatVer
        if fmtver == 0x15:
            nextOffset = self.header.FirEntOffsetVx15
            entHeaderSize = size_IconCacheEntHeader15
            typeEntHeaderRecord = TIconCacheEntHeader15
        else:
            if debug_mode: assert fmtver in [0x1f, 0x20]
            nextOffset = self.header.FirEntOffsetVx20
            entHeaderSize = size_IconCacheEntHeader20
            typeEntHeaderRecord = TIconCacheEntHeader20
        data.position = nextOffset
        i = 0
        while data.position < data.size:
            data.position = nextOffset
            buf = data.read(entHeaderSize)
            eh = _cast(buf, typeEntHeaderRecord)
            hc = _cast(buf, TIconCacheEntHeaderCommon)
            try:
                if hc.Signature.decode('utf-8') != signIconCacheFile:
                    break
            except UnicodeDecodeError:
                break

            nextOffset = (data.position - entHeaderSize) + hc.EntLen
            if (hc.EntLen == 0) or (nextOffset >= data.size): break
            if (hc.NameLen == 0) or (hc.IconLen == 0): continue
            iconName = data.read(hc.NameLen).decode('utf-16').translate(str.maketrans('?:\\/', '????')).replace('?', '')
            #print(iconName, end='')

            if hc.IconOffset > 0: data.position += hc.IconOffset
            buf = data.read(hc.IconLen)
            sign = TDataAccess(buf).read(2, 'H')
            if sign == signJPG: imgType = 'JPG'
            elif sign == signBMP: imgType = 'BMP'
            else: imgType = 'PNG'

            if fmtver == 0x15: iconSize = ''
            else: iconSize = '%dx%d' % (eh.IconResX, eh.IconResY)

            i += 1
            rec = []
            rec.append(iconName)                                # Name
            rec.append(iconSize)                                # ResXY
            rec.append(imgType)                                 # ImgType
            rec.append(buf)   # Data
            h = hashlib.sha1()
            h.update(buf)
            rec.append(h.hexdigest())                           # SHA1
            thumbsData.append(rec)
            if dirname:
                CreateDir(dirname)
                fn = iconName + '.' + imgType.lower()
                with open('%s%c%s' % (dirname, PathDelimiter, fn), 'wb') as f:
                    #print(' - exported', end='')
                    f.write(buf)
            #print('')
        #print('\r\nExported. - %d files\r\n' % i)
        return result


def printHelp():
    print(
        r"""
        Usage:
           IconCacheParser.py <IconCache Filename> <Output .db Filename> [/export:<Path to export>]
    
           >python IconCacheParser.py
           >python IconCacheParser.py c:\samples\iconcache_32.db re.db
           >python IconCacheParser.py c:\samples\iconcache_48.db re.db /export:c:\export_dir     ; iconcache~.db내 이미지들을 지정 폴더(/export)에 저장한다.
        """)

# def main(srcfile, app_path, export_dir = None):
#     """
#     import IconCacheParser
#     #IconCacheParser.main('c:\sample\iconcache_32.db', 'out.db')
#     #IconCacheParser.main('c:\sample\iconcache_32.db', 'out.db', 'iconcache_export')
#     with open('c:\sample\iconcache_32.db', 'rb') as f:
#       f.seek(0)
#       IconCacheParser.main(f, 'out.db')
#     """
#     #argv = [__file__, srcfile, dest_dbfile, '/export:' + export_dir if export_dir else '']
#     __main(srcfile,app_path, export_dir)

#def __main(argv, argc):
def main(srcfile, app_path, export_dir):
    # argc = len(argv)
    # if argc <= 2:
    #     printHelp()
    #     exit(0)
    #
    # optExport = '/export:'
    # export_dir = None
    # optExport = findCmdLineSwitch(argv, optExport)
    # if optExport:
    #     export_dir = ExcludeTrailingBackslash(optExport)
    #     if os.path.isfile(export_dir): exit(1, "Error: It's file")

    #fn = argv[1]
    fn = srcfile
    if type(fn) is str:
        src_files = []
        if ExtractFilePath(fn) == '': fn = app_path + fn
        if FileExists(fn): src_files.append(fn)
        else: exit(1, 'Error: File not found - "%s"' % fn)
    else:
        src_files = [fn]
    '''
    dest_file = argv[2]
    if ExtractFilePath(dest_file) == '': dest_file = app_path + dest_file

    # 결과 db를 생성한다.
    if FileExists(dest_file): os.remove(dest_file)
    DDL = ['CREATE TABLE ThumbsData (_id integer PRIMARY KEY AUTOINCREMENT, Name VARCHAR(255), ResXY VARCHAR(15), ImgType VARCHAR(6), Data STRING, SHA1 VARCHAR(20));']
    db = TSQLite3(dest_file)
    if db.conn is None:
        exit(1, 'Error: Cannot create the database connection.')
    for sql in DDL:
        db.execSQL(sql)

    def insertDatasetIntoTable(db, table, dataset):
        if len(dataset) == 1: return
        if debug_mode: assert len(dataset[0]) == len(dataset[1])
        sql = db.getInsertSQL(table, dataset[0])
        del dataset[0]
        if db.execmanySQL(sql, dataset):
            db.commit()
    '''
    #print('Processing...')
    for fn in src_files:
        #print(ExtractFileName(fn if type(fn) is str else fn.name))
        IconCacheFileParser = TIconCacheFileParser(fn, export_dir)
        if IconCacheFileParser.header == None:
            print(1, 'Error: Unknown format')
            continue
        result = IconCacheFileParser.parse()
        if debug_mode:
            assert len(result['ThumbsData'][0]) == 5
        """
        # 결과를 db에 저장한다.
        tables = ['ThumbsData']
        for table in tables:
            insertDatasetIntoTable(db, table, result[table])
        """
        return result

    #print('Finished.')

# if sys.version_info < (3, 8):
#     print('\'%s\' \r\nError: \'%s\' works on Python v3.8 and above.' % (sys.version, ExtractFileName(__file__)))
#     exit(1)
#
# if __name__ == "__main__":
#     main(sys.argv, len(sys.argv))
