# -*- coding: utf-8 -*-
"""module for Prefetch."""
import os
from datetime import datetime, timedelta

from modules import manager
from modules import interface
from modules.windows_prefetch import PFExport2


class PREFETCHConnector(interface.ModuleConnector):
    NAME = 'prefetch_connector'
    DESCRIPTION = 'Module for Prefetch'

    _plugin_classes = {}

    def __init__(self):
        super(PREFETCHConnector, self).__init__()

    def Connect(self, par_id, configuration, source_path_spec, knowledge_base):

        this_file_path = os.path.dirname(os.path.abspath(__file__)) + os.sep + 'schema' + os.sep

        # 모든 yaml 파일 리스트
        yaml_list = [this_file_path + 'lv1_os_win_prefetch.yaml',
                     this_file_path + 'lv1_os_win_prefetch_run_info.yaml',
                     this_file_path + 'lv1_os_win_prefetch_volume_info.yaml']

        # 모든 테이블 리스트
        table_list = ['lv1_os_win_prefetch',
                      'lv1_os_win_prefetch_run_info',
                      'lv1_os_win_prefetch_volume_info']

        if not self.check_table_from_yaml(configuration, yaml_list, table_list):
            return False

        query_separator = self.GetQuerySeparator(source_path_spec, configuration)
        # extension -> sig_type 변경해야 함
        query = f"SELECT name, parent_path, extension, ctime, ctime_nano, inode FROM file_info " \
                f"WHERE par_id='{par_id}' and parent_path like '%Windows{query_separator}Prefetch'  " \
                f"and extension = 'pf';"

        prefetch_files = configuration.cursor.execute_query_mul(query)

        if len(prefetch_files) == 0:
            # print("There are no prefetch files")
            return False

        insert_prefetch_info = []
        insert_prefetch_run_info = []
        insert_prefetch_volume_info = []

        if configuration.source_type == 'storage media device' or configuration.source_type == 'storage media image':
            tsk_file_system = self.get_tsk_file_system(source_path_spec, configuration)

        # tsk_file_system = self.get_tsk_file_system(source_path_spec, configuration)
        for prefetch in prefetch_files:
            if configuration.source_type == 'directory' or configuration.source_type == 'file':
                prefetch_path = prefetch[1][prefetch[1].find(source_path_spec.location) + len(source_path_spec.location):] + query_separator + prefetch[0]
            else:
                prefetch_path = prefetch[1][prefetch[1].find(query_separator):] + query_separator + prefetch[0]
            # file_name = "SVCHOST.EXE-36E2D733.pf"
            file_name = prefetch[0]
            file_path = prefetch[1]

            # Ignore ReadyBoot directory and slack
            if file_name.find("-slack") != -1 or file_name.find("ReadyBoot") != -1:
                continue

            output_path = configuration.root_tmp_path + os.path.sep + configuration.case_id \
                          + os.path.sep + configuration.evidence_id + os.path.sep + par_id

            if not os.path.exists(output_path):
                os.mkdir(output_path)

            if configuration.source_type == 'storage media device' or configuration.source_type == 'storage media image':
                self.extract_file_to_path(tsk_file_system=tsk_file_system,
                                          inode=int(prefetch[5]),
                                          file_name=file_name,
                                          output_path=output_path)
            elif configuration.source_type == 'directory' or configuration.source_type == 'file':
                self.ExtractTargetFileToPath(
                    source_path_spec=source_path_spec,
                    configuration=configuration,
                    file_path=prefetch_path,
                    output_path=output_path)

            fn = output_path + os.path.sep + file_name
            app_path = os.path.abspath(os.path.dirname(__file__)) + os.path.sep + "windows_prefetch"

            # TODO: slack 처리해야 함
            try:
                results = PFExport2.main(fn, app_path)  # filename, app_path

            except Exception:
                continue

            if not results:
                os.remove(output_path + os.sep + file_name)
                continue

            ### prefetch_info ###
            result = results['PrefetchInfo'][1]

            tmp = []
            last_run_times = result[8].split(',')
            prefetch_name = result[1][result[1].rfind(os.path.sep) + 1:]
            tmp.append(par_id)
            tmp.append(configuration.case_id)
            tmp.append(configuration.evidence_id)
            tmp.append(prefetch_name)  # prefetch_name
            tmp.append(result[5])  # program_name
            if result[6] == '':
                tmp.append(' ')
            else:
                tmp.append(result[6])  # program_path
            tmp.append(str(result[7]))  # program_run_count

            if configuration.source_type == 'storage media device' or configuration.source_type == 'storage media image':
                created_time = str(datetime(1601, 1, 1) + timedelta(seconds=float(str(prefetch[3]) + '.' + str(prefetch[4])))).replace(
                    ' ', 'T') + 'Z'

            elif configuration.source_type == 'directory' or configuration.source_type == 'file':
                created_time = datetime.utcfromtimestamp(prefetch[3]).strftime('%Y-%m-%d %H:%M:%S')

            created_time = configuration.apply_time_zone(created_time, knowledge_base.time_zone)
            tmp.append(created_time)  # 생성시간
            tmp.append(' ')  # file_hash
            try:
                last_run_time = last_run_times[0].replace(' ', 'T') + 'Z'
                last_run_time = configuration.apply_time_zone(last_run_time, knowledge_base.time_zone)
                tmp.append(last_run_time)  # last_run_time
            except IndexError:
                tmp.append(' ')
            try:
                second_last_run_time = last_run_times[1].replace(' ', 'T') + 'Z'
                second_last_run_time = configuration.apply_time_zone(second_last_run_time, knowledge_base.time_zone)
                tmp.append(second_last_run_time)  # 2nd_last_run_time
            except IndexError:
                tmp.append(' ')
            try:
                third_last_run_time = last_run_times[2].replace(' ', 'T') + 'Z'
                third_last_run_time = configuration.apply_time_zone(third_last_run_time, knowledge_base.time_zone)
                tmp.append(third_last_run_time)  # 3rd_last_run_time
            except IndexError:
                tmp.append(' ')
            try:
                fourth_last_run_time = last_run_times[3].replace(' ', 'T') + 'Z'
                fourth_last_run_time = configuration.apply_time_zone(fourth_last_run_time, knowledge_base.time_zone)
                tmp.append(fourth_last_run_time)  # 4th_last_run_time
            except IndexError:
                tmp.append(' ')
            try:
                fifth_last_run_time = last_run_times[4].replace(' ', 'T') + 'Z'
                fifth_last_run_time = configuration.apply_time_zone(fifth_last_run_time, knowledge_base.time_zone)
                tmp.append(fifth_last_run_time)  # 5th_last_run_time
            except IndexError:
                tmp.append(' ')
            try:
                sixth_last_run_time = last_run_times[5].replace(' ', 'T') + 'Z'
                sixth_last_run_time = configuration.apply_time_zone(sixth_last_run_time, knowledge_base.time_zone)
                tmp.append(sixth_last_run_time)  # 6th_last_run_time
            except IndexError:
                tmp.append(' ')
            try:
                seventh_last_run_time = last_run_times[6].replace(' ', 'T') + 'Z'
                seventh_last_run_time = configuration.apply_time_zone(seventh_last_run_time, knowledge_base.time_zone)
                tmp.append(seventh_last_run_time)  # 7th_last_run_time
            except IndexError:
                tmp.append(' ')
            try:
                eightth_last_run_time = last_run_times[7].replace(' ', 'T') + 'Z'
                eightth_last_run_time = configuration.apply_time_zone(eightth_last_run_time, knowledge_base.time_zone)
                tmp.append(eightth_last_run_time)  # 8th_last_run_time
            except IndexError:
                tmp.append(' ')

            insert_prefetch_info.append(tuple(tmp))

            # prefetch_run_info
            for idx, result in enumerate(results['RunInfo']):
                if idx == 0:
                    continue
                insert_prefetch_run_info.append([par_id, configuration.case_id, configuration.evidence_id,
                                                 prefetch_name, result[1], result[2], result[3], result[4],
                                                 '/' + '/'.join(prefetch[1].replace('\\', '/').split('/')[1:]) + '/' +
                                                 prefetch[0]])

            # prefetch_volume_info
            for idx, result in enumerate(results['VolInfo']):
                if idx == 0:
                    continue
                if result[2] is not None:
                    result[2] = str(result[2]).replace(' ', 'T') + 'Z'
                    result[2] = configuration.apply_time_zone(result[2], knowledge_base.time_zone)  # creation_time
                insert_prefetch_volume_info.append([par_id, configuration.case_id, configuration.evidence_id,
                                                    prefetch_name, result[1], result[2], result[3], result[4]])

            os.remove(output_path + os.sep + file_name)

        query = "Insert into lv1_os_win_prefetch values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, " \
                "%s, %s);"
        configuration.cursor.bulk_execute(query, insert_prefetch_info)

        query = "Insert into lv1_os_win_prefetch_run_info values (%s, %s, %s, %s, %s, %s, %s, %s, %s);"
        configuration.cursor.bulk_execute(query, insert_prefetch_run_info)

        query = "Insert into lv1_os_win_prefetch_volume_info values (%s, %s, %s, %s, %s, %s, %s, %s);"
        configuration.cursor.bulk_execute(query, insert_prefetch_volume_info)


manager.ModulesManager.RegisterModule(PREFETCHConnector)
