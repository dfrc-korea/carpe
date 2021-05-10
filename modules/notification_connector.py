# -*- coding: utf-8 -*-
"""module for kakaotalk decrypt."""
import os

from modules import logger
from modules import manager
from modules import interface
from modules.windows_notification import notification_parser as noti


class NotificationConnector(interface.ModuleConnector):
    NAME = 'notification_connector'
    DESCRIPTION = 'Module for Notification'

    _plugin_classes = {}

    def __init__(self):
        super(NotificationConnector, self).__init__()

    def Connect(self, par_id, configuration, source_path_spec, knowledge_base):

        this_file_path = os.path.dirname(
            os.path.abspath(__file__)) + os.sep + 'schema' + os.sep + 'notification' + os.sep

        yaml_list = [this_file_path + 'lv1_os_win_notification_old.yaml',
                     this_file_path + 'lv1_os_win_notification_new.yaml']

        table_list = ['lv1_os_win_notification_old',
                      'lv1_os_win_notification_new']

        if not self.check_table_from_yaml(configuration, yaml_list, table_list):
            return False

        users = []
        for user_accounts in knowledge_base._user_accounts.values():
            for hostname in user_accounts.values():
                if hostname.identifier.find('S-1-5-21') == -1:
                    continue
                users.append(hostname.username)

        query_separator = self.GetQuerySeparator(source_path_spec, configuration)
        path_separator = self.GetPathSeparator(source_path_spec)
        for user in users:
            filepath = f'root{query_separator}Windows{query_separator}System32{query_separator}config'
            query = f"SELECT name, parent_path FROM file_info WHERE par_id = '{par_id}' and " \
                    f"((name like 'SOFTWARE' and parent_path like '{filepath}') or " \
                    f"(name like 'SOFTWARE.LOG1' and parent_path like '{filepath}') or " \
                    f"(name like 'SOFTWARE.LOG2' and parent_path like '{filepath}'))"

            results = configuration.cursor.execute_query_mul(query)

            if len(results) == 0 or results == -1:
                # print("There are no registry files")
                return False

            file_objects = {
                "primary": None,
                "log1": None,
                "log2": None
            }

            for file in results:
                if file[0] == 'SOFTWARE':
                    file_objects['primary'] = self.LoadTargetFileToMemory(source_path_spec=source_path_spec,
                                                                          configuration=configuration,
                                                                          file_path=file[1][4:] + path_separator + file[
                                                                              0])
                elif file[0] == 'SOFTWARE.LOG1':
                    file_objects['log1'] = self.LoadTargetFileToMemory(source_path_spec=source_path_spec,
                                                                       configuration=configuration,
                                                                       file_path=file[1][4:] + path_separator + file[0])
                elif file[0] == 'SOFTWARE.LOG2':
                    file_objects['log2'] = self.LoadTargetFileToMemory(source_path_spec=source_path_spec,
                                                                       configuration=configuration,
                                                                       file_path=file[1][4:] + path_separator + file[0])

            if file_objects['primary'] == None:
                return False

            major_version, build_number = noti.get_win_version(file_objects)

            # file_objects['primary'].close()
            # file_objects['log1'].close()
            # file_objects['log2'].close()

            if major_version == 10:
                user_path = f'{query_separator}Users{query_separator}{user}'
                output_path = configuration.root_tmp_path + os.sep + configuration.case_id + os.sep + \
                              configuration.evidence_id + os.sep + par_id
                info = [par_id, configuration.case_id, configuration.evidence_id]
                noti_list = []

                # 1607 (Redstone 1) and over
                if build_number >= 14393:
                    noti_path = f"{query_separator}AppData{query_separator}Local{query_separator}Microsoft{query_separator}Windows{query_separator}Notifications"
                    if not self.ExtractTargetDirToPath(source_path_spec=source_path_spec,
                                                       configuration=configuration,
                                                       dir_path=user_path + noti_path,
                                                       output_path=output_path):
                        # print("There are no notification files")
                        return False

                    noti_data = noti.new_noti_parser(output_path + os.sep + 'Notifications'
                                                     + os.sep + 'wpndatabase.db')
                    for data in noti_data:
                        data[5] = configuration.apply_time_zone(data[5], knowledge_base.time_zone)  # expiry_time
                        data[6] = configuration.apply_time_zone(data[6], knowledge_base.time_zone)  # arrival_time
                        data[7] = configuration.apply_time_zone(data[7], knowledge_base.time_zone)  # boot_id
                        data[10] = configuration.apply_time_zone(data[10], knowledge_base.time_zone)  # created_time
                        data[11] = configuration.apply_time_zone(data[11], knowledge_base.time_zone)  # modified_time
                        noti_list.append(info + list(data))

                    query = f"Insert into {table_list[1]} values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, " \
                            f"%s, %s, %s, %s, %s);"
                else:
                    noti_path = f"{query_separator}AppData{query_separator}Local{query_separator}" \
                                f"Microsoft{query_separator}Windows{query_separator}Notifications{query_separator}appdb.dat"
                    if not self.ExtractTargetFileToPath(source_path_spec=source_path_spec,
                                                        configuration=configuration,
                                                        file_path=user_path + noti_path,
                                                        output_path=output_path):
                        print("There are no notification files")
                        return False

                    noti_tuple = noti.old_noti_parser(output_path + os.sep + 'appdb.dat')
                    for data in noti_tuple:
                        noti_list.append(info + list(data))
                    query = f"Insert into {table_list[0]} values (%s, %s, %s, %s, %s, %s, %s, %s, %s);"
            else:
                print("Notification exists only Windows 10")
                return False

            configuration.cursor.bulk_execute(query, noti_list)


manager.ModulesManager.RegisterModule(NotificationConnector)
