########################################################################################################################
# $LogFile Log-Record class
#
#  This part of code is only focussing on the Log Record of the $LogFile $DATA attribute
#  Used:
#   -   NTFS documentation, R. Russon, Y. Fledel, 2009, page 38-42
#   -   Finding Forensic Information on Creating a Folder in $LogFile of NTFS, M. K. Rogers, 2012
#
# Issues:
#   -   LogFile's structure is difficult to interpret
#   -   Starting spot of first RCRD not yet fixed, offsets are wrong
########################################################################################################################

import os
from binascii import hexlify
from modules.NTFS.ntfs_parse.usn_jrnl.utils import reverse_hexlify_int
from modules.NTFS.ntfs_parse.usn_jrnl import UsnRecord
from modules.NTFS.ntfs_parse.mft import MFTEntry, AttributeFactory, AttributeTypeEnum
from .logfile_utils import search_fixup, replace_fixup, writeout_as_xxd, get_operation_type


class RCRDRecord:
    PAGE_HEADER_LENGTH = 64
    LSN_HEADER_LENGTH = 48
    SECTOR_SIZE = 512
    SECTOR_AMOUNT = 8

    def __init__(self, data, page_nr, dump_dir, remaining=None, offset=0, cluster_size=4096):
        self.data = data
        self.nr = str(page_nr)
        self.dump_dir = dump_dir
        self.offset = offset
        self.cluster_size = cluster_size
        self.leftover = None
        self.prev_leftover = remaining
        self.lsn_stop = 0
        self.error = 0
        self.lsn_entries = []

        self.header = LoggingPageHeader(data[:self.PAGE_HEADER_LENGTH])
        if self.header.malformed_page():
            self.dump_page_to_file(header=True)
            return

        # searching for the fixup_value on the sector endings and replacing them with original code.
        self.offset_dict = search_fixup(self, data)
        if self.offset_dict:
            self.data = replace_fixup(self, data)

        # part that checks if there is a remaining LSN to parse from previous page
        if self.prev_leftover:
            self.parse_prev_leftover()

        # if offset is given start from a different location, otherwise start after page header
        cursor = self.offset if self.offset else self.PAGE_HEADER_LENGTH

        # take the lowest to use as a parsing stop.
        self.lsn_stop = min(self.header.next_record_offset + self.LSN_HEADER_LENGTH, self.cluster_size)

        i = 1
        # parse all the LSN entries and append them to a list 'lsn_entries'
        while cursor + self.LSN_HEADER_LENGTH <= self.lsn_stop:
            # LSN Header
            lsn_header = LSNRecordHeader(self.data[cursor:cursor + self.LSN_HEADER_LENGTH], i, self.nr)
            # LSN Data
            cursor += self.LSN_HEADER_LENGTH
            lsn_data = LSNRecordData(self.data[cursor:cursor + lsn_header.data_length], i)
            # Check validity
            if self.error > 1:
                self.dump_page_to_file(cursor=cursor)
                # print('2nd error')
                break
            elif lsn_header.malformed_entry() or lsn_data.malformed_entry():
                cursor = self.header.next_record_offset
                self.error += 1
                self.dump_page_to_file(cursor=cursor)
                # print('1st error')
                continue
            cursor += lsn_header.data_length
            # check if data is not split across next page
            if lsn_header.is_split:
                self.leftover = LeftOverData(lsn_header, lsn_data, self.data[self.header.next_record_offset:])
                continue
            # append to list and set new offsets
            self.lsn_entries.append((lsn_header, lsn_data))
            i += 1

    ####################################################################################################################
    # class functions

    # parse remaining split LSN from previous page
    def parse_prev_leftover(self):
        finalizing_data = self.data[self.PAGE_HEADER_LENGTH:self.PAGE_HEADER_LENGTH+self.prev_leftover.missing_data_length]
        self.prev_leftover.data += finalizing_data
        self.prev_leftover.lsn_data = LSNRecordData(self.prev_leftover.data, 0)
        self.prev_leftover.lsn_hdr.page_nr = self.nr
        self.prev_leftover.lsn_hdr.nr = str(0)
        if not self.prev_leftover.lsn_hdr.malformed_entry() and not self.prev_leftover.lsn_data.malformed_entry():
            self.lsn_entries.append((self.prev_leftover.lsn_hdr, self.prev_leftover.lsn_data))
            self.offset = self.PAGE_HEADER_LENGTH + self.prev_leftover.missing_data_length

    # dump raw data to file
    def dump_page_to_file(self, header=None, cursor=None):
        pre = 'non_valid_page_' if header else 'page_'
        offset = '_'+str(cursor) if cursor else ''
        # dump_path = os.path.join(os.getcwd(), self.dump_dir) if self.dump_dir else os.getcwd()
        # print(dump_path)
        filename = os.path.join(self.dump_dir, pre+self.nr+offset)
        with open(filename, 'wb') as f:
            f.write(self.data)

    ####################################################################################################################
    # PRINT functions
    def writeout_parsed(self, out):
        self.writeout_basic(out)

    def writeout_headers(self, out):
        self.writeout_page_header(out)
        for (lsn_header, lsn_data) in self.lsn_entries:
            lsn_header.writeout_parsed(out)

    def writeout_basic(self, out):
        self.writeout_page_header(out)
        for (lsn_header, lsn_data) in self.lsn_entries:
            lsn_header.writeout_parsed(out)
            lsn_data.writeout_parsed(out)

    def writeout_leftover(self, out):
        if self.leftover:
            self.leftover.writeout_header(out)
            self.leftover.writeout_data(out)
            #self.leftover.writeout_raw_data(out)
        else:
            out.write('    ---- No LEFTOVER ----\n')

    def writeout_all(self, out):
        self.writeout_page_header(out)
        for (lsn_header, lsn_data) in self.lsn_entries:
            lsn_header.writeout_parsed(out)
            lsn_data.writeout_parsed(out)
            lsn_data.writeout_operation_data(out)
            lsn_data.writeout_itrprt_op_data(out)
        self.writeout_leftover(out)

    def writeout_page_header(self, out):
        out.write('\n'
                  '=================================================================================================\n'
                  '= RCRD Record %s\n' % self.nr)
        out.write('  ---- log page Header --------------------------------------------------------------------------\n')
        for (description, low, high), value, value_raw in self.header.all_fields_described():
            out.write('  %-30s | %-5s | %-11s | %s\n' % (description, str(low) + '-' + str(high),
                                                           value, hexlify(value_raw)))

    def export_csv(self, csv_writer):
        if not self.lsn_entries:
            csv_writer.writerow(self.formatted_output())
            return
        for (lsn_hdr, lsn_data) in self.lsn_entries:
            record = self.formatted_output()
            record.extend(lsn_hdr.formatted_output())
            record.extend(lsn_data.formatted_output())
            csv_writer.writerow(record)

    # Some ordering variables, used in the future, not finished
    @property
    def connector_prev_lsn(self):
        if self.lsn_entries:
            return self.lsn_entries[0][0].previous_lsn
        else:
            return None

    @property
    def connector_last_lsn(self):
        return self.header.last_end_lsn

    @property
    def entry_count(self):
        return len(self.lsn_entries)

    @property
    def formatted_csv_column_headers(self):
        return ['conn prev LSN',  # Page info
                'conn last LSN',
                ]

    @property
    def lsn_header_csv_columns(self):
        return LSNRecordHeader.formatted_csv_column_headers()

    @property
    def lsn_data_csv_columns(self):
        return LSNRecordData.formatted_csv_column_headers()

    def formatted_output(self):
        return[self.connector_prev_lsn,
               self.connector_last_lsn
               ]


########################################################################################################################
# Logging page header
class LoggingPageHeader:
    MAGIC_NUMBER                    = ('magic number (name)', 0, 3)
    UPDATE_SEQ_ARRAY_OFFSET         = ('update seq. array offset', 4, 5)
    UPDATE_SEQ_ARRAY_COUNT          = ('update seq. array count', 6, 7)
    LAST_LSN_or_OFFSET_TO_NEXT_PAGE = ('last lsn / offset to next page', 8, 15)
    FLAGS                           = ('flags', 16, 19)
    PAGE_COUNT                      = ('page count', 20, 21)
    PAGE_POSITION                   = ('page position', 22, 23)
    NEXT_RECORD_OFFSET              = ('next record offset', 24, 25)
    RESERVED1                       = ('reserved1', 26, 31)
    LAST_END_LSN                    = ('last end lsn', 32, 39)
    FIXUP_VALUE                     = ('fixup value', 40, 41)
    FIXUP_ARRAY                     = ('fixup array', 42, 57)
    RESERVED2                       = ('reserved2', 58, 63)

    def __init__(self, data):
        self.data = data
        self.length = 64

    def malformed_page(self):
        return True if self.magic_number_raw != b'\x52\x43\x52\x44' or \
                       self.fixup_value_raw == b'\x00\x00' \
                       else False

    ####################################################################################################################
    # Raw values
    @property
    def magic_number_raw(self): return self.data[self.MAGIC_NUMBER[1]:self.MAGIC_NUMBER[2]+1]

    @property
    def update_seq_array_offset_raw(self): return self.data[self.UPDATE_SEQ_ARRAY_OFFSET[1]:self.UPDATE_SEQ_ARRAY_OFFSET[2]+1]

    @property
    def update_seq_array_count_raw(self): return self.data[self.UPDATE_SEQ_ARRAY_COUNT[1]:self.UPDATE_SEQ_ARRAY_COUNT[2]+1]

    @property
    def last_lsn_or_offset_to_next_page_raw(self): return self.data[self.LAST_LSN_or_OFFSET_TO_NEXT_PAGE[1]:self.LAST_LSN_or_OFFSET_TO_NEXT_PAGE[2]+1]

    @property
    def flags_raw(self): return self.data[self.FLAGS[1]:self.FLAGS[2]+1]

    @property
    def page_count_raw(self): return self.data[self.PAGE_COUNT[1]:self.PAGE_COUNT[2]+1]

    @property
    def page_position_raw(self): return self.data[self.PAGE_POSITION[1]:self.PAGE_POSITION[2]+1]

    @property
    def next_record_offset_raw(self): return self.data[self.NEXT_RECORD_OFFSET[1]:self.NEXT_RECORD_OFFSET[2]+1]

    @property
    def reserved1_raw(self): return self.data[self.RESERVED1[1]:self.RESERVED1[2]+1]

    @property
    def last_end_lsn_raw(self): return self.data[self.LAST_END_LSN[1]:self.LAST_END_LSN[2]+1]

    @property
    def fixup_value_raw(self): return self.data[self.FIXUP_VALUE[1]:self.FIXUP_VALUE[2]+1]

    @property
    def fixup_array_raw(self): return self.data[self.FIXUP_ARRAY[1]:self.FIXUP_ARRAY[2]+1]

    @property
    def reserved2_raw(self): return self.data[self.RESERVED2[1]:self.RESERVED2[2]+1]

    ####################################################################################################################
    # Interpreted values
    @property
    def magic_number(self):
        magic_nr = self.magic_number_raw
        return magic_nr.decode() if magic_nr == b'\x52\x43\x52\x44' else hexlify(magic_nr)

    @property
    def update_seq_array_offset(self): return reverse_hexlify_int(self.update_seq_array_offset_raw)

    @property
    def update_seq_array_count(self): return reverse_hexlify_int(self.update_seq_array_count_raw)

    @property
    def last_lsn_or_offset_to_next_page(self): return reverse_hexlify_int(self.last_lsn_or_offset_to_next_page_raw)

    @property
    def flags(self): return reverse_hexlify_int(self.flags_raw)

    @property
    def page_count(self): return reverse_hexlify_int(self.page_count_raw)

    @property
    def page_position(self): return reverse_hexlify_int(self.page_position_raw)

    @property
    def next_record_offset(self): return reverse_hexlify_int(self.next_record_offset_raw)

    @property
    def last_end_lsn(self): return reverse_hexlify_int(self.last_end_lsn_raw)

    @property
    def fixup_value(self): return hexlify(self.fixup_value_raw)

    @property
    def fixup_array(self): return hexlify(self.fixup_array_raw)

    ####################################################################################################################
    # Derived values

    ####################################################################################################################
    # Printing

    def all_fields_described(self):
        return(
            (self.MAGIC_NUMBER, self.magic_number, self.magic_number_raw),
            (self.UPDATE_SEQ_ARRAY_OFFSET, self.update_seq_array_offset, self.update_seq_array_offset_raw),
            (self.UPDATE_SEQ_ARRAY_COUNT, self.update_seq_array_count, self.update_seq_array_count_raw),
            (self.LAST_LSN_or_OFFSET_TO_NEXT_PAGE, self.last_lsn_or_offset_to_next_page, self.last_lsn_or_offset_to_next_page_raw),
            (self.FLAGS, self.flags, self.flags_raw),
            (self.PAGE_COUNT, self.page_count, self.page_count_raw),
            (self.PAGE_POSITION, self.page_position, self.page_position_raw),
            (self.NEXT_RECORD_OFFSET, self.next_record_offset, self.next_record_offset_raw),
            (self.RESERVED1, '', self.reserved1_raw),
            (self.LAST_END_LSN, self.last_end_lsn, self.last_end_lsn_raw),
            (self.FIXUP_VALUE, self.fixup_value, self.fixup_value_raw),
            (self.FIXUP_ARRAY, '', self.fixup_array_raw),
            (self.RESERVED2, '', self.reserved2_raw),
        )


########################################################################################################################
# LSN Record header
class LSNRecordHeader:
    THIS_LSN               = ('this lsn', 0, 7)
    PREVIOUS_LSN           = ('previous lsn', 8, 15)
    UNDO_NEXT_LSN          = ('undo next lsn', 16, 23)
    DATA_LENGTH            = ('data length', 24, 27)
    SEQ_NUMBER             = ('sequence number', 28, 29)
    CLIENT_INDEX           = ('client index', 30, 31)
    RECORD_TYPE            = ('record type', 32, 35)
    TRANSACTION_ID         = ('transaction ID', 36, 39)
    FLAG                   = ('flag', 40,41 )
    RESERVED               = ('reserved', 42, 47)

    def __init__(self, data, nr, page_nr):
        self.data = data
        self.length = 48
        self.nr = str(nr)
        self.page_nr = page_nr
        self.transaction_num = None

    def malformed_entry(self):
        return True if self.this_lsn == 0 or \
                       self.record_type == 0 or \
                       self.record_type > 37 \
                       else False

    ####################################################################################################################
    # Raw values

    @property
    def this_lsn_raw(self): return self.data[self.THIS_LSN[1]:self.THIS_LSN[2]+1]

    @property
    def previous_lsn_raw(self): return self.data[self.PREVIOUS_LSN[1]:self.PREVIOUS_LSN[2]+1]

    @property
    def undo_next_lsn_raw(self): return self.data[self.UNDO_NEXT_LSN[1]:self.UNDO_NEXT_LSN[2]+1]

    @property
    def data_length_raw(self): return self.data[self.DATA_LENGTH[1]:self.DATA_LENGTH[2]+1]

    @property
    def seq_number_raw(self): return self.data[self.SEQ_NUMBER[1]:self.SEQ_NUMBER[2]+1]

    @property
    def client_index_raw(self): return self.data[self.CLIENT_INDEX[1]:self.CLIENT_INDEX[2]+1]

    @property
    def record_type_raw(self): return self.data[self.RECORD_TYPE[1]:self.RECORD_TYPE[2]+1]

    @property
    def transaction_id_raw(self): return self.data[self.TRANSACTION_ID[1]:self.TRANSACTION_ID[2]+1]

    @property
    def flag_raw(self): return self.data[self.FLAG[1]:self.FLAG[2]+1]

    @property
    def reserved_raw(self): return self.data[self.RESERVED[1]:self.RESERVED[2]+1]

    ####################################################################################################################
    # Interpreted values
    @property
    def this_lsn(self): return reverse_hexlify_int(self.this_lsn_raw)

    @property
    def previous_lsn(self): return reverse_hexlify_int(self.previous_lsn_raw)

    @property
    def undo_next_lsn(self): return reverse_hexlify_int(self.undo_next_lsn_raw)

    @property
    def data_length(self): return reverse_hexlify_int(self.data_length_raw)

    @property
    def seq_number(self): return reverse_hexlify_int(self.seq_number_raw)

    @property
    def client_index(self): return reverse_hexlify_int(self.client_index_raw)

    @property
    def record_type(self): return reverse_hexlify_int(self.record_type_raw)

    @property
    def transaction_id(self): return reverse_hexlify_int(self.transaction_id_raw)

    @property
    def flag(self): return reverse_hexlify_int(self.flag_raw)

    # @property
    # def reserved(self): return self.

    ####################################################################################################################
    # Derived values
    @property
    def deriv_record_type(self):
        rcd_type = self.record_type
        if   rcd_type == 1: return 'transaction'
        elif rcd_type == 2: return 'checkpoint'
        else              : return 'unknown'

    @property
    def is_split(self):
        return bool(self.flag & 1)  # <- bitwise AND operation with 1

    @property
    def deriv_split_record(self):
        if self.is_split: return 'LSN entry is split'
        else            : return ''

    ####################################################################################################################
    # Printing
    def all_fields_described(self):
        return (
            (self.THIS_LSN, self.this_lsn, self.this_lsn_raw),
            (self.PREVIOUS_LSN, self.previous_lsn, self.previous_lsn_raw),
            (self.UNDO_NEXT_LSN, self.undo_next_lsn, self.undo_next_lsn_raw),
            (self.DATA_LENGTH, self.data_length, self.data_length_raw),
            (self.SEQ_NUMBER, self.seq_number, self.seq_number_raw),
            (self.CLIENT_INDEX, self.client_index, self.client_index_raw),
            (self.RECORD_TYPE, self.deriv_record_type, self.record_type_raw),
            (self.TRANSACTION_ID, self.transaction_id, self.transaction_id_raw),
            (self.FLAG, self.deriv_split_record, self.flag_raw),
            (self.RESERVED, '', self.reserved_raw)
        )

    def writeout_parsed(self, out):
        out.write('\n')
        out.write('    ---- log LSN header '+self.nr+' -------------------------------------------------------------\n')
        out.write('    ---- RCRD page: '+self.page_nr+'\n')
        for (description, low, high), value, value_raw in self.all_fields_described():
            out.write('    %-32s | %-7s | %-25s | %s\n' % (description, str(low) + '-' + str(high),
                                                          value, hexlify(value_raw)))

    @staticmethod
    def formatted_csv_column_headers():
        return ['page nr',
                'nr in page',
                'transaction num',
                'this LSN',
                'previous LSN',
                'undo next LSN',
                'data length',
                'sequence nr',
                'client index',
                'record type',
                'derived record type',
                'transaction id',
                'flag',
                'is split?',
                ]

    def formatted_output(self):
        return [self.page_nr,
                self.nr,
                self.transaction_num,
                self.this_lsn,
                self.previous_lsn,
                self.undo_next_lsn,
                self.data_length,
                self.seq_number,
                self.client_index,
                self.record_type,
                self.deriv_record_type,
                self.transaction_id,
                self.flag,
                self.is_split,
                ]


########################################################################################################################
# LSN Record data
class LSNRecordData:
    REDO_OPERATION         = ('redo operation', 0, 1)
    UNDO_OPERATION         = ('undo operation', 2, 3)
    REDO_OFFSET            = ('redo offset', 4, 5)
    REDO_LENGTH            = ('redo length', 6, 7)
    UNDO_OFFSET            = ('undo offset', 8, 9)
    UNDO_LENGTH            = ('undo length', 10, 11)
    TARGET_ATTRIBUTE       = ('target attribute', 12, 13)
    LCNs_TO_FOLLOW         = ('LCNs to follow', 14, 15)
    RECORD_OFFSET          = ('record offset', 16, 17)
    ATTR_OFFSET            = ('Attribute offset', 18, 19)
    MFT_CLUSTER_INDEX      = ('mft cluster index', 20, 21)
    ALIGNMENT_or_RESERVED1 = ('alignment / reserved 1', 22, 23)
    TARGET_VCN             = ('target virtual cluster nr (vcn)', 24, 27)
    ALIGNMENT_or_RESERVED2 = ('alignment / reserved 2', 28, 31)
    TARGET_LCN             = ('target logical cluster nr (lcn)', 32, 35)
    ALIGNMENT_or_RESERVED3 = ('alignment / reserved 3', 36, 39)
    OPERATION_CODE_DATA    = {'descr': 'data depend on op-code',
                              'start': 40,
                              'end'  : 4031}  # remaining of 4K page

    def __init__(self, data, nr):
        # delins: data is attached to this object here, but this lsn may actually get popped from the lsn list,
        # giving it different date (from the next page). Is this handled well?
        # Perhaps it's safer to add an if clause in the parsing loop to explicitly handle the case of a split
        # record there.
        self.data = data
        self.nr = str(nr)
        self.OPERATION_CODE_DATA['start'] = self.redo_offset
        self.OPERATION_CODE_DATA['end'] = self.undo_offset + self.undo_length

    def malformed_entry(self):
        return True if self.redo_operation > 37 or \
                       self.undo_operation > 37 \
                       else False


    ####################################################################################################################
    # Raw values
    @property
    def redo_operation_raw(self): return self.data[self.REDO_OPERATION[1]:self.REDO_OPERATION[2]+1]

    @property
    def undo_operation_raw(self): return self.data[self.UNDO_OPERATION[1]:self.UNDO_OPERATION[2]+1]

    @property
    def redo_offset_raw(self): return self.data[self.REDO_OFFSET[1]:self.REDO_OFFSET[2]+1]

    @property
    def redo_length_raw(self): return self.data[self.REDO_LENGTH[1]:self.REDO_LENGTH[2]+1]

    @property
    def undo_offset_raw(self): return self.data[self.UNDO_OFFSET[1]:self.UNDO_OFFSET[2]+1]

    @property
    def undo_length_raw(self): return self.data[self.UNDO_LENGTH[1]:self.UNDO_LENGTH[2]+1]

    @property
    def target_attribute_raw(self): return self.data[self.TARGET_ATTRIBUTE[1]:self.TARGET_ATTRIBUTE[2]+1]

    @property
    def lcns_to_follow_raw(self): return self.data[self.LCNs_TO_FOLLOW[1]:self.LCNs_TO_FOLLOW[2] + 1]

    @property
    def record_offset_raw(self): return self.data[self.RECORD_OFFSET[1]:self.RECORD_OFFSET[2]+1]

    @property
    def attr_offset_raw(self): return self.data[self.ATTR_OFFSET[1]:self.ATTR_OFFSET[2]+1]

    @property
    def mft_cluster_index_raw(self): return self.data[self.MFT_CLUSTER_INDEX[1]:self.MFT_CLUSTER_INDEX[2]+1]

    @property
    def alignment_or_reserved1_raw(self): return self.data[self.ALIGNMENT_or_RESERVED1[1]:self.ALIGNMENT_or_RESERVED1[2]+1]

    @property
    def target_vcn_raw(self): return self.data[self.TARGET_VCN[1]:self.TARGET_VCN[2]+1]

    @property
    def alignment_or_reserved2_raw(self): return self.data[self.ALIGNMENT_or_RESERVED2[1]:self.ALIGNMENT_or_RESERVED2[2]+1]

    @property
    def target_lcn_raw(self): return self.data[self.TARGET_LCN[1]:self.TARGET_LCN[2]+1]

    @property
    def alignment_or_reserved3_raw(self): return self.data[self.ALIGNMENT_or_RESERVED3[1]:self.ALIGNMENT_or_RESERVED3[2]+1]

    @property
    def operation_code_data_raw(self): return self.data[self.OPERATION_CODE_DATA['start']:self.OPERATION_CODE_DATA['end']]

    @property
    def redo_data_raw(self):
        return self.data[self.redo_offset:(self.redo_offset+self.redo_length)]

    @property
    def undo_data_raw(self):
        return self.data[self.undo_offset:(self.undo_offset+self.undo_length)]

    ####################################################################################################################
    # Interpreted values
    @property
    def redo_operation(self): return reverse_hexlify_int(self.redo_operation_raw)

    @property
    def undo_operation(self): return reverse_hexlify_int(self.undo_operation_raw)

    @property
    def redo_offset(self): return reverse_hexlify_int(self.redo_offset_raw)

    @property
    def redo_length(self): return reverse_hexlify_int(self.redo_length_raw)

    @property
    def undo_offset(self): return reverse_hexlify_int(self.undo_offset_raw)

    @property
    def undo_length(self): return reverse_hexlify_int(self.undo_length_raw)

    @property
    def target_attribute(self): return reverse_hexlify_int(self.target_attribute_raw)

    @property
    def lcns_to_follow(self): return reverse_hexlify_int(self.lcns_to_follow_raw)

    @property
    def record_offset(self): return reverse_hexlify_int(self.record_offset_raw)

    @property
    def attr_offset(self): return reverse_hexlify_int(self.attr_offset_raw)

    @property
    def mft_cluster_index(self): return reverse_hexlify_int(self.mft_cluster_index_raw)

    # @property
    # def alignment_or_reserved1(self): return self.

    @property
    def target_vcn(self): return reverse_hexlify_int(self.target_vcn_raw)

    # @property
    # def alignment_or_reserved2(self): return self.

    @property
    def target_lcn(self): return reverse_hexlify_int(self.target_lcn_raw)

    # @property
    # def alignment_or_reserved3(self): return self.
    #
    # @property
    # def data(self): return self.

    @property
    def interpret_operation_data(self):
        return OperationCode(self.redo_operation, self.undo_operation, self.redo_data_raw, self.undo_data_raw,
                             self.redo_length, self.undo_length, self.deriv_inum)

    ####################################################################################################################
    # Derived values
    @property
    def deriv_redo_operation_type(self):
        return get_operation_type(self.redo_operation)

    @property
    def deriv_undo_operation_type(self):
        return get_operation_type(self.undo_operation)

    @property
    def deriv_lcns_to_follow(self):
        lcn_type = self.lcns_to_follow
        if lcn_type == 0  : return 'no next rcd'
        elif lcn_type == 1: return 'has next rcd'
        else              : return 'unknown'

    @property
    def deriv_inum(self):
        # (mft_cluster_index * sector_size)/MFT_entry_size => (index*512)/1024 => index/2
        return int(self.target_vcn * 4 + self.mft_cluster_index / 2)

    ####################################################################################################################
    # Printing
    def all_fields_described(self):
        return (
            (self.REDO_OPERATION, self.deriv_redo_operation_type, self.redo_operation_raw),
            (self.UNDO_OPERATION, self.deriv_undo_operation_type, self.undo_operation_raw),
            (self.REDO_OFFSET, self.redo_offset, self.redo_offset_raw),
            (self.REDO_LENGTH, self.redo_length, self.redo_length_raw),
            (self.UNDO_OFFSET, self.undo_offset, self.undo_offset_raw),
            (self.UNDO_LENGTH, self.undo_length, self.undo_length_raw),
            (self.TARGET_ATTRIBUTE, self.target_attribute, self.target_attribute_raw),
            (self.LCNs_TO_FOLLOW, self.deriv_lcns_to_follow, self.lcns_to_follow_raw),
            (self.RECORD_OFFSET, self.record_offset, self.record_offset_raw),
            (self.ATTR_OFFSET, self.attr_offset, self.attr_offset_raw),
            (self.MFT_CLUSTER_INDEX, self.mft_cluster_index, self.mft_cluster_index_raw),
            (self.ALIGNMENT_or_RESERVED1, '', self.alignment_or_reserved1_raw),
            (self.TARGET_VCN, self.target_vcn, self.target_vcn_raw),
            (self.ALIGNMENT_or_RESERVED2, '', self.alignment_or_reserved2_raw),
            (self.TARGET_LCN, self.target_lcn, self.target_lcn_raw),
            (self.ALIGNMENT_or_RESERVED3, '', self.alignment_or_reserved3_raw),
            (self.opcode_data_field_described(), '', b'')
        )

    # helper function to get the basic info printed
    def opcode_data_field_described(self):
        descriptive_data = (self.OPERATION_CODE_DATA['descr'],
                            self.OPERATION_CODE_DATA['start'],
                            self.OPERATION_CODE_DATA['end'])
        return descriptive_data

    def writeout_parsed(self, out):
        out.write('    ---- log LSN Data '+self.nr+' ---------------------------------------------------------------\n')
        for (description, low, high), value, value_raw in self.all_fields_described():
            out.write('    %-32s | %-7s | %-25s | %s\n' % (description, str(low) + '-' + str(high),
                                                           value, hexlify(value_raw)))

    def writeout_operation_data(self, out):
        out.write('      ---- op-code Data '+self.nr+'--------------------------------------------------------------\n')
        out.write('      redo:\n')
        writeout_as_xxd(self.redo_data_raw, out)
        out.write('      undo:\n')
        writeout_as_xxd(self.undo_data_raw, out)

    def writeout_itrprt_op_data(self, out):
        # if self.interpret_operation_data and self.interpret_operation_data.operation_object:
        if self.interpret_operation_data.operation_object:
            self.interpret_operation_data.writeout_parsed(out)

    @staticmethod
    def formatted_csv_column_headers():
        return ['redo operation',
                'undo operation',
                'deriv redo',
                'deriv undo',
                'redo offset',
                'redo length',
                'undo offset',
                'undo length',
                'target attribute',
                'lcn to follow?',
                'record offset',
                'attribute offset',
                'MFT cluster index',
                'target VCN',
                'target LCN',
                'deriv inum',
                'em_MFT seq value',
                'em_USN usn',
                'em_ATTR filename'
                ]

    def formatted_output(self):
        record = [self.redo_operation,
                  self.undo_operation,
                  self.deriv_redo_operation_type,
                  self.deriv_undo_operation_type,
                  self.redo_offset,
                  self.redo_length,
                  self.undo_offset,
                  self.undo_length,
                  self.target_attribute,
                  self.lcns_to_follow,
                  self.record_offset,
                  self.attr_offset,
                  self.mft_cluster_index,
                  self.target_vcn,
                  self.target_lcn,
                  self.deriv_inum
                  ]

        if self.interpret_operation_data.operation_object:
            if self.interpret_operation_data.operation_type == 'embedded mft':
                record.extend([self.interpret_operation_data.operation_object.sequence_value, None, None])
            elif self.interpret_operation_data.operation_type == 'embedded usn':
                record.extend([None, self.interpret_operation_data.operation_object.usn, None])
            elif self.interpret_operation_data.operation_type == 'embedded mft attribute' and \
                    self.interpret_operation_data.operation_object.header.enum == 'FILE_NAME':
                        record.extend([None, None, self.interpret_operation_data.operation_object.name])
            else:
                record.extend([None, None, None])
        else:
            record.extend([None, None, None])
        return record


########################################################################################################################
# Helper class to make interaction with leftover data easier
class LeftOverData:
    def __init__(self, lsn_hdr, lsn_data, data):
        self.lsn_hdr = lsn_hdr
        self.lsn_data = lsn_data
        self.data = data[self.lsn_hdr.length:]
        self.data_length = len(self.data)
        self.missing_data_length = self.lsn_hdr.data_length - self.data_length

    def writeout_header(self, out):
        out.write('    ---- log LSN header -----LEFTOVER-----LEFTOVER-----LEFTOVER-----LEFTOVER-----LEFTOVER--------\n')
        for (description, low, high), value, value_raw in self.lsn_hdr.all_fields_described():
            out.write('    %-32s | %-7s | %-25s | %s\n' % (description, str(low) + '-' + str(high),
                                                           value, hexlify(value_raw)))

    def writeout_data(self, out):
        out.write('    ---- log LSN Data -------LEFTOVER-----LEFTOVER-----LEFTOVER-----LEFTOVER-----LEFTOVER--------\n')
        for (description, low, high), value, value_raw in self.lsn_data.all_fields_described():
            out.write('    %-32s | %-7s | %-25s | %s\n' % (description, str(low) + '-' + str(high),
                                                           value, hexlify(value_raw)))

    def writeout_raw_data(self, out):
        out.write('    ---- raw Data ~~ excl header ~~---LEFTOVER-----LEFTOVER-----LEFTOVER-----LEFTOVER------------\n')
        writeout_as_xxd(self.data, out)


########################################################################################################################
# Helper class for interpreting operation data (redo/undo operations)
class OperationCode:
    NO_OPERATION                     = 0
    COMPENSATION_LOG_RECORD          = 1
    INITIALIZE_FILE_RECORD_SEGMENT   = 2
    DEALLOCATE_FILE_RECORD_SEGMENT   = 3
    WRITE_END_OF_FILE_RECORD_SEGMENT = 4
    CREATE_ATTRIBUTE                 = 5
    DELETE_ATTRIBUTE                 = 6
    UPDATE_RESIDENT_VALUE            = 7
    UPDATE_NONRESIDENT_VALUE         = 8
    UPDATE_MAPPING_PAIRS             = 9
    DELETE_DIRTY_CLUSTERS            = 10
    SET_NEW_ATTRIBUTE_SIZES          = 11
    ADD_INDEX_ENTRY_ROOT             = 12
    DELETE_INDEX_ENTRY_ROOT          = 13
    ADD_INDEX_ENTRY_ALLOCATION       = 14
    DELETE_INDEX_ENTRY_ALLOCATION    = 15
    SET_INDEX_ENTRY_VCN_ALLOCATION   = 18
    UPDATE_FILE_NAME_ROOT            = 19
    UPDATE_FILE_NAME_ALLOCATION      = 20
    SET_BITS_IN_NONRESIDENT_BITMAP   = 21
    CLEAR_BITS_IN_NONRESIDENT_BITMAP = 22
    PREPARE_TRANSACTION              = 25
    COMMIT_TRANSACTION               = 26
    FORGET_TRANSACTION               = 27
    OPEN_NON_RESIDENT_ATTRIBUTE      = 28
    DIRTY_PAGE_TABLE_DUMP            = 31
    TRANSACTION_TABLE_DUMP           = 32
    UPDATE_RECORD_DATA_ROOT          = 33

    def __init__(self, redo_op, undo_op, redo_data, undo_data, redo_length, undo_length, deriv_inum):
        self.operation_type = None
        self.operation_object = None

        if redo_op == self.SET_BITS_IN_NONRESIDENT_BITMAP and undo_op == self.CLEAR_BITS_IN_NONRESIDENT_BITMAP:
            pass
        # getting the MFT entry out of the data
        elif redo_op == self.INITIALIZE_FILE_RECORD_SEGMENT and undo_op == self.NO_OPERATION and redo_length > 0 and len(redo_data) > 0:
            self.operation_type = 'embedded mft'
            self.operation_object = MFTEntry(inum=deriv_inum, data=redo_data, logfile_parse=True)
        elif redo_op == self.DELETE_ATTRIBUTE and undo_op == self.CREATE_ATTRIBUTE and undo_length > 0 and len(undo_data) > 0:
            self.operation_type = 'embedded mft attribute'
            self.operation_object = AttributeFactory.create_attribute(undo_data)
        elif redo_op == self.CREATE_ATTRIBUTE and undo_op == self.DELETE_ATTRIBUTE and redo_length > 0 and len(redo_data) > 0:
            self.operation_type = 'embedded mft attribute'
            self.operation_object = AttributeFactory.create_attribute(redo_data)
        elif redo_op == self.CREATE_ATTRIBUTE and undo_op == self.DELETE_ATTRIBUTE:
            pass
        elif redo_op == self.DELETE_INDEX_ENTRY_ALLOCATION and undo_op == self.ADD_INDEX_ENTRY_ALLOCATION:
            pass
        elif redo_op == self.ADD_INDEX_ENTRY_ALLOCATION and undo_op == self.DELETE_INDEX_ENTRY_ALLOCATION:
            pass
        elif redo_op == self.UPDATE_NONRESIDENT_VALUE and undo_op == self.NO_OPERATION:
            record = UsnRecord(redo_data, 0)
            if record:
                self.operation_object = record
                self.operation_type = 'embedded usn'

    def writeout_parsed(self, out):
        self.operation_object.writeout_parsed(out)
