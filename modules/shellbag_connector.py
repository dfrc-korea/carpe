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
    TABLE_NAME = 'lv1_os_win_reg_shellbag'

    _plugin_classes = {}

    def __init__(self):
        super(ShellbagConnector, self).__init__()

    def Connect(self, configuration, source_path_spec, knowledge_base):

        this_file_path = os.path.dirname(os.path.abspath(__file__)) + os.sep + 'schema' + os.sep + 'registry' + os.sep
        # Load Schema
        if not self.LoadSchemaFromYaml(this_file_path + 'lv1_os_win_reg_shellbag.yaml'):
            logger.error('cannot load schema from yaml: {0:s}'.format(self.TABLE_NAME))
            return False

        # if table is not existed, create table
        if not configuration.cursor.check_table_exist(self.TABLE_NAME):
            ret = self.CreateTable(configuration.cursor)
            if not ret:
                logger.error('cannot create database table name: {0:s}'.format(self.TABLE_NAME))
                return False

        if source_path_spec.parent.type_indicator != dfvfs_definitions.TYPE_INDICATOR_TSK_PARTITION:
            par_id = configuration.partition_list['p1']
        else:
            par_id = configuration.partition_list[getattr(source_path_spec.parent, 'location', None)[1:]]

        if par_id == None:
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

            query = f"Insert into {self.TABLE_NAME} values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"
            configuration.cursor.bulk_execute(query, insert_shellbag_info)


manager.ModulesManager.RegisterModule(ShellbagConnector)
