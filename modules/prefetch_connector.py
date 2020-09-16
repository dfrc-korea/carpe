# -*- coding: utf-8 -*-
"""module for Prefetch."""
import os, sys
import time
from datetime import datetime, timedelta

from modules import logger
from modules import manager
from modules import interface
from modules.windows_prefetch import PFExport2
from dfvfs.lib import definitions as dfvfs_definitions


class PREFETCHConnector(interface.ModuleConnector):
    NAME = 'prefetch_connector'
    DESCRIPTION = 'Moudle for Prefetch'

    _plugin_classes = {}

    def __init__(self):
        super(PREFETCHConnector, self).__init__()

    def Connect(self, configuration, source_path_spec, knowledge_base):

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

        if source_path_spec.parent.type_indicator != dfvfs_definitions.TYPE_INDICATOR_TSK_PARTITION:
            par_id = configuration.partition_list['p1']
        else:
            par_id = configuration.partition_list[getattr(source_path_spec.parent, 'location', None)[1:]]

        if par_id is None:
            return False

        print('[MODULE]: Prefetch Connect - partition ID(%s)' % par_id)

        # extension -> sig_type 변경해야 함
        query = f"SELECT name, parent_path, extension, ctime, ctime_nano FROM file_info WHERE par_id='{par_id}' and " \
                f"parent_path = 'root/Windows/Prefetch' and extension = 'pf';"

        prefetch_files = configuration.cursor.execute_query_mul(query)

        if len(prefetch_files) == 0:
            return False

        insert_prefetch_info = []
        insert_prefetch_run_info = []
        insert_prefetch_volume_info = []

        for prefetch in prefetch_files:
            prefetch_path = prefetch[1][prefetch[1].find('/'):] + '/' + prefetch[0]  # document full path
            fileExt = prefetch[2]

            # fileName = "SVCHOST.EXE-36E2D733.pf"
            fileName = prefetch[0]

            # Ignore ReadyBoot directory and slack
            if fileName.find("-slack") != -1 or fileName.find("ReadyBoot") != -1:
                continue

            output_path = configuration.root_tmp_path + os.path.sep + configuration.case_id \
                          + os.path.sep + configuration.evidence_id + os.path.sep + par_id

            if not os.path.exists(output_path):
                os.mkdir(output_path)

            self.ExtractTargetFileToPath(
                source_path_spec=source_path_spec,
                configuration=configuration,
                file_path=prefetch_path,
                output_path=output_path)

            fn = output_path + os.path.sep + fileName
            app_path = os.path.abspath(os.path.dirname(__file__)) + os.path.sep + "windows_prefetch"
            # TODO: slack 처리해야 함
            results = PFExport2.main(fn, app_path)  # filename, app_path

            if not results:
                os.remove(output_path + os.sep + fileName)
                continue

            ### prefetch_info ###
            result = results['PrefetchInfo'][1]

            tmp = []
            last_run_time = result[8].split(',')
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
            tmp.append(
                str(datetime(1970, 1, 1) + timedelta(seconds=float(str(prefetch[3]) + '.' + str(prefetch[4])))).replace(
                    ' ', 'T') + 'Z')  # 생성시간
            tmp.append(' ')  # file_hash
            try:
                tmp.append(last_run_time[0].replace(' ', 'T') + 'Z')  # last_run_time
            except IndexError:
                tmp.append(' ')
            try:
                tmp.append(last_run_time[1].replace(' ', 'T') + 'Z')  # 2nd_last_run_time
            except IndexError:
                tmp.append(' ')
            try:
                tmp.append(last_run_time[2].replace(' ', 'T') + 'Z')  # 3rd_last_run_time
            except IndexError:
                tmp.append(' ')
            try:
                tmp.append(last_run_time[3].replace(' ', 'T') + 'Z')  # 4th_last_run_time
            except IndexError:
                tmp.append(' ')
            try:
                tmp.append(last_run_time[4].replace(' ', 'T') + 'Z')  # 5th_last_run_time
            except IndexError:
                tmp.append(' ')
            try:
                tmp.append(last_run_time[5].replace(' ', 'T') + 'Z')  # 6th_last_run_time
            except IndexError:
                tmp.append(' ')
            try:
                tmp.append(last_run_time[6].replace(' ', 'T') + 'Z')  # 7th_last_run_time
            except IndexError:
                tmp.append(' ')
            try:
                tmp.append(last_run_time[7].replace(' ', 'T') + 'Z')  # 8th_last_run_time
            except IndexError:
                tmp.append(' ')

            insert_prefetch_info.append(tuple(tmp))

            ### prefetch_run_info ###
            for idx, result in enumerate(results['RunInfo']):
                if idx == 0:
                    continue
                insert_prefetch_run_info.append(tuple(
                    [par_id, configuration.case_id, configuration.evidence_id, prefetch_name, result[1], result[2],
                     result[3], result[4]]))

            ### prefetch_volume_info ###
            for idx, result in enumerate(results['VolInfo']):
                if idx == 0:
                    continue
                insert_prefetch_volume_info.append(tuple(
                    [par_id, configuration.case_id, configuration.evidence_id, prefetch_name, result[1], result[2],
                     result[3], result[4]]))

            os.remove(output_path + os.sep + fileName)

        query = "Insert into lv1_os_win_prefetch values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"
        configuration.cursor.bulk_execute(query, insert_prefetch_info)

        query = "Insert into lv1_os_win_prefetch_run_info values (%s, %s, %s, %s, %s, %s, %s, %s);"
        configuration.cursor.bulk_execute(query, insert_prefetch_run_info)

        query = "Insert into lv1_os_win_prefetch_volume_info values (%s, %s, %s, %s, %s, %s, %s, %s);"
        configuration.cursor.bulk_execute(query, insert_prefetch_volume_info)


manager.ModulesManager.RegisterModule(PREFETCHConnector)
