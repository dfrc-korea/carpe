# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import os, sys, re
from datetime import datetime

from utility import database

class Eventlog_Information:
    par_id = ''
    case_id = ''
    evd_id = ''
    task = ''
    time = ''
    user_sid = ''
    event_id = ''
    source = ''
    event_id_description = ''

def EVENTLOGPCONOFF(configuration):

    #db = database.Database()
    #db.open()

    event_list = []
    event_count = 0
    # 1074 뺏음. 재시작이라서
    query = f"SELECT data, event_id, time_created, source, user_sid FROM lv1_os_win_evt_total WHERE (evd_id='{configuration.evidence_id}') and (event_id like '6005' or event_id like '6006') and (source like '%System%')"
    #result_query = db.execute_query_mul(query)
    result_query = configuration.cursor.execute_query_mul(query)
    for result_data in result_query:
        eventlog_information = Eventlog_Information()
        try:
            if result_data[1] == '6005' or result_data[1] == '12':
                event_list.append(eventlog_information)
                event_list[event_count].task = 'System On'
                event_list[event_count].event_id = result_data[1]
                event_list[event_count].time = result_data[2]
                event_list[event_count].source = result_data[3]
                event_list[event_count].user_sid = result_data[4]
                if result_data[1] == '6005':
                    event_list[event_count].event_id_description = 'The event log service was started'
                elif result_data[1] == '12':
                    event_list[event_count].event_id_description = 'The operating system started'
                event_count = event_count + 1
            elif result_data[1] == '6006' or result_data[1] == '13':
                event_list.append(eventlog_information)
                event_list[event_count].task = 'System Off'
                event_list[event_count].event_id = result_data[1]
                event_list[event_count].time = result_data[2]
                event_list[event_count].source = result_data[3]
                event_list[event_count].user_sid = result_data[4]
                if result_data[1] == '6006':
                    event_list[event_count].event_id_description = 'The Event log service was stopped.'
                elif result_data[1] == '13':
                    event_list[event_count].event_id_description = 'The operating system is shutting down'
                event_count = event_count + 1
        except:
            print("EVENT LOG PC ON OFF ERROR")

    #db.close()

    return event_list
