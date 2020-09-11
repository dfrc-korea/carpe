#
# yjSysUtils.py, 200609
#
from modules.windows_thumbnailcache.lib.delphi import *
import os.path
import struct
from sys import flags, argv

#debug_mode = flags.debug == 1      # >python -d
debug_mode = __debug__             # >python -O
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

class TDataAccess:
  def __init__(self, blob = ''):
    self.position = 0
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
      이진데이터(blob)내 특정 위치(stPos)의 데이터를 읽는다.  
      v = read(1, 'B', pos)
      v = read(4, offset = pos)
    """
    if offset == -1: offset = self.position
    self.position = offset + length
    blob = self.data[offset: self.position]
    if blob != b'':
      if fmt == '': v = blob
      else: 
        if debug_mode: assert struct.calcsize(fmt) == length
        v = struct.unpack(fmt, blob)
        if len(v) == 1: v = v[0]
      return v
    else:    # 위치가 data를 벗어난 경우...
      return None

  def tell(self):
    return self.position
