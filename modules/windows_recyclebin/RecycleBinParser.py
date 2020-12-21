import sys, os
from modules.windows_recyclebin.lib.delphi import *
from modules.windows_recyclebin.lib.yjSysUtils import *
from ctypes import *
import datetime
from modules.windows_recyclebin.lib import \
    Filetimes  # https://gist.github.com/Mostafa-Hamdy-Elgiar/9714475f1b3bc224ea063af81566d873
import json


class TIFileStruct(LittleEndianStructure):
    _fields_ = [
        ('Header', c_uint64),
        ('Size', c_uint64),
        ('DeletedTimeStamp', c_uint64),
    ]


def typeCast(buf, type):
    return cast(c_char_p(buf), POINTER(type)).contents


def filetime_to_datetime(filetime, inchour):
    try:
        return Filetimes.filetime_to_dt(filetime) + datetime.timedelta(hours=inchour)
    except Exception:
        return None


def getIfileInfo(fileName):
    """ $I 파일 정보를 구한다. """
    v = os.path.split(fileName)
    ifname = v[1]
    if debug_mode:
        assert ifname[:2] == '$I'
    rfname = os.path.join(v[0], '$R' + ifname[2:])
    del v

    def getType():
        if os.path.isdir(rfname):
            t = 'folder'
        else:
            if os.path.isfile(rfname):
                t = 'file'
            else:
                t = ''
        return t

    def timestamp2str(timestamp):
        try:
            v = filetime_to_datetime(timestamp, 0).isoformat()
        except OSError:
            v = '%d' % timestamp
        except Exception:
            v = ''
        return v

    dump = TDataAccess()
    try:
        dump.loadFile(fileName)
    except:
        return

    r = typeCast(dump.read(sizeof(TIFileStruct)), TIFileStruct)
    # name
    if r.Header == 2:  # WIN10
        name_len = (dump.read(4, '<L') * 2)
    else:  # WIN7
        name_len = 520
        if debug_mode:
            assert r.Header == 1
            assert os.path.getsize(fileName) == 544
    name = struct.unpack_from('<%ds' % name_len, dump.read(name_len))[0].decode('utf-16-le').rstrip('\x00').replace(
        '\\', '/')

    return {'Type': getType(), 'Name': name, 'Size': r.Size, 'Deleted_Time': timestamp2str(r.DeletedTimeStamp) + 'Z',
            '$I': ifname}


def printHelp():
    print(
        """
지정된 쓰레기통 폴더(Recycle Bin Path)의 파일들을 보여줍니다. 모든 결과는 json 포맷으로 출력됩니다.

  RecycleBinParser.py <Recycle Bin Path> [/to_file:<Output Filename>]

사용예> 
    >python RecycleBinParser.py C:\$Recycle.Bin\S-1-5-42-2867809058-3762516759-3994543984-1102                         결과를 화면에 보여줍니다.
    >python RecycleBinParser.py C:\$Recycle.Bin\S-1-5-42-2867809058-3762516759-3994543984-1102 /to_file:r.json         결과를 r.json 파일에 저장합니다.
    >python -d RecycleBinParser.py C:\$Recycle.Bin\S-1-5-42-2867809058-3762516759-3994543984-1102                      (debug mode로) 결과를 화면에 보여줍니다.
  """)


def main(fn, app_path):
    ifileInfoList = []

    ifileInfoList.append(getIfileInfo(fn))
    return ifileInfoList

