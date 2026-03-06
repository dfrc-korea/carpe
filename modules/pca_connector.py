# -*- coding: utf-8 -*-
"""module for PCA."""
import os
from datetime import datetime

from modules import manager
from modules import interface

class PCAConnector(interface.ModuleConnector):
    NAME = 'pca_connector'
    DESCRIPTION = 'Module for Pca'

    _plugin_classes = {}

    def __init__(self):
        super(PCAConnector, self).__init__()

    def _convert_to_utc_string(self, input_datetime):
        # 문자열을 datetime 객체로 변환
        dt_obj = datetime.strptime(input_datetime, "%Y-%m-%d %H:%M:%S.%f")
        
        # UTC 시간 문자열로 변환
        formatted_time = dt_obj.strftime('%Y-%m-%dT%H:%M:%SZ')
        
        return formatted_time

    def Connect(self, par_id, configuration, source_path_spec, knowledge_base):

        this_file_path = os.path.dirname(os.path.abspath(__file__)) + os.sep + 'schema' + os.sep

        # 모든 yaml 파일 리스트
        yaml_list = [this_file_path + 'lv1_os_win_pca_applaunch.yaml',
                     this_file_path + 'lv1_os_win_pca_generaldb.yaml']

        # 모든 테이블 리스트
        table_list = ['lv1_os_win_pca_applaunch',
                      'lv1_os_win_pca_generaldb']

        if not self.check_table_from_yaml(configuration, yaml_list, table_list):
            return False

        query_separator = self.GetQuerySeparator(source_path_spec, configuration)

        query = f"SELECT name, parent_path, inode FROM file_info " \
                f"WHERE par_id='{par_id}' and parent_path like '%Windows{query_separator}appcompat{query_separator}pca'  " \
                f"and extension = 'txt';"

        pca_files = configuration.cursor.execute_query_mul(query)

        if len(pca_files) == 0:
            #print("There are no pca files")
            return False

        insert_pca_applaunch_info = []
        insert_pca_generaldb_info = []

        if configuration.source_type == 'storage media device' or configuration.source_type == 'storage media image':
            tsk_file_system = self.get_tsk_file_system(source_path_spec, configuration)

        for pca in pca_files:
            if configuration.source_type == 'directory' or configuration.source_type == 'file':
                pca_path = pca[1][pca[1].find(source_path_spec.location) + len(source_path_spec.location):] + query_separator + pca[0]
            else:
                pca_path = pca[1][pca[1].find(query_separator):] + query_separator + pca[0]

            file_name = pca[0]
            file_path = pca[1]

            output_path = configuration.root_tmp_path + os.path.sep + configuration.case_id \
                          + os.path.sep + configuration.evidence_id + os.path.sep + par_id

            if not os.path.exists(output_path):
                os.mkdir(output_path)

            if configuration.source_type == 'storage media device' or configuration.source_type == 'storage media image':
                self.extract_file_to_path(tsk_file_system=tsk_file_system,
                                          inode=int(pca[2]),
                                          file_name=file_name,
                                          output_path=output_path)
                                    
            elif configuration.source_type == 'directory' or configuration.source_type == 'file':
                self.ExtractTargetFileToPath(
                    source_path_spec=source_path_spec,
                    configuration=configuration,
                    file_path=pca_path,
                    output_path=output_path)


            fn = output_path + os.path.sep + file_name
            app_path = os.path.abspath(os.path.dirname(__file__)) + os.path.sep + "windows_pca"

            try:
                tmp_filepath = output_path + os.sep + file_name

                if "PcaAppLaunchDic" in file_name:
                    with open(tmp_filepath, 'r', encoding='ansi') as file:
                        for line in file:
                            tmp = []
                            tmp.append(par_id)
                            tmp.append(configuration.case_id)
                            tmp.append(configuration.evidence_id)
                            tmp += line.strip().split('|')
                            if len(tmp) != 5:
                                continue   
                            tmp[4] = self._convert_to_utc_string(tmp[4])
                            insert_pca_applaunch_info.append(tmp)
                elif "PcaGeneralDb" in file_name:
                    with open(tmp_filepath, 'r', encoding='utf-16-le') as file:
                        for line in file:
                            tmp = []
                            tmp.append(par_id)
                            tmp.append(configuration.case_id)
                            tmp.append(configuration.evidence_id)
                            tmp += line.strip().split('|')
                            if len(tmp) != 11:
                                continue
                            tmp[3] = self._convert_to_utc_string(tmp[3])
                            insert_pca_generaldb_info.append(tmp)
                else:
                    print("Unsupported file name format:", file_name)
            except Exception as e:
                print("error", e)

            os.remove(output_path + os.sep + file_name)

        query = "Insert into lv1_os_win_pca_applaunch values (%s, %s, %s, %s, %s);"
        configuration.cursor.bulk_execute(query, insert_pca_applaunch_info)

        query = "Insert into lv1_os_win_pca_generaldb values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"
        configuration.cursor.bulk_execute(query, insert_pca_generaldb_info)

manager.ModulesManager.RegisterModule(PCAConnector)
