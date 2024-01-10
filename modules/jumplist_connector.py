# -*- coding: utf-8 -*-
"""module for Jumplist."""
import os

from modules import manager
from modules import interface
from modules import logger
from modules.windows_jumplist import JumpListParser
from modules.windows_jumplist.res import res_jumplist


class JumpListConnector(interface.ModuleConnector):
    NAME = 'jumplist_connector'
    DESCRIPTION = 'Module for Jumplist'

    _plugin_classes = {}

    def __init__(self):
        super(JumpListConnector, self).__init__()

    def Connect(self, par_id, configuration, source_path_spec, knowledge_base):

        this_file_path = os.path.dirname(os.path.abspath(__file__)) + os.sep + 'schema' + os.sep

        # 모든 yaml 파일 리스트
        yaml_list = [this_file_path + 'lv1_os_win_jumplist_automatics.yaml',
                     this_file_path + 'lv1_os_win_jumplist_custom.yaml']

        # 모든 테이블 리스트
        table_list = ['lv1_os_win_jumplist_automatics',
                      'lv1_os_win_jumplist_custom']

        if not self.check_table_from_yaml(configuration, yaml_list, table_list):
            return False

        # extension -> sig_type 변경해야 함
        # query_separator = '/' if source_path_spec.location == '/' else source_path_spec.location * 2
        query_separator = self.GetQuerySeparator(source_path_spec, configuration)
        path_separator = self.GetPathSeparator(source_path_spec)

        query = f"SELECT name, parent_path, extension, inode FROM file_info WHERE par_id like '{par_id}' and " \
                f"extension like 'automaticDestinations-ms' and " \
                f"parent_path like 'root{query_separator}Users{query_separator}%{query_separator}" \
                f"AppData{query_separator}Roaming{query_separator}Microsoft{query_separator}Windows" \
                f"{query_separator}Recent{query_separator}AutomaticDestinations';"

        jumplist_automatic_files = configuration.cursor.execute_query_mul(query)

        query = f"SELECT name, parent_path, extension, inode FROM file_info WHERE par_id like '{par_id}' and " \
                f"extension like 'customDestinations-ms' and " \
                f"parent_path like 'root{query_separator}Users{query_separator}%{query_separator}" \
                f"AppData{query_separator}Roaming{query_separator}Microsoft{query_separator}Windows" \
                f"{query_separator}Recent{query_separator}CustomDestinations';"

        jumplist_custom_files = configuration.cursor.execute_query_mul(query)

        if len(jumplist_automatic_files) == 0 and len(jumplist_custom_files) == 0:
            # print("There are no jumplist files")
            return False

        output_path = configuration.root_tmp_path + os.path.sep + configuration.case_id + os.path.sep + \
                      configuration.evidence_id + os.path.sep + par_id

        if not os.path.exists(output_path):
            os.mkdir(output_path)

        
        try:
            tsk_file_system = self.get_tsk_file_system(source_path_spec, configuration)
        except Exception as exeption:
            logger.error(exeption)
            return
        insert_jumplist_automatic_file = []
        insert_jumplist_custom_file = []
        for jumplist_automatic_file in jumplist_automatic_files:
            file_name = jumplist_automatic_file[0]
            # file_path = jumplist_automatic_file[1][jumplist_automatic_file[1].find(query_separator):] \
            #             + query_separator + file_name  # document full path

            self.extract_file_to_path(tsk_file_system=tsk_file_system,
                                      inode=int(jumplist_automatic_file[3]),
                                      file_name=file_name,
                                      output_path=output_path)

            # self.ExtractTargetFileToPath(
            #     source_path_spec=source_path_spec,
            #     configuration=configuration,
            #     file_path=file_path,
            #     output_path=output_path)

            fn = output_path + os.path.sep + file_name
            app_path = os.path.abspath(os.path.dirname(__file__)) + os.path.sep + "windows_jumplist"
            try:
                results = JumpListParser.main(fn, app_path)  # filename, app_path
            except ValueError as e:
                print("Error: " + str(e))
                continue

            app_id = file_name[:file_name.rfind('.')]

            if app_id in res_jumplist.app_id_list:
                application_name = res_jumplist.app_id_list[app_id]
            else:
                application_name = None

            for idx, result in enumerate(results['DestList']):
                if idx == 0:
                    continue
                if result[1] is None:
                    record_time = None
                else:
                    record_time = str(configuration.apply_time_zone(
                        str(result[1]).replace(' ', 'T') + 'Z',
                        knowledge_base.time_zone))

                insert_jumplist_automatic_file.append([par_id, configuration.case_id, configuration.evidence_id,
                                                       result[5], (result[6] + result[5]).replace('\\', '/'),
                                                       record_time, result[2], result[3], result[7], result[11],
                                                       result[12], app_id, application_name,
                                                       '/' + '/'.join(jumplist_automatic_file[1].replace('\\', '/').split('/')[1:]) + '/' + jumplist_automatic_file[0]])

            os.remove(output_path + os.sep + file_name)

        for jumplist_custom_file in jumplist_custom_files:
            file_name = jumplist_custom_file[0]
            # file_path = jumplist_custom_file[1][jumplist_custom_file[1].find(
            #     query_separator):] + query_separator + file_name  # document full path

            self.extract_file_to_path(tsk_file_system=tsk_file_system,
                                      inode=int(jumplist_custom_file[3]),
                                      file_name=file_name,
                                      output_path=output_path)

            # self.ExtractTargetFileToPath(
            #     source_path_spec=source_path_spec,
            #     configuration=configuration,
            #     file_path=file_path,
            #     output_path=output_path)

            fn = output_path + os.path.sep + file_name
            app_path = os.path.abspath(os.path.dirname(__file__)) + os.path.sep + "windows_jumplist"
            results = JumpListParser.main(fn, app_path)  # filename, app_path
            if not results:
                os.remove(output_path + os.sep + file_name)
                continue

            for idx, result in enumerate(results['LnkData']):
                if idx == 0:
                    continue
                insert_jumplist_custom_file.append([par_id, configuration.case_id, configuration.evidence_id,
                                                    file_name, result[0], result[1], result[2], result[3], result[4]])

            os.remove(output_path + os.sep + file_name)

        query = "Insert into lv1_os_win_jumplist_automatics values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"
        configuration.cursor.bulk_execute(query, insert_jumplist_automatic_file)

        query = "Insert into lv1_os_win_jumplist_custom values (%s, %s, %s, %s, %s, %s, %s, %s, %s);"
        configuration.cursor.bulk_execute(query, insert_jumplist_custom_file)


manager.ModulesManager.RegisterModule(JumpListConnector)
