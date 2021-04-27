# -*- coding: utf-8 -*-
"""module for android forensics."""
import os
import io
import platform
import subprocess
import sqlite3

from datetime import datetime
from modules import logger
from modules import manager
from modules import interface


class AndForensicsConnector(interface.ModuleConnector):
    NAME = 'andforensics_connector'
    DESCRIPTION = 'Module for AndForensics'
    TABLE_NAME = 'lv1_os_android_andforensics'

    _plugin_classes = {}

    def __init__(self):
        super(AndForensicsConnector, self).__init__()

    def Connect(self, par_id, configuration, source_path_spec, knowledge_base):
        """Connector to connect to AndForensics.

        Args:
            par_id: partition id.
            configuration: configuration values.
            source_path_spec (dfvfs.PathSpec): path specification of the source file.
            knowledge_base (KnowledgeBase): knowledge base.

        """
        # Check Filesystem
        query = f"SELECT filesystem FROM partition_info WHERE par_id like '{par_id}'"
        filesystem = configuration.cursor.execute_query(query)

        if filesystem is None or filesystem[0] != "TSK_FS_TYPE_EXT4":
            #print("No EXT filesystem.")
            return False

        # Check Platform
        if platform.platform().find('Windows') >= 0:
            print("No Linux platform.")
            return False

        # 이미지를 복사해와야함 andforensics
        if os.path.exists(configuration.source_path):
            cmd = 'python3.6 /home/byeongchan/modules/andForensics/andForensics.py -i \'{0:s}\' -o \'{1:s}\' ' \
                  '-proc {2:d}'.format(os.path.dirname(configuration.source_path),
                                       configuration.tmp_path + os.sep + 'andForensics', 10)

            proc = subprocess.Popen(cmd, shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
            ret_code = proc.stdout.read()
            f = io.StringIO(str(ret_code))
            result_msg = f.readline()
            # print(result_msg)
            f.close()
            if result_msg[-14:-3] == 'Process End':

                base_name = os.path.basename(configuration.source_path)
                output_path = configuration.tmp_path + os.sep + 'andForensics' + os.sep \
                              + os.path.basename(configuration.source_path)
                analysis_db_path = output_path + os.sep + 'analysis_' + base_name + '.db'
                load_db_path = output_path + os.sep + 'loaddb_' + base_name + '.db'
                preprocess_db_path = output_path + os.sep + 'preprocess_' + base_name + '.db'

                this_file_path = os.path.dirname(
                    os.path.abspath(__file__)) + os.sep + 'schema' + os.sep + 'android' + os.sep

                yaml_list = [this_file_path + 'lv1_os_and_app_list.yaml',
                             this_file_path + 'lv1_os_and_call_history.yaml',
                             this_file_path + 'lv1_os_and_emb_file.yaml',
                             this_file_path + 'lv1_os_and_file_history.yaml',
                             this_file_path + 'lv1_os_and_geodata.yaml',
                             this_file_path + 'lv1_os_and_id_pw_hash.yaml',
                             this_file_path + 'lv1_os_and_web_browser_history.yaml']

                old_table_list = ['application_list', 'call_history', 'embedded_file', 'file_history',
                                  'geodata', 'id_password_hash', 'web_browser_history']

                new_table_list = ['lv1_os_and_app_list', 'lv1_os_and_call_history', 'lv1_os_and_emb_file',
                                  'lv1_os_and_file_history', 'lv1_os_and_geodata', 'lv1_os_and_id_pw_hash',
                                  'lv1_os_and_web_browser_history']

                if not self.check_table_from_yaml(configuration, yaml_list, new_table_list):
                    return False

                info = tuple([par_id, configuration.case_id, configuration.evidence_id])
                try:
                    conn = sqlite3.connect(analysis_db_path)
                    cursor = conn.cursor()
                    for idx, table in enumerate(old_table_list):
                        cursor.execute(f'select * from {table}')
                        rows = cursor.fetchall()
                        rows_list = []
                        for row in rows:
                            if table is 'application_list':
                                row = row[:5] + _convert_timestamp(row[5:13]) + row[13:]
                            rows_list.append(info + row)
                        print(rows_list)
                        query = ""
                        if table is 'application_list':
                            query = f"Insert into {new_table_list[idx]} values (%s, %s, %s, %s, %s, %s, %s, %s, %s, " \
                                    f"%s, %s, %s, %s, %s, %s, %s, %s, %s);"
                        if table is 'call_history':
                            query = f"Insert into {new_table_list[idx]} values (%s, %s, %s, %s, %s, %s, %s, %s, %s, " \
                                    f"%s, %s, %s)"
                        elif table is 'embedded_file':
                            query = f"Insert into {new_table_list[idx]} values (%s, %s, %s, %s, %s, %s, %s, %s, %s, " \
                                    f"%s, %s, %s, %s, %s)"
                        elif table is 'file_history' or table is 'id_password_hash':
                            query = f"Insert into {new_table_list[idx]} values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
                        elif table is 'geodata':
                            query = f"Insert into {new_table_list[idx]} values (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
                        elif table is 'web_browser_history':
                            query = f"Insert into {new_table_list[idx]} values (%s, %s, %s, %s, %s, %s, %s, %s, " \
                                    f"%s, %s, %s)"

                        configuration.cursor.bulk_execute(query, rows_list)

                    self.mask_table(configuration, 'call_history')

                except Exception as exception:
                    logger.error('Database error : {0!s}'.format(exception))
                finally:
                    conn.close()
            else:
                logger.info('')

    def mask_table(self, configuration, table_name):
        if table_name is 'call_history':
            query = "update lv1_os_and_call_history set timestamp = regexp_replace(timestamp, " \
                    "'(\\\\d{2,3}-)\\\\d{1,2}(\\\\d{2}-)\\\\d{2}(\\\\d{2})', " \
                    "'\\\\1**\\\\2**\\\\3');"
            configuration.cursor.execute_query(query)
            query = "update lv1_os_and_call_history set phonenumber = regexp_replace(phonenumber, " \
                    "'((?:(?:0|\\\\+82)(?:10|2|3[1-3]|4[1-4]|5[0-5]|6[1-4]|70)-?)\\\\d{1,2})\\\\d{2}(-?)\\\\d{2}(\\\\d{2})', " \
                    "'\\\\1**\\\\2**\\\\3')"
            configuration.cursor.execute_query(query)
            query = "update lv1_os_and_call_history set file = regexp_replace(file, " \
                    "'(통화 녹음 )([가-힣]|(?:\\\\d{6}))(?:\\\\s|\\\\S)*(_\\\\d{6}_\\\\d{6})', " \
                    "'\\\\1\\\\2*\\\\3')"
            configuration.cursor.execute_query(query)
            query = "update lv1_os_and_call_history SET contents = if(CHAR_LENGTH(contents)-CHAR_LENGTH(REPLACE(contents,'|',''))=2," \
                    "    CONCAT_WS('|'," \
                    "              REGEXP_REPLACE(SUBSTRING_INDEX(contents, '|', 1)," \
                    "                             '(^\\\\S|\\\\s)(?:\\\\S|\\\\s)*(\\\\(contact_name:string_num\\\\))', '\\\\1*\\\\2')," \
                    "              REGEXP_REPLACE(SUBSTRING_INDEX(SUBSTRING_INDEX(contents, '|', 2), '|', -1)," \
                    "                             '(^\\\\S|\\\\s)(?:\\\\S|\\\\s)*(\\\\(contact_name:string\\\\))', '\\\\1*\\\\2')," \
                    "              REGEXP_REPLACE(SUBSTRING_INDEX(SUBSTRING_INDEX(contents, '|', 3), '|', -1)," \
                    "                             '(^\\\\S|\\\\s)(?:\\\\S|\\\\s)*(\\\\(contact_name:string_num_mixed\\\\))', '\\\\1*\\\\2')" \
                    "        )," \
                    "    CONCAT_WS('|'," \
                    "              SUBSTRING_INDEX(contents, '|', 1)," \
                    "              REGEXP_REPLACE(SUBSTRING_INDEX(SUBSTRING_INDEX(contents, '|', 2), '|', -1)," \
                    "                             '(^\\\\S|\\\\s)(?:\\\\S|\\\\s)*(\\\\(name:string\\\\))', '\\\\1*\\\\2')," \
                    "              REGEXP_REPLACE(SUBSTRING_INDEX(SUBSTRING_INDEX(contents, '|', 3), '|', -1)," \
                    "                             '(^(?:\\\\S|\\\\s){2})(?:\\\\S|\\\\s)*(\\\\(m_subject:string_num\\\\))', '\\\\1*\\\\2')," \
                    "              REGEXP_REPLACE(SUBSTRING_INDEX(SUBSTRING_INDEX(contents, '|', 4), '|', -1)," \
                    "                             '(^(?:\\\\S|\\\\s){2})(?:\\\\S|\\\\s)*(\\\\(m_subject:string\\\\))', '\\\\1*\\\\2')," \
                    "              REGEXP_REPLACE(SUBSTRING_INDEX(SUBSTRING_INDEX(contents, '|', 5), '|', -1)," \
                    "                             '(^(?:\\\\S|\\\\s){2})(?:\\\\S|\\\\s)*(\\\\(m_subject:string_num_mixed\\\\))', '\\\\1*\\\\2')," \
                    "              REGEXP_REPLACE(SUBSTRING_INDEX(SUBSTRING_INDEX(contents, '|', 6), '|', -1)," \
                    "                             '(^(?:\\\\S|\\\\s){3})(?:\\\\S|\\\\s)*(\\\\(m_content:string_num_mixed\\\\))', '\\\\1*\\\\2')," \
                    "              REGEXP_REPLACE(SUBSTRING_INDEX(SUBSTRING_INDEX(contents, '|', 7), '|', -1)," \
                    "                             '(^(?:\\\\S|\\\\s){3})(?:\\\\S|\\\\s)*(\\\\(m_content:string_num\\\\))', '\\\\1*\\\\2')," \
                    "              REGEXP_REPLACE(SUBSTRING_INDEX(SUBSTRING_INDEX(contents, '|', 8), '|', -1)," \
                    "                             '(^(?:\\\\S|\\\\s){3})(?:\\\\S|\\\\s)*(\\\\(m_content:string\\\\))', '\\\\1*\\\\2')," \
                    "              REGEXP_REPLACE(SUBSTRING_INDEX(SUBSTRING_INDEX(contents, '|', 9), '|', -1)," \
                    "                             '(^\\\\S|\\\\s)(?:\\\\S|\\\\s)*(\\\\(cnap_name:string_num_mixed\\\\))', '\\\\1*\\\\2')," \
                    "              REGEXP_REPLACE(SUBSTRING_INDEX(SUBSTRING_INDEX(contents, '|', 10), '|', -1)," \
                    "                             '(^\\\\S|\\\\s)(?:\\\\S|\\\\s)*(\\\\(cnap_name:string\\\\))', '\\\\1*\\\\2')" \
                    "        )" \
                    ")"
            configuration.cursor.execute_query(query)


manager.ModulesManager.RegisterModule(AndForensicsConnector)


def _convert_timestamp(timestamp):
    if timestamp is None:
        return 'N/A'

    if isinstance(timestamp, tuple):
        to_timestamp = []
        for t in timestamp:
            to_timestamp.append(datetime.fromtimestamp(t).strftime('%Y-%m-%dT%H:%M:%SZ'))
        return tuple(to_timestamp)
    else:
        return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%dT%H:%M:%SZ')
