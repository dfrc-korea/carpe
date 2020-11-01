# -*- coding: utf-8 -*-
"""module for shellbags."""
import os

from modules import logger
from modules import manager
from modules import interface
from modules.OverTheShellbag import OverTheShellbag as shellbag
from dfvfs.lib import definitions as dfvfs_definitions


class ShellbagConnector(interface.ModuleConnector):
    NAME = 'shellbag_connector'
    DESCRIPTION = 'Module for shellbag'

    _plugin_classes = {}

    def __init__(self):
        super(ShellbagConnector, self).__init__()

    def Connect(self, par_id, configuration, source_path_spec, knowledge_base):

        this_file_path = os.path.dirname(os.path.abspath(__file__)) + os.sep + 'schema' + os.sep + 'registry' + os.sep

        yaml_list = [this_file_path + 'lv1_os_win_reg_shellbag.yaml']
        table_list = ['lv1_os_win_reg_shellbag']

        if not self.check_table_from_yaml(configuration, yaml_list, table_list):
            return False

        # TODO file path list를 뽑아야함
        filename = 'UsrClass.dat'
        username = list()
        for user_accounts in knowledge_base._user_accounts.values():
            for hostname in user_accounts.values():
                if hostname.identifier.find('S-1-5-21') == -1:
                    continue
                username.append(hostname.username)

        for user in username:
            filepath = f'root/Users/{user}/AppData/Local/Microsoft/Windows'
            query = f"SELECT name, parent_path FROM file_info WHERE par_id = '{par_id}' and " \
                    f"((name like 'UsrClass.dat' and parent_path like '{filepath}') or " \
                    f"(name like 'UsrClass.dat.LOG1' and parent_path like '{filepath}') or " \
                    f"(name like 'UsrClass.dat.LOG2' and parent_path like '{filepath}'))"

            results = configuration.cursor.execute_query_mul(query)

            if len(results) == 0 or results == -1:
                return False

            file_objects = {
                "primary": None,
                "log1": None,
                "log2": None
            }

            for file in results:
                if file[0] == 'UsrClass.dat':
                    file_objects['primary'] = self.LoadTargetFileToMemory(source_path_spec=source_path_spec,
                                                                          configuration=configuration,
                                                                          file_path=file[1][4:] + '/' + file[0])
                elif file[0] == 'UsrClass.dat.LOG1':
                    file_objects['log1'] = self.LoadTargetFileToMemory(source_path_spec=source_path_spec,
                                                                       configuration=configuration,
                                                                       file_path=file[1][4:] + '/' + file[0])
                elif file[0] == 'UsrClass.dat.LOG2':
                    file_objects['log2'] = self.LoadTargetFileToMemory(source_path_spec=source_path_spec,
                                                                       configuration=configuration,
                                                                       file_path=file[1][4:] + '/' + file[0])

            shellbag_results = shellbag.Main(file_objects)

            file_objects['primary'].close()
            file_objects['log1'].close()
            file_objects['log2'].close()

            info = tuple([par_id, configuration.case_id, configuration.evidence_id, user])
            insert_shellbag_info = []
            for item in shellbag_results:
                item = info + item
                insert_shellbag_info.append(tuple(item))

            query = f"Insert into {table_list[0]} values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"
            configuration.cursor.bulk_execute(query, insert_shellbag_info)


manager.ModulesManager.RegisterModule(ShellbagConnector)
