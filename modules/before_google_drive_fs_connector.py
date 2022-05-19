# [Google Drive Old Version]

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
        tmp = configuration.root_tmp_path + os.sep + configuration.case_id + os.sep + \
                      configuration.evidence_id + os.sep + par_id
        if not os.path.exists(tmp):
            os.mkdir(tmp)
            if not os.path.exists(output_path):
                os.mkdir(output_path)

        google_drive_fs_path = ''
        for spec in find_specs:
            self.ExtractTargetDirToPath(source_path_spec=source_path_spec,
                                        configuration=configuration,
                                        file_spec=spec,
                                        output_path=output_path)
            path_spec_generator = self._path_spec_extractor.ExtractPathSpecs(
                [source_path_spec], find_specs=[spec], recurse_file_system=False,
                resolver_context=configuration.resolver_context)

            for path_spec in path_spec_generator:
                google_drive_fs_path = path_spec.location

        if not os.path.exists(output_path):
            # print("There are no google drive files")
            return False


        this_file_path = os.path.dirname(os.path.abspath(__file__)) + os.sep + 'schema' + os.sep
        yaml_list = [this_file_path + 'lv1_app_google_drive_fschange.yaml']
        table_list = ['lv1_app_google_drive_fschange']

        if not self.check_table_from_yaml(configuration, yaml_list, table_list):
            return False

        try:
            f_data = []
            file_list = os.listdir(output_path)
            info = [par_id, configuration.case_id, configuration.evidence_id]

            for db in file_list:
                fs_data = gs.fschange_parse(output_path + os.sep, db)
                for d in fs_data:
                    f_data.append(info + d + [google_drive_fs_path])
        except:
            return False

        if f_data is None:
            return False

        query = f"INSERT INTO lv1_app_google_drive_fschange values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        configuration.cursor.bulk_execute(query, f_data)
        shutil.rmtree(output_path)


manager.ModulesManager.RegisterModule(GoogledrivefscConnector)
