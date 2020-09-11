from enum import Enum


_INDENT = '    '
_WIDTH = 100
_BIG_BAR = _WIDTH * '=' + '\n'
_SMALL_BAR = _WIDTH * '-' + '\n'
_INDENTED_SMALL_BAR = _INDENT + (_WIDTH - len(_INDENT)) * '-' + '\n'


class AttributeTypeEnum(Enum):
    STANDARD_INFORMATION = 'StandardInformation'    # 0x10      16
    ATTRIBUTE_LIST = 'AttributeList'                # 0x20      32
    FILE_NAME = 'FileName'                          # 0x30      48
    OBJECT_ID= 'ObjectID'                           # 0x40      64
    SECURITY_DESCRIPTOR = 'SecurityDescriptor'      # 0x50      80
    VOLUME_NAME = 'VolumeID'                        # 0x60      96
    VOLUME_INFORMATION = 'VolumeInformation'        # 0x70      112
    DATA = 'Data'                                   # 0x80      128
    INDEX_ROOT = 'IndexRoot'                        # 0x90      144
    INDEX_ALLOCATION = 'IndexAllocation'            # 0xA0      160
    BITMAP = 'Bitmap'                               # 0xB0      176
    REPARSE_POINT = 'ReparsePoint'                  # 0xC0      192
    EA_INFORMATION = 'EAAttribute'                  # 0xD0      208
    EA = 'EA'                                       # 0xE0      224
    PROPERTY_SET = 'PropertySet'                    # 0xF0      240
    LOGGED_UTILITY_STREAM = 'LoggedUtilityStream'   # 0x100     256
    UNKNOWN = 'unkown'                              # -         -
    NONE = 'none'                                   # -         -


class AttributeTypeEnumConverter():
    _map = {
        16: AttributeTypeEnum.STANDARD_INFORMATION,
        32: AttributeTypeEnum.ATTRIBUTE_LIST,
        48: AttributeTypeEnum.FILE_NAME,
        64: AttributeTypeEnum.OBJECT_ID,
        80: AttributeTypeEnum.UNKNOWN,
        96: AttributeTypeEnum.VOLUME_NAME,
        112: AttributeTypeEnum.VOLUME_INFORMATION,
        128: AttributeTypeEnum.DATA,
        144: AttributeTypeEnum.INDEX_ROOT,
        160: AttributeTypeEnum.INDEX_ALLOCATION,
        176: AttributeTypeEnum.BITMAP,
        192: AttributeTypeEnum.REPARSE_POINT,
        208: AttributeTypeEnum.EA_INFORMATION,
        224: AttributeTypeEnum.EA,
        240: AttributeTypeEnum.PROPERTY_SET,
        256: AttributeTypeEnum.LOGGED_UTILITY_STREAM
    }

    @staticmethod
    def from_identifier(identifier):
        try:
            return AttributeTypeEnumConverter._map[identifier]
        except KeyError:
            return AttributeTypeEnum.NONE


class InumRange():
    def __init__(self, range_string):
        self.range_string = range_string
        self.ranges = self._clean_inum_range()

    def _clean_inum_range(self):
        # Perhaps do more stuff here in the future; remove doubles, sort, etc.
        cleaned = []
        ranges = self.range_string.split(',')
        for range in ranges:
            split = range.split('-')
            if len(split) == 1:
                cleaned.append((int(split[0]), int(split[0])))
            else:
                cleaned.append((int(split[0]), int(split[1])))
        return cleaned

    @property
    def iterate(self):
        for first, last in self.ranges:
            for i in range(first, last + 1):
                yield i

    @property
    def is_singular(self):
        # If there's more than one range, False
        if len(self.range) > 1:
            return False
        # There's one range. Is the range is not singular, return False
        elif len(self.range[0]) > 1:
            return False
        else:
            return True
