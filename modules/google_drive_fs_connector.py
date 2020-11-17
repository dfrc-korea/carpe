import os
from modules import manager
from modules import interface
from modules import logger
from modules.Googledrive import google_drive_backsync as gs
from dfvfs.lib import definitions as dfvfs_definitions
import shutil


class GoogledrivefscConnector(interface.ModuleConnector):
    NAME = 'Google_drive_fs_Connector'
    DESCRIPTION = 'Module for Googledrive_Sync_fschange'

    _plugin_classes = {}

    def __init__(self):
        super(GoogledrivefscConnector, self).__init__()

    def Connect(self, par_id, configuration, source_path_spec, knowledge_base):

        # Load schema
        yaml_path = os.path.dirname(
            os.path.abspath(__file__)) + os.sep + 'schema' + os.sep + 'lv1_app_google_drive_path.yaml'
        if not self.LoadSchemaFromYaml(yaml_path):
            logger.error('cannot load schema from yaml: {0:s}'.format(self.NAME))
            return False

        # Search artifact paths
        paths = self._schema['Paths']
        separator = self._schema['Path_Separator']
        environment_variables = knowledge_base.GetEnvironmentVariables()

        find_specs = self.BuildFindSpecs(paths, separator, environment_variables)
        if len(find_specs) < 0:
            return False

        output_path = configuration.root_tmp_path + os.sep + configuration.case_id + os.sep + \
                      configuration.evidence_id + os.sep + par_id + os.sep + 'DB'

        if not os.path.exists(output_path):
            os.mkdir(output_path)

        for spec in find_specs:
            self.ExtractTargetDirToPath(source_path_spec=source_path_spec,
                                        configuration=configuration,
                                        file_spec=spec,
                                        output_path=output_path)

        this_file_path = os.path.dirname(os.path.abspath(__file__)) + os.sep + 'schema' + os.sep
        yaml_list = [this_file_path + 'lv1_app_google_drive_fschange.yaml']
        table_list = ['lv1_app_google_drive_fschange']

        if not self.check_table_from_yaml(configuration, yaml_list, table_list):
            return False

        if source_path_spec.parent.type_indicator != dfvfs_definitions.TYPE_INDICATOR_TSK_PARTITION:
            par_id = configuration.partition_list['p1']
        else:
            par_id = configuration.partition_list[getattr(source_path_spec.parent, 'location', None)[1:]]

        if par_id is None:
            return False

        # users = []
        # for user_accounts in knowledge_base._user_accounts.values():
        #    for hostname in user_accounts.values():
        #        if hostname.identifier.find('S-1-5-21') == -1:
        #            continue
        #        users.append(hostname.username)

        # for user in users:
        #    user_path = f"/Users/{user}"
        #    gs_path = f"/AppData/Local/Google/Drive"
        try:
            f_data = []
            file_list = os.listdir(output_path)
            info = [par_id, configuration.case_id, configuration.evidence_id]

            for db in file_list:
                fs_data = gs.fschange_parse(output_path + os.sep, db)
                for d in fs_data:
                    f_data.append(info + d)

            query = f"INSERT INTO lv1_app_google_drive_fschange values (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
        except:
            return False

        configuration.cursor.bulk_execute(query, f_data)
        shutil.rmtree(output_path)


manager.ModulesManager.RegisterModule(GoogledrivefscConnector)
