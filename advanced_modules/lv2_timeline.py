
import datetime
import os

from advanced_modules import manager
from advanced_modules import interface
from advanced_modules import logger
from dfvfs.lib import definitions as dfvfs_definitions


class LV2TIMELINEAnalyzer(interface.AdvancedModuleAnalyzer):

    NAME = 'lv2_timeline'
    DESCRIPTION = 'Moudle for LV2 Timeline'

    _plugin_classes = {}

    def _convert_timestamp(self, timestamp):
        time = datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%dT%H:%M:%S')
        return time

    def __init__(self):
        super(LV2TIMELINEAnalyzer, self).__init__()

    def Analyze(self, par_id, configuration, source_path_spec, knowledge_base):
        print('[MODULE]: LV2 Timeline Analyzer')

        this_file_path = os.path.dirname(os.path.abspath(__file__)) + os.sep + 'schema' + os.sep
        # 모든 yaml 파일 리스트
        yaml_list = [this_file_path+'lv2_timeline.yaml']

        # 모든 테이블 리스트
        table_list = ['lv2_timeline']

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

        print("not yet")