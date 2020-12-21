import os.path
import struct


def findCmdSwitchInArgList(argList, switch, ignoreCase=True):
    """
    Argument List에서 command switch를 찾는다. 
  
    optViewFields = '/view_fields:'
    optDeletedRecords = '/deleted_records'
    argv = 'SQLiteParser.py external.db files /view_fields:_data,date_modified,date_added /deleted_records'.split()
    v1 = findArgSwitchInList(argv, optViewFields)       # _data,date_modified,date_added
    v2 = findArgSwitchInList(argv, optDeletedRecords)   # True
  """
    argc = len(argList)
    for i in range(1, argc):
        if ignoreCase:
            argv = argList[i].lower()
            switch = switch.lower()
        else:
            argv = argList[i]
        if argv == switch:
            return True
        elif argv.startswith(switch):
            value = argv[len(switch):]
            if value == '':
                return True
            else:
                return value
        else:
            False


class TDataAccess:
    def __init__(self, blob=''):
        self.position = 0
        self.data = blob

    def __del__(self):
        self.data = ''
        pass

    def loadFile(self, fileName):
        f = open(fileName, 'rb')
        self.data = f.read()
        f.close()
        return len(self.data)

    def read(self, length, fmt='', stPos=-1):
        """
      이진데이터(blob)내 특정 위치(stPos)의 데이터를 읽는다.  
      v = read(data, 1, 'B', pos)
      v = read(data, 4, stPos = pos)
    """
        if stPos == -1:
            stPos = self.position
        self.position = stPos + length
        blob = self.data[stPos: self.position]
        if blob != b'':
            if fmt == '':
                v = blob
            else:
                v = struct.unpack(fmt, blob)[0]
            return v
        else:
            return None

    def tell():
        return self.position
