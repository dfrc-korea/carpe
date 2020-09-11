########################################################################################################################
# $LogFile Restart-Record class
#
#  This part of code is only focussing on the Restart Record of the $LogFile $DATA attribute
#  Used:
#   -   NTFS documentation, R. Russon, Y. Fledel, 2009, page 38-42
#   -   Finding Forensic Information on Creating a Folder in $LogFile of NTFS, M. K. Rogers, 2012
#
# Issues:
#   -   LogFile's structure is difficult to interpret
########################################################################################################################

from binascii import hexlify
from modules.NTFS.ntfs_parse.usn_jrnl.utils import reverse_hexlify_int
from .logfile_utils import search_fixup, replace_fixup


class RSTRRecord:
    SECTOR_SIZE = 512
    SECTOR_AMOUNT = 8

    def __init__(self, data):
        self.header = RestartPageHeader(data[:48])     # 0x00 - 0x2F
        self.offset_dict = search_fixup(self, data)
        if self.offset_dict:
            self.data = replace_fixup(self, data)
        else:
            raise Exception('Fixup error')
        self.restart_area = RestartArea(self.data[48:112])  # 0x30 - 0x6F
        self.log_client = LogClient(self.data[112:])        # 0x70 - END (0xC0)

    ####################################################################################################################
    # PRINT functions
    def writeout_parsed(self, out):
        out.write('\n'
                  '=================================================================================================\n'
                  '= RSTR Record\n')
        out.write('    ---- Restart Page Header --------------------------------------------------------------------\n')
        for (description, low, high), value, value_raw in self.header.all_fields_described():
            out.write('    %-36s | %-7s | %-11s | %s\n' % (description, str(low) + '-' + str(high),
                                                           value, hexlify(value_raw)))
        out.write('    ---- Restart Area ---------------------------------------------------------------------------\n')
        for (description, low, high), value, value_raw in self.restart_area.all_fields_described():
            out.write('    %-36s | %-7s | %-11s | %s\n' % (description, str(low) + '-' + str(high),
                                                           value, hexlify(value_raw)))
        out.write('    ---- Log Client -----------------------------------------------------------------------------\n')
        for (description, low, high), value, value_raw in self.log_client.all_fields_described():
            out.write('    %-36s | %-7s | %-11s | %s\n' % (description, str(low) + '-' + str(high),
                                                           value, hexlify(value_raw)))


########################################################################################################################
# RESTART page header
class RestartPageHeader:
    MAGIC_NUMBER           = ('magic number (name)', 0, 3)
    UPDATE_SEQUENCE_OFFSET = ('update seq. offset', 4, 5)
    UPDATE_SEQUENCE_COUNT  = ('update seq. count', 6, 7)
    CHECK_DISK_LSN         = ('check disk lsn', 8, 15)
    SYSTEM_PAGE_SIZE       = ('system page size', 16, 19)
    LOG_PAGE_SIZE          = ('log page size', 20, 23)
    RESTART_AREA_OFFSET    = ('restart area offset', 24, 25)
    MINOR_VERSION          = ('minor version', 26, 27)
    MAJOR_VERSION          = ('major version', 28, 29)
    FIXUP_VALUE            = ('fixup value', 30, 31)
    FIXUP_ARRAY            = ('fixup array', 32, 47)

    def __init__(self, data):
        self.data = data

    ####################################################################################################################
    # Raw values
    @property
    def magic_number_raw(self): return self.data[self.MAGIC_NUMBER[1]:self.MAGIC_NUMBER[2]+1]

    @property
    def update_sequence_offset_raw(self): return self.data[self.UPDATE_SEQUENCE_OFFSET[1]:self.UPDATE_SEQUENCE_OFFSET[2]+1]

    @property
    def update_sequence_count_raw(self): return self.data[self.UPDATE_SEQUENCE_COUNT[1]:self.UPDATE_SEQUENCE_COUNT[2]+1]

    @property
    def check_disk_lsn_raw(self): return self.data[self.CHECK_DISK_LSN[1]:self.CHECK_DISK_LSN[2]+1]

    @property
    def system_page_size_raw(self): return self.data[self.SYSTEM_PAGE_SIZE[1]:self.SYSTEM_PAGE_SIZE[2]+1]

    @property
    def log_page_size_raw(self): return self.data[self.LOG_PAGE_SIZE[1]:self.LOG_PAGE_SIZE[2]+1]

    @property
    def restart_area_offset_raw(self): return self.data[self.RESTART_AREA_OFFSET[1]:self.RESTART_AREA_OFFSET[2]+1]

    @property
    def minor_version_raw(self): return self.data[self.MINOR_VERSION[1]:self.MINOR_VERSION[2]+1]

    @property
    def major_version_raw(self): return self.data[self.MAJOR_VERSION[1]:self.MAJOR_VERSION[2]+1]

    @property
    def fixup_value_raw(self): return self.data[self.FIXUP_VALUE[1]:self.FIXUP_VALUE[2]+1]

    @property
    def fixup_array_raw(self): return self.data[self.FIXUP_ARRAY[1]:self.FIXUP_ARRAY[2]+1]

    ####################################################################################################################
    # Interpreted values
    @property
    def magic_number(self): return self.magic_number_raw.decode()

    @property
    def update_sequence_offset(self): return reverse_hexlify_int(self.update_sequence_offset_raw)

    @property
    def update_sequence_count(self): return reverse_hexlify_int(self.update_sequence_count_raw)

    @property
    def system_page_size(self): return reverse_hexlify_int(self.system_page_size_raw)

    @property
    def log_page_size(self): return reverse_hexlify_int(self.log_page_size_raw)

    @property
    def restart_area_offset(self): return reverse_hexlify_int(self.restart_area_offset_raw)

    @property
    def minor_version(self): return reverse_hexlify_int(self.minor_version_raw)

    @property
    def major_version(self): return reverse_hexlify_int(self.major_version_raw)

    @property
    def fixup_value(self): return hexlify(self.fixup_value_raw)

    ####################################################################################################################
    # Derived values

    ####################################################################################################################
    # Printing

    def all_fields_described(self):
        return(
            (self.MAGIC_NUMBER, self.magic_number, self.magic_number_raw),
            (self.UPDATE_SEQUENCE_OFFSET, self.update_sequence_offset, self.update_sequence_offset_raw),
            (self.UPDATE_SEQUENCE_COUNT, self.update_sequence_count, self.update_sequence_count_raw),
            (self.CHECK_DISK_LSN, '', self.check_disk_lsn_raw),
            (self.SYSTEM_PAGE_SIZE, self.system_page_size, self.system_page_size_raw),
            (self.LOG_PAGE_SIZE, self.log_page_size, self.log_page_size_raw),
            (self.RESTART_AREA_OFFSET, self.restart_area_offset, self.restart_area_offset_raw),
            (self.MINOR_VERSION, self.minor_version, self.minor_version_raw),
            (self.MAJOR_VERSION, self.major_version, self.major_version_raw),
            (self.FIXUP_VALUE, self.fixup_value, self.fixup_value_raw),
            (self.FIXUP_ARRAY, '', self.fixup_array_raw),
        )


########################################################################################################################
# RESTART area
class RestartArea:
    CURRENT_LSN            = ('current lsn', 0, 7)
    LOG_CLIENTS            = ('log clients', 8, 9)
    CLIENT_FREE_LIST       = ('client free list', 10, 11)
    CLIENT_IN_USE_LIST     = ('client in-use list', 12, 13)
    FLAGS                  = ('flags', 14, 15)
    SEQUENCE_NUMBER_BITS   = ('seq. number bits', 16, 19)
    RESTART_AREA_LENGTH    = ('restart area length', 20, 21)
    CLIENT_ARRAY_OFFSET    = ('client array offset', 22, 23)
    FILE_SIZE              = ('file size', 24, 31)
    LAST_LSN_DATA_LENGTH   = ('last lsn data length', 32, 35)
    LOG_RECORD_HD_LENGTH   = ('log record hd length', 36, 37)
    LOGPAGE_DATA_OFFSET    = ('log page data offset', 38, 39)
    RESTARTLOG_OPEN_COUNT  = ('restart log open count', 40, 43)
    RESERVED_STRT_AREA     = ('reserved', 44, 63)

    def __init__(self, data):
        self.data = data

    ####################################################################################################################
    # Raw values
    @property
    def current_lsn_raw(self): return self.data[self.CURRENT_LSN[1]:self.CURRENT_LSN[2]+1]

    @property
    def log_clients_raw(self): return self.data[self.LOG_CLIENTS[1]:self.LOG_CLIENTS[2]+1]

    @property
    def client_free_list_raw(self): return self.data[self.CLIENT_FREE_LIST[1]:self.CLIENT_FREE_LIST[2]+1]

    @property
    def client_in_use_list_raw(self): return self.data[self.CLIENT_IN_USE_LIST[1]:self.CLIENT_IN_USE_LIST[2]+1]

    @property
    def flags_raw(self): return self.data[self.FLAGS[1]:self.FLAGS[2]+1]

    @property
    def sequence_number_bits_raw(self): return self.data[self.SEQUENCE_NUMBER_BITS[1]:self.SEQUENCE_NUMBER_BITS[2]+1]

    @property
    def restart_area_length_raw(self): return self.data[self.RESTART_AREA_LENGTH[1]:self.RESTART_AREA_LENGTH[2]+1]

    @property
    def client_array_offset_raw(self): return self.data[self.CLIENT_ARRAY_OFFSET[1]:self.CLIENT_ARRAY_OFFSET[2]+1]

    @property
    def file_size_raw(self): return self.data[self.FILE_SIZE[1]:self.FILE_SIZE[2]+1]

    @property
    def last_lsn_data_length_raw(self): return self.data[self.LAST_LSN_DATA_LENGTH[1]:self.LAST_LSN_DATA_LENGTH[2]+1]

    @property
    def log_record_hd_length_raw(self): return self.data[self.LOG_RECORD_HD_LENGTH[1]:self.LOG_RECORD_HD_LENGTH[2]+1]

    @property
    def logpage_data_offset_raw(self): return self.data[self.LOGPAGE_DATA_OFFSET[1]:self.LOGPAGE_DATA_OFFSET[2]+1]

    @property
    def restartlog_open_count_raw(self): return self.data[self.RESTARTLOG_OPEN_COUNT[1]:self.RESTARTLOG_OPEN_COUNT[2]+1]

    @property
    def reserved_strt_area_raw(self): return self.data[self.RESERVED_STRT_AREA[1]:self.RESERVED_STRT_AREA[2]+1]

    ####################################################################################################################
    # Interpreted values
    @property
    def current_lsn(self): return reverse_hexlify_int(self.current_lsn_raw)

    @property
    def log_clients(self): return reverse_hexlify_int(self.log_clients_raw)

    @property
    def sequence_number_bits(self): return reverse_hexlify_int(self.sequence_number_bits_raw)

    @property
    def restart_area_length(self): return reverse_hexlify_int(self.restart_area_length_raw)

    @property
    def client_array_offset(self): return reverse_hexlify_int(self.client_array_offset_raw)

    @property
    def file_size(self): return reverse_hexlify_int(self.file_size_raw)

    @property
    def last_lsn_data_length(self): return reverse_hexlify_int(self.last_lsn_data_length_raw)

    @property
    def log_record_hd_length(self): return reverse_hexlify_int(self.log_record_hd_length_raw)

    @property
    def logpage_data_offset(self): return reverse_hexlify_int(self.logpage_data_offset_raw)

    @property
    def restartlog_open_count(self): return reverse_hexlify_int(self.restartlog_open_count_raw)

    ####################################################################################################################
    # Derived values

    ####################################################################################################################
    # Printing

    def all_fields_described(self):
        return(
            (self.CURRENT_LSN, self.current_lsn, self.current_lsn_raw),
            (self.LOG_CLIENTS, self.log_clients, self.log_clients_raw),
            (self.CLIENT_FREE_LIST, '', self.client_free_list_raw),
            (self.CLIENT_IN_USE_LIST, '', self.client_in_use_list_raw),
            (self.FLAGS, '', self.flags_raw),
            (self.SEQUENCE_NUMBER_BITS, self.sequence_number_bits, self.sequence_number_bits_raw),
            (self.RESTART_AREA_LENGTH, self.restart_area_length, self.restart_area_length_raw),
            (self.CLIENT_ARRAY_OFFSET, self.client_array_offset, self.client_array_offset_raw),
            (self.FILE_SIZE, self.file_size, self.file_size_raw),
            (self.LAST_LSN_DATA_LENGTH, self.last_lsn_data_length, self.last_lsn_data_length_raw),
            (self.LOG_RECORD_HD_LENGTH, self.log_record_hd_length, self.log_record_hd_length_raw),
            (self.LOGPAGE_DATA_OFFSET, self.logpage_data_offset, self.logpage_data_offset_raw),
            (self.RESTARTLOG_OPEN_COUNT, self.restartlog_open_count, self.restartlog_open_count_raw),
            (self.RESERVED_STRT_AREA, '', self.reserved_strt_area_raw),
        )


########################################################################################################################
# LOG CLIENT
class LogClient:
    OLDEST_LSN             = ('oldest lsn', 0, 7)
    CLIENT_RESTART_LSN     = ('client restart lsn', 8, 15)
    PREVIOUS_CLIENT        = ('previous client', 16, 17)
    NEXT_CLIENT            = ('next client', 18, 19)
    SEQUENCE_NUMBER        = ('seq. number', 20, 21)
    RESERVED_LC_AREA       = ('reserved', 22, 27)
    CLIENT_NAME_LENGTH     = ('client name length', 28, 31)
    CLIENT_NAME_1          = ('client name 1', 32, 47)
    CLIENT_NAME_2          = ('client name 2', 48, 63)
    CLIENT_NAME_3          = ('client name 3', 64, 79)
    CLIENT_NAME_4          = ('client name 4', 80, 95)

    def __init__(self, data):
        self.data = data

    ####################################################################################################################
    # Raw values
    @property
    def oldest_lsn_raw(self): return self.data[self.OLDEST_LSN[1]:self.OLDEST_LSN[2]+1]

    @property
    def client_restart_lsn_raw(self): return self.data[self.CLIENT_RESTART_LSN[1]:self.CLIENT_RESTART_LSN[2]+1]

    @property
    def previous_client_raw(self): return self.data[self.PREVIOUS_CLIENT[1]:self.PREVIOUS_CLIENT[2]+1]

    @property
    def next_client_raw(self): return self.data[self.NEXT_CLIENT[1]:self.NEXT_CLIENT[2]+1]

    @property
    def sequence_number_raw(self): return self.data[self.SEQUENCE_NUMBER[1]:self.SEQUENCE_NUMBER[2]+1]

    @property
    def reserved_lc_area_raw(self): return self.data[self.RESERVED_LC_AREA[1]:self.RESERVED_LC_AREA[2]+1]

    @property
    def client_name_length_raw(self): return self.data[self.CLIENT_NAME_LENGTH[1]:self.CLIENT_NAME_LENGTH[2]+1]

    @property
    def client_name_1_raw(self): return self.data[self.CLIENT_NAME_1[1]:self.CLIENT_NAME_1[2]+1]

    @property
    def client_name_2_raw(self): return self.data[self.CLIENT_NAME_2[1]:self.CLIENT_NAME_2[2]+1]

    @property
    def client_name_3_raw(self): return self.data[self.CLIENT_NAME_3[1]:self.CLIENT_NAME_3[2]+1]

    @property
    def client_name_4_raw(self): return self.data[self.CLIENT_NAME_4[1]:self.CLIENT_NAME_4[2]+1]

    ####################################################################################################################
    # Interpreted values
    @property
    def oldest_lsn(self): return reverse_hexlify_int(self.oldest_lsn_raw)

    @property
    def client_restart_lsn(self): return reverse_hexlify_int(self.client_restart_lsn_raw)

    @property
    def client_name_length(self): return reverse_hexlify_int(self.client_name_length_raw)

    @property
    def client_name_1(self): return self.client_name_1_raw.decode(encoding='UTF-16').rstrip('\0')

    @property
    def client_name_2(self): return self.client_name_2_raw.decode(encoding='UTF-16').rstrip('\0')

    @property
    def client_name_3(self): return self.client_name_3_raw.decode(encoding='UTF-16').rstrip('\0')

    @property
    def client_name_4(self): return self.client_name_4_raw.decode(encoding='UTF-16').rstrip('\0')

    ####################################################################################################################
    # Derived values

    ####################################################################################################################
    # Printing

    def all_fields_described(self):
        return(
            (self.OLDEST_LSN, self.oldest_lsn, self.oldest_lsn_raw),
            (self.CLIENT_RESTART_LSN, self.client_restart_lsn, self.client_restart_lsn_raw),
            (self.PREVIOUS_CLIENT, '', self.previous_client_raw),
            (self.NEXT_CLIENT, '', self.next_client_raw),
            (self.SEQUENCE_NUMBER, '', self.sequence_number_raw),
            (self.RESERVED_LC_AREA, '', self.reserved_lc_area_raw),
            (self.CLIENT_NAME_LENGTH, self.client_name_length, self.client_name_length_raw),
            (self.CLIENT_NAME_1, self.client_name_1, self.client_name_1_raw),
            (self.CLIENT_NAME_2, self.client_name_2, self.client_name_2_raw),
            (self.CLIENT_NAME_3, self.client_name_3, self.client_name_3_raw),
            (self.CLIENT_NAME_4, self.client_name_4, self.client_name_4_raw)
        )
