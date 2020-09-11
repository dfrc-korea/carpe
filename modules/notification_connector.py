# -*- coding: utf-8 -*-
"""module for kakaotalk decrypt."""
import os

from modules import logger
from modules import manager
from modules import interface
from modules.windows_notification import notification_parser as noti
from dfvfs.lib import definitions as dfvfs_definitions



class NotificationConnector(interface.ModuleConnector):
    NAME = 'notification_connector'
    DESCRIPTION = 'Module for notification'
    TABLE_NAME = 'lv1_os_win_notification'

    _plugin_classes = {}

    def __init__(self):
        super(NotificationConnector, self).__init__()

    def Connect(self, configuration, source_path_spec, knowledge_base):

        this_file_path = os.path.dirname(
            os.path.abspath(__file__)) + os.sep + 'schema' + os.sep + 'notification' + os.sep

        yaml_list = [this_file_path + 'lv1_os_win_notification_old.yaml',
                     this_file_path + 'lv1_os_win_notification_new.yaml']

        table_list = ['lv1_os_win_notification_old',
                      'lv1_os_win_notification_new']

        if not self.check_table_from_yaml(configuration, yaml_list, table_list):
            return False

        if source_path_spec.parent.type_indicator != dfvfs_definitions.TYPE_INDICATOR_TSK_PARTITION:
            par_id = configuration.partition_list['p1']
        else:
            par_id = configuration.partition_list[getattr(source_path_spec.parent, 'location', None)[1:]]

        if par_id == None:
            return False

        print('[MODULE]: Notification Start! - partition ID(%s)' % par_id)


        # Get user name (나중에 고쳐야함)
        users = []
        for user_accounts in knowledge_base._user_accounts.values():
            for hostname in user_accounts.values():
                if hostname.identifier.find('S-1-5-21') == -1:
                    continue
                users.append(hostname.username)

        # Search registry path
        path = f'/Windows/System32/config/SOFTWARE'
        file_object = self.LoadTargetFileToMemory(source_path_spec=source_path_spec,
                                                  configuration=configuration,
                                                  file_path=path)
        if file_object is None:
            print('Registry key is not found')
            return False

        major_version, build_number = noti.get_win_version(file_object)

        file_object.close()

        for user in users:
            if major_version == 10:
                user_path = f'C:\\Users\\{user}'

                # 1607 (Redstone 1) and over
                if build_number >= 14393:
                    noti_path = "\\AppData\\Local\\Microsoft\\Windows\\Notifications\\wpndatabase.db"
                    noti_tuple = noti.new_noti_parser(user_path + noti_path)
                else:
                    noti_path = "\\AppData\\Local\\Microsoft\\Windows\\Notifications\\appdb.dat"
                    noti_tuple = noti.old_noti_parser(user_path + noti_path)
                return noti_tuple
            else:
                print("Notification exists only Windows 10")
                return ""

            info = tuple([par_id, configuration.case_id, configuration.evidence_id])

            for result in results:
                result = info + result
                query = f"Insert into {self.TABLE_NAME} values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"
                configuration.cursor.execute_query(query)


manager.ModulesManager.RegisterModule(NotificationConnector)
