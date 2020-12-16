import os

# MFT entry history class
class MFTEntryHistory:
    def __init__(self, mft_object):
        self.mft_entry = mft_object[0]
        self.sequence_val = mft_object[1]
        self.file_name = mft_object[2]
        self.file_path = mft_object[3]
        self.file_size = mft_object[5]
        self.history = {}

    def add_history(self, mft_seq_val, mft_seq_val_hist):
        self.history[mft_seq_val] = mft_seq_val_hist

    def collect_data(self, info):
        # MFT data
        total_tuple = self.mft_entry, self.sequence_val, self.file_name, self.file_size, self.file_path

        # Detail
        detail = {}
        for mft_history_key in sorted(self.history.keys()):
            detail[mft_history_key] = self.history[mft_history_key].collect_data()

        # Collect
        total_list = []
        for values in detail.values():
            for value in values:
                total_list.append(info + total_tuple + value)

        return total_list


# MFT sequence value history class
class MFTSequenceValueHistory:
    def __init__(self, mft_reference_number):
        self.mft_reference_number = mft_reference_number
        self.mft_entry_number, self.seq_value = get_ref_mft_entry_and_seq_num(mft_reference_number)
        self.usn_record_list = []

    def add_usn_record(self, usn_record_object):
        self.usn_record_list.append(usn_record_object)

    def collect_data(self):
        usn_data_list = []
        for usn_record in self.usn_record_list:
            if usn_record.reason == '':
                continue
            total_tuple = usn_record.file_name, usn_record.timestamp, usn_record.reason
            usn_data_list.append(total_tuple)
        return usn_data_list


# UsnJrnl class
class UsnJrnl:
    def __init__(self, usnjrnl_list):
        self.usnjrnl_list = usnjrnl_list
        self.records = []

    def parse(self):
        for record in self.usnjrnl_list:
            self.records.append(UsnRecord(record))

    @property
    def grouped_by_entry(self):
        result = {}
        for record in self.records:
            if record.file_ref_num not in result.keys():
                result[record.file_ref_num] = {}
            if record.file_ref_seq_num not in result[record.file_ref_num].keys():
                result[record.file_ref_num][record.file_ref_seq_num] = []
            result[record.file_ref_num][record.file_ref_seq_num].append(record)
        return result


class UsnRecord:
    def __init__(self, record):
        self.usn = record[0]
        self.reason = process_reason(record[1])
        self.file_ref_num = record[2]
        self.file_ref_mft_entry, self.file_ref_seq_num = get_ref_mft_entry_and_seq_num(record[2])
        self.timestamp = record[3]
        self.file_name = record[4]
        self.file_path_from_mft = record[5]


def combine_usnjrnl(mft, mft_ref_num, seq_val_dict):
    # The basic, current, MFT entry information
    if mft_ref_num in mft.keys():
        mft_entry_hist = MFTEntryHistory(mft[mft_ref_num])
    else:
        # mft_ref_num is not $MFT
        return mft_ref_num

    # For each entry in our $UsnJrnl items (grouped on sequence value)
    for seq_val, records in seq_val_dict.items():
        # Add a MFT history object to the history dict.
        mft_entry_hist.add_history(seq_val, mft_seq_val_hist=MFTSequenceValueHistory(mft_ref_num))
        # Filling the history dict with matching USN and $LogFile records
        for usn_record in records:
            mft_entry_hist.history[seq_val].usn_record_list.append(usn_record)
    return mft_entry_hist


def preprocess_mft(records):
    result = {}
    for record in records:
        mft_ref_entry, seq_num = get_ref_mft_entry_and_seq_num(record[0])
        file_name = os.path.split(record[1])[1]
        file_path = record[1]
        si_create_time = record[2]
        file_size = record[3]
        result[record[0]] = [mft_ref_entry, seq_num, file_name, file_path, si_create_time, file_size]
    return result


def get_ref_mft_entry_and_seq_num(mft_ref_num):
    mft_ref_num = format(int(mft_ref_num), '016x')
    return int(mft_ref_num[4:], 16), int(mft_ref_num[:4], 16)


def collect_mft(info, mft_record):
    # info, mft_entry, sequence_val, file_name, file_size, file_path, usn_file_name, timestamp, reason
    return info + (
        mft_record[0], mft_record[1], mft_record[2], mft_record[5], mft_record[3], mft_record[2], mft_record[4],
        'MFT_FILE_CREATE')


def collect_usnjrnl(info, usn_records_list):
    # info, mft_entry, sequence_val, file_name, file_size, file_path, usn_file_name, timestamp, reason
    result_data = []
    for usn_records in usn_records_list:
        for usn_record in usn_records:
            result_data.append(info + (usn_record.file_ref_mft_entry, usn_record.file_ref_seq_num, usn_record.file_name,
                                       '?', usn_record.file_path_from_mft, usn_record.file_name, usn_record.timestamp,
                                       usn_record.reason))
    return result_data


def process_reason(usn_reason):
    usn_reason_list = usn_reason.replace(' ', '').split('|')
    if 'USN_REASON_FILE_DELETE' not in usn_reason:
        if usn_reason_list[-1] == 'USN_REASON_CLOSE':
            return ''
        else:
            return usn_reason_list[0]
    return 'USN_REASON_FILE_DELETE'
