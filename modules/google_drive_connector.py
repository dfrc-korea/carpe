import os

from modules import manager
from modules import interface
from modules.Googledrive import google_drive as gs
from dfvfs.lib import definitions as dfvfs_definitions


class GoogledrivefsConnector(interface.ModuleConnector):
    NAME = 'Google_drive_Connector'
    DESCRIPTION = 'Module for Googledrive_Filestream'

    _plugin_classes = {}

    def __init__(self):
        super(GoogledrivefsConnector, self).__init__()

    def Connect(self, par_id, configuration, source_path_spec, knowledge_base):
        this_file_path = os.path.dirname(os.path.abspath(__file__)) + os.sep + 'schema' + os.sep

        yaml_list = [this_file_path + 'lv1_app_google_drive.yaml']

        table_list = ['lv1_app_google_drive']

        if not self.check_table_from_yaml(configuration, yaml_list, table_list):
            return False

        users = []
        for user_accounts in knowledge_base._user_accounts.values():
            for hostname in user_accounts.values():
                if hostname.identifier.find('S-1-5-21') == -1:
                    continue
                users.append(hostname.username)

        query_separator = '/' if source_path_spec.location == '/' else source_path_spec.location * 2

        for user in users:
            user_path = f"{query_separator}Users{query_separator}{user}"
            gs_path = f"{query_separator}AppData{query_separator}Local" \
                      f"{query_separator}Google{query_separator}DriveFS"

            output_path = configuration.root_tmp_path + os.sep + configuration.case_id + os.sep + \
                          configuration.evidence_id + os.sep + par_id

            self.ExtractTargetDirToPath(source_path_spec=source_path_spec,
                                        configuration=configuration,
                                        dir_path=user_path + gs_path,
                                        output_path=output_path)

            try:
                info = [par_id, configuration.case_id, configuration.evidence_id]
                account_list = gs.g_account(output_path + os.sep + "DriveFS" + os.sep)
                db_path = []

                for g_user in account_list:
                    for u in g_user:
                        db_path.append(output_path + os.sep + "DriveFS" + os.sep + u + os.sep)
                google_data = []
                for db in db_path:
                    data = gs.gdrive_parse(db)
                    for d in data:
                        google_data.append(info + d + [user_path + gs_path])

                query = f"INSERT INTO lv1_app_google_drive values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"

                configuration.cursor.bulk_execute(query, google_data)

            except:
                return False


manager.ModulesManager.RegisterModule(GoogledrivefsConnector)
