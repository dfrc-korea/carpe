import sys
from modules.app_email.lib.yjSysUtils import *


def __main(argv, argc):
    app_dir = os.path.dirname(os.path.realpath(__file__))
    fn = ''
    if argc > 1: fn = argv[1]

    if fn == '':
        print('\nUsage :\n')
        print('  >python EmailBoxParser <Filename> [-eml|-mbox|-msg|-ost|-pst]\n')
        print('  >python EmailBoxParser a.pst -pst')
        print('  >python -d EmailBoxParser a.pst -pst')
        print('  >python EmailBoxParser a.eml -eml')
        print('')
        exit(1)

    fileTypes = ['eml', 'mbox', 'msg', 'ost', 'pst']
    fileExt = ''
    for ft in fileTypes:
        if findCmdLineSwitch(argv, '-' + ft, ignoreCase=True):
            fileExt = '.' + ft
            break

    from modules.app_email.EmailBoxClass import EmailBox
    EmailBox.appDir = app_dir
    EmailBox.parse(fn, fileExt)


if sys.version_info < (3, 8):
    print('\'%s\' \r\nError: \'%s\' works on Python v3.8 and above.' % (sys.version, ExtractFileName(__file__)))
    exit(1)

if __name__ == "__main__":
    __main(sys.argv, len(sys.argv))