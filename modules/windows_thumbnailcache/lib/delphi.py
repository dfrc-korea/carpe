#
# delphi.py, 200413
#
import os
import errno

def CreateDir(dir):
    try:
        if not os.path.isdir(dir):
            os.makedirs(os.path.join(dir))
            return True
    except OSError as e:
        if e.errno != errno.EEXIST: raise
    return False

def DirectoryExists(dir):
    return os.path.isdir(dir)

def ExtractFilePath(fn):
  v = os.path.dirname(fn)
  if v == '':  return ''
  else:
    return v + PathDelimiter

def ExtractFileDir(fn):
  return os.path.dirname(fn)

def ExtractFileName(fn):
  return os.path.basename(fn)

def ExtractFileExt(fn):
  p = fn.rfind('.')
  if p == -1: return ''
  return fn[p:]

def ChangeFileExt(fn, ext):
  p = fn.rfind('.')
  if p == -1: return ''
  return fn[:p] + ext

def FileExists(fn):
  return os.path.isfile(fn)

def IncludeTrailingBackslash(v):
  return os.path.join(v, '')

def ExcludeTrailingBackslash(v):
  return v.rstrip(PathDelimiter)

IncludeTrailingPathDelimiter = IncludeTrailingBackslash
ExcludeTrailingPathDelimiter = ExcludeTrailingBackslash
PathDelimiter = '\\'
_NonPathDelimiter = '/'
if os.path.join('_', '').find(PathDelimiter) == -1: 
  PathDelimiter = '/'
  _NonPathDelimiter = '\\'
