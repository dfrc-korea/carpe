# -*- coding: utf-8 -*-
"""module for DFIR_NTFS_caller."""

import os, platform

from modules import manager
from modules import interface
from modules.NTFS import mft_parser, logfile_parser, usnjrnl_parser
from modules.NTFS.dfir_ntfs import USN, LogFile, MFT
import json

from modules.NTFS.logfile_parser import detail_parse


class NTFSConnector(interface.ModuleConnector):
    NAME = 'ntfs_connector'
    DESCRIPTION = 'Module for DFIR_NTFS'

    _plugin_classes = {}


    def __init__(self):
        super(NTFSConnector, self).__init__()
        self._mft_path = None
        self._mftmirr_path = None
        self._usnjrnl_path = None
        self._logfile_path = None
        self.path_dict = {}

    def Connect(self, par_id, configuration, source_path_spec, knowledge_base):

        this_file_path = os.path.dirname(os.path.abspath(__file__)) + os.sep + 'schema' + os.sep + 'ntfs' + os.sep

        yaml_list = [this_file_path + 'lv1_fs_ntfs_mft.yaml',
                     this_file_path + 'lv1_fs_ntfs_logfile_restart_area.yaml',
                     this_file_path + 'lv1_fs_ntfs_logfile_log_record.yaml',
                     this_file_path + 'lv1_fs_ntfs_usnjrnl.yaml']

        table_list = ['lv1_fs_ntfs_mft',
                      'lv1_fs_ntfs_logfile_restart_area',
                      'lv1_fs_ntfs_logfile_log_record',
                      'lv1_fs_ntfs_usnjrnl']

        if not self.check_table_from_yaml(configuration, yaml_list, table_list):
            return False

        query_separator = self.GetQuerySeparator(source_path_spec, configuration)
        # extension -> sig_type 변경해야 함
        query = f"SELECT name, parent_path, extension, ctime, ctime_nano, inode FROM file_info " \
                f"WHERE par_id='{par_id}' and (name like '$MFT' or name like '$MFTMirr' or name like '$UsnJrnl' or name like '$LogFile');" \

        ntfs_files = configuration.cursor.execute_query_mul(query)

        if len(ntfs_files) == 0:
            return False

        # path, name, ads_name
        file_list = [['\\', '$MFT', None], ['\\', '$MFTMirr', None], ['\\$Extend\\', '$UsnJrnl', '$J'],
                     ['\\', '$LogFile', None]]

        output_path = configuration.root_tmp_path + os.sep + configuration.case_id + os.sep + \
                      configuration.evidence_id + os.sep + par_id

        for file in file_list:
            file_path = file[0] + file[1]
            if platform.platform()[0:7] != 'Windows':
                file_path = file_path.replace('\\', '/')[1:]

            self.ExtractTargetFileToPath(source_path_spec=source_path_spec,
                                         configuration=configuration,
                                         file_path=file_path,
                                         output_path=output_path,
                                         data_stream_name=file[2])
        #
        # if configuration.source_type == 'storage media device' or configuration.source_type == 'storage media image' or platform.platform()[0:7] == 'Windows':
        #     for file in file_list:
        #         file_path = file[0] + file[1]
        #         if platform.platform()[0:7] != 'Windows':
        #             file_path = file_path.replace('\\', '/')
        #
        #         self.ExtractTargetFileToPath(source_path_spec=source_path_spec,
        #                                      configuration=configuration,
        #                                      file_path=file[0] + file[1],
        #                                      output_path=output_path,
        #                                      data_stream_name=file[2])
        # else:
        #     for file in ntfs_files:
        #         data_stream = None
        #         if file[0] == '$UsnJrnl':
        #             data_stream = '$J'
        #
        #         file_path = file[1] + os.sep + file[0]
        #
        #         self.ExtractTargetFileToPath(source_path_spec=source_path_spec,
        #                                      configuration=configuration,
        #                                      file_path=file_path,
        #                                      output_path=output_path,
        #                                      data_stream_name=data_stream)

        self._mft_path = output_path + os.sep + '$MFT'
        self._mftmirr_path = output_path + os.sep + '$MFTMirr'
        self._logfile_path = output_path + os.sep + '$LogFile'
        self._usnjrnl_path = output_path + os.sep + '$UsnJrnl_$J'

        mft_file = None

        if os.path.exists(self._mft_path):
            self.print_run_info('Parse $MFT', start=True)
            mft_file = self.process_mft(par_id, configuration, table_list, knowledge_base)
            self.print_run_info('Parse $MFT', start=False)
        else:
            print('', end='')
            # print("There is no $MFT")

        if os.path.exists(self._mft_path) and os.path.exists(self._logfile_path):
            self.print_run_info('Parse $LogFile', start=True)
            self.process_logfile(par_id, configuration, table_list, knowledge_base, mft_file)
            self.print_run_info('Parse $LogFile', start=False)
        else:
            print('', end='')
            # print("There is no $LogFile")

        if os.path.exists(self._mft_path) and os.path.exists(self._usnjrnl_path):
            self.print_run_info('Parse $UsnJrnl', start=True)
            self.process_usnjrnl(par_id, configuration, table_list, knowledge_base, mft_file)
            self.print_run_info('Parse $UsnJrnl', start=False)
        else:
            print('', end='')
            # print("There is no $UsnJrnl")

    def process_mft(self, par_id, configuration, table_list, knowledge_base):
        mft_object = open(self._mft_path, 'rb')

        mft_file = MFT.MasterFileTableParser(mft_object)

        info = [par_id, configuration.case_id, configuration.evidence_id]

        mft_list = []
        for file_record in mft_file.file_records():
            try:
                file_paths = mft_file.build_full_paths(file_record, True)
                self.path_dict[file_record] = [e[0] for e in file_paths]
            except MFT.MasterFileTableException:
                continue
            # TODO: file_path 중복 수정
            if not file_paths:
                mft_item = mft_parser.mft_parse(info, mft_file, file_record, file_paths, knowledge_base.time_zone)

            else:
                mft_item = mft_parser.mft_parse(info, mft_file, file_record, [file_paths[0]], knowledge_base.time_zone)

            mft_list.extend(mft_item)

        query = f"Insert into {table_list[0]} values(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, " \
                f"%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"

        configuration.cursor.bulk_execute(query, mft_list)
        # print(f'mft num: {len(mft_list)}')

        return mft_file

    def process_logfile(self, par_id, configuration, table_list, knowledge_base, mft_file):
        logfile_object = open(self._logfile_path, 'rb')
        log_file = LogFile.LogFileParser(logfile_object)

        restart_area_list = []
        log_record_list = []
        info = [par_id, configuration.case_id, configuration.evidence_id]

        for log_item in log_file.parse_ntfs_records():
            if not type(log_item):
                continue
            elif type(log_item) is LogFile.NTFSRestartArea:
                output_data = logfile_parser.restart_area_parse(log_item)
                if not output_data:
                    continue

                restart_area_list.append(info + output_data)

            elif type(log_item) is LogFile.NTFSLogRecord:
                output_data = logfile_parser.log_record_parse(log_item, mft_file, self.path_dict,
                                                              knowledge_base.time_zone)
                if not output_data:
                    continue
                log_record_list.append(info + output_data + [" "])


        log_record_list = detail_parse(log_record_list)


        restart_area_query = f"Insert into {table_list[1]} values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s," \
                             f" %s, %s);"
        log_record_query = f"Insert into {table_list[2]} values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, " \
                           f"%s, %s, %s, %s, %s);"

        # print(f'restart area num: {len(restart_area_list)}')
        # print(f'log record num: {len(log_record_list)}')
        configuration.cursor.bulk_execute(restart_area_query, restart_area_list)
        configuration.cursor.bulk_execute(log_record_query, log_record_list)




    def process_usnjrnl(self, par_id, configuration, table_list, knowledge_base, mft_file):
        usn_object = open(self._usnjrnl_path, 'rb')
        usn_journal = USN.ChangeJournalParser(usn_object)

        query = f"Insert into {table_list[3]} values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"

        usnjrnl_list = []
        for usn_record in usn_journal.usn_records():
            usnjrnl_item = usnjrnl_parser.usnjrnl_parse(mft_file, usn_record, self.path_dict, knowledge_base.time_zone)
            info = [par_id, configuration.case_id, configuration.evidence_id]
            values = info + usnjrnl_item
            usnjrnl_list.append(values)

        # print(f'usnjrnl num: {len(usnjrnl_list)}')
        configuration.cursor.bulk_execute(query, usnjrnl_list)


manager.ModulesManager.RegisterModule(NTFSConnector)
