# -*- coding: utf-8 -*-
"""module for LV2."""
import os, sys, dateutil
from datetime import datetime

from advanced_modules import manager
from advanced_modules import interface
from advanced_modules import logger
from dfvfs.lib import definitions as dfvfs_definitions


class LV2OSAPPHISTORYAnalyzer(interface.AdvancedModuleAnalyzer):
    NAME = 'lv2_os_app_history_analyzer'
    DESCRIPTION = 'Module for LV2 OS APP History'

    _plugin_classes = {}

    def __init__(self):
        super(LV2OSAPPHISTORYAnalyzer, self).__init__()

    def Analyze(self, par_id, configuration, source_path_spec, knowledge_base):

        this_file_path = os.path.dirname(os.path.abspath(__file__)) + os.sep + 'schema' + os.sep
        # 모든 yaml 파일 리스트
        yaml_list = [this_file_path + 'lv2_os_app_history.yaml']

        # 모든 테이블 리스트
        table_list = ['lv2_os_app_history']

        # 모든 테이블 생성
        for count in range(0, len(yaml_list)):
            if not self.LoadSchemaFromYaml(yaml_list[count]):
                logger.error('cannot load schema from yaml: {0:s}'.format(table_list[count]))
                return False

            # if table is not existed, create table
            if not configuration.cursor.check_table_exist(table_list[count]):
                ret = self.CreateTable(configuration.cursor)
                if not ret:
                    logger.error('cannot create database table name: {0:s}'.format(table_list[count]))
                    return False

        # UserAssist
        query = f"SELECT file_name, last_run_time FROM lv1_os_win_reg_user_assist WHERE par_id='{par_id}';"
        results = configuration.cursor.execute_query_mul(query)

        if type(results) == int or len(results) == 0:
            pass
        else:
            insert_data = []
            for result in results:
                if dateutil.parser.parse(str(result[1])) > dateutil.parser.parse('1970-01-01T00:00:00+00:00'):
                    insert_data.append(tuple(
                        [par_id, configuration.case_id, configuration.evidence_id, result[0][result[0].rfind('/') + 1:],
                         result[1], result[0], '', 'UserAssist']))

            query = "Insert into lv2_os_app_history values (%s, %s, %s, %s, %s, %s, %s, %s);"
            configuration.cursor.bulk_execute(query, insert_data)

        # Amcache - file_entries
        query = f"SELECT file_name, key_last_updated_time, full_path FROM lv1_os_win_reg_amcache_file WHERE par_id='{par_id}';"
        results = configuration.cursor.execute_query_mul(query)

        if type(results) == int or len(results) == 0:
            pass
        else:
            insert_data = []
            for result in results:
                if dateutil.parser.parse(str(result[1])) > dateutil.parser.parse('1970-01-01T00:00:00+00:00'):
                    insert_data.append(tuple(
                        [par_id, configuration.case_id, configuration.evidence_id, result[0], result[1], result[2], '',
                         'Amcache-file_entries']))

            query = "Insert into lv2_os_app_history values (%s, %s, %s, %s, %s, %s, %s, %s);"
            configuration.cursor.bulk_execute(query, insert_data)

        # Prefetch - reference_file 추후에 추가
        query = f"SELECT program_name, program_path, program_run_count, file_created_time, last_run_time, " \
                f"`2nd_last_run_time`, `3rd_last_run_time`, `4th_last_run_time`, `5th_last_run_time`, " \
                f"`6th_last_run_time`, `7th_last_run_time`, `8th_last_run_time` " \
                f"FROM lv1_os_win_prefetch WHERE par_id='{par_id}';"
        results = configuration.cursor.execute_query_mul(query)

        if type(results) == int or len(results) == 0:
            pass
        else:
            insert_data = []
            for result in results:
                if dateutil.parser.parse(result[3]) > dateutil.parser.parse('1970-01-01T00:00:00+00:00') :
                    insert_data.append(tuple(
                        [par_id, configuration.case_id, configuration.evidence_id, result[0], result[3], result[1], '',
                         'Prefetch']))
                if result[4] != ' ':
                    if dateutil.parser.parse(result[4]) > dateutil.parser.parse('1970-01-01T00:00:00+00:00'):
                        insert_data.append(tuple(
                            [par_id, configuration.case_id, configuration.evidence_id, result[0], result[4], result[1], '',
                             'Prefetch']))
                if result[5] != ' ':
                    if dateutil.parser.parse(result[5]) > dateutil.parser.parse('1970-01-01T00:00:00+00:00'):
                        insert_data.append(tuple(
                            [par_id, configuration.case_id, configuration.evidence_id, result[0], result[5], result[1], '',
                             'Prefetch']))
                if result[6] != ' ':
                    if dateutil.parser.parse(result[6]) > dateutil.parser.parse('1970-01-01T00:00:00+00:00'):
                        insert_data.append(tuple(
                            [par_id, configuration.case_id, configuration.evidence_id, result[0], result[6], result[1], '',
                             'Prefetch']))
                if result[7] != ' ':
                    if dateutil.parser.parse(result[7]) > dateutil.parser.parse('1970-01-01T00:00:00+00:00'):
                        insert_data.append(tuple(
                            [par_id, configuration.case_id, configuration.evidence_id, result[0], result[7], result[1], '',
                             'Prefetch']))
                if result[8] != ' ':
                    if dateutil.parser.parse(result[8]) > dateutil.parser.parse('1970-01-01T00:00:00+00:00'):
                        insert_data.append(tuple(
                            [par_id, configuration.case_id, configuration.evidence_id, result[0], result[8], result[1], '',
                             'Prefetch']))
                if result[9] != ' ':
                    if dateutil.parser.parse(result[9]) > dateutil.parser.parse('1970-01-01T00:00:00+00:00'):
                        insert_data.append(tuple(
                            [par_id, configuration.case_id, configuration.evidence_id, result[0], result[9], result[1], '',
                             'Prefetch']))
                if result[10] != ' ':
                    if dateutil.parser.parse(result[10]) > dateutil.parser.parse('1970-01-01T00:00:00+00:00'):
                        insert_data.append(tuple(
                            [par_id, configuration.case_id, configuration.evidence_id, result[0], result[10], result[1], '',
                             'Prefetch']))
                if result[11] != ' ':
                    if dateutil.parser.parse(result[11]) > dateutil.parser.parse('1970-01-01T00:00:00+00:00'):
                        insert_data.append(tuple(
                            [par_id, configuration.case_id, configuration.evidence_id, result[0], result[11], result[1], '',
                             'Prefetch']))

            query = "Insert into lv2_os_app_history values (%s, %s, %s, %s, %s, %s, %s, %s);"
            configuration.cursor.bulk_execute(query, insert_data)

        # Windows Timeline
        query = f"SELECT program_name, start_time, content FROM lv1_os_win_windows_timeline WHERE par_id='{par_id}';"
        results = configuration.cursor.execute_query_mul(query)

        if type(results) == int or len(results) == 0:
            pass
        else:
            insert_data = []
            for result in results:
                if dateutil.parser.parse(result[1]) > dateutil.parser.parse('1970-01-01T00:00:00+00:00') :
                    insert_data.append(tuple(
                        [par_id, configuration.case_id, configuration.evidence_id, result[0][result[0].rfind('/') + 1:],
                         result[1], result[0], result[2],
                         'Windows Timeline']))

            query = "Insert into lv2_os_app_history values (%s, %s, %s, %s, %s, %s, %s, %s);"
            configuration.cursor.bulk_execute(query, insert_data)

        # Eventlog - application
        query = f"SELECT application_name, time, path FROM lv1_os_win_event_logs_applications WHERE par_id='{par_id}';"
        results = configuration.cursor.execute_query_mul(query)

        if type(results) == int or len(results) == 0:
            pass
        else:
            insert_data = []
            for result in results:
                if dateutil.parser.parse(str(result[1])) > dateutil.parser.parse('1970-01-01T00:00:00+00:00') :
                    insert_data.append(tuple(
                        [par_id, configuration.case_id, configuration.evidence_id, result[0],
                         str(result[1]), result[2], '',
                         'Eventlogs-Application']))

            query = "Insert into lv2_os_app_history values (%s, %s, %s, %s, %s, %s, %s, %s);"
            configuration.cursor.bulk_execute(query, insert_data)

        # Jumplist - automatics
        query = f"SELECT file_name, file_path, record_time, application_name " \
                f"FROM lv1_os_win_jumplist_automatics WHERE par_id='{par_id}';"
        results = configuration.cursor.execute_query_mul(query)

        if type(results) == int or len(results) == 0:
            pass
        else:
            insert_data = []
            for result in results:
                if dateutil.parser.parse(str(result[2])) > dateutil.parser.parse('1970-01-01T00:00:00+00:00'):
                    insert_data.append(tuple(
                        [par_id, configuration.case_id, configuration.evidence_id, result[3],
                         result[2], '', result[1],
                         'Jumplist-automatics']))

            query = "Insert into lv2_os_app_history values (%s, %s, %s, %s, %s, %s, %s, %s);"
            configuration.cursor.bulk_execute(query, insert_data)


manager.AdvancedModulesManager.RegisterModule(LV2OSAPPHISTORYAnalyzer)