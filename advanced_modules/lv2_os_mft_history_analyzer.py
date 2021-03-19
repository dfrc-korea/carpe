
import datetime
import os

from advanced_modules import manager
from advanced_modules import interface
from advanced_modules import logger


class LV2OSMFTHISTORYAnalyzer(interface.AdvancedModuleAnalyzer):

    NAME = 'lv2_os_mft_history_analyzer'
    DESCRIPTION = 'Module for LV2 OS MFT History'

    _plugin_classes = {}

    def _convert_timestamp(self, timestamp):
        time = datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%dT%H:%M:%S')
        return time

    def __init__(self):
        super(LV2OSMFTHISTORYAnalyzer, self).__init__()

    def Analyze(self, par_id, configuration, source_path_spec, knowledge_base):
        this_file_path = os.path.dirname(os.path.abspath(__file__)) + os.sep + 'schema' + os.sep
        # 모든 yaml 파일 리스트
        yaml_list = [this_file_path+'lv2_os_mft_history.yaml']

        # 모든 테이블 리스트
        table_list = ['lv2_os_mft_history']

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

        query = f"SELECT file_id, par_id, inode, name, dir_type, size, extension, mtime, atime, ctime, etime, mtime_nano," \
                f" atime_nano, ctime_nano, etime_nano, parent_path, parent_id FROM file_info WHERE par_id='{par_id}' and not type = \"7\";"
        results = configuration.cursor.execute_query_mul(query)

        if len(results) == 0:
            pass

        else:
            insert_data = []
            for result in results:

                mtime = result[7] # mtime = file modified time
                ctime = result[9] # ctime = file created time
                mtime_nano = result[11]
                ctime_nano = result[13]

                # Copied file distinction
                if mtime - ctime == 0:
                    if mtime_nano - ctime_nano == 0:
                        is_copied = "N"
                    elif mtime_nano - ctime_nano > 0:
                        is_copied = "N"
                    elif mtime_nano - ctime_nano < 0:
                        is_copied = "Y"
                elif mtime - ctime > 0:
                    is_copied = "N"
                elif mtime - ctime < 0:
                    is_copied = "Y"

                # Make Standard Timestamp Format
                if result[7] > 11644473600 or result[9] > 11644473600:
                    mtime = self._convert_timestamp(result[7] - 11644473600)+"."+str(result[11])+"Z"
                    atime = self._convert_timestamp(result[8] - 11644473600)+"."+str(result[12])+"Z"
                    ctime = self._convert_timestamp(result[9] - 11644473600)+"."+str(result[13])+"Z"
                    etime = self._convert_timestamp(result[10] - 11644473600)+"."+str(result[14])+"Z"

                else:
                    mtime = self._convert_timestamp(result[7]) + "." + str(result[11]) + "Z"
                    atime = self._convert_timestamp(result[8]) + "." + str(result[12]) + "Z"
                    ctime = self._convert_timestamp(result[9]) + "." + str(result[13]) + "Z"
                    etime = self._convert_timestamp(result[10]) + "." + str(result[14]) + "Z"

                file_id = result[0]
                par_id = result[1]
                inode = result[2]
                name = result[3]
                dir_type = result[4]
                size = result[5]
                extension = result[6]
                parent_path = result[15]
                parent_id = result[16]

                insert_data.append(tuple([par_id, configuration.case_id, configuration.evidence_id, file_id, inode, name,
                                          dir_type, size, extension, mtime, atime, ctime, etime, parent_path, parent_id, is_copied]))

            query = "Insert into lv2_os_mft_history values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"
            configuration.cursor.bulk_execute(query, insert_data)


manager.AdvancedModulesManager.RegisterModule(LV2OSMFTHISTORYAnalyzer)