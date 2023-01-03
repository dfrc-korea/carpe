from modules.NTFS import util
from modules.NTFS.dfir_ntfs import WSL, Attributes, MFT


def mft_parse(info, mft_file, file_record, file_paths, time_zone):
    mft_list = []

    attr_standard_information = None
    file_size = None
    ads_set = set()
    objid_time = None

    wsl_found = False
    wsl_mtime = ''
    wsl_atime = ''
    wsl_chtime = ''
    file_type = ''

    for attribute in file_record.attributes():
        if type(attribute) is MFT.AttributeRecordResident:
            attribute_value = attribute.value_decoded()

            if type(attribute_value) is Attributes.StandardInformation:
                if attr_standard_information is None:
                    attr_standard_information = attribute_value

                file_type = Attributes.ResolveFileAttributes(attribute_value.get_file_attributes())

            if type(attribute_value) is Attributes.ObjectID:
                if objid_time is None:
                    objid_time = attribute_value.get_timestamp()

            if type(attribute_value) is Attributes.EA:
                if not wsl_found:
                    for ea_name, ea_flags, ea_value in attribute_value.data_parsed():
                        if ea_name == b'LXATTRB\x00':
                            try:
                                lxattrb = WSL.LXATTRB(ea_value)
                            except ValueError:
                                pass
                            else:
                                wsl_found = True
                                wsl_atime = util.format_timestamp(lxattrb.get_atime(), time_zone)
                                wsl_mtime = util.format_timestamp(lxattrb.get_mtime(), time_zone)
                                wsl_chtime = util.format_timestamp(lxattrb.get_chtime(), time_zone)

            if attribute.type_code == Attributes.ATTR_TYPE_DATA and attribute.name is None:
                if file_size is None:
                    file_size = str(len(attribute.value))

            if attribute.type_code == Attributes.ATTR_TYPE_DATA and attribute.name is not None:
                ads_set.add(attribute.name)
        else:
            if attribute.type_code == Attributes.ATTR_TYPE_DATA and attribute.name is None and attribute.lowest_vcn == 0:
                if file_size is None:
                    file_size = str(attribute.file_size)

            if attribute.type_code == Attributes.ATTR_TYPE_DATA and attribute.name is not None:
                ads_set.add(attribute.name)

    if file_size is None:
        file_size = '?'

    if len(ads_set) > 0:
        ads_list = ' '.join(sorted(ads_set))
    else:
        ads_list = ''

    if objid_time is None:
        objid_time = ''
    else:
        objid_time = util.format_timestamp(objid_time, time_zone)

    if attr_standard_information is not None:
        si_mtime = util.format_timestamp(attr_standard_information.get_mtime(), time_zone)
        si_atime = util.format_timestamp(attr_standard_information.get_atime(), time_zone)
        si_ctime = util.format_timestamp(attr_standard_information.get_ctime(), time_zone)
        si_etime = util.format_timestamp(attr_standard_information.get_etime(), time_zone)
        si_usn = attr_standard_information.get_usn()
    else:
        si_mtime = ''
        si_atime = ''
        si_ctime = ''
        si_etime = ''
        si_usn = ''

    fr_lsn = file_record.get_logfile_sequence_number()

    if file_record.is_in_use():
        fr_in_use = 'Y'
    else:
        fr_in_use = 'N'

    if file_record.get_flags() & MFT.FILE_FILE_NAME_INDEX_PRESENT > 0:
        fr_directory = 'Y'
    else:
        fr_directory = 'N'

    fr_number = str(MFT.EncodeFileRecordSegmentReference(file_record.get_master_file_table_number(), file_record.get_sequence_number()))

    if len(file_paths) > 0:
        for file_path, attr_file_name in file_paths:
            fn_mtime = util.format_timestamp(attr_file_name.get_mtime(), time_zone)
            fn_atime = util.format_timestamp(attr_file_name.get_atime(), time_zone)
            fn_ctime = util.format_timestamp(attr_file_name.get_ctime(), time_zone)
            fn_etime = util.format_timestamp(attr_file_name.get_etime(), time_zone)

            mft_list.append(info + ['File record', fr_number, fr_in_use, fr_directory, fr_lsn, file_path,
                            si_mtime, si_atime, si_ctime, si_etime, si_usn, fn_mtime, fn_atime, fn_ctime, fn_etime,
                            objid_time, file_size, ads_list, wsl_mtime, wsl_atime, wsl_chtime, file_type])
    else:
        mft_list.append(info + ['File record', fr_number, fr_in_use, fr_directory, fr_lsn, '',
                        si_mtime, si_atime, si_ctime, si_etime, si_usn, '', '', '', '', objid_time, file_size, ads_list,
                        wsl_mtime, wsl_atime, wsl_chtime, file_type])

    # Parse a file name index in this file record (if present).
    attr_index_root = None

    if file_record.get_flags() & MFT.FILE_FILE_NAME_INDEX_PRESENT > 0:
        for attribute in file_record.attributes():
            if type(attribute) is MFT.AttributeRecordResident:
                attribute_value = attribute.value_decoded()

                if type(attribute_value) is Attributes.IndexRoot:
                    if attribute_value.get_indexed_attribute_type_code() == Attributes.ATTR_TYPE_FILE_NAME:
                        attr_index_root = attribute_value
                        break

        if attr_index_root is not None:
            for index_entry in attr_index_root.index_entries():
                attr_file_name_raw = index_entry.get_attribute()
                if attr_file_name_raw is None:
                    continue

                attr_file_name = Attributes.FileName(attr_file_name_raw)

                if len(file_paths) > 0:
                    dir_path = file_paths[0][0]
                    if dir_path == '/.':
                        dir_path = ''

                    file_path = MFT.PATH_SEPARATOR.join([dir_path, attr_file_name.get_file_name()])
                else:
                    file_path = MFT.PATH_SEPARATOR.join(['<Unknown>', attr_file_name.get_file_name()])

                fr_number = str(index_entry.get_file_reference())

                if attr_file_name.get_file_attributes() & Attributes.DUP_FILE_NAME_INDEX_PRESENT > 0:
                    fr_directory = 'Y'
                else:
                    fr_directory = 'N'

                fn_mtime = util.format_timestamp(attr_file_name.get_mtime(), time_zone)
                fn_atime = util.format_timestamp(attr_file_name.get_atime(), time_zone)
                fn_ctime = util.format_timestamp(attr_file_name.get_ctime(), time_zone)
                fn_etime = util.format_timestamp(attr_file_name.get_etime(), time_zone)

                file_size = attr_file_name.get_file_size()

                mft_list.append(info + ['Index record', fr_number, '?', fr_directory, '', file_path, '', '', '', '',
                                        '', fn_mtime, fn_atime, fn_ctime, fn_etime, '', file_size, '', '', '', '', file_type])

    # Parse slack space in this file record (if present).
    for slack in file_record.slack():
        for attr_file_name in slack.carve():
            parent_directory_reference = attr_file_name.get_parent_directory()
            parent_fr_number, parent_fr_sequence = MFT.DecodeFileRecordSegmentReference(
                parent_directory_reference)

            try:
                parent_file_record = mft_file.get_file_record_by_number(parent_fr_number, parent_fr_sequence)
                parent_file_paths = mft_file.build_full_paths(parent_file_record)
            except MFT.MasterFileTableException:
                parent_file_path = None
            else:
                if len(parent_file_paths) > 0:
                    parent_file_path = parent_file_paths[0]
                else:
                    parent_file_path = None

            if parent_file_path is not None:
                if parent_file_path == '/.':
                    parent_file_path = ''

                file_path = MFT.PATH_SEPARATOR.join([parent_file_path, attr_file_name.get_file_name()])
            else:
                file_path = MFT.PATH_SEPARATOR.join(['<Unknown>', attr_file_name.get_file_name()])

            if attr_file_name.get_file_attributes() & Attributes.DUP_FILE_NAME_INDEX_PRESENT > 0:
                fr_directory = 'Y'
            else:
                fr_directory = 'N'

            fn_mtime = util.format_timestamp(attr_file_name.get_mtime(), time_zone)
            fn_atime = util.format_timestamp(attr_file_name.get_atime(), time_zone)
            fn_ctime = util.format_timestamp(attr_file_name.get_ctime(), time_zone)
            fn_etime = util.format_timestamp(attr_file_name.get_etime(), time_zone)

            file_size = attr_file_name.get_file_size()

            mft_list.append(info + ['Slack', '?', '?', fr_directory, '', file_path, '', '', '', '', '',
                                    fn_mtime, fn_atime, fn_ctime, fn_etime, '', file_size, '', '', '', '', file_type])

    return mft_list

