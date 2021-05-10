# -*- coding: utf-8 -*-
"""module for RecycleBin."""
import os, sys

from modules import manager
from modules import interface
from modules.windows_recyclebin import RecycleBinParser

class RecycleBinConnector(interface.ModuleConnector):

    NAME = 'recyclebin_connector'
    DESCRIPTION = 'Module for RecycleBin'

    _plugin_classes = {}

    def __init__(self):
        super(RecycleBinConnector, self).__init__()

    def Connect(self, par_id, configuration, source_path_spec, knowledge_base):

        this_file_path = os.path.dirname(os.path.abspath(__file__)) + os.sep + 'schema' + os.sep
        # 모든 yaml 파일 리스트
        yaml_list = [this_file_path + 'lv1_os_win_recyclebin.yaml']

        # 모든 테이블 리스트
        table_list = ['lv1_os_win_recyclebin']

        if not self.check_table_from_yaml(configuration, yaml_list, table_list):
            return False

        query_separator = self.GetQuerySeparator(source_path_spec, configuration)
        path_separator = self.GetPathSeparator(source_path_spec)
        # extension -> sig_type 변경해야 함
        query = f"SELECT name, parent_path, extension, ctime, ctime_nano FROM file_info WHERE par_id like '{par_id}' and " \
                f"parent_path like 'root{query_separator}$Recycle.Bin{query_separator}S-1-5-21%' and name like '$I%';"

        recyclebin_files = configuration.cursor.execute_query_mul(query)

        if len(recyclebin_files) == 0:
            # print("There are no recycle bin files")
            return False

        insert_recyclebin_info = []

        for recyclebin_file in recyclebin_files:
            recyclebin_file_path = recyclebin_file[1][recyclebin_file[1].find(path_separator):] + \
                path_separator + recyclebin_file[0]  # document full path
            fileName = recyclebin_file[0]

            if fileName.find("-slack") != -1:
                continue

            output_path = configuration.root_tmp_path + os.path.sep + configuration.case_id + \
                          os.path.sep + configuration.evidence_id + os.path.sep + par_id

            if not os.path.exists(output_path):
                os.mkdir(output_path)

            self.ExtractTargetFileToPath(
                source_path_spec=source_path_spec,
                configuration=configuration,
                file_path=recyclebin_file_path,
                output_path=output_path)

            fn = output_path + os.path.sep + fileName
            app_path = os.path.abspath(os.path.dirname(__file__)) + os.path.sep + "windows_recyclebin"
            results = RecycleBinParser.main(fn, app_path)  # filename, app_path

            if not results:
                os.remove(output_path + os.sep + fileName)
                continue

            if results == [None]:
                continue

            deleted_time = configuration.apply_time_zone(results[0]['Deleted_Time'], knowledge_base.time_zone)
            insert_recyclebin_info.append([par_id, configuration.case_id, configuration.evidence_id,
                                           results[0]['Name'], results[0]['Size'], deleted_time, results[0]['$I'],
                                           '/$Recycle.Bin/S-1-5-21/'])

            os.remove(output_path + os.sep + fileName)

        query = "Insert into lv1_os_win_recyclebin values (%s, %s, %s, %s, %s, %s, %s, %s);"
        configuration.cursor.bulk_execute(query, insert_recyclebin_info)


manager.ModulesManager.RegisterModule(RecycleBinConnector)