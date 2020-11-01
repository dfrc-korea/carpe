# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import os, sys, re
from datetime import datetime

from utility import database

class Process_Information:
    par_id = ''
    case_id = ''
    evd_id = ''
    task = ''
    time = ''
    process_name = ''
    user_sid = ''
    event_id = ''
    source = ''
    event_id_description = ''

def EVENTLOGPROCESS(configuration):

    #db = database.Database()
    #db.open()

    process_list = []
    process_count = 0
    query = f"SELECT data, event_id, time_created, source, user_sid FROM lv1_os_win_evt_total WHERE (evd_id='{configuration.evidence_id}') and (event_id like '4688' or event_id like '4689') and source like '%Security.evtx%'"
    #result_query = db.execute_query_mul(query)
    result_query = configuration.cursor.execute_query_mul(query)
    for result_data in result_query:
        process_information = Process_Information()
        try:
            if result_data[1] == '4688':
                process_list.append(process_information)
                process_list[process_count].task = 'Process creation'
                process_list[process_count].event_id = result_data[1]
                process_list[process_count].time = result_data[2]
                process_list[process_count].source = result_data[3]
                process_list[process_count].user_sid = result_data[4]
                process_list[process_count].event_id_description = 'A new process has been created'
                if 'NewProcessName' in result_data[0]:
                    dataInside = r"NewProcessName\">(.*)<"
                    m = re.search(dataInside, result_data[0])
                    process_list[process_count].process_name = m.group(1).replace('\\','/')
                process_count = process_count + 1
            elif result_data[1] == '4689':
                process_list.append(process_information)
                process_list[process_count].task = 'Process termination'
                process_list[process_count].event_id = result_data[1]
                process_list[process_count].time = result_data[2]
                process_list[process_count].source = result_data[3]
                process_list[process_count].user_sid = result_data[4]
                process_list[process_count].event_id_description = 'A process has exited'
                if 'ProcessName' in result_data[0]:
                    dataInside = r"ProcessName\">(.*)<"
                    m = re.search(dataInside, result_data[0])
                    process_list[process_count].process_name = m.group(1).replace('\\','/')
                process_count = process_count + 1

        except:
            print("EVENT LOG PROCESS ERROR")

    #db.close()

    return process_list
