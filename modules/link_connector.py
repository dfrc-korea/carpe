# -*- coding: utf-8 -*-
"""module for Link."""
import os, sys

from modules import logger
from modules import manager
from modules import interface
from modules.windows_jumplist import LNKFileParser
from dfvfs.lib import definitions as dfvfs_definitions


class LINKConnector(interface.ModuleConnector):

    NAME = 'link_connector'
    DESCRIPTION = 'Module for Link'

    _plugin_classes = {}

    def __init__(self):
        super(LINKConnector, self).__init__()

    def Connect(self, configuration, source_path_spec, knowledge_base):
        print('[MODULE]: Link Connect')

        this_file_path = os.path.dirname(os.path.abspath(__file__)) + os.sep + 'schema' + os.sep
        # 모든 yaml 파일 리스트
        yaml_list = [this_file_path + 'lv1_os_win_link.yaml']

        # 모든 테이블 리스트
        table_list = ['lv1_os_win_link']

        if not self.check_table_from_yaml(configuration, yaml_list, table_list):
            return False

        if source_path_spec.parent.type_indicator != dfvfs_definitions.TYPE_INDICATOR_TSK_PARTITION:
            par_id = configuration.partition_list['p1']
        else:
            par_id = configuration.partition_list[getattr(source_path_spec.parent, 'location', None)[1:]]

        if par_id == None:
            return False

        # extension -> sig_type 변경해야 함
        query = f"SELECT name, parent_path, extension FROM file_info WHERE par_id like '{par_id}' and " \
                f"extension like 'lnk';"

        jumplist_automatic_files = configuration.cursor.execute_query_mul(query)

        if len(jumplist_automatic_files) == 0:
            return False



        insert_link_file = []

        for link_file in jumplist_automatic_files:
            file_path = link_file[1][link_file[1].find('/'):] + '/' + link_file[0]  # document full path
            fileExt = link_file[2]
            fileName = link_file[0]
            #print(fileName)
            output_path = configuration.root_tmp_path + os.path.sep + configuration.case_id + os.path.sep + configuration.evidence_id + os.path.sep + par_id

            if not os.path.exists(output_path):
                os.mkdir(output_path)

            file_object = self.LoadTargetFileToMemory(
                source_path_spec=source_path_spec,
                configuration=configuration,
                file_path=file_path)

            app_path = os.path.abspath(os.path.dirname(__file__)) + os.path.sep + "windows_jumplist"  # Jumplist 폴더 내의 링크 파서 사용
            results = LNKFileParser.main(file_object, app_path, fileName)  # filename, app_path

            file_object.close()

            if results == False:
                continue
            machine_id = ""
            file_name = ""
            file_path = ""
            file_size = ""
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
                    file_path = result[3].replace('\\','/')
                elif result[2] == '대상 파일 생성일':
                    target_creation_time = str(result[3]).replace(' ', 'T') + 'Z'
                elif result[2] == '대상 파일 사용일':
                    target_access_time = str(result[3]).replace(' ', 'T') + 'Z'
                elif result[2] == '대상 파일 수정일':
                    target_write_time = str(result[3]).replace(' ', 'T') + 'Z'
                elif result[2] == '볼륨 이름':
                    volume_label = result[3]
                elif result[2] == '볼륨 종류':
                    drive_type = result[3]

            if file_path == '':
                continue

            insert_link_file.append(tuple([par_id, configuration.case_id, configuration.evidence_id, machine_id, file_name, file_path, file_size, target_creation_time, target_access_time, target_write_time, drive_type, volume_label, drive_serial_number, mac_address]))


            #os.remove(output_path + os.sep + fileName)

        query = "Insert into lv1_os_win_link values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"
        configuration.cursor.bulk_execute(query, insert_link_file)



manager.ModulesManager.RegisterModule(LINKConnector)