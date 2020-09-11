#
# yjSysUtils.py, 200720
#
from modules.app_email.lib.delphi import *
from ctypes import sizeof, c_char_p, c_uint32, c_ushort, c_ubyte, cast, POINTER, LittleEndianStructure
import os.path
import struct
from sys import flags, argv

debug_mode = flags.debug == 1      # >python -d
#debug_mode = __debug__             # >python -O    ; -O 옵션 사용시 최적화 모드로 실행 (디버그 모드 꺼짐)
app_path = IncludeTrailingBackslash(os.getcwd())   # 현재 작업 경로
#app_path = IncludeTrailingBackslash(os.path.dirname(argv[0]))  # 메인 모듈 경로

def findCmdLineSwitch(argList, switch, ignoreCase = True):
  """ 
    Argument List에서 command switch를 찾는다. 
  
    optViewFields = '/view_fields:'
    optDeletedRecords = '/deleted_records'
    argv = 'SQLiteParser.py external.db files /view_fields:_data,date_modified,date_added /deleted_records'.split()
    v1 = findCmdLineSwitch(argv, optViewFields)       # _data,date_modified,date_added
    v2 = findCmdLineSwitch(argv, optDeletedRecords)   # True
  """
  argc = len(argList)
  for i in range(1, argc):
    if type(argList[i]) is not str: continue
    if ignoreCase:
       argv = argList[i].lower()
       switch = switch.lower()
    else:
      argv = argList[i]
    if argv == switch: return True
    elif argv.startswith(switch):
      value = argv[len(switch):]
      if value == '': return True
      else: return value
    else: False

class TGUID(LittleEndianStructure):
    _fields_ = [
        ('D1', c_uint32),
        ('D2', c_ushort),
        ('D3', c_ushort),
        ('D4', c_ubyte * 8)
    ]

def GUIDToString(v):
    '''
    사용예 :
        from ctypes import *
        class TMyRecord(LittleEndianStructure):
            _pack_ = 1
            _fields_ = [
                ('Id', TGUID),
                ...
            ]
        print(GUIDToString(myrec.Id))
    '''
    if debug_mode: assert type(v) is TGUID
    r = '%.8X-%.4X-%.4X-%.2X%.2X-%.2X%.2X%.2X%.2X%.2X%.2X' % (v.D1, v.D2, v.D3, v.D4[0], v.D4[1], v.D4[2], v.D4[3], v.D4[4], v.D4[5], v.D4[6], v.D4[7])
    return r

def _cast(buf, fmt):
    if debug_mode: assert type(buf) is bytes
    return cast(c_char_p(buf), POINTER(fmt)).contents

class TDataAccess:
  def __init__(self, blob = '', pos = 0):
    self.position = pos
    self.data = blob
    self.size = len(blob)

  def __del__(self):
    self.data = ''
    pass

  def loadFile(self, fileName):
    f = open(fileName, 'rb')
    self.data = f.read()
    self.size = len(self.data)
    f.close()
    return len(self.data)

  def read(self, length, fmt = '', offset = -1):
    """
      이진데이터(blob)내 지정 위치(offset)의 데이터를 읽는다.  
      v = read(1, 'B')
      v = read(1, 'B', pos)
      v = read(4, offset = pos)
    """
    if offset == -1: offset = self.position
    self.position = offset + length
    blob = self.data if (offset == 0) and (self.position == self.size) else self.data[offset: self.position]
    if blob != b'':
      if fmt == '': v = blob
      else: 
        if debug_mode: assert struct.calcsize(fmt) == length
        v = struct.unpack(fmt, blob)
        if len(v) == 1: v = v[0]
      return v
    else:
      return None

  def read_recdata(self, rectype, offset = -1):
    """
      이진데이터(blob)내 지정 위치(offset)의 레코드 데이터를 읽는다.  
      from ctypes import *
      class TDestListEntry(LittleEndianStructure):
        ('Checksum', c_uint64),
        ('NewVolumeID', c_ubyte * 16),
        ('NewObjectID', c_ubyte * 16)

      e = read_recdata(sizeof(TDestListEntry), TDestListEntry)
      e = read_recdata(sizeof(TDestListEntry), TDestListEntry, pos)
    """
    if debug_mode: assert rectype._pack_ == 1
    if offset == -1: offset = self.position
    self.position = offset + sizeof(rectype)
    return _cast(self.data[offset: self.position], rectype) if self.position <= self.size else None

  def tell(self):
    return self.position


import importlib
def loadModule(module_name, class_name = None):
    """ MsOxMessage = load_module('lib.msg_parser', 'MsOxMessage')  # = from lib.msg_parser import MsOxMessage """
    mod = importlib.import_module(module_name)
    if class_name == None: return mod
    else: return getattr(mod, class_name)
