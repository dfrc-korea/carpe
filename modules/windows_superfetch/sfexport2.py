import os.path
import sys
import struct
from modules.windows_superfetch.lib import superfetch
from modules.windows_superfetch.lib import delphi as pas

tail_slash_mark = lambda v: v + '\\' if v.find('/') == -1 else v + '/'
app_path = tail_slash_mark(os.path.dirname(os.path.abspath(__file__)))  # 현재 소스 경로


def utf16le_str(data):
    s = ''
    if (len(data) > 1000) or ((len(data) % 2) == 1):
        return s
    for v in range(1, len(data), 1):
        if (v % 2) == 1:
            b1 = ord(data[v - 1:v])
            b2 = ord(data[v:v + 1])
            if (b2 == 0) and ((b1 < 32) or (b1 in [60, 61, 62, 63])):  # <, =, >, ?
                return ''
    try:
        s = data.decode('utf-16-le')
    except UnicodeDecodeError:
        s = ''
    return s


def getVolumeHeader(data, stpos, fileinfo):
    pos = stpos
    # Unknown01,8 | Unknown02,8 | NumberOfEntry,4 | Unknown03,4 | Unknown04,4 | Unknown05,4 | TimeStamp,8 | VolumeID,4 | Unknown06,4 | Unknown07,8 | NameLength,2 | Unknown08,2 | Padding,4 | Unknown09,4 | Unknown10,4
    pos += 8  # Unknown02
    pos += 8  # NumberOfEntry 시작점
    pos += 4  # Unknown03
    pos += 4  # Unknown04
    pos += 4  # Unknown05
    pos += 4  # TimeStamp 시작점
    ft = struct.unpack('<Q', data[pos:pos + 8])[0]
    try:
        fileinfo['Time'] = superfetch.filetime_to_datetime(ft, 0).isoformat()
    except OSError:
        fileinfo['Time'] = ''
    pos += 8  # VolumeId 시작점
    fileinfo['Volume ID'] = '0000%X%X-0000%X%X' % (data[pos + 3], data[pos + 2], data[pos + 1], data[pos])
    pos += 4  # Unknown06
    pos += 4  # Unknown07
    pos += 8  # NameLength 시작점
    l = struct.unpack('<H', data[pos:pos + 2])[0]  # volume_name 길이
    if __debug__: assert l < 255
    fileinfo['_vol_len'] = l
    pos += 2  # Unknown08
    pos += 2  # Padding 시작점
    pos += 4  # Unknown09
    pos += 4  # Unknown10
    return pos


def getVolumeHeader_0xExx38(data, stpos, fileinfo):
    pos = stpos
    # Unknown01,4 | Unknown02,4 | NumberOfEntry,4 | Unknown03,4 | Unknown04,4 | Unknown05,4 | TimeStamp,8 | VolumeID,4 | Unknown06,4 | Unknown07,4 | NameLength,2 | Unknown08,2 | Unknown09,4 | Unknown10,4
    pos += 4  # Unknown02
    pos += 4  # NumberOfEntry
    pos += 4  # Unknown03
    pos += 4  # Unknown04
    pos += 4  # Unknown05
    pos += 4  # TimeStamp 시작점
    ft = struct.unpack('<Q', data[pos:pos + 8])[0]
    try:
        fileinfo['Time'] = superfetch.filetime_to_datetime(ft, 0).isoformat()
    except OSError:
        fileinfo['Time'] = ''
    pos += 8  # VolumeId 시작점
    fileinfo['Volume ID'] = '0000%X%X-0000%X%X' % (data[pos + 3], data[pos + 2], data[pos + 1], data[pos])
    pos += 4  # Unknown06
    pos += 4  # Unknown07
    pos += 4  # NameLength 시작점
    l = struct.unpack('<H', data[pos:pos + 2])[0]  # volume_name 길이
    if __debug__: assert l < 255
    fileinfo['_vol_len'] = l
    pos += 2  # Unknown08
    pos += 2  # Unknown09
    pos += 4  # Unknown10
    return pos


def main(file_name):
    fn = file_name
    """if __debug__:    
    ''
    
  if fn == '':
    if len(sys.argv) >= 2:
      fn = sys.argv[1]
      if pas.ExtractFilePath(fn) == '':
        fn = app_path + sys.argv[1]
    else:
      print('\nUsage: <Superfetch Filename>\n')
      print('>python sfexport2 AgGlGlobalHistory.db')
      print('>python -O sfexport2 AgGlGlobalHistory.db\n')
      exit()"""

    if not pas.FileExists(fn):
        print('Error: File not found')
        exit()

    fileinfo = {}
    data = superfetch.read_superfetchfile(fn, fileinfo)
    pos = 0

    # http://www.tmurgent.com/appv/en/resources/87-tools/performance-tools/141-superfetch-tools
    """
    ?? Windows 7에서 AgCx_?.db 파일은 Windows 64비트에만 있는? 32비트에는 없음?
    ?? Windows 7에서 AgGlUAD_*.db 파일은 32비트에만 있는? 64비트에는 없음?
    !! Windows 10 64비트에는 위 AgCx_?.db, AgGlUAD_*.db 파일들이 다 존재함.

    Windows 7 (MEM0 file) :
      - Magic : 0xE, Type : 0x1
        . AgGlFaultHistory.db
        . AgGlFgAppHistory.db
        . AgGlGlobalHistory.db                
        . AgGlUAD_S-1-5-21-827085296-3822811798-1751263389-1000.db
      - Magic : 0xE, Type : 0xB
        . AgCx_SC1.db                                                  
        . AgCx_SC4.db
        . AgGlUAD_P_S-1-5-21-827085296-3822811798-1751263389-1000.db   

    Windows 8 이상 (MAM file) :
      - Magic : 0x3, Type : 0x15       
        . AgGlFaultHistory.db         
        . AgGlFgAppHistory.db
        . AgGlGlobalHistory.db      
        . AgGlUAD_S-1-5-21-3639241982-753217345-396389062-1001.db
      - Magic : 0x3, Type : 0xB 
        . AgCx_SC4.db
        . AgGlUAD_P_S-1-5-21-3639241982-753217345-396389062-1001.db    
      - Magic : 0x3 , Type : 0x13 
        . dynrespri.7db
        . cadrespri.7db         
      - Magic : 0x3 , Type : 0x16 
        . ResPriHMStaticDb.ebd                   

    압축 안되어 있는 파일 :
      - Magic : 0xE, Type : 0xE (Unk=e)
        . AgRobust.db         
      - Magic : 0xF, Type : 0xE (Unk=f)
        . AgRobust.db        
      - Magic : 0xF, Type : 0x0 (Unk=f)
        . dynreservedpri.db    ?? 이 파일은 Windows 8.x 에서만 생성되는 듯?
      -  Magic : 0x5, Type : B7 (Unk=5)
        . AgAppLaunch.db          
  """
    if __debug__:
        assert (fileinfo['Magic'] in [0x3, 0xE]) or (fileinfo['Magic'] in [0x5, 0xF])

    magic = fileinfo['Magic']
    type = fileinfo['FileType']

    # Signature,4 | FileSize,4 | HeaderSize,4 | FileType,4 | FileParams,36 | VolumeCounter,4 | TotalEnteriesInVolumes,4
    pos += 8
    header_size = struct.unpack('<i', data[pos: pos + 4])[0]
    pos += 8
    v1 = struct.unpack('<i', data[pos: pos + 4])[0]
    pos += 4
    pos = header_size
    pos += 7
    pos = pos >> 3 << 3

    proc_n = []
    fmt_type = lambda magic, type: [magic, type]
    proc_n = tuple(fmt_type(magic, type) + [v1])
    """if __debug__: 
    print('Header Pos: %d' % pos)
    print('Format Type: 0x%X, 0x%X, 0x%X\n' % (proc_n[0], proc_n[1], proc_n[2]))"""
    del magic
    del type
    """
    proc_n:
      (0x3, ?, v1) : Windows 8 이상 (MAM file)
      (0xE, ? , v1) : Windows 7 (MEM0 file)

      (0xE, 0xE, v1) : 압축 안되어 있는 파일 (Unk=e)
      (0xF, ?, v1) : 압축 안되어 있는 파일 (Unk=f)

    v1: Windows 7
      0x48 : 64 비트 버전
      0x38 : 32 비트 버전

    v1: Windows 8
      (확인안됨)

    v1: Windows 10
      0x60 : 64 비트 버전 (단, AgRobust.db는 Windows 10 64 비트라도 0x48임) 
      0x48 : 32 비트 버전
  """
    fileinfo = {}
    fileinfo['Name'] = ''
    fileinfo['Time'] = 0
    fileinfo['Volume ID'] = ''
    fileinfo['Volume Name'] = ''

    if proc_n == (0xE, 0x1, 0x48):
        pos = getVolumeHeader(data, pos, fileinfo)  # 대상파일 : AgGl*History.db  (Windows 7)
    elif proc_n == (0xE, 0x1, 0x38):
        pos = getVolumeHeader_0xExx38(data, pos, fileinfo)  # 대상파일 : AgGl*History.db  (Windows 7 x86)
    elif proc_n == (0xE, 0xB, 0x48):
        pos = getVolumeHeader(data, pos, fileinfo)  # 대상파일 : AgCx_SC?.db      (Windows 7)
    elif proc_n == (0xE, 0xB, 0x38):
        pos = getVolumeHeader_0xExx38(data, pos, fileinfo)  # 대상파일 : AgGlUAD_*.db     (Windows 7 x86)
    elif proc_n == (0x3, 0x15, 0x60):
        pos = getVolumeHeader(data, pos, fileinfo)  # 대상파일 : AgGl~History.db
    elif proc_n == (0x3, 0x0B, 0x60):
        pos = getVolumeHeader(data, pos, fileinfo)  # 대상파일 : AgCx_SC?.db
    elif proc_n == (0x3, 0x13, 0x60):
        pos = getVolumeHeader(data, pos, fileinfo)  # 대상파일 : dynrespri.7db, cadrespri.7db
    elif proc_n == (0x3, 0x16, 0x60):  # 대상파일 : ResPriHMStaticDb.ebd
        pos = getVolumeHeader(data, pos, fileinfo)
        p = data.find('Volume Serial Number :'.encode('utf-16-le'), pos, pos + 1024)  # Volume Serial Number : 1
        if p != -1:
            pos = p
            p = data.find(b'\x00\x00\x00', p + 10)  # 문자열 끝위치(utf-16-le). 만약 문자열 끝이 '1'이라면, 31 00 00 00 이 된다.
            b = data[pos:p + 1]
            if __debug__: assert ((p + 1) - pos) == len(b)
            v = b.decode('utf-16-le')
            if fileinfo['_vol_len'] != len(v):
                print('Error: Wrong format')
                exit()
            fileinfo['Volume Name'] = v
            pos += len(b)
    elif proc_n == (0xE, 0xE, 0x38):
        pos = getVolumeHeader_0xExx38(data, pos, fileinfo)  # 대상파일 : AgRobust.db  (Windows 7 x86)
    elif proc_n == (0xE, 0xE, 0x48):
        pos = getVolumeHeader(data, pos, fileinfo)  # 대상파일 : AgRobust.db  (Windows 7)
    elif proc_n == (0xF, 0xE, 0x48):
        pos = getVolumeHeader(data, pos, fileinfo)  # 대상파일 : AgRobust.db  (Windows 8 이상)
    elif proc_n == (0xF, 0x0, 0x48):
        pos = getVolumeHeader(data, pos, fileinfo)  # 대상파일 : dynreservedpri.db  (Windows 8)
    else:
        print('Error: Unknown format')
        return False

    # db 이름
    if (proc_n[0] == 0xE) and (proc_n[1] == 0x1):
        fileinfo['Name'] = data[244:data.find(b'\x00', 244)].decode('utf8')
    elif (proc_n[0] == 0x3) and (proc_n[1] == 0x15):
        fileinfo['Name'] = data[252:data.find(b'\x00', 252)].decode('utf8')
    if fileinfo['Name'] == '': fileinfo['Name'] = pas.ExtractFileName(fn) + '?'

    result = dict()
    result['reference_point'] = list()
    result['file_info'] = None

    volume_name = ''
    if fileinfo['Volume Name'] == '': volume_name = '!'
    if __debug__: cnt = 0
    while True:
        pos = data.find(b'\x5C\x00', pos)  # \WINDOWS\... , \USERS\... , \...
        if pos == -1:
            break
        v = ord(data[pos + 2:pos + 3])
        if (v < 32) or (v > 126):
            pos += 3
            continue

        p = data.find(b'\x00\x00\x00', pos)  # 문자열(utf-16-le) 끝위치
        b = data[pos:p + 1]
        if __debug__: assert ((p + 1) - pos) == len(b)
        v = utf16le_str(b)
        if v != '':
            if volume_name == '!':
                volume_name = ''
                assert fileinfo['Volume Name'] == ''
                if fileinfo['_vol_len'] != len(v):  # 결함 확인
                    print('Error: Wrong format?')
                    exit()
                fileinfo['Volume Name'] = v
            else:
                if len(v.rstrip()) > 1:
                    result['reference_point'].append(v)
            if __debug__:
                _p = data.rfind(struct.pack('<i', len(v) * 4), pos - 70, pos - 1)  # 이진 데이터(data)내 현재 문자열(v) 길이가 명시된 위치 유추
                # print('pos: %d (gap: %d)' % (_p, pos - _p))
                cnt += 1
        pos += len(b)
    # if __debug__: print('cnt : %d' % cnt)

    if fileinfo.get('_vol_len') != None: del fileinfo['_vol_len']
    # print('\n%s\n' % fileinfo)
    result['file_info'] = fileinfo

    return result
