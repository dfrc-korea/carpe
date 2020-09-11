import os.path
import sys
from lib import delphi as pas
from lib import superfetch

tail_slash_mark = lambda v: v + '\\' if v.find('/') == -1 else v + '/'
app_path = tail_slash_mark(os.path.dirname( os.path.abspath( __file__ ) ))  # 현재 소스 경로

fn = ''
if __debug__:
  #fn = r'C:\Users\yjlee1\Documents\VS Code\decomp\AgGlGlobalHistory.db' 
  #fn = app_path + 'F_AgGlGlobalHistory.db'
  #fn = app_path + 'AgGlGlobalHistory.db'
  ''

if fn == '':
  if len(sys.argv) >= 2:
    fn = app_path + sys.argv[1]
  else:
    print('\nUsage: <Compressed Superfetch Filename> [Output Filename]\n')
    print('>python sfdecompressor AgGlGlobalHistory.db\n')
    print('>python sfdecompressor AgGlGlobalHistory.db decoAgGlGlobalHistory.db \n')
    exit()

destfile = ''
try:    
  sys.argv[2]
except IndexError:
  destfile = app_path + 'result_' + pas.ExtractFileName(fn)
superfetch.decompress(fn, destfile)
exit()
