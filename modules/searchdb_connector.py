# -*- coding: utf-8 -*-
"""module for ESE database."""
import os
import struct
import pyesedb
from datetime import datetime, timedelta

from modules import logger
from modules import manager
from modules import interface
from modules.windows_search_db import searchdb_parser
from utility import errors


class SearchDBConnector(interface.ModuleConnector):
    NAME = 'searchdb_connector'
    DESCRIPTION = 'Module for SearchDB'
    TABLE_NAME = 'lv1_os_win_searchdb'

    _plugin_classes = {}

    def __init__(self):
        super(SearchDBConnector, self).__init__()

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
        yaml_list = [this_file_path + 'lv1_os_win_searchdb_gthr.yaml',
                     this_file_path + 'lv1_os_win_searchdb_gthrpth.yaml']

        # 모든 테이블 리스트
        table_list = ['lv1_os_win_searchdb_gthr',
                      'lv1_os_win_searchdb_gthrpth']

        if not self.check_table_from_yaml(configuration, yaml_list, table_list):
            return False

        query_separator = self.GetQuerySeparator(source_path_spec, configuration)
        # extension -> sig_type 변경해야 함
        query = f"SELECT name, parent_path, extension, ctime, ctime_nano FROM file_info WHERE par_id='{par_id}' and " \
                f"parent_path like 'root{query_separator}ProgramData{query_separator}Microsoft{query_separator}" \
                f"Search{query_separator}Data{query_separator}Applications{query_separator}Windows' and name = 'Windows.edb';"

        searchdb_file = configuration.cursor.execute_query_mul(query)

        if len(searchdb_file) == 0:
            # print("There are no searchdb files")
            return False

        # Search artifact paths
        path = f'{query_separator}ProgramData{query_separator}Microsoft{query_separator}Search' \
               f'{query_separator}Data{query_separator}Applications{query_separator}Windows{query_separator}Windows.edb'
        file_object = self.LoadTargetFileToMemory(
            source_path_spec=source_path_spec,
            configuration=configuration,
            file_path=path)
        try:
            results = searchdb_parser.main(database=file_object)
        except Exception as e:
            logger.error(str(e))
            print(str(e))
            return False
        if results is None:
            return False
        #file_object.close()
        insert_searchdb_gthr = []
        insert_searchdb_gthrpth = []

        try:
            for idx, result in enumerate(results['SystemIndex_Gthr']):
                if idx == 0:
                    continue
                timestamp = struct.unpack('>Q', result[3])[0]  # last_modified
                try:
                    time = str(datetime.utcfromtimestamp(timestamp / 10000000 - 11644473600)).replace(' ', 'T') + 'Z'
                    time = configuration.apply_time_zone(time, knowledge_base.time_zone)
                except Exception:
                    time = None
                insert_searchdb_gthr.append(
                    tuple([par_id, configuration.case_id, configuration.evidence_id, str(result[0]),
                           str(result[1]), str(result[2]), time, str(result[4]), str(result[5]),
                           str(result[6]), str(result[7]), str(result[8]), str(result[9]),
                           str(None), str(result[11]), str(result[12]),  # user_data blob 임시 처리
                           str(result[13]), str(result[14]), str(result[15]), str(result[16]),
                           str(result[17]), str(result[18]), str(result[19])]))
        except Exception as exception:
            logger.error('Search DB parsing Error: {0!s}'.format(exception))

        for idx, result in enumerate(results['SystemIndex_GthrPth']):
            if idx == 0:
                continue
            insert_searchdb_gthrpth.append(
                tuple([par_id, configuration.case_id, configuration.evidence_id, str(result[0]), str(result[1]),
                       str(result[2]), '/ProgramData/Microsoft/Search/Data/Applications/Windows/Windows.edb']))

        query = "Insert into lv1_os_win_searchdb_gthr values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, " \
                "%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"
        configuration.cursor.bulk_execute(query, insert_searchdb_gthr)

        query = "Insert into lv1_os_win_searchdb_gthrpth values (%s, %s, %s, %s, %s, %s, %s);"
        configuration.cursor.bulk_execute(query, insert_searchdb_gthrpth)


manager.ModulesManager.RegisterModule(SearchDBConnector)
