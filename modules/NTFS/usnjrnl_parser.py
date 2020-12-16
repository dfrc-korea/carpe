from modules.NTFS import util
from modules.NTFS.dfir_ntfs import USN, MFT


def usnjrnl_parse(mft_file, usn_record, path_dict, time_zone):
    r_usn = usn_record.get_usn()
    r_source = USN.ResolveSourceCodes(usn_record.get_source_info())
    r_reason = USN.ResolveReasonCodes(usn_record.get_reason())
    fr_reference_number = usn_record.get_file_reference_number()
    parent_fr_reference_number = usn_record.get_parent_file_reference_number()

    if type(usn_record) is USN.USN_RECORD_V2_OR_V3:
        r_timestamp = util.format_timestamp(usn_record.get_timestamp(), time_zone)
        fr_file_name = usn_record.get_file_name()
    else:
        r_timestamp = ''
        fr_file_name = ''

    fr_number, fr_sequence = MFT.DecodeFileRecordSegmentReference(fr_reference_number)

    try:
        file_record = mft_file.get_file_record_by_number(fr_number, fr_sequence)
        if file_record in path_dict.keys():
            file_paths = path_dict[file_record]
        else:
            file_paths = mft_file.build_full_paths(file_record)
    except MFT.MasterFileTableException:
        fr_file_path = ''
    else:
        if len(file_paths) > 0:
            fr_file_path = file_paths[0]
        else:
            fr_file_path = ''

    return [r_usn, r_source, r_reason, str(fr_reference_number), str(parent_fr_reference_number), r_timestamp,
            fr_file_name, fr_file_path]
