# -*- coding: utf-8 -*-
"""module for RecycleBin."""
import os, sys
import time
from datetime import datetime

from modules import logger
from modules import manager
from modules import interface
from modules.windows_recyclebin import RecycleBinParser

class RECYCLEBINConnector(interface.ModuleConnector):

    NAME = 'recyclebin_connector'
    DESCRIPTION = 'Moudle for RecycleBin'

    _plugin_classes = {}

    def __init__(self):
        super(RECYCLEBINConnector, self).__init__()

    def Connect(self, par_id, configuration, source_path_spec, knowledge_base):

        this_file_path = os.path.dirname(os.path.abspath(__file__)) + os.sep + 'schema' + os.sep
        # 모든 yaml 파일 리스트
        yaml_list = [this_file_path + 'lv1_os_win_recyclebin.yaml']

        # 모든 테이블 리스트
        table_list = ['lv1_os_win_recyclebin']

        if not self.check_table_from_yaml(configuration, yaml_list, table_list):
            return False

        # extension -> sig_type 변경해야 함
        query = f"SELECT name, parent_path, extension, ctime, ctime_nano FROM file_info WHERE par_id like '{par_id}' and " \
                f"parent_path like 'root/$Recycle.Bin/S-1-5-21%' and name like '$I%';"

        recyclebin_files = configuration.cursor.execute_query_mul(query)

        if len(recyclebin_files) == 0:
            return False

        insert_recyclebin_info = []

        for recyclebin_file in recyclebin_files:
            recyclebin_file_path = recyclebin_file[1][recyclebin_file[1].find('/'):] + '/' + recyclebin_file[0]  # document full path
            fileExt = recyclebin_file[2]
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
            app_path = os.path.abspath(os.path.dirname(__file__))+os.path.sep+"windows_recyclebin"
            results = RecycleBinParser.main(fn, app_path)  # filename, app_path

            if not results:
                os.remove(output_path + os.sep + fileName)
                continue

            insert_recyclebin_info.append(tuple([par_id, configuration.case_id, configuration.evidence_id, results[0]['Name'], results[0]['Size'], results[0]['Deleted_Time'], results[0]['$I']]))

            os.remove(output_path + os.sep + fileName)

        query = "Insert into lv1_os_win_recyclebin values (%s, %s, %s, %s, %s, %s, %s);"
        configuration.cursor.bulk_execute(query, insert_recyclebin_info)


manager.ModulesManager.RegisterModule(RECYCLEBINConnector)