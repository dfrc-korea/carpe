########################################################################################################################
# USNJrnl classes
#
########################################################################################################################

import csv
from binascii import hexlify
import os
import sys

from modules.NTFS.ntfs_parse import reverse, reverse_hexlify, reverse_hexlify_int, filetime_to_datetime
from modules.NTFS.ntfs_parse import FileAttributesFlag


class UsnJrnl:
    def __init__(self, file):
        self.file_name = file
        self.records = []

    def parse(self, number=None):
        n_parsed = 0
        with open(self.file_name, 'rb') as f:
            while n_parsed != number:
                pos = f.tell()

                bytes = f.read(4)
                if len(bytes) == 0:
                    # EOF
                    break
                size = reverse_hexlify_int(bytes)
                if size == 0:
                    # We've hit a bunch of zeroes. Complete this useless line en start looping.
                    # The file often contains blobs of zeroes as it consists of multiple runs, each padded with zeroes
                    # in the end if a full USN record doesn't fit anymore.
                    pos = f.tell()
                    if pos % 16 != 0:
                        f.seek(16 - pos % 16, os.SEEK_CUR)
                    while True:
                        line = f.read(16)
                        if len(line) == 0:
                            # EOF
                            # print('breaking')
                            return
                        if line != b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00':
                            break

                    # Done skipping rows of zeroes.
                    size = reverse_hexlify_int(line[0:4])

                    # Reset from reading the last line
                    f.seek(-16, os.SEEK_CUR)
                    pos = f.tell()

                else:
                    # This flow needs to reset its cursor.
                    f.seek(pos)
                record = UsnRecord(f.read(size), offset_bytes=pos)
                if not record:
                    # Record could not be parsed. At this moment, this is a weak promise that stuff will work.
                    # If this happens, just stop. Probably this is the end of the file where we will find gibberish
                    return
                self.records.append(record)
                n_parsed += 1

    def print_all(self):
        for record in self.records[0:10]:
            record.collect_data()

    def print_statistics(self):
        print('count:', len(self.records))

    def export_csv(self, output_file=None):
        if len(self.records) == 0:
            return
        first = self.records[0]
        if output_file:
            with open(output_file, 'w') as f:
                csv_writer = csv.writer(f)
                csv_writer.writerow(first.formatted_csv_column_headers())
                for index in range(len(self.records)):
                    record = self.records[index]
                    csv_writer.writerow(record.formatted_csv())
        else:
            csv_writer = csv.writer(sys.stdout)
            csv_writer.writerow(first.formatted_csv_column_headers())
            for index in range(len(self.records)):
                record = self.records[index]
                csv_writer.writerow(record.formatted_csv())

    @property
    def grouped_by_entry(self):
        result = {}
        for record in self.records:
            if record.file_ref_mft_entry not in result.keys():
                result[record.file_ref_mft_entry] = {}
            if record.file_ref_seq_num not in result[record.file_ref_mft_entry].keys():
                result[record.file_ref_mft_entry][record.file_ref_seq_num] = []
            result[record.file_ref_mft_entry][record.file_ref_seq_num].append(record)
        return result


class UsnRecord():
    def __new__(cls, data, offset_bytes):
        major_version = reverse_hexlify_int(data[4:6])
        if major_version == 2:
            return UsnRecordV2(data, offset_bytes)


class UsnRecordBase():
    # Fields that are shared by both the USN record version 2 and 3 (4 is unknown at this moment)
    RECORD_LENGTH = ('record length', 0, 3)
    MAJOR_VERSION = ('major version', 4, 5)
    MINOR_VERSION = ('minor version', 6, 7)

    REASON_MAP = {
        0x00000001: 'DATA_OVERWRITE',
        0x00000002: 'DATA_EXTEND',
        0x00000004: 'DATA_TRUNCATION',
        0x00000010: 'NAMED_DATA_OVERWRITE',
        0x00000020: 'NAMED_DATA_EXTEND',
        0x00000040: 'NAMED_DATA_TRUNCATION',
        0x00000100: 'FILE_CREATE',
        0x00000200: 'FILE_DELETE',
        0x00000400: 'EA_CHANGE',
        0x00000800: 'SECURITY_CHANGE',
        0x00001000: 'RENAME_OLD_NAME',
        0x00002000: 'RENAME_NEW_NAME',
        0x00004000: 'INDEXABLE_CHANGE',
        0x00008000: 'BASIC_INFO_CHANGE',
        0x00010000: 'HARD_LINK_CHANGE',
        0x00020000: 'COMPRESSION_CHANGE',
        0x00040000: 'ENCRYPTION_CHANGE',
        0x00080000: 'OBJECT_ID_CHANGE',
        0x00100000: 'REPARSE_POINT_CHANGE',
        0x00200000: 'STREAM_CHANGE',
        0x80000000: 'CLOSE'
    }

    REASON_TUPLE = (
        (0x00000001, 'DATA_OVERWRITE'),
        (0x00000002, 'DATA_EXTEND'),
        (0x00000004, 'DATA_TRUNCATION'),
        (0x00000010, 'NAMED_DATA_OVERWRITE'),
        (0x00000020, 'NAMED_DATA_EXTEND'),
        (0x00000040, 'NAMED_DATA_TRUNCATION'),
        (0x00000100, 'FILE_CREATE'),
        (0x00000200, 'FILE_DELETE'),
        (0x00000400, 'EA_CHANGE'),
        (0x00000800, 'SECURITY_CHANGE'),
        (0x00001000, 'RENAME_OLD_NAME'),
        (0x00002000, 'RENAME_NEW_NAME'),
        (0x00004000, 'INDEXABLE_CHANGE'),
        (0x00008000, 'BASIC_INFO_CHANGE'),
        (0x00010000, 'HARD_LINK_CHANGE'),
        (0x00020000, 'COMPRESSION_CHANGE'),
        (0x00040000, 'ENCRYPTION_CHANGE'),
        (0x00080000, 'OBJECT_ID_CHANGE'),
        (0x00100000, 'REPARSE_POINT_CHANGE'),
        (0x00200000, 'STREAM_CHANGE'),
        (0x80000000, 'CLOSE')
    )



    # Source info
    USN_SOURCE_DATA_MANAGEMENT = 0x00000001
    USN_SOURCE_AUXILARY_DATA = 0x00000002
    USN_SOURCE_REPLICATION_MANAGEMENT = 0x00000004

    def __init__(self, data=None, offset_bytes=None):
        record_length = reverse_hexlify_int(data[0:4])
        self.data = data[0:record_length]
        self.offset_bytes = offset_bytes
        self.file_attributes_object = FileAttributesFlag(self.file_attributes)

    ####################################################################################################################
    # Raw values

    @property
    def record_length_raw(self):
        return self.data[0:4]

    @property
    def major_version_raw(self):
        return self.data[4:6]

    @property
    def minor_version_raw(self):
        return self.data[6:8]

    # Placeholders to be overridden by subclasses.
    @property
    def file_reference_number_raw(self): raise NotImplementedError()

    @property
    def parent_file_reference_number_raw(self): raise NotImplementedError()

    @property
    def usn_raw(self): raise NotImplementedError()

    @property
    def timestamp_raw(self): raise NotImplementedError()

    @property
    def reason_raw(self): raise NotImplementedError()

    @property
    def source_info_raw(self): raise NotImplementedError()

    @property
    def security_id_raw(self): raise NotImplementedError()

    @property
    def file_attributes_raw(self): raise NotImplementedError()

    @property
    def file_name_length_raw(self): raise NotImplementedError()

    @property
    def file_name_offset_raw(self): raise NotImplementedError()

    @property
    def file_name_raw(self):
        return self.data[self.file_name_offset : self.file_name_offset + self.file_name_length]

    ####################################################################################################################
    # Interpreted values

    @property
    def record_length(self):
        return reverse_hexlify_int(self.record_length_raw)

    @property
    def major_version(self):
        return reverse_hexlify_int(self.major_version_raw)

    @property
    def minor_version(self):
        return reverse_hexlify_int(self.minor_version_raw)

    @property
    def file_reference_number(self):
        return hexlify(self.file_reference_number_raw)

    @property
    def parent_file_reference_number(self):
        return hexlify(self.parent_file_reference_number_raw)

    @property
    def usn(self):
        return reverse_hexlify_int(self.usn_raw)

    @property
    def timestamp(self):
        return reverse_hexlify_int(self.timestamp_raw)

    @property
    def reason(self):
        return reverse_hexlify_int(self.reason_raw)

    @property
    def source_info(self):
        return reverse_hexlify_int(self.source_info_raw)

    @property
    def security_id(self):
        return reverse_hexlify_int(self.security_id_raw)

    @property
    def file_attributes(self):
        return reverse_hexlify_int(self.file_attributes_raw)

    @property
    def file_name_length(self):
        return reverse_hexlify_int(self.file_name_length_raw)

    @property
    def file_name_offset(self):
        return reverse_hexlify_int(self.file_name_offset_raw)

    @property
    def file_name(self):
        return self.file_name_raw.decode('utf-16')

    ####################################################################################################################
    # Derived values

    @property
    def timestamp_datetime(self):
        if not hasattr(self, '_timestamp_datetime'):
            self._timestamp_datetime = filetime_to_datetime(self.timestamp_raw)
        return self._timestamp_datetime

    @property
    def usn_source_data_management_flag_set(self):
        return bool(self.source_info & UsnRecordV2.USN_SOURCE_DATA_MANAGEMENT)

    @property
    def usn_source_auxiliary_data_flag_set(self):
        return bool(self.source_info & UsnRecordV2.USN_SOURCE_AUXILARY_DATA)

    @property
    def usn_source_replication_management_flag_set(self):
        return bool(self.source_info & UsnRecordV2.USN_SOURCE_REPLICATION_MANAGEMENT)

    @property
    def file_attributes_string(self):
        return '|'.join(self.file_attributes_object.reason_list())

    @property
    def reason_string(self):
        return '|'.join([second for first, second in self.REASON_TUPLE if self.reason & first])

    ####################################################################################################################
    # Printing

    def all_fields_described(self):
        return (
            (UsnRecordBase.RECORD_LENGTH, self.record_length, self.record_length_raw),
            (UsnRecordBase.MAJOR_VERSION, self.major_version, self.major_version_raw),
            (UsnRecordBase.MINOR_VERSION, self.minor_version, self.minor_version_raw),
        )

    def extra_pairs(self):
        return ()

    def formatted_csv(self):
        return [
            self.record_length,
            self.major_version,
            self.minor_version,
            #self.file_ref_num,
            #self.parent_file_reference_number,
            self.usn,
            self.timestamp_datetime,
            self.reason_string,
            self.source_info,
            self.security_id,
            self.file_attributes_string,
            self.file_name_length,
            self.file_name_offset,
            self.file_name
        ]

    def formatted_csv_column_headers(self):
        formatted = [
            'record length',
            'major version',
            'minor version',
            #'file reference number',
            #'parent file reference number',
            'usn',
            'timestamp',
            'reason',
            'source info',
            'security id',
            'file attributes',
            'file name length',
            'file name offset',
            'file name'
        ]
        return formatted

    def print(self):
        _INDENT = '    '
        for (description, low, high), value, value_raw in self.all_fields_described():
            print(_INDENT + '%-26s | %-5s | %-18s | %s' % (description, str(low) + '-' + str(high), value, hexlify(value_raw)))
        #print()
        #print(_INDENT + '%-47s | %s' % ('parent directory file reference sequence number', self.parent_directory_file_reference_sequence_number))
        #print(_INDENT + '%-47s | %s' % ('parent_directory_file_reference_mft entry', self.parent_directory_file_reference_mft_entry))
        #print(_INDENT + '%-47s | %s' % ('file creation time datetime', self.file_creation_time_datetime))
        #print(_INDENT + '%-47s | %s' % ('file modified time datetime', self.file_modification_time_datetime))
        #print(_INDENT + '%-47s | %s' % ('mft modified time datetime', self.mft_modification_time_datetime))
        #print(_INDENT + '%-47s | %s' % ('file access time datetime', self.file_access_time_datetime))
        #self.print_attribute_bottom()
    def print(self):
        pass

    def writeout_parsed(self, out, indent=0):
        for (description, low, high), value, value_raw in self.all_fields_described():
            out.write('%s%-26s | %-5s | %-18s | %s\n' % (indent * ' ', description, str(low) + '-' + str(high), value, hexlify(value_raw)))
        for key, val in self.extra_pairs():
            out.write('%-15s%s\n' % (key + ':', val))



class UsnRecordV2(UsnRecordBase):
    # Fields that, although shared with USN record version 3, are in different positions.
    FILE_REFERENCE_NUMBER = ('file reference number', 8, 15)
    PARENT_FILE_REFERENCE_NUMBER = ('parent file reference number', 16, 23)
    USN = ('usn', 24, 31)
    TIMESTAMP = ('timestamp', 32, 39)
    REASON = ('reason', 40, 43)
    SOURCE_INFO = ('source info', 44, 47)
    SECURITY_ID = ('security id', 48, 51)
    FILE_ATTRIBUTES = ('file attributes', 52, 55)
    FILE_NAME_LENGTH = ('file name length', 56, 57)
    FILE_NAME_OFFSET = ('file name offset', 58,59)
    FILE_NAME = ('file name', 60, '+')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    ####################################################################################################################
    # Raw values

    # First three fields are parsed in parent class.

    @property
    def file_reference_number_raw(self):
        return self.data[8:16]

    @property
    def parent_file_reference_number_raw(self):
        return self.data[16:24]

    @property
    def usn_raw(self):
        return self.data[24:32]

    @property
    def timestamp_raw(self):
        return self.data[32:40]

    @property
    def reason_raw(self):
        return self.data[40:44]

    @property
    def source_info_raw(self):
        return self.data[44:48]

    @property
    def security_id_raw(self):
        return self.data[48:52]

    @property
    def file_attributes_raw(self):
        return self.data[52:56]

    @property
    def file_name_length_raw(self):
        return self.data[56:58]

    @property
    def file_name_offset_raw(self):
        return self.data[58:60]

    @property
    def file_name_raw(self):
        return self.data[self.file_name_offset : self.file_name_offset + self.file_name_length]

    ####################################################################################################################
    # Interpreted values


    ####################################################################################################################
    # Derived values

    @property
    def parent_file_reference_mft_entry(self):
        return reverse_hexlify_int(self.parent_file_reference_number_raw[0:6])

    @property
    def parent_file_reference_sequence_number(self):
        return reverse_hexlify_int(self.parent_file_reference_number_raw[6:8])

    @property
    def file_reference_mft_entry(self):
        return reverse_hexlify_int(self.file_reference_number_raw[0:6])

    @property
    def file_reference_sequence_number(self):
        return reverse_hexlify_int(self.file_reference_number_raw[6:8])

    ####################################################################################################################
    # Printing

    def formatted_csv(self):
        formatted = super().formatted_csv()
        formatted.extend([
            self.file_reference_mft_entry,
            self.file_reference_sequence_number,
            self.parent_file_reference_mft_entry,
            self.parent_file_reference_sequence_number
        ])
        return formatted

    def formatted_csv_column_headers(self):
        formatted = super().formatted_csv_column_headers()
        formatted.extend([
            'file reference mft entry',
            'file reference sequence number',
            'parent file reference mft entry',
            'parent file reference sequence number'
        ])
        return formatted

    def all_fields_described(self):
        return super().all_fields_described() + (
            (UsnRecordV2.FILE_REFERENCE_NUMBER, self.file_reference_number, self.file_reference_number_raw),
            (UsnRecordV2.PARENT_FILE_REFERENCE_NUMBER, self.parent_file_reference_number, self.parent_file_reference_number_raw),
            (UsnRecordV2.USN, self.usn, self.usn_raw),
            (UsnRecordV2.TIMESTAMP, self.timestamp, self.timestamp_raw),
            (UsnRecordV2.REASON, self.reason, self.reason_raw),
            (UsnRecordV2.SOURCE_INFO, self.source_info, self.source_info_raw),
            (UsnRecordV2.SECURITY_ID, self.security_id, self.security_id_raw),
            (UsnRecordV2.FILE_ATTRIBUTES, self.file_attributes, self.file_attributes_raw),
            (UsnRecordV2.FILE_NAME_LENGTH, self.file_name_length, self.file_name_length_raw),
            (UsnRecordV2.FILE_NAME_OFFSET, self.file_name_offset, self.file_name_offset_raw),
            (UsnRecordV2.FILE_NAME, self.file_name, self.file_name_length_raw)
        )

    def extra_pairs(self):
        return super().extra_pairs() + (
            ('frme', self.file_reference_mft_entry),
            ('frsn', self.file_reference_sequence_number),
            ('pfrme', self.parent_file_reference_mft_entry),
            ('pfrsn', self.parent_file_reference_sequence_number)
        )


class UsnRecordV3(UsnRecordBase):
    # Fields that, although shared with USN record version 3, are in different positions.
    FILE_REFERENCE_NUMBER = ('file reference number', 8, 23)
    PARENT_FILE_REFERENCE_NUMBER = ('parent file reference number', 24, 39)
    USN = ('usn', 40, 47)
    TIMESTAMP = ('timestamp', 48, 55)
    REASON = ('reason', 56, 59)
    SOURCE_INFO = ('source info', 60, 63)
    SECURITY_ID = ('security id', 64, 67)
    FILE_ATTRIBUTES = ('file attributes', 68, 71)
    FILE_NAME_LENGTH = ('file name length', 72, 73)
    FILE_NAME_OFFSET = ('file name offset', 74, 75)
    FILE_NAME = ('file name', 76, '+')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    ####################################################################################################################
    # Raw values

    # First three fields are parsed in parent class.

    @property
    def file_reference_number_raw(self):
        return self.data[8:24]

    @property
    def parent_file_reference_number_raw(self):
        return self.data[24:40]

    @property
    def usn_raw(self):
        return self.data[40:48]

    @property
    def timestamp_raw(self):
        return self.data[48:56]

    @property
    def reason_raw(self):
        return self.data[56:60]

    @property
    def source_info_raw(self):
        return self.data[60:64]

    @property
    def security_id_raw(self):
        return self.data[64:68]

    @property
    def file_attributes_raw(self):
        return self.data[68:72]

    @property
    def file_name_length_raw(self):
        return self.data[72:74]

    @property
    def file_name_offset_raw(self):
        return self.data[74:76]

    @property
    def file_name_raw(self):
        return self.data[self.file_name_offset:self.file_name_length]

    ####################################################################################################################
    # Interpreted values


    ####################################################################################################################
    # Derived values

    @property
    def parent_file_reference_sequence_number(self): raise NotImplementedError('Not sure if and how to implement this.')

    @property
    def parent_file_reference_mft_entry(self): raise NotImplementedError('Not sure if and how to implement this.')

    @property
    def file_reference_sequence_number(self): raise NotImplementedError('Not sure if and how to implement this.')

    @property
    def file_reference_mft_entry(self): raise NotImplementedError('Not sure if and how to implement this.')

    ####################################################################################################################
    # Printing


class UsnRecordV4(UsnRecordBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        raise NotImplementedError("There's no information on V4 available yet.")

    ####################################################################################################################
    # Raw values

    ####################################################################################################################
    # Interpreted values

    ####################################################################################################################
    # Derived values

    ####################################################################################################################
    # Printing
