# -*- coding: utf-8 -*-
"""module for Mssql Recovery."""
import os

from modules import manager
from modules import interface

from modules.mssql_recovery import main as mssql


class MssqlRecoveryConnector(interface.ModuleConnector):
    NAME = 'mssql_recovery_connector'
    DESCRIPTION = 'Module for mssql'

    def __init__(self):
        super(MssqlRecoveryConnector, self).__init__()

    def Connect(self, par_id, configuration, source_path_spec, knowledge_base):

        # Search artifact path
        db_file = 'test_DB.mdf'
        path = f'/Users/dfrct/Desktop/Data/{db_file}'  # temp
        output_path = configuration.root_tmp_path + os.sep + configuration.case_id + os.sep + \
                      configuration.evidence_id + os.sep + par_id

        # Extract MsSQL file Directory
        self.ExtractTargetFileToPath(source_path_spec=source_path_spec,
                                     configuration=configuration,
                                     file_path=path,
                                     output_path=output_path)

        input_path = output_path + f'\\{db_file}'
        if os.path.exists(input_path):
            mssql.main(input_path, output_path)


manager.ModulesManager.RegisterModule(MssqlRecoveryConnector)
