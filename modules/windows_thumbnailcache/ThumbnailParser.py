import os.path, sys
from ctypes import *
from modules.windows_thumbnailcache.lib.olefile import olefile
from modules.windows_thumbnailcache.lib.yjSysUtils import *
#from lib.yjSQLite3 import TSQLite3
import base64, hashlib


def exit(exit_code, msg=None):
    if debug_mode: exit_code = 0
    if msg: print(msg)
    sys.exit(exit_code)


def _cast(buf, fmt):
    if debug_mode: assert type(buf) is bytes
    return cast(c_char_p(buf), POINTER(fmt)).contents


signJPG = 0xD8FF
signThumbnailCacheFile = 'CMMM'
signBMP = 0x4D42


class TThumbnailCacheFileHeader(LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ('Signature', c_char * 4),  # CMMM
        ('FormatVer', c_uint32),  # $20 : FirstEntOffset=$10, $15 : FirstEntOffset=$0C
        ('CacheType', c_uint32),
        ('FirEntOffsetVx15', c_uint32),
        ('FirEntOffsetVx20', c_uint32),
        ('Unknown', c_uint32)
    ]


class TThumbnailCacheEntHeaderCommon(LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ('Signature', c_char * 4),  # CMMM
        ('EntLen', c_uint32),
        ('Unknown1', c_byte * 8),
        ('NameLen', c_uint32),
        ('ThumbnailOffset', c_uint32),
        ('ThumbnailLen', c_uint32)
    ]


class TThumbnailCacheEntHeader15(LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ('HC', TThumbnailCacheEntHeaderCommon),
        ('Unknown2', c_byte * 20)
    ]


class TThumbnailCacheEntHeader20(LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ('HC', TThumbnailCacheEntHeaderCommon),
        ('ThumbnailResX', c_uint32),
        ('ThumbnailResY', c_uint32),
        ('Unknown2', c_byte * 20)
    ]


class TThumbsFileParser:
    def __init__(self, fileName, exportDirName, src_id=None):
        self.fileName = fileName
        self.exportDirName = exportDirName
        self.one = None
        err = False
        if olefile.isOleFile(fileName):
            self.ole = olefile.OleFileIO(fileName)
            self.header = None
        else:
            self.ole = None
            try:
                with open(fileName, 'rb') as f:
                    data = f.read()
                    if len(data) <= sizeof(TThumbnailCacheFileHeader):
                        err = True
                        return
                    self.data = TDataAccess(data)
                self.header = _cast(self.data.read(sizeof(TThumbnailCacheFileHeader)), TThumbnailCacheFileHeader)
                if self.header.Signature.decode('utf-8') != signThumbnailCacheFile:
                    err = True
                    return
            finally:
                if err: self.header = None

    def parse(self, sep):
        #print(sep)
        dirname = self.exportDirName
        result = {'ThumbsData': [['Name', 'filesize', 'imagetype', 'Data', 'SHA1']]}
        thumbsData = result['ThumbsData']
        if sep == 'ole':
            ole = self.ole
            i = 0
            for item in ole.listdir():
                name = item[0]
                #print('>', name, end='')
                rec = []
                rec.append(name)
                with ole.openstream(item) as f:
                    f = ole.openstream(item)
                    data = f.read(100)
                    p = data.find(struct.pack('H', signJPG))
                    if p == -1: continue
                    f = ole.openstream(item)
                    data = TDataAccess(f.read()).data[p:]
                i += 1
                rec.append(data)  # Data
                h = hashlib.sha1()
                h.update(data)
                rec.append(h.hexdigest())  # SHA1
                thumbsData.append(rec)
                if dirname:
                    CreateDir(dirname)
                    with open('%s%c%s.jpg' % (dirname, PathDelimiter, name), 'wb') as f:
                        #print(' - exported', end='')
                        f.write(data)
                #print('')
            #print('\r\nWindows XP Version Exported. - %d files\r\n' % i)

        else:
            size_ThumbnailCacheEntHeader15 = sizeof(TThumbnailCacheEntHeader15)
            size_ThumbnailCacheEntHeader20 = sizeof(TThumbnailCacheEntHeader20)
            if debug_mode: assert size_ThumbnailCacheEntHeader15 == 48
            data = self.data
            dirname = self.exportDirName
            fmtver = self.header.FormatVer
            #            result = {'ThumbsData': [['Name', 'ResXY', 'ImgType', 'Data', 'SHA1']] }
            #           thumbsData = result['ThumbsData']

            fmtver = self.header.FormatVer
            if fmtver == 0x15:
                nextOffset = self.header.FirEntOffsetVx15
                entHeaderSize = size_ThumbnailCacheEntHeader15
                typeEntHeaderRecord = TThumbnailCacheEntHeader15
            else:
                if debug_mode: assert fmtver in [0x1f, 0x20]
                nextOffset = self.header.FirEntOffsetVx20
                entHeaderSize = size_ThumbnailCacheEntHeader20
                typeEntHeaderRecord = TThumbnailCacheEntHeader20
            data.position = nextOffset
            i = 0
            while data.position < data.size:
                data.position = nextOffset
                buf = data.read(entHeaderSize)
                eh = _cast(buf, typeEntHeaderRecord)
                hc = _cast(buf, TThumbnailCacheEntHeaderCommon)
                if hc.Signature.decode('utf-8') != signThumbnailCacheFile: break

                nextOffset = (data.position - entHeaderSize) + hc.EntLen
                if (hc.EntLen == 0) or (nextOffset >= data.size): break
                if (hc.NameLen == 0) or (hc.ThumbnailLen == 0): continue
                ThumbnailName = data.read(hc.NameLen).decode('utf-16').translate(
                    str.maketrans('?:\\/', '????')).replace('?', '')
                #print(ThumbnailName, end='')

                if hc.ThumbnailOffset > 0: data.position += hc.ThumbnailOffset
                buf = data.read(hc.ThumbnailLen)
                sign = TDataAccess(buf).read(2, 'H')
                if sign == signJPG:
                    imgType = 'JPG'
                elif sign == signBMP:
                    imgType = 'BMP'
                else:
                    imgType = 'PNG'

                if fmtver == 0x15:
                    ThumbnailSize = ''
                else:
                    ThumbnailSize = '%dx%d' % (eh.ThumbnailResX, eh.ThumbnailResY)

                i += 1
                rec = []
                rec.append(ThumbnailName)  # Name
                rec.append(ThumbnailSize)  # filesize(ResXY)
                rec.append(imgType)  # ImgType
                #print(buf)
                rec.append(buf)  # Data
                h = hashlib.sha1()
                h.update(buf)
                rec.append(h.hexdigest())  # SHA1
                thumbsData.append(rec)
                if dirname:
                    CreateDir(dirname)
                    fn = ThumbnailName + '.' + imgType.lower()
                    with open('%s%c%s' % (dirname, PathDelimiter, fn), 'wb') as f:
                        #print(' - exported', end='')
                        f.write(buf)
                #print('')

            #print('\r\nWindows 10 Version Exported. - %d files\r\n' % i)
        return result


def printHelp():
    print(
        r"""
        Usage:
           ThumbnailParser.py <thumbs.db Filename> <Output .db Filename> [/export:<Path to export>]
    
           >python ThumbnailParser.py
           >python ThumbnailParser.py c:\samples\thumbs.db re.db
           >python ThumbnailParser.py c:\samples\thumbs.db re.db /export:c:\export_dir     ; thumbs.db의 이미지들을 지정 폴더(/export)에 저장한다.
        """)


def main(srcfile, app_path, export_dir):
    # argc = len(argv)
    # if argc <= 2:
    #     printHelp()
    #     exit(0)

    # optExport = '/export:'
    # export_dir = None
    # optExport = findCmdLineSwitch(argv, optExport)
    # if optExport:
    #     export_dir = ExcludeTrailingBackslash(optExport)
    #     if os.path.isfile(export_dir): exit(1, "Error: It's file")

    #fn = argv[1]
    fn = srcfile
    # 처리할 소스 파일(src_files)을 구한다.
    src_files = []
    if ExtractFilePath(fn) == '': fn = app_path + fn
    if FileExists(fn):
        src_files.append(fn)
    else:
        exit(1, 'Error: File not found - "%s"' % fn)
    '''
    dest_file = argv[2]
    if ExtractFilePath(dest_file) == '': dest_file = app_path + dest_file
    '''
    '''
    # 결과 db를 생성한다.
    if FileExists(dest_file): os.remove(dest_file)
    DDL = ['CREATE TABLE ThumbsData (_id integer PRIMARY KEY AUTOINCREMENT, Name VARCHAR(255), Data STRING, SHA1 VARCHAR(20));']
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
        #print(ExtractFileName(fn))
        ThumbsFileParser = TThumbsFileParser(fn, export_dir)
        if ThumbsFileParser.ole != None and ThumbsFileParser.header == None:
            result = ThumbsFileParser.parse('ole')
        elif ThumbsFileParser.ole == None and ThumbsFileParser.header != None:
            result = ThumbsFileParser.parse('cmmm')
        elif ThumbsFileParser.ole == None and ThumbsFileParser.header == None:
            print('Error: Unknown format')
            continue
        #if debug_mode:
         #   assert len(result['ThumbsData'][0]) == 3
        return result
    '''
        # 결과를 db에 저장한다.
        tables = ['ThumbsData']
        for table in tables:
            insertDatasetIntoTable(db, table, result[table])
    '''
    #print('Finished.')


# if sys.version_info < (3, 8):
#     print('\'%s\' \r\nError: \'%s\' works on Python v3.8 and above.' % (sys.version, ExtractFileName(__file__)))
#     exit(1)

# if __name__ == "__main__":
#     app_path = IncludeTrailingBackslash(os.path.dirname(os.path.abspath(__file__)))  # 현재 소스 경로
#     main(sys.argv, len(sys.argv))
