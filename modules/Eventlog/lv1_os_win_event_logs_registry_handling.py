# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import os, sys, re
from datetime import datetime

from utility import database

class Registry_Handling_Information:
    par_id = ''
    case_id = ''
    evd_id = ''
    task = ''
    time = ''
    registry_path = ''
    registry_value_name = ''
    old_value = ''
    new_value = ''
    user_sid = ''
    event_id = ''
    source = ''
    event_id_description = ''

def EVENTLOGREGISTRYHANDLING(configuration):

    #db = database.Database()
    #db.open()

    registry_list = []
    registry_count = 0
    query = f"SELECT data, event_id, time_created, source, user_sid FROM lv1_os_win_evt_total WHERE (evd_id='{configuration.evidence_id}') and (event_id like '4657' and source like '%Security.evtx%')"
    #result_query = db.execute_query_mul(query)
    result_query = configuration.cursor.execute_query_mul(query)
    for result_data in result_query:
        registry_handling_information = Registry_Handling_Information()
        try:
            if result_data[1] == '4657':
                registry_list.append(registry_handling_information)
                registry_list[registry_count].task = 'Modified'
                registry_list[registry_count].event_id = result_data[1]
                registry_list[registry_count].time = result_data[2]
                registry_list[registry_count].source = result_data[3]
                registry_list[registry_count].user_sid = result_data[4]
                registry_list[registry_count].event_id_description = 'A registry value was modified'
                if 'SubjectUserName' in result_data[0]:
                    dataInside = r"SubjectUserName\">(.*)<"
                    m = re.search(dataInside, result_data[0])
                    registry_list[registry_count].user = m.group(1)
                if 'ObjectName' in result_data[0]:
                    dataInside = r"ObjectName\">(.*)<"
                    m = re.search(dataInside, result_data[0])
                    registry_list[registry_count].registry_path = m.group(1)
                if 'ObjectValueName' in result_data[0]:
                    dataInside = r"ObjectValueName\">(.*)<"
                    m = re.search(dataInside, result_data[0])
                    registry_list[registry_count].registry_value_name = m.group(1)
                if r"OldValue\" " in result_data[0]:
                    registry_list[registry_count].old_value = ' '
                if r"OldValue\">" in result_data[0]:
                    dataInside = r"OldValue\">(.*)<"
                    m = re.search(dataInside, result_data[0])
                    registry_list[registry_count].old_value = m.group(1)
                    registry_list[registry_count].registry_value_name = m.group(1)
                if r"NewValue\" " in result_data[0]:
                    registry_list[registry_count].new_value = ' '
                if 'NewValue' in result_data[0]:
                    dataInside = r"NewValue\">(.*)<"
                    m = re.search(dataInside, result_data[0])
                    registry_list[registry_count].new_value = m.group(1)
                registry_count = registry_count + 1
        except:
            print("EVENT LOG REGISTRY HANDLING ERROR")

    #db.close()

    return registry_list
