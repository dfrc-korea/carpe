from binascii import hexlify

from .attribute_headers import AttributeHeaderResident, AttributeHeaderNonResident
from .attributes import AttributeList, Bitmap, Data, EA, EAInformation, FileName, IndexAllocation, \
                        IndexRoot, LoggedUtilityStream, ObjectID, PropertySet, ReparsePoint, StandardInformation, \
                        UnknownAttribute, VolumeInformation, VolumeName, FileAttributesFlag
from .common import AttributeTypeEnum


class AttributeHeaderFactory():
    def __init__(self):
        raise Exception("This class is not supposed to be instantiated.")

    @staticmethod
    def create_attribute_header(data):
        # Working with the raw bytes here is odd but makes it a lot easier to maintain encapsulation in the actual
        # header class for everything else.
        non_resident_flag = int(hexlify(data[8:9]), 16)

        if non_resident_flag == 0:
            return AttributeHeaderResident(data)
        elif non_resident_flag == 1:
            return AttributeHeaderNonResident(data)


class AttributeFactory():
    _map = {
        AttributeTypeEnum.STANDARD_INFORMATION: StandardInformation,
        AttributeTypeEnum.ATTRIBUTE_LIST: AttributeList,
        AttributeTypeEnum.FILE_NAME: FileName,
        AttributeTypeEnum.OBJECT_ID: ObjectID,
        AttributeTypeEnum.VOLUME_NAME: VolumeName,
        AttributeTypeEnum.VOLUME_INFORMATION: VolumeInformation,
        AttributeTypeEnum.DATA: Data,
        AttributeTypeEnum.INDEX_ROOT: IndexRoot,
        AttributeTypeEnum.INDEX_ALLOCATION: IndexAllocation,
        AttributeTypeEnum.BITMAP: Bitmap,
        AttributeTypeEnum.REPARSE_POINT: ReparsePoint,
        AttributeTypeEnum.EA_INFORMATION: EAInformation,
        AttributeTypeEnum.EA: EA,
        AttributeTypeEnum.PROPERTY_SET: PropertySet,
        AttributeTypeEnum.LOGGED_UTILITY_STREAM: LoggedUtilityStream,
        AttributeTypeEnum.UNKNOWN: UnknownAttribute
    }

    def __init__(self):
        raise Exception("This class is not supposed to be instantiated.")

    def create_attribute(data):
        header = AttributeHeaderFactory.create_attribute_header(data)
        return AttributeFactory._map[header.enum](header=header, data=data)
