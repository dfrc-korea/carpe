# -*- coding: utf-8 -*-
"""module for LV2OSWINUSAGEHISTORYAnalyzer."""
import os
from advanced_modules import manager
from advanced_modules import interface
from advanced_modules import logger
from datetime import datetime, timedelta

from advanced_modules.windows_usage_history import lv2_visualization_usage_year as uy, lv2_visualization_usage_day_stat as uds, lv2_visualization_usage_day_detail as udd, lv2_visualization_timeline_month as tm


class LV2OSUSAGEHISTORYAnalyzer(interface.AdvancedModuleAnalyzer):

    NAME = 'lv2_os_usage_history_analyzer'
    DESCRIPTION = 'Module for LV2 OS Win Usage History Analyzer'

    _plugin_classes = {}

    def __init__(self):
        super(LV2OSUSAGEHISTORYAnalyzer, self).__init__()

    def Analyze(self, par_id, configuration, source_path_spec, knowledge_base):
        # try:

        #query_separator = "/" if source_path_spec.location == "/" else source_path_spec.location * 2
        query_separator = self.GetQuerySeparator(source_path_spec, configuration)
        path_separator = self.GetPathSeparator(source_path_spec)
        # query = f"SELECT name, parent_path, extension FROM file_info WHERE (par_id='{par_id}') " \
        #         f"and extension = 'evtx' and parent_path like 'root{query_separator}Windows{query_separator}" \
        #         f"System32{query_separator}winevt{query_separator}Logs'"
        # eventlog_files = configuration.cursor.execute_query_mul(query)
        #
        # if len(eventlog_files) == 0:
        #     return False
        # if source_path_spec.TYPE_INDICATOR != 'NTFS':
        #     return False

        this_file_path = os.path.dirname(os.path.abspath(__file__)) + os.sep + 'schema' + os.sep + 'visualization' + os.sep

        # 모든 yaml 파일 리스트
        yaml_list = [this_file_path + 'lv2_visualization_usage_day_detail.yaml',
                     this_file_path + 'lv2_visualization_usage_year.yaml',
                     this_file_path + 'lv2_visualization_usage_day_stat.yaml',
                     this_file_path + 'lv2_visualization_timeline_month.yaml']

        # 모든 테이블 리스트
        table_list = ['usage_day_detail',
                      'usage_year',
                      'usage_day_stat',
                      'timeline_month_2']

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

        # USAGE_DAY_DETAIL
        print('[MODULE] LV2 OS Win Usage History Analyzer - USAGE_DAY_DETAIL')
        insert_data = []
        for result in udd.USAGEDAYDETAIL(configuration, knowledge_base.time_zone):
            # try:
            insert_data.append(tuple(
                [result.regdate,
                 result.evdnc_type, result.artifact_type, result.information, configuration.case_id,
                 configuration.evidence_id]
            ))
            # except:
            #     insert_data.append(tuple(
            #         [result.regdate, result.evdnc_type, result.artifact_type, result.information,
            #          configuration.case_id, configuration.evidence_id]
            #     ))
        query = "Insert into usage_day_detail values (%s, %s, %s, %s, %s, %s);"
        if len(insert_data) > 0:
            configuration.cursor.bulk_execute(query, insert_data)

        #USAGE_YEAR
        print('[MODULE] LV2 OS Win Usage History Analyzer - USAGE_YEAR')
        insert_data = []
        for result in uy.USAGEYEAR(configuration):
            insert_data.append(tuple(
                [result.year, result.month, result.cnt, configuration.case_id, configuration.evidence_id]
            ))
        query = "Insert into usage_year values (%s, %s, %s, %s, %s);"
        if len(insert_data) > 0:
            configuration.cursor.bulk_execute(query, insert_data)

        #USAGE_DAY_STAT
        print('[MODULE] LV2 OS Win Usage History Analyzer - USAGE_DAY_STAT')
        insert_data = []
        for result in uds.USAGEDAYSTAT(configuration):
            insert_data.append(tuple(
                [result.year, result.month, result.day, result.hour, result.min, result.act, configuration.case_id, configuration.evidence_id]
            ))
        query = "Insert into usage_day_stat values (%s, %s, %s, %s, %s, %s, %s, %s);"
        if len(insert_data) > 0:
            configuration.cursor.bulk_execute(query, insert_data)


        #Timeline_month
        print('[MODULE] LV2 OS Win Usage History Analyzer - TIMELINE MONTH')
        insert_data = []
        query = "Insert into timeline_month_2 values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"
        for result in tm.TIMELINEMONTH(configuration):
            for i in result:
                i[0] = configuration.evidence_id
                insert_data.append(tuple(i))
        configuration.cursor.bulk_execute(query, insert_data)

        # except:
        #     print("LV2 OS Win Usage History Analyzer Error")


manager.AdvancedModulesManager.RegisterModule(LV2OSUSAGEHISTORYAnalyzer)
