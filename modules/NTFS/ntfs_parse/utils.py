from binascii import hexlify
from datetime import datetime, timedelta


_FILETIME_ORIGIN = datetime(1601, 1, 1)


def reverse(byte_string):
    arr = bytearray(byte_string)
    arr.reverse()
    return arr


def reverse_hexlify(byte_string):
    arr = bytearray(byte_string)
    arr.reverse()
    return hexlify(arr)


def reverse_hexlify_int(byte_string):
    arr = bytearray(byte_string)
    if arr == b'':
        return 0
    else:
        arr.reverse()
        return int(hexlify(arr), 16)


def filetime_to_datetime(byte_string):
    arr = bytearray(byte_string)
    arr.reverse()
    return _FILETIME_ORIGIN + timedelta(microseconds=int(hexlify(arr), 16) / 10)


def interpret(data):
    interpreted_data = ''
    for byte in range(len(data)):
        try:
            interpreted_data += data[byte:byte+1].decode() if data[byte:byte+1].decode().isprintable() else '.'
        except Exception as e:
            interpreted_data += '.'
    return interpreted_data


# print function to prettify the hex printed code
def writeout_as_xxd(data, out):
    for x in range(0, len(data), 16):
        interpreted = interpret(data[x:x+16])
        data_line = str(hexlify(data[x:x+16]))[2:-1]
        print_line = ''
        for i in range(0, len(data_line), 4):
            print_line += data_line[i:i+4] + ' '
        out.write('      %07x: %-40s %s\n' % (x, print_line, interpreted))
