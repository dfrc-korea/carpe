import struct
import datetime
from . import compressors as comp  # https://github.com/coderforlife/ms-compress/blob/master/test/compressors.py
from . import Filetimes  # https://gist.github.com/Mostafa-Hamdy-Elgiar/9714475f1b3bc224ea063af81566d873

"""
  1. 압축된 수퍼패치 db file :
     - Windows 8 이상 : MAM file
     - Vista : MEMO file
     - Windows 7 : MEM0 file

  2. db 압축 방식 :
     - MAM file (Win8이상) : XPRESS_HUFF 압축
     - MEMO file (Vista) : LZNT1 (=MSCOMP_LZNT1)
     - MEM0 file (Win7) : XPRESS_HUFF 압축 (MAM file과 달리, n개이상의 블록으로 나눠서 압축되어 있음)

  3. db Magic 값
     - MAM file (Win8이상) :0x3
     - MEMO file (Vista) : ?
     - MEM0 file (Win7) : 0xE

  4. 비압축 수퍼패치 db : Windows Vista, 7 and 8 이상
     - AgAppLaunch.db , Magic :  0x5
     - AgRobust.db (Windows 7) ,  Magic : 0xE
     - AgRobust.db (Windows 8 이상) , Magic : 0xf
"""


#
# Windows Superfetch database format : https://github.com/libyal/libagdb/blob/master/documentation/Windows%20SuperFetch%20(DB)%20format.asciidoc
#

def filetime_to_datetime(filetime, inchour):
    try:
        return Filetimes.filetime_to_dt(filetime) + datetime.timedelta(hours=inchour)
    except Exception:
        return None


def _decomp_MAMFile(srcfile, destfile=''):
    """ Superfetch file이나 Prefetch file의 MAM 포맷의 압축을 푼다. """
    f = open(srcfile, 'rb')
    data = f.read()
    f.close()

    # 압축된 파일인지 확인한다.
    """
    MAX\x84 : Windows 8 이상 수퍼패치 파일
    MAX\x04 : Windows 10 프리패치 파일
  """
    id = data[0:3].decode('utf8')  # MAM
    b1 = ord(data[3:4])  # b'\x84' , b'\x04'
    if (id != 'MAM') or (not b1 in [0x84, 0x04]):
        print('[Error] Unknown format.')
        exit()

    decomp_size = struct.unpack('<i', data[4:8])[0]  # 압축 풀었을때 데이터 크기 (decomp_size)
    compdata_stpos = 8  # Signature + Total uncompressed data size
    if b1 == 0x84:  # SuperFetch 포맷이면...
        compdata_stpos += 4  # Unknown (checksum?)

    data = data[compdata_stpos:]  # 압축된 데이터 (data)
    dest_data = bytearray(decomp_size)  # 압축 푼 데이터 출력 공간을 확보한다.
    dest_data = comp.XpressHuffman['OpenSrc'].Decompress(data, dest_data)

    if destfile == '':
        return dest_data
    else:
        o = open(destfile, 'wb')
        o.write(dest_data)
        o.close()
        return True


"""
  참고! MEMO는 Vista 수퍼패치 파일인데 이는 일단 배제했음.
        MEMO는 LZNT1 압축 알고리즘이 사용된다.
"""


def _decomp_MEM0File(srcfile, destfile=''):
    """ Superfetch file의 MEM0 포맷의 압축을 푼다. """
    f = open(srcfile, 'rb')
    data = f.read()
    f.close()
    data_size = len(data)

    id = data[0:3].decode('utf8')  # MEM
    b1 = chr(ord(data[3:4]))  # 0
    if (id != 'MEM') or (b1 != '0'):
        print('[Error] Unknown format.')
        exit()

    #
    # MEM0
    #
    decomp_size = struct.unpack('<i', data[4:8])[0]  # 압축 풀었을때 데이터 크기 (decomp_size)
    default_uncompblocksize = 0x10000  # The uncompressed block size is 65536 (0x10000) or the remaining uncompressed data size for the last block.
    f_pos = 8  # 8 = Signature + Total uncompressed data size
    dest_data = b''
    while f_pos < data_size:
        comp_blocksize = struct.unpack('<i', data[f_pos:f_pos + 4])[0]  # 현재 block 압축된 데이터 크기 (comp_blocksize)
        # if __debug__:
        #   print('comp_blocksize : %d' % comp_blocksize)
        f_pos += 4
        comp_data = data[f_pos:f_pos + comp_blocksize]  # 현재 block 압축 데이터
        f_pos += comp_blocksize
        if f_pos == data_size:  # last block일때
            default_uncompblocksize = decomp_size - len(dest_data)  # last block의 압축 풀었을때 크기

        temp_data = bytearray(default_uncompblocksize)
        temp_data = comp.XpressHuffman['OpenSrc'].Decompress(comp_data, temp_data)
        if len(temp_data) == default_uncompblocksize:
            dest_data += temp_data
        else:
            assert False
            exit()

    if destfile == '':
        return dest_data
    else:
        o = open(destfile, 'wb')
        o.write(dest_data)
        o.close()
        return True


def iscompressed(srcfile, headstr=[]):
    """ Superfetch file이 압축되어 있는지 확인한다. """
    f = open(srcfile, 'rb')
    try:
        id = f.read(3).decode('utf8')
        if id == 'MEM':  # MEM0, MEMO
            c = f.read(1)
            if c in [b'0', b'O']:
                id = id + chr(c[0])
            else:
                id = 'MEM?'
        elif id != 'MAM':  # MAM
            id = ''
    except UnicodeDecodeError:
        id = '?'
    finally:
        headstr.append(id)
        f.close()
    return len(id) >= 3


def decompress(srcfile, destfile=''):
    """ 압축된 Superfetch file의 압축을 푼다. """
    headstr = []
    if iscompressed(srcfile, headstr):
        if headstr[0] == 'MAM':
            return _decomp_MAMFile(srcfile, destfile)
        else:
            return _decomp_MEM0File(srcfile, destfile)


def read_superfetchfile(srcfile, fileinfo={}):
    """ Superfetch file을 읽는다. """
    head = []
    if iscompressed(srcfile, head):
        data = decompress(srcfile)
    else:
        f = open(srcfile, 'rb')
        data = f.read()
        f.close()
    fileinfo['Comp'] = head[0]
    fileinfo['Magic'] = data[0]
    fileinfo['FileType'] = data[12]
    return data
