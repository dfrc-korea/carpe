# -*- coding: utf-8 -*-
"""module for Link."""
import os
from datetime import datetime

from modules import manager
from modules import interface
from modules.windows_jumplist import LNKFileParser


class LINKConnector(interface.ModuleConnector):
    NAME = 'link_connector'
    DESCRIPTION = 'Module for Link'

    _plugin_classes = {}

    def __init__(self):
        super(LINKConnector, self).__init__()

    def Connect(self, par_id, configuration, source_path_spec, knowledge_base):
        query_separator = self.GetQuerySeparator(source_path_spec, configuration)
        path_separator = self.GetPathSeparator(source_path_spec)

        this_file_path = os.path.dirname(os.path.abspath(__file__)) + os.sep + 'schema' + os.sep

        # 모든 yaml 파일 리스트
        yaml_list = [this_file_path + 'lv1_os_win_link.yaml']

        # 모든 테이블 리스트
        table_list = ['lv1_os_win_link']

        if not self.check_table_from_yaml(configuration, yaml_list, table_list):
            return False

        # extension -> sig_type 변경해야 함
        query = f"SELECT name, parent_path, extension, mtime, atime, ctime, mtime_nano, atime_nano, ctime_nano, inode " \
                f"FROM file_info WHERE par_id like '{par_id}' and " \
                f"extension like 'lnk' and ("

        # This is not OS partition
        if len(knowledge_base._user_accounts.values()) == 0:
            # print("There are no lnk files")
            return False

        for user_accounts in knowledge_base._user_accounts.values():
            for hostname in user_accounts.values():
                if hostname.identifier.find('S-1-5-21') == -1:
                    continue
                query += f"parent_path like '%{hostname.username}%' or "
        query = query[:-4] + ");"

        lnk_files = configuration.cursor.execute_query_mul(query)
        if lnk_files == -1:
            # print("There are no lnk files")
            return False

        if len(lnk_files) == 0:
            # print("There are no lnk files")
            return False

        insert_link_file = []

        tsk_file_system = self.get_tsk_file_system(source_path_spec, configuration)
        for link_file in lnk_files:
            file_name = link_file[0]
            source = '/' + '/'.join(link_file[1].split(path_separator)[1:]) + '/' + file_name
            inode = int(link_file[9])

            file_object = self.extract_file_object(
                tsk_file_system=tsk_file_system,
                inode=inode
            )

            results = LNKFileParser.main(file_object, file_name)  # filename

            try:
                file_object.close()
            except AttributeError:
                pass

            if not results:
                continue
            machine_id = ""
            file_name = ""
            file_path = ""
            file_size = ""
            lnk_creation_time = str(datetime.utcfromtimestamp(int(str(link_file[5]).zfill(11) + str(link_file[8]).zfill(7)) / 10000000 - 11644473600)).replace(' ', 'T') + 'Z'
            lnk_access_time = str(datetime.utcfromtimestamp(int(str(link_file[4]).zfill(11) + str(link_file[7]).zfill(7)) / 10000000 - 11644473600)).replace(' ', 'T') + 'Z'
            lnk_write_time = str(datetime.utcfromtimestamp(int(str(link_file[3]).zfill(11) + str(link_file[6]).zfill(7)) / 10000000 - 11644473600)).replace(' ', 'T') + 'Z'
            lnk_creation_time = str(configuration.apply_time_zone(lnk_creation_time, knowledge_base.time_zone))
            lnk_access_time = str(configuration.apply_time_zone(lnk_access_time, knowledge_base.time_zone))
            lnk_write_time = str(configuration.apply_time_zone(lnk_write_time, knowledge_base.time_zone))
            target_creation_time = ""
            target_access_time = ""
            target_write_time = ""
            drive_type = ""
            volume_label = ""
            drive_serial_number = ""
            mac_address = ""

            for idx, result in enumerate(results['LinkHeaderInfo']):
                if idx == 0:
                    continue
                if result[2] == 'Base Path':
                    file_name = result[3][result[3].rfind('\\') + 1:]
                    file_path = result[3].replace('\\', '/')
                elif result[2] == '대상 파일 생성일':
                    target_creation_time = str(configuration.apply_time_zone(str(result[3]).replace(' ', 'T') + 'Z', knowledge_base.time_zone))
                elif result[2] == '대상 파일 사용일':
                    target_access_time = str(configuration.apply_time_zone(str(result[3]).replace(' ', 'T') + 'Z', knowledge_base.time_zone))
                elif result[2] == '대상 파일 수정일':
                    target_write_time = str(configuration.apply_time_zone(str(result[3]).replace(' ', 'T') + 'Z', knowledge_base.time_zone))
                elif result[2] == '볼륨 이름':
                    volume_label = result[3]
                elif result[2] == '볼륨 종류':
                    drive_type = result[3]
                elif result[2] == '대상 파일 크기':
                    file_size = result[3]
                elif result[2] == 'Machine Id':
                    machine_id = result[3]
                elif result[2] == 'Drive Serial Number':
                    drive_serial_number = result[3]
                elif result[2] == 'Mac Address':
                    mac_address = result[3]

            if file_path == '':
                continue

            insert_link_file.append(tuple(
                [par_id, configuration.case_id, configuration.evidence_id, machine_id, file_name, file_path,
                 file_size, lnk_creation_time, lnk_access_time, lnk_write_time,
                 target_creation_time, target_access_time, target_write_time, drive_type, volume_label,
                 drive_serial_number, mac_address, source]))

        query = "Insert into lv1_os_win_link values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"
        configuration.cursor.bulk_execute(query, insert_link_file)


manager.ModulesManager.RegisterModule(LINKConnector)
