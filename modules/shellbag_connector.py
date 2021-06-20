# -*- coding: utf-8 -*-
"""module for shellbags."""
import os

from modules import manager
from modules import interface
from modules.OverTheShellbag import OverTheShellbag as shellbag


class ShellbagConnector(interface.ModuleConnector):
    NAME = 'shellbag_connector'
    DESCRIPTION = 'Module for Shellbag'

    _plugin_classes = {}

    def __init__(self):
        super(ShellbagConnector, self).__init__()

    def Connect(self, par_id, configuration, source_path_spec, knowledge_base):

        this_file_path = os.path.dirname(os.path.abspath(__file__)) + os.sep + 'schema' + os.sep + 'registry' + os.sep

        yaml_list = [this_file_path + 'lv1_os_win_reg_shellbag.yaml']
        table_list = ['lv1_os_win_reg_shellbag']

        if not self.check_table_from_yaml(configuration, yaml_list, table_list):
            return False

        # This is not OS partition
        if len(knowledge_base._user_accounts.values()) == 0:
            # print("There are no Registry")
            return False

        # TODO file path list를 뽑아야함
        username = list()
        for user_accounts in knowledge_base._user_accounts.values():
            for hostname in user_accounts.values():
                if hostname.identifier.find('S-1-5-21') == -1:
                    continue
                username.append(hostname.username)

        query_separator = self.GetQuerySeparator(source_path_spec, configuration)
        path_separator = self.GetPathSeparator(source_path_spec)
        for user in username:
            filepath = f'root{query_separator}Users{query_separator}{user}{query_separator}' \
                f'AppData{query_separator}Local{query_separator}Microsoft{query_separator}Windows'
            query = f"SELECT name, parent_path FROM file_info WHERE par_id = '{par_id}' and " \
                    f"((name like 'UsrClass.dat' and parent_path like '{filepath}') or " \
                    f"(name like 'UsrClass.dat.LOG1' and parent_path like '{filepath}') or " \
                    f"(name like 'UsrClass.dat.LOG2' and parent_path like '{filepath}'))"

            results = configuration.cursor.execute_query_mul(query)

            if len(results) == 0 or results == -1:
                #print("There are no shellbag files")
                return False

            file_objects = {
                "primary": None,
                "log1": None,
                "log2": None
            }

            for file in results:
                if file[0] == 'UsrClass.dat' or file[0] == 'usrClass.dat':
                    file_objects['primary'] = self.LoadTargetFileToMemory(source_path_spec=source_path_spec,
                                                                          configuration=configuration,
                                                                          file_path=file[1][4:] + path_separator + file[0])
                elif file[0] == 'UsrClass.dat.LOG1' or file[0] == 'usrClass.dat.LOG1':
                    file_objects['log1'] = self.LoadTargetFileToMemory(source_path_spec=source_path_spec,
                                                                       configuration=configuration,
                                                                       file_path=file[1][4:] + path_separator + file[0])
                elif file[0] == 'UsrClass.dat.LOG2' or file[0] == 'usrClass.dat.LOG2':
                    file_objects['log2'] = self.LoadTargetFileToMemory(source_path_spec=source_path_spec,
                                                                       configuration=configuration,
                                                                       file_path=file[1][4:] + path_separator + file[0])

            shellbag_results = shellbag.Main(file_objects)

            # if file_objects['primary']:
            #     file_objects['primary'].close()
            # if file_objects['log1']:
            #     file_objects['log1'].close()
            # if file_objects['log2']:
            #     file_objects['log2'].close()

            info = [par_id, configuration.case_id, configuration.evidence_id, user]
            insert_shellbag_info = []
            for item in shellbag_results:
                item[3] = configuration.apply_time_zone(item[3], knowledge_base.time_zone)      # modification_time
                item[4] = configuration.apply_time_zone(item[4], knowledge_base.time_zone)      # access_time
                item[5] = configuration.apply_time_zone(item[5], knowledge_base.time_zone)      # creation_time
                item[6] = configuration.apply_time_zone(item[6], knowledge_base.time_zone)      # last_written_time
                item = info + item
                insert_shellbag_info.append(tuple(item))

            query = f"Insert into {table_list[0]} values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"
            configuration.cursor.bulk_execute(query, insert_shellbag_info)


manager.ModulesManager.RegisterModule(ShellbagConnector)
