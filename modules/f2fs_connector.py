# -*- coding: utf-8 -*-
"""module for f2fs."""
import os
import subprocess

from modules import manager
from modules import interface


class F2fsConnector(interface.ModuleConnector):
    NAME = 'f2fs_connector'
    DESCRIPTION = 'Module for f2fs'

    def __init__(self):
        super(F2fsConnector, self).__init__()

    def Connect(self, par_id, configuration, source_path_spec, knowledge_base):

        query_separator = self.GetQuerySeparator(source_path_spec, configuration)
        path_separator = self.GetPathSeparator(source_path_spec)
        path = f'{path_separator}ProgramData{path_separator}MySQL{path_separator}.+{path_separator}Data'
        output_path = configuration.root_tmp_path + os.sep + configuration.case_id + os.sep + \
                      configuration.evidence_id + os.sep + par_id

        # Extract MySQL file Directory
        if not self.ExtractTargetDirToPath(source_path_spec=source_path_spec,
                                           configuration=configuration,
                                           dir_path=path,
                                           output_path=output_path):
            print("There are no mysql files")
            return False

        this_file_path = os.path.dirname(os.path.abspath(__file__)) + os.sep + 'MYR' + os.sep

        subprocess.run(['start',
                        this_file_path + 'Release\\MYR.exe',  # MySQL Recovery program
                        output_path + f'\\Data',  # MySQL data directory
                        this_file_path + 'MySqlServerinfo.txt'])  # MySQL Server information


manager.ModulesManager.RegisterModule(F2fsConnector)
