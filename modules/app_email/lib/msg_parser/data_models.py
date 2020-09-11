# coding=utf-8
from datetime import datetime
from datetime import timedelta
from struct import unpack

from .properties import DATA_TYPE_MAP


class DataModel(object):
    def __init__(self):
        self.data_type_name = None

    @staticmethod
    def lookup_data_type_name(data_type):
        return DATA_TYPE_MAP.get(data_type)

    def get_value(self, data_value, data_type_name=None, data_type=None):

        if data_type_name:
            self.data_type_name = data_type_name
        elif data_type:
            self.data_type_name = self.lookup_data_type_name(data_type)
        else:
            raise Exception(
                "required arguments not provided to the constructor of the class."
            )

        if not hasattr(self, self.data_type_name):
            return None

        value = getattr(self, self.data_type_name)(data_value)
        return value

    @staticmethod
    def PtypUnspecified(data_value):
        return data_value

    @staticmethod
    def PtypNull(_):
        return None

    @staticmethod
    def PtypInteger16(data_value):
        return int(data_value.encode("hex"), 16)

    @staticmethod
    def PtypInteger32(data_value):
        return int(data_value.encode("hex"), 32)

    @staticmethod
    def PtypFloating32(data_value):
        return unpack("f", data_value)[0]

    @staticmethod
    def PtypFloating64(data_value):
        return unpack("d", data_value)[0]

    @staticmethod
    def PtypCurrency(data_value):
        return data_value

    @staticmethod
    def PtypFloatingTime(data_value):
        return data_value

    @staticmethod
    def PtypErrorCode(data_value):
        return unpack("I", data_value)[0]

    @staticmethod
    def PtypBoolean(data_value):
        return unpack("B", data_value[0])[0] != 0

    @staticmethod
    def PtypObject(data_value):
        if data_value and b"\x00" in data_value:
            data_value = data_value.replace(b"\x00", b"")
        return data_value

    @staticmethod
    def PtypInteger64(data_value):
        return unpack("q", data_value)[0]

    @staticmethod
    def PtypString8(data_value):
        if data_value and b"\x00" in data_value:
            data_value = data_value.replace(b"\x00", b"")
        return data_value

    """
    @staticmethod
    def PtypString(data_value):
        if data_vaue:
            data_value = data_value.decode("utf-16-le", errors="ignore").replace("\x00", "")
    """

    @staticmethod
    def PtypString(data_value):
        s = ''
        if data_value:
            try:
                s = data_value.decode('ascii')
            except UnicodeDecodeError:
                s = data_value.decode('cp949', errors='ignore')
            if s.find('\x00') != -1: s = data_value.decode("utf-16-le", errors="ignore")
        return s

    @staticmethod
    def PtypTime(data_value):
        return get_time(data_value)

    @staticmethod
    def PtypGuid(data_value):
        return data_value

    @staticmethod
    def PtypServerId(data_value):
        return data_value

    @staticmethod
    def PtypRestriction(data_value):
        return data_value

    @staticmethod
    def PtypRuleAction(data_value):
        return data_value

    @staticmethod
    def PtypBinary(data_value):
        if data_value and b"\x00" in data_value:
            data_value = data_value.replace(b"\x00", b"")
        return data_value

    @staticmethod
    def PtypMultipleInteger16(data_value):
        entry_count = int(len(data_value) / 2)
        return [unpack("h", bytes[i * 2 : (i + 1) * 2])[0] for i in range(entry_count)]

    @staticmethod
    def PtypMultipleInteger32(data_value):
        entry_count = int(len(data_value) / 4)
        return [unpack("i", bytes[i * 4 : (i + 1) * 4])[0] for i in range(entry_count)]

    @staticmethod
    def PtypMultipleFloating32(data_value):
        entry_count = int(len(data_value) / 4)
        return [unpack("f", bytes[i * 4 : (i + 1) * 4])[0] for i in range(entry_count)]

    @staticmethod
    def PtypMultipleFloating64(data_value):
        entry_count = int(len(data_value) / 8)
        return [unpack("d", bytes[i * 8 : (i + 1) * 8])[0] for i in range(entry_count)]

    @staticmethod
    def PtypMultipleCurrency(data_value):
        return data_value

    @staticmethod
    def PtypMultipleFloatingTime(data_value):
        entry_count = int(len(data_value) / 8)
        return [
            get_floating_time(bytes[i * 8 : (i + 1) * 8]) for i in range(entry_count)
        ]

    @staticmethod
    def PtypMultipleInteger64(data_value):
        entry_count = int(len(data_value) / 8)
        return [unpack("q", bytes[i * 8 : (i + 1) * 8])[0] for i in range(entry_count)]

    @staticmethod
    def PtypMultipleString(data_value):
        return data_value
        # string_list = []
        # for item_bytes in data_value:
        #     if item_bytes and '\x00' in item_bytes:
        #         item_bytes = item_bytes.replace('\x00', '')
        #     string_list.append(item_bytes.decode('utf-16-le'))
        # return string_list

    @staticmethod
    def PtypMultipleString8(data_value):
        return data_value

    @staticmethod
    def PtypMultipleTime(data_value):
        entry_count = int(len(data_value) / 8)
        return [get_time(bytes[i * 8 : (i + 1) * 8]) for i in range(entry_count)]

    @staticmethod
    def PtypMultipleGuid(data_value):
        entry_count = int(len(data_value) / 16)
        return [bytes[i * 16 : (i + 1) * 16] for i in range(entry_count)]

    @staticmethod
    def PtypMultipleBinary(data_value):
        return data_value


def get_floating_time(data_value):
    return datetime(year=1899, month=12, day=30) + timedelta(
        days=unpack("d", data_value)[0]
    )


def get_time(data_value):
    return datetime(year=1601, month=1, day=1) + timedelta(
        microseconds=unpack("q", data_value)[0] / 10.0
    )


def get_multi_value_offsets(data_value):
    ul_count = unpack("I", data_value[:4])[0]

    if ul_count == 1:
        rgul_data_offsets = [8]
    else:
        rgul_data_offsets = [
            unpack("Q", bytes[4 + i * 8 : 4 + (i + 1) * 8])[0] for i in range(ul_count)
        ]

    rgul_data_offsets.append(len(data_value))

    return ul_count, rgul_data_offsets
