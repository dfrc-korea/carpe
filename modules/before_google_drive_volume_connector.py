# [Google Drive Old Version]

import os

from modules import manager
from modules import interface
from modules.Googledrive import google_drive_backsync as gs
from dfvfs.lib import definitions as dfvfs_definitions


class GoogledrivevolConnector(interface.ModuleConnector):
    NAME = 'Google_drive_Volume_Connector'
    DESCRIPTION = 'Module for Googledrive_Sync_Volumeinfo'

    _plugin_classes = {}

    def __init__(self):
        super(GoogledrivevolConnector, self).__init__()

    def Connect(self, par_id, configuration, source_path_spec, knowledge_base):
        this_file_path = os.path.dirname(os.path.abspath(__file__)) + os.sep + 'schema' + os.sep

        yaml_list = [this_file_path + 'lv1_app_google_drive_snapshot_volume_info_entry.yaml']

        table_list = ['lv1_app_google_drive_snapshot_volume_info_entry']

        if not self.check_table_from_yaml(configuration, yaml_list, table_list):
            return False

        users = []
        for user_accounts in knowledge_base._user_accounts.values():
            for hostname in user_accounts.values():
                if hostname.identifier.find('S-1-5-21') == -1:
                    continue
                users.append(hostname.username)

        query_separator = self.GetQuerySeparator(source_path_spec, configuration)

        for user in users:
            user_path = f"{query_separator}Users{query_separator}{user}"
            gs_path = f"{query_separator}AppData{query_separator}Local" \
                      f"{query_separator}Google{query_separator}Drive"

            output_path = configuration.root_tmp_path + os.sep + configuration.case_id + os.sep + \
                          configuration.evidence_id + os.sep + par_id

            self.ExtractTargetDirToPath(source_path_spec=source_path_spec,
                                        configuration=configuration,
                                        dir_path=user_path + gs_path,
                                        output_path=output_path)

            try:
                v_data = []
                info = [par_id, configuration.case_id, configuration.evidence_id]
                volume_data = gs.snapshot_volume(output_path + os.sep + "Drive" + os.sep + 'user_default' + os.sep)

                for d in volume_data:
                    v_data.append(info + d + [user_path + gs_path])

                query = f"INSERT INTO lv1_app_google_drive_snapshot_volume_info_entry values (%s, %s, %s, %s, %s, %s, %s, %s)"
            except:
                return False

            configuration.cursor.bulk_execute(query, v_data)


manager.ModulesManager.RegisterModule(GoogledrivevolConnector)
