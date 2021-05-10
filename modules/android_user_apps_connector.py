# -*- coding: utf-8 -*-
"""module for android user apps."""

import os
from datetime import datetime, timedelta

from modules import logger
from modules import manager
from modules import interface
from modules.android_user_apps import main as android_user_apps
from utility import errors


class AndroidUserAppsConnector(interface.ModuleConnector):
    NAME = 'android_user_apps_connector'
    DESCRIPTION = 'Module for Android User Apps'

    def __init__(self):
        super(AndroidUserAppsConnector, self).__init__()

    def Connect(self, par_id, configuration, source_path_spec, knowledge_base):
        """Connector to connect to Android User Apps modules.

        Args:
            par_id: partition id.
            configuration: configuration values.
            source_path_spec (dfvfs.PathSpec): path specification of the source file.
            knowledge_base (KnowledgeBase): knowledge base.

        """

        # Check Filesystem
        query = f"SELECT filesystem FROM partition_info WHERE par_id like '{par_id}'"
        filesystem = configuration.cursor.execute_query(query)

        if filesystem == None or filesystem[0] != "TSK_FS_TYPE_EXT4":
            #print("No EXT filesystem.")
            return False

        this_file_path = os.path.dirname(os.path.abspath(__file__)) + os.sep + 'schema' + os.sep + 'android' + os.sep

        ### Create LV1 Table ###
        # 모든 yaml 파일 리스트
        yaml_list = [this_file_path + 'lv1_os_and_geodata.yaml']
        # 모든 테이블 리스트
        table_list = ['lv1_os_and_geodata']

        if not self.check_table_from_yaml(configuration, yaml_list, table_list):
            return False

        ### Load Application List ###
        if not self.LoadSchemaFromYaml(this_file_path + 'lv1_os_and_user_apps.yaml'):
            logger.error('cannot load schema from yaml: {0:s}'.format(self.NAME))
            return False

        # Search artifact paths
        paths = self._schema['Paths']
        separator = self._schema['Path_Separator']

        find_specs = self.BuildFindSpecs(paths, separator)
        if len(find_specs) < 1:
            return False

        output_path = configuration.root_tmp_path + os.sep + configuration.case_id + os.sep \
                      + configuration.evidence_id + os.sep + par_id + os.sep + 'AU2A_Raw_Files'

        if not os.path.exists(output_path):
            os.mkdir(output_path)

        for spec in find_specs:
            self.ExtractTargetDirToPath(source_path_spec=source_path_spec,
                                        configuration=configuration,
                                        file_spec=spec,
                                        output_path=output_path)

        results = android_user_apps.main(output_path)

        insert_geodata = list()
        for result in results:
            if result['title'] == "geodata":
                for data in result['data']:
                    if (data[2] == float(0) and data[3] == float(0)) or (
                            data[2] is None and data[3] is None):  # check longitude, latitude
                        continue

                    if data[1] is None:  # check timestamp
                        continue

                    if len(str(data[1])) == 10:  # Unixtime_seconds
                        time = str(datetime(1970, 1, 1) + timedelta(seconds=float(data[1]))).replace(' ', 'T') + 'Z'
                    elif len(str(data[1])) == 13:  # Unixtime_milliseconds
                        time = str(datetime(1970, 1, 1) + timedelta(milliseconds=float(data[1]))).replace(' ',
                                                                                                          'T') + 'Z'

                    insert_geodata.append(tuple([par_id, configuration.case_id, configuration.evidence_id,
                                                 data[0], time, data[2], data[3], data[4], data[5], data[6]]))

        query = "Insert into lv1_os_and_geodata values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"
        configuration.cursor.bulk_execute(query, insert_geodata)

        #
        #     if idx == 0:
        #         continue
        #     insert_prefetch_volume_info.append(tuple(
        #         [par_id, configuration.case_id, configuration.evidence_id, prefetch_name, result[1], result[2],
        #          result[3], result[4]]))
        #
        # os.remove(output_path + os.sep + fileName)
        #
        # query = "Insert into lv1_os_win_prefetch values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"
        # configuration.cursor.bulk_execute(query, insert_prefetch_info)


manager.ModulesManager.RegisterModule(AndroidUserAppsConnector)
