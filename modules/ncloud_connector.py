import os
from modules import manager
from modules import interface
from modules import logger
from modules.NaverNCloud import parse_file_info as nc
from dfvfs.lib import definitions as dfvfs_definitions


class ncloudConnector(interface.ModuleConnector):
    NAME = "NCloud_Connector"
    DESCRIPTION = "Module for NaverNCloud"

    _plugin_classes = {}

    def __init__(self):
        super(ncloudConnector, self).__init__()

    def Connect(self, par_id, configuration, source_path_spec, knowledge_base):
        # Load schema
        this_file_path = (
            os.path.dirname(os.path.abspath(__file__))
            + os.sep
            + "schema"
            + os.sep
        )
        yaml_list = [
            this_file_path
            + "naverncloud"
            + os.sep
            + "lv1_app_naverncloud_file_info.yaml"
        ]
        table_list = ["lv1_app_naverncloud_file_info"]

        query_separator = self.GetQuerySeparator(source_path_spec, configuration)
        path_separator = self.GetPathSeparator(source_path_spec)

        if not self.check_table_from_yaml(configuration, yaml_list, table_list):
            return False

        naver_select_query = f"SELECT name, parent_path, extension FROM file_info WHERE parent_path " \
                             f"like 'root{query_separator}Users{query_separator}%{query_separator}" \
                             f"AppData{query_separator}Local{query_separator}Naver{query_separator}" \
                             f"NaverNDrive{query_separator}%{query_separator}SyncLog' " \
                             f"AND name = 'ODSyncLog.db' " \
                             f"AND par_id = '{par_id}';"

        naver_query_results = configuration.cursor.execute_query_mul(naver_select_query)

        for file_name, parent_path, _ in naver_query_results:
            naver_file_path = (
                parent_path[parent_path.find(path_separator):] + path_separator + file_name
            )

            output_path = (
                configuration.root_tmp_path
                + os.sep
                + configuration.case_id
                + os.sep
                + configuration.evidence_id
                + os.sep
                + par_id
            )

            self.ExtractTargetFileToPath(
                source_path_spec=source_path_spec,
                configuration=configuration,
                file_path=naver_file_path,
                output_path=output_path
            )

            info = [par_id, configuration.case_id, configuration.evidence_id]
            naver_data = nc.parse_file_infomation(output_path + os.sep + file_name)

            for data in naver_data:
                naver_file_info_tuple = tuple(info + list(data))
                query = f"INSERT INTO lv1_app_naverncloud_file_info values (%s, %s, %s, %s, %s, %s)"

                configuration.cursor.bulk_execute(query, (naver_file_info_tuple,))

manager.ModulesManager.RegisterModule(ncloudConnector)
