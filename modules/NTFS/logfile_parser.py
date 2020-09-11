import json

from modules.NTFS import util
from modules.NTFS.dfir_ntfs import USN, LogFile, Attributes, MFT


def restart_area_parse(restart_area):
    restart_area_version = f"{restart_area.get_major_version()}.{restart_area.get_minor_version()}"

    # lsn, version, checkpoint, attribute_table, attribute_name, dirty_page_table, transaction_table
    restart_area_items = (restart_area.lsn, restart_area_version, restart_area.get_start_of_checkpoint_lsn(),
                          restart_area.get_open_attribute_table_lsn(), restart_area.get_open_attribute_table_length(),
                          restart_area.get_attribute_names_lsn(), restart_area.get_attribute_names_length(),
                          restart_area.get_dirty_page_table_lsn(), restart_area.get_dirty_page_table_length(),
                          restart_area.get_transaction_table_lsn(), restart_area.get_transaction_table_length())

    return restart_area_items


def log_record_parse(log_record, mft_file):
    target_attribute_name = None
    redo_op = log_record.get_redo_operation()
    undo_op = log_record.get_undo_operation()
    redo_data = log_record.get_redo_data()
    undo_data = log_record.get_undo_data()

    log_record_items = [log_record.lsn, log_record.transaction_id,
                        LogFile.ResolveNTFSOperation(redo_op), LogFile.ResolveNTFSOperation(undo_op)]

    target = log_record.calculate_mft_target_number()
    if target is not None:
        log_record_items.append(target)

        try:
            file_record = mft_file.get_file_record_by_number(target)
            file_paths = mft_file.build_full_paths(file_record)
        except MFT.MasterFileTableException:
            fr_file_path = None
        else:
            if len(file_paths) > 0:
                fr_file_path = file_paths[0]
            else:
                fr_file_path = None
        log_record_items.append(None)  # target_reference
        log_record_items.append(None)  # target_attribute_name
        log_record_items.append(fr_file_path)
    else:
        log_record_items.append(None)  # target_file_number
        target = log_record.calculate_mft_target_reference_and_name()
        if target is not None:
            target_reference, target_attribute_name = target

            log_record_items.append(target_reference)

            if target_attribute_name is None:
                target_attribute_name = '-'

            log_record_items.append(target_attribute_name)

            fr_number, fr_sequence = MFT.DecodeFileRecordSegmentReference(target_reference)

            try:
                file_record = mft_file.get_file_record_by_number(fr_number, fr_sequence)
                file_paths = mft_file.build_full_paths(file_record)
            except MFT.MasterFileTableException:
                fr_file_path = None
            else:
                if len(file_paths) > 0:
                    fr_file_path = file_paths[0]
                else:
                    fr_file_path = None
            log_record_items.append(fr_file_path)
        else:
            log_record_items.append(None)  # target_reference
            log_record_items.append(None)  # target_attribute_name
            log_record_items.append(None)  # file_path

        # current lsn 필드로부터 target vcn 필드 사이의 거리, 필요없어서 뺌
        # log_record_items.append(log_record.get_target_attribute())

    offset_in_target = log_record.calculate_offset_in_target()
    if offset_in_target is not None:
        log_record_items.append(offset_in_target)
    else:
        log_record_items.append('Unknown')

    lcns = []
    try:
        for lcn in log_record.get_lcns_for_page():
            lcns.append(str(lcn))
    except LogFile.ClientException:
        return log_record_items
    # output_lines.append('Warning: truncated page')
    # return '\n'.join(output_lines)

    if len(lcns) > 0:
        log_record_items.append(' '.join(lcns))
    else:
        log_record_items.append(None)  # lcns

    log_record_items.append(redo_data)
    log_record_items.append(undo_data)

    attr_items = {}

    if redo_op == LogFile.DeallocateFileRecordSegment:
        target_number = log_record.calculate_mft_target_number()
        if target_number is None:
            target_number = 'unknown'

    # self._deleted_files.append(str(target_number))

    if redo_op == LogFile.InitializeFileRecordSegment:
        frs_size = log_record.get_target_block_size() * 512
        if frs_size == 0:
            frs_size = 1024

        frs_buf = redo_data + (b'\x00' * (frs_size - len(redo_data)))

        try:
            frs = MFT.FileRecordSegment(frs_buf, False)
        except MFT.MasterFileTableException:
            pass
        else:
            try:
                for frs_attr in frs.attributes():
                    if type(frs_attr) is MFT.AttributeRecordNonresident:
                        continue

                    frs_attr_val = frs_attr.value_decoded()
                    if type(frs_attr_val) is Attributes.StandardInformation:
                        std_info = {
                            'attr_val': '$STANDARD_INFORMATION',
                            'm_time': util.format_timestamp(frs_attr_val.get_mtime()),
                            'a_time': util.format_timestamp(frs_attr_val.get_atime()),
                            'c_time': util.format_timestamp(frs_attr_val.get_ctime()),
                            'e_time': util.format_timestamp(frs_attr_val.get_etime()),
                            'file_attributes': Attributes.ResolveFileAttributes(
                                frs_attr_val.get_file_attributes())
                        }
                        attr_items['std_info'] = std_info

                    elif type(frs_attr_val) is Attributes.FileName:
                        file_name = {
                            'attr_val': '$FILE_NAME',
                            'm_time': util.format_timestamp(frs_attr_val.get_mtime()),
                            'a_time': util.format_timestamp(frs_attr_val.get_atime()),
                            'c_time': util.format_timestamp(frs_attr_val.get_ctime()),
                            'e_time': util.format_timestamp(frs_attr_val.get_etime()),
                            'file_name': frs_attr_val.get_file_name()
                        }

                        parent_reference = frs_attr_val.get_parent_directory()
                        file_name['parent_reference'] = parent_reference

                        fr_number, fr_sequence = MFT.DecodeFileRecordSegmentReference(parent_reference)

                        try:
                            file_record = mft_file.get_file_record_by_number(fr_number, fr_sequence)
                            file_paths = mft_file.build_full_paths(file_record)
                        except MFT.MasterFileTableException:
                            fr_file_path = None
                        else:
                            if len(file_paths) > 0:
                                fr_file_path = file_paths[0]
                            else:
                                fr_file_path = None
                        file_name['parent_file_path'] = fr_file_path
                        if 'file_name' in attr_items:
                            attr_items['second_file_name'] = file_name
                        else:
                            attr_items['file_name'] = file_name

                    elif type(frs_attr_val) is Attributes.ObjectID:
                        object_id = {
                            'attr_val': '$OBJECT_ID',
                            'guid': str(frs_attr_val.get_object_id()),
                            'timestamp': util.format_timestamp(frs_attr_val.get_timestamp())
                        }
                        attr_items['object_id'] = object_id

            except MFT.MasterFileTableException:
                pass

    if redo_op == LogFile.CreateAttribute or undo_op == LogFile.CreateAttribute or \
            redo_op == LogFile.WriteEndOfFileRecordSegment or undo_op == LogFile.WriteEndOfFileRecordSegment:
        if redo_op == LogFile.CreateAttribute:
            attr_buf = redo_data
        elif undo_op == LogFile.CreateAttribute:
            attr_buf = undo_data
        else:
            if len(redo_data) > len(undo_data):
                attr_buf = redo_data
            else:
                attr_buf = undo_data

        if len(attr_buf) >= 24:
            type_code, record_length, form_code, name_length, name_offset, flags, instance = \
                MFT.UnpackAttributeRecordPartialHeader(attr_buf[0: 16])
            value_length, value_offset, resident_flags, reserved = \
                MFT.UnpackAttributeRecordRemainingHeaderResident(attr_buf[16: 24])

            if value_offset > 0 and value_offset % 8 == 0 and value_length > 0:
                attr_value_buf = attr_buf[value_offset: value_offset + value_length]
                if len(attr_value_buf) == value_length:
                    if type_code == Attributes.ATTR_TYPE_STANDARD_INFORMATION:
                        attr_si = Attributes.StandardInformation(attr_value_buf)
                        std_info = {
                            'attr_val': '$STANDARD_INFORMATION',
                            'm_time': util.format_timestamp(attr_si.get_mtime()),
                            'a_time': util.format_timestamp(attr_si.get_atime()),
                            'c_time': util.format_timestamp(attr_si.get_ctime()),
                            'e_time': util.format_timestamp(attr_si.get_etime()),
                            'file_attributes': Attributes.ResolveFileAttributes(
                                attr_si.get_file_attributes())
                        }
                        attr_items['std_info'] = std_info

                    elif type_code == Attributes.ATTR_TYPE_FILE_NAME:
                        attr_fn = Attributes.FileName(attr_value_buf)

                        file_name = {
                            'attr_val': '$FILE_NAME',
                            'm_time': util.format_timestamp(attr_fn.get_mtime()),
                            'a_time': util.format_timestamp(attr_fn.get_atime()),
                            'c_time': util.format_timestamp(attr_fn.get_ctime()),
                            'e_time': util.format_timestamp(attr_fn.get_etime()),
                            'file_name': attr_fn.get_file_name()
                        }

                        parent_reference = attr_fn.get_parent_directory()
                        file_name['parent_reference'] = parent_reference

                        fr_number, fr_sequence = MFT.DecodeFileRecordSegmentReference(parent_reference)

                        try:
                            file_record = mft_file.get_file_record_by_number(fr_number, fr_sequence)
                            file_paths = mft_file.build_full_paths(file_record)
                        except MFT.MasterFileTableException:
                            fr_file_path = None
                        else:
                            if len(file_paths) > 0:
                                fr_file_path = file_paths[0]
                            else:
                                fr_file_path = None
                        file_name['parent_file_path'] = fr_file_path
                        attr_items['file_name'] = file_name

                    elif type_code == Attributes.ATTR_TYPE_OBJECT_ID:
                        attr_objid = Attributes.ObjectID(attr_value_buf)

                        object_id = {
                            'attr_val': '$OBJECT_ID',
                            'guid': str(attr_objid.get_object_id()),
                            'timestamp': util.format_timestamp(attr_objid.get_timestamp())
                        }
                        attr_items['object_id'] = object_id

    if redo_op == LogFile.AddIndexEntryRoot or redo_op == LogFile.AddIndexEntryAllocation or \
            redo_op == LogFile.WriteEndOfIndexBuffer or undo_op == LogFile.AddIndexEntryRoot or \
            undo_op == LogFile.AddIndexEntryAllocation or undo_op == LogFile.WriteEndOfIndexBuffer:
        if redo_op == LogFile.AddIndexEntryRoot or redo_op == LogFile.AddIndexEntryAllocation or \
                redo_op == LogFile.WriteEndOfIndexBuffer:
            index_entry = Attributes.IndexEntry(redo_data)
        else:
            index_entry = Attributes.IndexEntry(undo_data)

        attr_value_buf = index_entry.get_attribute()
        if attr_value_buf is not None and len(attr_value_buf) > 66:
            attr_fn = Attributes.FileName(attr_value_buf)

            file_name = {
                'attr_val': '$FILE_NAME in index'
            }
            try:
                file_name['mtime'] = util.format_timestamp(attr_fn.get_mtime())
                file_name['atime'] = util.format_timestamp(attr_fn.get_atime())
                file_name['ctime'] = util.format_timestamp(attr_fn.get_ctime())
                file_name['etime'] = util.format_timestamp(attr_fn.get_etime())
                file_name['file_name'] = attr_fn.get_file_name()
            except (ValueError, OverflowError):
                pass

            parent_reference = attr_fn.get_parent_directory()
            file_name['parent_reference'] = parent_reference

            fr_number, fr_sequence = MFT.DecodeFileRecordSegmentReference(parent_reference)

            try:
                file_record = mft_file.get_file_record_by_number(fr_number, fr_sequence)
                file_paths = mft_file.build_full_paths(file_record)
            except MFT.MasterFileTableException:
                fr_file_path = None
            else:
                if len(file_paths) > 0:
                    fr_file_path = file_paths[0]
                else:
                    fr_file_path = None

            file_name['parent_file_path'] = fr_file_path
            attr_items['file_name_index'] = file_name

    if offset_in_target is not None and (redo_op == LogFile.UpdateResidentValue
                                         or undo_op == LogFile.UpdateResidentValue):
        frs_size = log_record.get_target_block_size() * 512
        if frs_size == 0:
            frs_size = 1024

        if frs_size == 1024 or frs_size == 4096:
            si_attr_offset = 56 + 24
            if frs_size == 4096:
                si_attr_offset = 72 + 24

            if si_attr_offset <= offset_in_target <= si_attr_offset + 32:
                buf = redo_data
                if len(buf) >= 8:
                    attr_si = Attributes.StandardInformationPartial(buf, offset_in_target - si_attr_offset)

                    possible_std_info_redo = {
                        'attr_val': 'Possible update to $STANDARD_INFORMATION (redo data)',
                        'mtime': util.format_timestamp(attr_si.get_mtime()),
                        'atime': util.format_timestamp(attr_si.get_atime()),
                        'ctime': util.format_timestamp(attr_si.get_ctime()),
                        'etime': util.format_timestamp(attr_si.get_etime())
                    }
                    attr_items['possible_std_info_redo'] = possible_std_info_redo

                buf = undo_data
                if len(buf) >= 8:
                    attr_si = Attributes.StandardInformationPartial(buf, offset_in_target - si_attr_offset)

                    possible_std_info_undo = {
                        'attr_val': 'Possible update to $STANDARD_INFORMATION (undo data)',
                        'mtime': util.format_timestamp(attr_si.get_mtime()),
                        'atime': util.format_timestamp(attr_si.get_atime()),
                        'ctime': util.format_timestamp(attr_si.get_ctime()),
                        'etime': util.format_timestamp(attr_si.get_etime())
                    }
                    attr_items['possible_std_info_undo'] = possible_std_info_undo

    if target_attribute_name == '$J':
        usn_data_1 = None
        usn_data_2 = None

        if redo_op == LogFile.UpdateNonresidentValue:
            usn_data_1 = redo_data
        if undo_op == LogFile.UpdateNonresidentValue:
            usn_data_2 = undo_data

        usn = {}
        for usn_data in [usn_data_1, usn_data_2]:
            if usn_data is not None:
                try:
                    usn_record = USN.GetUsnRecord(usn_data)
                except (NotImplementedError, ValueError):
                    pass
                else:
                    if type(usn_record) is USN.USN_RECORD_V4:
                        usn['version'] = 'version 4'
                    else:
                        usn['version'] = 'version 2 or 3'

                    usn['usn'] = usn_record.get_usn()
                    usn['source_info'] = USN.ResolveSourceCodes(usn_record.get_source_info())
                    usn['reason'] = USN.ResolveReasonCodes(usn_record.get_reason())
                    usn['file_ref_num'] = usn_record.get_file_reference_number()
                    usn['parent_file_reference_number'] = usn_record.get_parent_file_reference_number()

                    if type(usn_record) is USN.USN_RECORD_V2_OR_V3:
                        usn['timestamp'] = util.format_timestamp(usn_record.get_timestamp())
                        usn['file_name'] = usn_record.get_file_name()

                    attr_items['usn'] = usn

    log_record_items.append(str(json.dumps(attr_items)))

    return log_record_items