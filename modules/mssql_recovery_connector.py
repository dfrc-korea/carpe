# -*- coding: utf-8 -*-
"""module for Mssql Recovery."""
import os

from modules import manager
from modules import interface

from modules.mssql_recovery import main as mssql


class MssqlRecoveryConnector(interface.ModuleConnector):
    NAME = 'mssql_recovery_connector'
    DESCRIPTION = 'Module for Mssql'

    def __init__(self):
        super(MssqlRecoveryConnector, self).__init__()

    def Connect(self, par_id, configuration, source_path_spec, knowledge_base):

        # Search .mdf path
        query = f"SELECT name, parent_path FROM file_info WHERE par_id like '{par_id}' and extension like 'mdf'"

        mdf_files = configuration.cursor.execute_query_mul(query)

        if len(mdf_files) == 0:
            # print("There are no mssql files")
            return False

        # db_file = 'test_DB.mdf'
        # path = f'{path_separator}Users{path_separator}dfrct{path_separator}Desktop' \
        #     f'{path_separator}Data{path_separator}{db_file}'  # temp

        # Search artifact path
        query_separator = self.GetQuerySeparator(source_path_spec, configuration)
        path_separator = self.GetPathSeparator(source_path_spec)
        output_path = configuration.root_tmp_path + os.sep + configuration.case_id + os.sep + \
                      configuration.evidence_id + os.sep + par_id

        for mdf_file in mdf_files:

            file_name = mdf_file[0]
            file_path = mdf_file[1][mdf_file[1].find(path_separator):] + path_separator + file_name

            # Extract MsSQL file
            self.ExtractTargetFileToPath(source_path_spec=source_path_spec,
                                         configuration=configuration,
                                         file_path=file_path,
                                         output_path=output_path)

            input_path = output_path + f'{os.sep}{file_name}'
            if os.path.exists(input_path):
                mssql.main(input_path, output_path)


manager.ModulesManager.RegisterModule(MssqlRecoveryConnector)
