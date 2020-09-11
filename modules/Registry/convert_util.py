def convertbe(bytes):
    result = bytes
    return result


def convertle(bytes):
    result = bytes[::-1]
    return result


def convert2mixedendian(data):
    # mixed endian 변환
    le1 = data[0:4]
    le2 = data[4:6]
    le3 = data[6:8]
    be1 = data[8:10]
    be2 = data[10:]

    guid = convertle(le1).hex() + "-" + convertle(le2).hex() + "-" + convertle(le3).hex() + "-" + convertbe(
        be1).hex() + "-" + convertbe(be2).hex()

    return guid.upper()