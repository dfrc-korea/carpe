# -*- coding: utf-8 -*-
"""module for ESE database."""
import os, struct
import pyesedb
from datetime import datetime, timedelta

from modules import logger
from modules import manager
from modules import interface
from modules.windows_filehistory import filehistory_parser
from utility import errors


class FileHistoryConnector(interface.ModuleConnector):
    NAME = 'filehistory_connector'
    DESCRIPTION = 'Module for FileHistory'
    TABLE_NAME = 'lv1_os_win_filehistory'

    _plugin_classes = {}

    def __init__(self):
        super(FileHistoryConnector, self).__init__()

    def Connect(self, par_id, configuration, source_path_spec, knowledge_base):
        """Connector to connect to ESE database modules.

		Args:
			par_id: partition id.
			configuration: configuration values.
			source_path_spec (dfvfs.PathSpec): path specification of the source file.
			knowledge_base (KnowledgeBase): knowledge base.

		"""

        this_file_path = os.path.dirname(os.path.abspath(__file__)) + os.sep + 'schema' + os.sep

        # 모든 yaml 파일 리스트
        yaml_list = [this_file_path + 'lv1_os_win_filehistory_file.yaml',
                     this_file_path + 'lv1_os_win_filehistory_namespace.yaml',
                     this_file_path + 'lv1_os_win_filehistory_string.yaml']

        # 모든 테이블 리스트
        table_list = ['lv1_os_win_filehistory_file',
                      'lv1_os_win_filehistory_namespace',
                      'lv1_os_win_filehistory_string']

        if not self.check_table_from_yaml(configuration, yaml_list, table_list):
            return False

        # extension -> sig_type 변경해야 함
        query = f"SELECT name, parent_path, extension, ctime, ctime_nano FROM file_info WHERE par_id='{par_id}' and " \
                f"(parent_path like '%FileHistory%Configuration' and name like 'Catalog%edb') ORDER by ctime DESC;"

        filehistory_file = configuration.cursor.execute_query_mul(query)

        if len(filehistory_file) == 0:
            return False

        insert_filehistory_namespace = []
        insert_filehistory_string = []
        insert_filehistory_file = []

        filehistory_path = filehistory_file[0][1][filehistory_file[0][1].find('/'):] + '/' + filehistory_file[0][0]

        file_object = self.LoadTargetFileToMemory(
            source_path_spec=source_path_spec,
            configuration=configuration,
            file_path=filehistory_path)

        results = filehistory_parser.main(database=file_object)
        if results == False:
            file_object.close()
            return False
        file_object.close()

        for idx, result in enumerate(results['namespace']):
            if idx == 0:
                continue
            file_created = result[5]
            file_modified = result[6]

            try:
                file_created_time = str(datetime.utcfromtimestamp(file_created / 10000000 - 11644473600)).replace(' ',
                                                                                                                  'T') + 'Z'
            except ValueError:
                file_created_time = None
            try:
                file_modified_time = str(datetime.utcfromtimestamp(file_modified / 10000000 - 11644473600)).replace(' ',
                                                                                                                    'T') + 'Z'
            except ValueError:
                file_modified_time = None

            insert_filehistory_namespace.append(
                tuple([par_id, configuration.case_id, configuration.evidence_id, str(result[0]),
                       str(result[1]), str(result[2]), str(result[3]), str(result[4]), file_created_time,
                       file_modified_time,
                       str(result[7]), str(result[8]), str(result[9]), str(result[10])]))

        for idx, result in enumerate(results['file']):
            if idx == 0:
                continue
            insert_filehistory_file.append(
                tuple([par_id, configuration.case_id, configuration.evidence_id, str(result[0]),
                       str(result[1]), str(result[2]), str(result[3]), str(result[4]), str(result[5]), str(result[6]),
                       str(result[7]), str(result[8])]))

        for idx, result in enumerate(results['string']):
            if idx == 0:
                continue
            insert_filehistory_string.append(
                tuple([par_id, configuration.case_id, configuration.evidence_id, str(result[0]),
                       str(result[1])]))

        query = "Insert into lv1_os_win_filehistory_namespace values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"
        configuration.cursor.bulk_execute(query, insert_filehistory_namespace)

        query = "Insert into lv1_os_win_filehistory_file values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"
        configuration.cursor.bulk_execute(query, insert_filehistory_file)

        query = "Insert into lv1_os_win_filehistory_string values (%s, %s, %s, %s, %s);"
        configuration.cursor.bulk_execute(query, insert_filehistory_string)
        pass


manager.ModulesManager.RegisterModule(FileHistoryConnector)
