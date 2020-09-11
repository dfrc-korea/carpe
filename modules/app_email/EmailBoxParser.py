import sys
from lib.yjSysUtils import *
from lib.delphi import *

def main(argv, argc):
    app_dir = os.path.dirname(os.path.realpath(__file__))
    fn = ''
    if argc > 1: fn = argv[1]

    if fn == '':
        print('\nUsage :\n')
        print('  >python -O EmailBoxParser <Filename> [-eml|-mbox|-msg|-ost|-pst]\n')
        print('  >python -O EmailBoxParser a.pst -pst')
        print('  >python -O EmailBoxParser a.eml -eml')
        print('')
        exit()
    
    fileTypes = ['eml', 'mbox', 'msg', 'ost', 'pst']
    fileExt = ''
    for ft in fileTypes:
        if findCmdSwitchInArgList(argv, '-' + ft, ignoreCase = True): 
            fileExt = '.' + ft
            break
0
    from EmailBoxClass import EmailBox
    EmailBox.appDir = app_dir3
    EmailBox.parse(fn, fileExt)

#if sys.version_info < (3, 8):
#    print('[Version Error] \'%s\'  works on Python v3.8 and above. - \r\n  Current version is \'%s\'' % (__file__, sys.version))
#    exit()

if __name__ == "__main__":
    main(sys.argv, len(sys.argv))

