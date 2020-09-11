from binascii import hexlify
from collections import OrderedDict

from modules.NTFS.ntfs_parse import reverse, reverse_hexlify, reverse_hexlify_int, filetime_to_datetime, FileAttributesFlag
from .common import _WIDTH, _INDENT, _BIG_BAR, _SMALL_BAR, _INDENTED_SMALL_BAR, AttributeTypeEnumConverter, AttributeTypeEnum

from modules.NTFS.ntfs_parse import writeout_as_xxd


class Attribute:
    def __init__(self, header=None, data=None, enum=None):
        self.header = header
        self.data = data[:header.attribute_length]
        if self.header.is_resident:
            self.content_data = self.data[
                                self.header.content_offset:
                                self.header.content_offset + self.header.content_size]
        else:
            self.content_data = b''

    @property
    def enum(self):
        return self.header.enum

    def all_fields_described(self):
        return ()

    def extra_pairs(self):
        return ()

    @property
    def content_data_hex(self):
        return hexlify(self.content_data)

    def writeout_parsed(self, out):
        # Top
        out.write('%s: %s, Typenr.: %s / %s, Name: "%s", %s\n' % ('Attribute',
                                                            self.header.enum.value,
                                                            hex(self.header.type),
                                                            self.header.type,
                                                            self.header.name,
                                                            'Resident' if self.header.is_resident else 'Non-resident'))
        out.write(_SMALL_BAR)

        # Header
        self.header.writeout_parsed(out)

        # Attribute content. To be overwritten in subclasses
        if self.header.is_resident:
            out.write(_INDENTED_SMALL_BAR)
            self.writeout_content_parsed(out)

        # Hook into the writing function for subclasses to overwrite
        self.writeout_additional(out)

        # Bottom
        out.write(_BIG_BAR)

    def writeout_content_parsed(self, out):
        if len(self.all_fields_described()) == 0 and len(self.extra_pairs()) == 0:
            out.write('%s%s\n' % (_INDENT, 'Content part not implemented yet\n'))
            writeout_as_xxd(self.content_data, out)
        else:
            for (description, low, high), value, value_raw in self.all_fields_described():
                out.write('%s%-30s | %-5s | %-18s | %s\n' % (
                    _INDENT,
                    description,
                    str(low) + '-' + str(high),
                    value,
                    hexlify(value_raw)))

            if len(self.extra_pairs()) > 0 and len(self.all_fields_described()) > 0:
                out.write('\n')

            for key, value in self.extra_pairs():
                out.write('%s%-50s %s\n' % (
                    _INDENT,
                    key + ':',
                    value))

    def writeout_additional(self, out):
        pass


class StandardInformation(Attribute):
    CREATION_TIME = ('creation time', 0, 7)
    FILE_ALTERED_TIME = ('file altered time', 8,15)
    MFT_ALTERED_TIME = ('mft altered time', 16, 23)
    FILE_ACCESSED_TIME = ('file accessed time', 24, 31)
    FLAGS = ('flags', 32, 35)
    MAXIMUM_NUMBER_OF_VERSIONS = ('maximum version of numbers', 36, 39)
    VERSION_NUMBER = ('version number', 40, 43)
    CLASS_ID = ('class id', 44, 47)
    OWNER_ID = ('owner id', 48, 51)
    SECURITY_ID = ('security id', 52, 55)
    QUOTA_CHARGED = ('quota charged', 56, 63)
    USN = ('USN', 64, 71)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.content_data = self.data[
                            self.header.content_offset:
                            self.header.content_offset + self.header.content_size]
        self.flags_set = FileAttributesFlag(self.flags)

    ####################################################################################################################
    # Raw values

    @property
    def creation_time_raw(self):
        return self.content_data[0:8]

    @property
    def file_altered_time_raw(self):
        return self.content_data[8:16]

    @property
    def mft_altered_time_raw(self):
        return self.content_data[16:24]

    @property
    def file_accessed_time_raw(self):
        return self.content_data[24:32]

    @property
    def flags_raw(self):
        return self.content_data[32:36]

    @property
    def maximum_number_of_versions_raw(self):
        return self.content_data[36:40]

    @property
    def version_number_raw(self):
        return self.content_data[40:44]

    @property
    def class_id_raw(self):
        return self.content_data[44:48]

    @property
    def owner_id_raw(self):
        return self.content_data[48:52]

    @property
    def security_id_raw(self):
        return self.content_data[52:56]

    @property
    def quota_charged_raw(self):
        return self.content_data[56:64]

    @property
    def usn_raw(self):
        return self.content_data[64:72]


    ####################################################################################################################
    # Interpreted values

    @property
    def creation_time(self):
        return reverse_hexlify_int(self.creation_time_raw)

    @property
    def file_altered_time(self):
        return reverse_hexlify_int(self.file_altered_time_raw)

    @property
    def mft_altered_time(self):
        return reverse_hexlify_int(self.mft_altered_time_raw)

    @property
    def file_accessed_time(self):
        return reverse_hexlify_int(self.file_accessed_time_raw)

    @property
    def flags(self):
        return reverse_hexlify_int(self.flags_raw)

    @property
    def maximum_number_of_versions(self):
        return reverse_hexlify_int(self.maximum_number_of_versions_raw)

    @property
    def version_number(self):
        return reverse_hexlify_int(self.version_number_raw)

    @property
    def class_id(self):
        return reverse_hexlify_int(self.class_id_raw)

    @property
    def owner_id(self):
        return reverse_hexlify_int(self.owner_id_raw)

    @property
    def security_id(self):
        return reverse_hexlify_int(self.security_id_raw)

    @property
    def quota_charged(self):
        return reverse_hexlify_int(self.quota_charged_raw)

    @property
    def usn(self):
        return reverse_hexlify_int(self.usn_raw)


    ####################################################################################################################
    # Derived values

    @property
    def creation_time_datetime(self):
        if not hasattr(self, '_creation_time_datetime'):
            self._creation_time_datetime = filetime_to_datetime(self.creation_time_raw)
        return self._creation_time_datetime

    @property
    def file_altered_time_datetime(self):
        if not hasattr(self, '_file_altered_time_datetime'):
            self._file_altered_time_datetime = filetime_to_datetime(self.file_altered_time_raw)
        return self._file_altered_time_datetime

    @property
    def mft_altered_time_datetime(self):
        if not hasattr(self, '_mft_altered_time_datetime'):
            self._mft_altered_time_datetime = filetime_to_datetime(self.mft_altered_time_raw)
        return self._mft_altered_time_datetime

    @property
    def file_accessed_time_datetime(self):
        if not hasattr(self, '_file_accessed_time_datetime'):
            self._file_accessed_time_datetime = filetime_to_datetime(self.file_accessed_time_raw)
        return self._file_accessed_time_datetime

    @property
    def flags_string(self):
        return '|'.join(self.flags_set.reason_list())

    ####################################################################################################################
    # Printing

    def all_fields_described(self):
        base_tuple = (
            (StandardInformation.CREATION_TIME, self.creation_time, self.creation_time_raw),
            (StandardInformation.FILE_ALTERED_TIME, self.file_altered_time, self.file_altered_time_raw),
            (StandardInformation.MFT_ALTERED_TIME, self.mft_altered_time, self.mft_altered_time_raw),
            (StandardInformation.FILE_ACCESSED_TIME,self.file_accessed_time, self.file_accessed_time_raw),
            (StandardInformation.FLAGS, self.flags, self.flags_raw),
            (StandardInformation.MAXIMUM_NUMBER_OF_VERSIONS, self.maximum_number_of_versions, self.maximum_number_of_versions_raw),
            (StandardInformation.VERSION_NUMBER, self.version_number, self.version_number_raw),
            (StandardInformation.CLASS_ID, self.class_id, self.class_id_raw)
        )

        if len(self.content_data) == 48:
            return base_tuple
        elif len(self.content_data) == 72:
            return base_tuple + (
                (StandardInformation.OWNER_ID, self.owner_id, self.owner_id_raw),
                (StandardInformation.SECURITY_ID, self.security_id, self.security_id_raw),
                (StandardInformation.QUOTA_CHARGED, self.quota_charged, self.quota_charged_raw),
                (StandardInformation.USN, self.usn, self.usn_raw)
            )
        else:
            raise Exception('StandardInformation is of length ' + str(len(self.content_data)) + ', case unaccounted for')

    def extra_pairs(self):
        return (
            ('creation time datetime', self.creation_time_datetime),
            ('file altered time datetime', self.file_altered_time_datetime),
            ('mft altered time datetime', self.mft_altered_time_datetime),
            ('file accessed time datetime', self.file_accessed_time_datetime)
        )

    @staticmethod
    def format_csv_column_headers():
        return [
            'SI creation time',
            'SI file altered time',
            'SI mft altered time',
            'SI file accessed time',
            'SI flags',
            'SI maximum number of versions',
            'SI version number',
            'SI class id',
            'SI owner id',
            'SI security id',
            'SI quota charged',
            'SI usn'
        ]

    def format_csv(self):
        return [
            self.creation_time_datetime,
            self.file_altered_time_datetime,
            self.mft_altered_time_datetime,
            self.file_accessed_time_datetime,
            self.flags_string,
            self.maximum_number_of_versions,
            self.version_number,
            self.class_id,
            self.owner_id,
            self.security_id,
            self.quota_charged,
            self.usn
        ]


class AttributeList(Attribute):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    ####################################################################################################################
    # Raw values

    ####################################################################################################################
    # Interpreted values

    ####################################################################################################################
    # Derived values

    ####################################################################################################################
    # Printing


class FileName(Attribute):
    PARENT_DIRECTORY_FILE  = ('parent directory file', 0, 7)
    FILE_CREATION_TIME = ('file creation time', 8, 15)
    FILE_MODIFICATION_TIME = ('file modification time', 16, 23)
    MFT_MODIFICATION_TIME = ('mft modification time', 24, 31)
    FILE_ACCESS_TIME = ('file access time', 32, 39)
    FILE_ALLOCATED_SIZE = ('file allocated size', 40, 47)
    FILE_REAL_SIZE = ('file real size', 48, 55)
    FLAGS = ('flags', 56, 59)
    REPARSE_VALUE = ('reparse value', 60, 63)
    NAME_LENGTH = ('name length', 64, 64)
    NAMESPACE = ('namespace', 65, 65)
    NAME = ('name', 66, '+')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.content_data = self.data[
                            self.header.content_offset:
                            self.header.content_offset + self.header.content_size]
        self.flags_set = FileAttributesFlag(self.flags)

    ####################################################################################################################
    # Raw values

    @property
    def parent_directory_file_reference_raw(self):
        return self.content_data[0:8]

    @property
    def file_creation_time_raw(self):
        return self.content_data[8:16]

    @property
    def file_modification_time_raw(self):
        return self.content_data[16:24]

    @property
    def mft_modification_time_raw(self):
        return self.content_data[24:32]

    @property
    def file_access_time_raw(self):
        return self.content_data[32:40]

    @property
    def file_allocated_size_raw(self):
        return self.content_data[40:48]

    @property
    def file_real_size_raw(self):
        return self.content_data[48:56]

    @property
    def flags_raw(self):
        return self.content_data[56:60]

    @property
    def reparse_value_raw(self):
        return self.content_data[60:64]

    @property
    def name_length_raw(self):
        return self.content_data[64:65]

    @property
    def namespace_raw(self):
        return self.content_data[65:66]

    @property
    def name_raw(self):
        return self.content_data[66:66+self.name_length*2]

    ####################################################################################################################
    # Interpreted values

    @property
    def parent_directory_file_reference(self):
        return hexlify(self.parent_directory_file_reference_raw).decode()

    @property
    def file_creation_time(self):
        return reverse_hexlify_int(self.file_creation_time_raw)

    @property
    def file_modification_time(self):
        return reverse_hexlify_int(self.file_modification_time_raw)

    @property
    def mft_modification_time(self):
        return reverse_hexlify_int(self.mft_modification_time_raw)

    @property
    def file_access_time(self):
        return reverse_hexlify_int(self.file_access_time_raw)

    @property
    def file_allocated_size(self):
        return reverse_hexlify_int(self.file_allocated_size_raw)

    @property
    def file_real_size(self):
        return reverse_hexlify_int(self.file_allocated_size_raw)

    @property
    def flags(self):
        return reverse_hexlify_int(self.flags_raw)

    @property
    def reparse_value(self):
        return reverse_hexlify_int(self.reparse_value_raw)

    @property
    def name_length(self):
        return reverse_hexlify_int(self.name_length_raw)

    @property
    def namespace(self):
        return reverse_hexlify_int(self.namespace_raw)

    @property
    def name(self):
        return self.name_raw.decode('utf-16')

    ####################################################################################################################
    # Derived values

    @property
    def parent_directory_file_reference_sequence_number(self):
        return reverse_hexlify_int(self.parent_directory_file_reference_raw[6:8])

    @property
    def parent_directory_file_reference_mft_entry(self):
        return reverse_hexlify_int(self.parent_directory_file_reference_raw[0:6])

    @property
    def file_creation_time_datetime(self):
        try:
            if not hasattr(self, '_file_creation_time_datetime'):
                self._file_creation_time_datetime = filetime_to_datetime(self.file_creation_time_raw)
            return self._file_creation_time_datetime
        except ValueError:
            return None

    @property
    def file_modification_time_datetime(self):
        try:
            if not hasattr(self, '_file_modification_time_datetime'):
                self._file_modification_time_datetime = filetime_to_datetime(self.file_modification_time_raw)
            return self._file_modification_time_datetime
        except ValueError:
            return None
    @property
    def mft_modification_time_datetime(self):
        try:
            if not hasattr(self, '_mft_modification_time_datetime'):
                self._mft_modification_time_datetime = filetime_to_datetime(self.mft_modification_time_raw)
            return self._mft_modification_time_datetime
        except ValueError:
            return None
    @property
    def file_access_time_datetime(self):
        try:
            if not hasattr(self, '_file_access_time_datetime'):
                self._file_access_time_datetime = filetime_to_datetime(self.file_access_time_raw)
            return self._file_access_time_datetime
        except ValueError:
            return None

    @property
    def flags_string(self):
        return '|'.join(self.flags_set.reason_list())

    ####################################################################################################################
    # Printing

    def all_fields_described(self):
        return (
            (FileName.PARENT_DIRECTORY_FILE, self.parent_directory_file_reference, self.parent_directory_file_reference_raw),
            (FileName.FILE_CREATION_TIME, self.file_creation_time, self.file_creation_time_raw),
            (FileName.FILE_MODIFICATION_TIME, self.file_modification_time, self.file_modification_time_raw),
            (FileName.MFT_MODIFICATION_TIME, self.mft_modification_time, self.file_modification_time_raw),
            (FileName.FILE_ACCESS_TIME, self.file_access_time, self.file_access_time_raw),
            (FileName.FILE_ALLOCATED_SIZE, self.file_allocated_size, self.file_allocated_size_raw),
            (FileName.FILE_REAL_SIZE, self.file_real_size, self.file_real_size_raw),
            (FileName.FLAGS, self.flags, self.flags_raw),
            (FileName.REPARSE_VALUE, self.reparse_value, self.reparse_value_raw),
            (FileName.NAME_LENGTH, self.name_length, self.name_length_raw),
            (FileName.NAMESPACE, self.namespace, self.namespace_raw),
            (FileName.NAME, self.name, self.name_raw)
        )

    def extra_pairs(self):
        return (
            ('parent directory file reference sequence number', self.parent_directory_file_reference_sequence_number),
            ('parent_directory_file_reference_mft entry', self.parent_directory_file_reference_mft_entry),
            ('file creation time datetime', self.file_creation_time_datetime),
            ('file modified time datetime', self.file_modification_time_datetime),
            ('mft modified time datetime', self.mft_modification_time_datetime),
            ('file access time datetime', self.file_access_time_datetime)
        )

    @staticmethod
    def format_csv_column_headers():
        return [
            'FN file creation time',
            'FN file modification time',
            'FN mft modification time',
            'FN file access time',
            'FN file allocated size',
            'FN file real size',
            'FN flags',
            'FN reparse value',
            'FN name length',
            'FN namespace',
            'FN name',
            'FN pdfme',
            'FN pdfsn'
        ]

    def format_csv(self):
        return [
            self.file_creation_time_datetime,
            self.file_modification_time_datetime,
            self.mft_modification_time_datetime,
            self.file_access_time_datetime,
            self.file_allocated_size,
            self.file_real_size,
            self.flags_string,
            self.reparse_value,
            self.name_length,
            self.namespace,
            self.name,
            self.parent_directory_file_reference_mft_entry,
            self.parent_directory_file_reference_sequence_number
        ]


class ObjectID(Attribute):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    ####################################################################################################################
    # Raw values

    ####################################################################################################################
    # Interpreted values

    ####################################################################################################################
    # Derived values

    ####################################################################################################################
    # Printing


class VolumeName(Attribute):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    ####################################################################################################################
    # Raw values

    ####################################################################################################################
    # Interpreted values

    ####################################################################################################################
    # Derived values

    ####################################################################################################################
    # Printing


class VolumeInformation(Attribute):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    ####################################################################################################################
    # Raw values

    ####################################################################################################################
    # Interpreted values

    ####################################################################################################################
    # Derived values

    ####################################################################################################################
    # Printing


class Data(Attribute):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    ####################################################################################################################
    # Raw values

    ####################################################################################################################
    # Interpreted values

    ####################################################################################################################
    # Derived values

    ####################################################################################################################
    # Printing

    '''
    def extra_pairs(self):
        if self.header.is_resident:
            return (('data hex', self.content_data_hex),)
        else:
            return ()
    '''

class NodeHeader():
    OFFSET_START_INDEX_ENTRY_LIST   = ('offset start index entry list', 0, 3)
    OFFSET_TO_END_USED_PORTION      = ('offset to end used portion', 4, 7)
    OFFSET_TO_END_ALLOCATION        = ('offset to end allocation', 8,  11)
    FLAGS                           = ('flags', 12, 15)

    def __init__(self, data):
        # 16 bytes of note header data
        self.data = data

    ####################################################################################################################
    # Raw values

    @property
    def offset_start_index_entry_list_raw(self):
        return self.data[0:4]

    @property
    def offset_to_end_used_portion_raw(self):
        return self.data[4:8]

    @property
    def offset_to_end_allocation_raw(self):
        return self.data[8:12]

    @property
    def flags_raw(self):
        return self.data[12:16]

    ####################################################################################################################
    # Interpreted values

    @property
    def offset_start_index_entry_list(self):
        return reverse_hexlify_int(self.offset_start_index_entry_list_raw)

    @property
    def offset_to_end_used_portion(self):
        return reverse_hexlify_int(self.offset_to_end_used_portion_raw)

    @property
    def offset_to_end_allocation(self):
        return reverse_hexlify_int(self.offset_to_end_allocation_raw)

    @property
    def flags(self):
        return reverse_hexlify_int(self.flags_raw)

    ####################################################################################################################
    # Derived values

    @property
    def has_children(self):
        return bool(self.flags)

    ####################################################################################################################
    # Printing

    def all_fields_described(self):
        return (
            (NodeHeader.OFFSET_START_INDEX_ENTRY_LIST, self.offset_start_index_entry_list, self.offset_start_index_entry_list_raw),
            (NodeHeader.OFFSET_TO_END_USED_PORTION, self.offset_to_end_used_portion, self.offset_to_end_used_portion_raw),
            (NodeHeader.OFFSET_TO_END_ALLOCATION, self.offset_to_end_allocation, self.offset_to_end_allocation_raw),
            (NodeHeader.FLAGS, self.flags, self.flags_raw)
        )

    def extra_pairs(self):
        return (
            ('has children', 'Yes' if self.has_children else 'No'),
        )


class IndexEntry():
    FIRST_EIGHT             = ('undefined', 0, 7)
    LENGTH_OF_THIS_ENTRY    = ('length of this entry', 8, 9)
    LENGTH_OF_CONTENT       = ('length of content', 10, 11)
    FLAGS                   = ('flags', 12, 15)

    def __init__(self, data):
        # data is possiby larger than this entry + content actually is. We don't know until we parse this entry.
        entry_length = reverse_hexlify_int(data[0:8])
        self.data = data[0 : entry_length]
        self.content_data = self.data[16 : 16 + self.length_of_content]

    ####################################################################################################################
    # Raw values

    @property
    def first_eight_raw(self):
        return self.data[0:8]

    @property
    def length_of_this_entry_raw(self):
        return self.data[8:10]

    @property
    def length_of_content_raw(self):
        return self.data[10:12]
    @property
    def flags_raw(self):
        return self.data[12:16]

    ####################################################################################################################
    # Interpreted values

    @property
    def first_eight(self):
        return reverse_hexlify_int(self.first_eight_raw)

    @property
    def length_of_this_entry(self):
        return reverse_hexlify_int(self.length_of_this_entry_raw)

    @property
    def length_of_content(self):
        return reverse_hexlify_int(self.length_of_content_raw)
    @property
    def flags(self):
        return reverse_hexlify_int(self.flags_raw)

    ####################################################################################################################
    # Derived values

    @property
    def child_node_exists(self):
        return bool(self.flags & 1)

    @property
    def last_entry_in_list(self):
        return bool(self.flags & 2)

    ####################################################################################################################
    # Printing

    def all_fields_described(self):
        return (
            (self.FIRST_EIGHT, self.first_eight, self.first_eight_raw),
            (self.LENGTH_OF_THIS_ENTRY, self.length_of_this_entry, self.length_of_this_entry_raw),
            (self.LENGTH_OF_CONTENT, self.length_of_content, self.length_of_content_raw),
            (self.FLAGS, self.flags, self.flags_raw)
        )

    def extra_pairs(self):
        return (
            ('child node exists', 'Yes' if self.child_node_exists else 'No'),
            ('last entry in list', 'Yes' if self.last_entry_in_list else 'No')
        )


class HeaderStub():
    def __init__(self, attribute_length=None, enum=None):
        self.attribute_length = attribute_length
        self.is_resident = True
        self.content_offset = 0
        self.content_size = attribute_length
        self.attribute_identifier = enum.name
        self.enum = enum

class DirectoryIndexEntry(IndexEntry):
    FIRST_EIGHT = ('mft file reference', 0, 7)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.content = FileName(header=HeaderStub(attribute_length=self.length_of_content, enum=AttributeTypeEnum.FILE_NAME), data=self.content_data)

    ####################################################################################################################
    # Derived values

    @property
    def file_reference_mft_entry(self):
        return reverse_hexlify_int(self.first_eight_raw[0:6])

    @property
    def file_reference_sequence_number(self):
        return reverse_hexlify_int(self.first_eight_raw[6:8])

    ####################################################################################################################
    # Printing

    def extra_pairs(self):
        return (
            ('file reference mft entry', self.file_reference_mft_entry),
            ('file reference sequence number', self.file_reference_sequence_number)
        ) + super().extra_pairs()



class IndexRoot(Attribute):
    TYPE_OF_ATTRIBUTE_IN_INDEX      = ('type of attribute in index', 0, 3)
    COLLATION_SORTING_RULE          = ('collation sorting rule', 4, 7)
    SIZE_OF_EACH_RECORD_BYTES       = ('size of each record bytes', 8, 11)
    SIZE_OF_EACH_RECORD_CLUSTERS    = ('size of each record clusters', 12, 12)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # content_data is all bytes for this attribute excluding the header.
        self.content_data = self.data[
                    self.header.content_offset:
                    self.header.content_offset + self.header.content_size]
        self.node_header = NodeHeader(self.content_data[16:32])
        self.entries = OrderedDict()

        # More work is needed in case the IndexRoot has children. Skip for now.
        if self.node_header.has_children:
            return

        # The node header starts at offset 16 and calculates from that offset
        offset = 16 + self.node_header.offset_start_index_entry_list

        if self.type_of_attribute_in_index_enum == AttributeTypeEnum.FILE_NAME:
            self.entries[AttributeTypeEnum.FILE_NAME] = OrderedDict()
            more_entries = True
            while offset < self.node_header.offset_to_end_used_portion and more_entries:
                entry = DirectoryIndexEntry(self.content_data[offset :])
                self.entries[AttributeTypeEnum.FILE_NAME][entry.content.name] = entry
                offset += entry.length_of_this_entry
                more_entries = not entry.last_entry_in_list

    ####################################################################################################################
    # Raw values

    @property
    def type_of_attribute_in_index_raw(self):
        return self.content_data[0:4]

    @property
    def collation_sorting_rule_raw(self):
        return self.content_data[4:8]

    @property
    def size_of_each_record_bytes_raw(self):
        return self.content_data[8:12]

    @property
    def size_of_each_record_clusters_raw(self):
        return self.content_data[12:13]

    ####################################################################################################################
    # Interpreted values

    @property
    def type_of_attribute_in_index(self):
        return reverse_hexlify_int(self.type_of_attribute_in_index_raw)

    @property
    def collation_sorting_rule(self):
        return reverse_hexlify_int(self.collation_sorting_rule_raw)

    @property
    def size_of_each_record_bytes(self):
        return reverse_hexlify_int(self.size_of_each_record_bytes_raw)

    @property
    def size_of_each_record_clusters(self):
        return reverse_hexlify_int(self.size_of_each_record_clusters_raw)

    ####################################################################################################################
    # Derived values

    @property
    def type_of_attribute_in_index_enum(self):
        return AttributeTypeEnumConverter.from_identifier(self.type_of_attribute_in_index)

    ####################################################################################################################
    # Printing

    def all_fields_described(self):
        return (
            (IndexRoot.TYPE_OF_ATTRIBUTE_IN_INDEX, self.type_of_attribute_in_index, self.type_of_attribute_in_index_raw),
            (IndexRoot.COLLATION_SORTING_RULE, self.collation_sorting_rule, self.collation_sorting_rule_raw),
            (IndexRoot.SIZE_OF_EACH_RECORD_BYTES, self.size_of_each_record_bytes, self.size_of_each_record_bytes_raw),
            (IndexRoot.SIZE_OF_EACH_RECORD_CLUSTERS, self.size_of_each_record_clusters, self.size_of_each_record_clusters_raw)
        ) + (
            (('-- Node header:', '', ''), '', b''),
        ) +self.node_header.all_fields_described()

    def extra_pairs(self):
        return (
            ('type of attribute in index enum', self.type_of_attribute_in_index_enum.value),
            ('-- Node header', '')
        ) + self.node_header.extra_pairs()

    def writeout_additional(self, out):
        for vals1 in self.entries.values():
            for vals2 in vals1.values():
                out.write('\n%sEntry\n%s\n' % (_INDENT, _INDENTED_SMALL_BAR))
                for (description, low, high), value, value_raw in vals2.all_fields_described():
                    out.write('%s%-30s | %-5s | %-18s | %s\n' % (
                        _INDENT,
                        description,
                        str(low) + '-' + str(high),
                        value,
                        hexlify(value_raw)))
                out.write('\n')

                for key, value in vals2.extra_pairs():
                    out.write('%s%-50s %s\n' % (
                        _INDENT,
                        key + ':',
                        value))
                out.write('\n')
                vals2.content.writeout_content_parsed(out)


class IndexAllocation(Attribute):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    ####################################################################################################################
    # Raw values

    ####################################################################################################################
    # Interpreted values

    ####################################################################################################################
    # Derived values

    ####################################################################################################################
    # Printing


class Bitmap(Attribute):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    ####################################################################################################################
    # Raw values

    ####################################################################################################################
    # Interpreted values

    ####################################################################################################################
    # Derived values

    ####################################################################################################################
    # Printing


class ReparsePoint(Attribute):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    ####################################################################################################################
    # Raw values

    ####################################################################################################################
    # Interpreted values

    ####################################################################################################################
    # Derived values

    ####################################################################################################################
    # Printing


class EAInformation(Attribute):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    ####################################################################################################################
    # Raw values

    ####################################################################################################################
    # Interpreted values

    ####################################################################################################################
    # Derived values

    ####################################################################################################################
    # Printing


class EA(Attribute):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    ####################################################################################################################
    # Raw values

    ####################################################################################################################
    # Interpreted values

    ####################################################################################################################
    # Derived values

    ####################################################################################################################
    # Printing


class PropertySet(Attribute):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    ####################################################################################################################
    # Raw values

    ####################################################################################################################
    # Interpreted values

    ####################################################################################################################
    # Derived values

    ####################################################################################################################
    # Printing


class LoggedUtilityStream(Attribute):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    ####################################################################################################################
    # Raw values

    ####################################################################################################################
    # Interpreted values

    ####################################################################################################################
    # Derived values

    ####################################################################################################################
    # Printing


class UnknownAttribute(Attribute):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    ####################################################################################################################
    # Raw values

    ####################################################################################################################
    # Interpreted values

    ####################################################################################################################
    # Derived values

    ####################################################################################################################
    # Printing