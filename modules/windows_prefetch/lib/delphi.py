import os
import errno
import platform

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
  tmp_fn = fn
  if platform.system() == 'Linux':
      tmp_fn = tmp_fn.replace('\\', '/')
  elif platform.system() == 'Windows':
      tmp_fn = tmp_fn.replace('/', '\\')
  v = os.path.dirname(tmp_fn)
  if v == '':  return ''
  else:
    return v + _PathDelimiter

def ExtractFileDir(fn):
  return os.path.dirname(fn)

def ExtractFileName(fn):
  tmp_fn = fn
  if platform.system() == 'Linux':
      tmp_fn = tmp_fn.replace('\\', '/')
  elif platform.system() == 'Windows':
      tmp_fn = tmp_fn.replace('/', '\\')
  return os.path.basename(tmp_fn)

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

IncludeTrailingPathDelimiter = IncludeTrailingBackslash
_PathDelimiter = '\\'
_NonPathDelimiter = '/'
if os.path.join('_', '').find(_PathDelimiter) == -1: 
  _PathDelimiter = '/'
  _NonPathDelimiter = '\\'
