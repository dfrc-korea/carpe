# -*- coding: utf-8 -*-
"""module for LV2COMMUNICATIONAnalyzer."""
import os
from advanced_modules import manager
from advanced_modules import interface
from advanced_modules import logger
from datetime import datetime, timedelta


class LV2COMMUNICATIONAnalyzer(interface.AdvancedModuleAnalyzer):

    NAME = 'lv2_communication_analyzer'
    DESCRIPTION = 'Module for LV2 Communication Analyzer'

    _plugin_classes = {}

    def __init__(self):
        super(LV2COMMUNICATIONAnalyzer, self).__init__()

    def Analyze(self, par_id, configuration, source_path_spec, knowledge_base):

        this_file_path = os.path.dirname(os.path.abspath(__file__)) + os.sep + 'schema' + os.sep

        # 모든 yaml 파일 리스트
        yaml_list = [this_file_path + 'lv2_communication.yaml']

        # 모든 테이블 리스트
        table_list = ['lv2_communication']

        if not self.check_table_from_yaml(configuration, yaml_list, table_list):
            return False

        #KAKAOTALK
        print('[MODULE] LV2 Communication Analyzer - KAKAOTALK')

        # par_id 넣어줘야함. 임시로 where par_id는 뻇음
        query = f"SELECT friends.name, friends.phone_number, chatlogs.message, chatlogs.created_at, chatrooms.private_meta, chatrooms.members " \
                f"FROM lv1_app_kakaotalk_mobile_chatlogs as chatlogs, lv1_app_kakaotalk_mobile_friends as friends, " \
                f"lv1_app_kakaotalk_mobile_chatrooms as chatrooms where chatlogs.user_id = friends.id and chatlogs.chat_id = chatrooms.id and par_id='{par_id}';"
        results = configuration.cursor.execute_query_mul(query)
        if results == -1 or len(results) == 0:
            pass
        else:
            insert_data = []
            for result in results:
                if result[1] == '':
                    if result[4] is None:
                        #insert_data.append(tuple([par_id, configuration.case_id, configuration.evidence_id, 'KAKAOTALK', 'Outgoing', result[0][1:2], result[1], result[2][2:5], datetime.fromtimestamp(int(result[3])).isoformat()+'Z', result[4], result[5]]))
                        insert_data.append(tuple(
                            [par_id, configuration.case_id, configuration.evidence_id, 'KAKAOTALK', 'Outgoing',
                             result[0], result[1], result[2][2:5],
                             datetime.fromtimestamp(int(result[3])).isoformat() + 'Z', result[4], result[5]]))
                    else:
                        #insert_data.append(tuple([par_id, configuration.case_id, configuration.evidence_id, 'KAKAOTALK', 'Outgoing', result[0][1:2], result[1][4:6], result[2][2:5], datetime.fromtimestamp(int(result[3])).isoformat() + 'Z', result[4].replace('우리서', ''), result[5]]))
                        insert_data.append(tuple(
                            [par_id, configuration.case_id, configuration.evidence_id, 'KAKAOTALK', 'Outgoing',
                             result[0], result[1], result[2][2:5],
                             datetime.fromtimestamp(int(result[3])).isoformat() + 'Z', result[4], result[5]]))
                else:
                    if result[4] is None:
                        #insert_data.append(tuple([par_id, configuration.case_id, configuration.evidence_id, 'KAKAOTALK', 'Incoming', result[0][1:2], result[1][4:6], result[2][2:5], datetime.fromtimestamp(int(result[3])).isoformat()+'Z', result[4], result[5]]))
                        insert_data.append(tuple(
                            [par_id, configuration.case_id, configuration.evidence_id, 'KAKAOTALK', 'Incoming',
                             result[0], result[1], result[2][2:5],
                             datetime.fromtimestamp(int(result[3])).isoformat() + 'Z', result[4], result[5]]))
                    else:
                        #insert_data.append(tuple([par_id, configuration.case_id, configuration.evidence_id, 'KAKAOTALK', 'Incoming', result[0][1:2], result[1][4:6], result[2][2:5], datetime.fromtimestamp(int(result[3])).isoformat() + 'Z', result[4].replace('우리서', ''), result[5]]))
                        insert_data.append(tuple(
                            [par_id, configuration.case_id, configuration.evidence_id, 'KAKAOTALK', 'Incoming',
                             result[0], result[1], result[2][2:5],
                             datetime.fromtimestamp(int(result[3])).isoformat() + 'Z', result[4], result[5]]))
            query = "Insert into lv2_communication values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"
            configuration.cursor.bulk_execute(query, insert_data)


        #MESSAGES
        print('[MODULE] LV2 Communication Analyzer - SMS')
        query = f"SELECT sms.type, sms.address, sms.body, sms.date FROM lv1_os_and_basic_app_sms as sms " \
                f"WHERE par_id='{par_id}';"
        results = configuration.cursor.execute_query_mul(query)
        if results == -1 or len(results) == 0:
            pass
        else:
            insert_data = []
            for result in results:
                if result[0] == 'sent':
                    #insert_data.append(tuple([par_id, configuration.case_id, configuration.evidence_id, 'SMS', 'Outgoing', 'NULL', result[1], result[2], result[3], 'NULL', 'NULL']))
                    insert_data.append(tuple([par_id, configuration.case_id, configuration.evidence_id, 'SMS', 'Outgoing', 'NULL', result[1][4:6], result[2][2:5], result[3], 'NULL', 'NULL']))
                else:
                    #insert_data.append(tuple([par_id, configuration.case_id, configuration.evidence_id, 'SMS', 'Incoming', 'NULL', result[1], result[2], result[3], 'NULL', 'NULL']))
                    insert_data.append(tuple([par_id, configuration.case_id, configuration.evidence_id, 'SMS', 'Incoming', 'NULL', result[1][4:6], result[2][2:5], result[3], 'NULL', 'NULL']))
            query = "Insert into lv2_communication values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"
            configuration.cursor.bulk_execute(query, insert_data)

        print('[MODULE] LV2 Communication Analyzer - MMS')
        query = f"SELECT `from`, `to`, body, `date` FROM lv1_os_and_basic_app_mms " \
                f"WHERE par_id='{par_id}';"
        results = configuration.cursor.execute_query_mul(query)
        if results == -1 or len(results) == 0:
            pass
        else:
            insert_data = []
            for result in results:
                if result[0] == 'insert-address-token':
                    if result[2] != None:
                        #insert_data.append(tuple([par_id, configuration.case_id, configuration.evidence_id, 'MMS', 'Outgoing', 'NULL', result[1], result[2], result[3], 'NULL', 'NULL']))
                        insert_data.append(tuple([par_id, configuration.case_id, configuration.evidence_id, 'MMS', 'Outgoing', 'NULL', result[1][4:6], result[2][2:5], result[3], 'NULL', 'NULL']))
                    else:
                        insert_data.append(tuple([par_id, configuration.case_id, configuration.evidence_id, 'MMS', 'Outgoing', 'NULL', result[1][4:6], result[2], result[3], 'NULL', 'NULL']))
                else:
                    if result[2] != None:
                        #insert_data.append(tuple([par_id, configuration.case_id, configuration.evidence_id, 'MMS', 'Incoming', 'NULL', result[0], result[2], result[3], 'NULL', 'NULL']))
                        insert_data.append(tuple([par_id, configuration.case_id, configuration.evidence_id, 'MMS', 'Incoming', 'NULL', result[0][4:6], result[2][2:5], result[3], 'NULL', 'NULL']))
                    else:
                        insert_data.append(tuple([par_id, configuration.case_id, configuration.evidence_id, 'MMS', 'Incoming', 'NULL', result[0][4:6], result[2], result[3], 'NULL', 'NULL']))
            query = "Insert into lv2_communication values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"
            configuration.cursor.bulk_execute(query, insert_data)

        print('[MODULE] LV2 Communication Analyzer - CALLS')
        query = f"SELECT call_l.type, call_l.partner, call_l.duration_in_secs, call_l.call_date " \
                f"FROM lv1_os_and_basic_app_call_logs as call_l WHERE par_id='{par_id}'"
        results = configuration.cursor.execute_query_mul(query)
        if results == -1 or len(results) == 0:
            pass
        else:
            insert_data = []
            for result in results:
                #insert_data.append(tuple([par_id, configuration.case_id, configuration.evidence_id, 'CALLS', result[0], 'NULL', result[1], 'Duration : '+result[2]+' seconds', result[3], 'NULL', 'NULL']))
                insert_data.append(tuple(
                    [par_id, configuration.case_id, configuration.evidence_id, 'CALLS', result[0], 'NULL',
                     result[1][4:6], 'Duration : ' + result[2] + ' seconds', result[3], 'NULL', 'NULL']))
            query = "Insert into lv2_communication values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"
            configuration.cursor.bulk_execute(query, insert_data)


manager.AdvancedModulesManager.RegisterModule(LV2COMMUNICATIONAnalyzer)
