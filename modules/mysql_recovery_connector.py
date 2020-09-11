# -*- coding: utf-8 -*-
"""module for Mysql Recovery."""
import subprocess
import os

from modules import manager
from modules import interface
from dfvfs.lib import definitions as dfvfs_definitions


class MysqlRecoveryConnector(interface.ModuleConnector):

    NAME = 'mysql_recovery_connector'
    DESCRIPTION = 'Moudle for Prefetch'

    def __init__(self):
        super(MysqlRecoveryConnector, self).__init__()

    def Connect(self, configuration, source_path_spec, knowledge_base):

        if source_path_spec.parent.type_indicator != dfvfs_definitions.TYPE_INDICATOR_TSK_PARTITION:
            par_id = configuration.partition_list['p1']
        else:
            par_id = configuration.partition_list[getattr(source_path_spec.parent, 'location', None)[1:]]

        if par_id == None:
            return False

        print('[MODULE]: Mysql Recovery Start - partition ID(%s)' % par_id)

        # Search artifact path
        db_dir = 'test_schema'
        path = f'\\Users\\dfrct\\Desktop\\{db_dir}'     # temp
        output_path = configuration.root_tmp_path + os.sep + configuration.case_id + os.sep + \
                      configuration.evidence_id + os.sep + par_id

        # Extract MySQL file Directory
        self.ExtractTargetDirToPath(source_path_spec=source_path_spec,
                                    configuration=configuration, dir_path=path,
                                    output_path=output_path)

        this_file_path = os.path.dirname(os.path.abspath(__file__)) + os.sep + 'MYR' + os.sep

        p = subprocess.run(['start',
                            this_file_path + 'Release\\MYR.exe',         # MySQL Recovery program
                            output_path + f'\\{db_dir}',               # MySQL data directory
                            this_file_path + 'MySqlServerinfo.txt'])    # MySQL Server information


manager.ModulesManager.RegisterModule(MysqlRecoveryConnector)
