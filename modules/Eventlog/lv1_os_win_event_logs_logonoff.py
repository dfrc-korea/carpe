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

def EVENTLOGONOFF(configuration):

    #db = database.Database()
    #db.open()

    event_list = []
    event_count = 0
    query = f"SELECT data, event_id, time_created, source, user_sid FROM lv1_os_win_evt_total WHERE (evd_id='{configuration.evidence_id}') and ((event_id like '4624' and source like '%Security%' and data like '%S-1-5-21%') or (event_id like '4634' and source like '%Security%') or (event_id like '4625' and source like '%Security%') or (event_id like '4648' and source like '%Security%') or (event_id like '7002' and source like '%Security%') or (event_id like '1' and source like '%User Profile Service%') or (event_id like '2' and source like '%User Profile Service%') or (event_id like '3' and source like '%User Profile Service%') or (event_id like '4' and source like '%User Profile Service%'))"
    #result_query = db.execute_query_mul(query)
    result_query = configuration.cursor.execute_query_mul(query)
    for result_data in result_query:
        eventlog_information = Eventlog_Information()
        try:
            if result_data[1] == '4624' or result_data[1] == '4648':
                event_list.append(eventlog_information)
                event_list[event_count].task = 'LogOn - Success'
                event_list[event_count].event_id = result_data[1]
                event_list[event_count].time = result_data[2]
                event_list[event_count].source = result_data[3]
                event_list[event_count].user_sid = result_data[4]
                if result_data[1] == '4624':
                    event_list[event_count].event_id_description = 'Log on Successfully'
                elif result_data[1] == '4648':
                    event_list[event_count].event_id_description = 'A logon was attempted using explicit credentials'
                dataInside = r"TargetUserName\">(.*)<"
                m = re.search(dataInside, result_data[0])
                event_list[event_count].user = m.group(1)
                event_count = event_count + 1
            elif result_data[1] == '1' or result_data[1] == '2':
                event_list.append(eventlog_information)
                event_list[event_count].task = 'LogOn - Success'
                event_list[event_count].event_id = result_data[1]
                event_list[event_count].time = result_data[2]
                event_list[event_count].source = result_data[3]
                event_list[event_count].user_sid = result_data[4]
                if result_data[1] == '1':
                    event_list[event_count].event_id_description = 'Received user logon notification'
                elif result_data[1] == '2':
                    event_list[event_count].event_id_description = 'Finished processing user logon notification'
                event_count = event_count + 1
            elif result_data[1] == '4634' or result_data[1] == '7002':
                event_list.append(eventlog_information)
                event_list[event_count].task = 'LogOff'
                event_list[event_count].event_id = result_data[1]
                event_list[event_count].time = result_data[2]
                event_list[event_count].source = result_data[3]
                event_list[event_count].user_sid = result_data[4]
                if result_data[1] == '4634':
                    event_list[event_count].event_id_description = 'Log off Successfully'
                elif result_data[1] == '7002':
                    event_list[event_count].event_id_description = 'User logoff notification for customer experience improvement program'
                dataInside = r"TargetUserName\">(.*)<"
                m = re.search(dataInside, result_data[0])
                event_list[event_count].user = m.group(1)
                event_count = event_count + 1
            elif result_data[1] == '3' or result_data[1] == '4':
                event_list.append(eventlog_information)
                event_list[event_count].task = 'LogOff'
                event_list[event_count].event_id = result_data[1]
                event_list[event_count].time = result_data[2]
                event_list[event_count].source = result_data[3]
                event_list[event_count].user_sid = result_data[4]
                if result_data[1] == '3':
                    event_list[event_count].event_id_description = 'Receviced user logoff notification'
                elif result_data[1] == '4':
                    event_list[event_count].event_id_description = 'Finished processing user logoff notification'
                event_count = event_count + 1
            elif result_data[1] == '4625':
                event_list.append(eventlog_information)
                event_list[event_count].task = 'LogOn - Failed'
                event_list[event_count].event_id = result_data[1]
                event_list[event_count].time = result_data[2]
                event_list[event_count].source = result_data[3]
                event_list[event_count].user_sid = result_data[4]
                event_list[event_count].event_id_description = 'Log on failed'
                dataInside = r"TargetUserName\">(.*)<"
                m = re.search(dataInside, result_data[0])
                event_list[event_count].user = m.group(1)
                event_count = event_count + 1
        except:
            print("EVENT LOG LOG ON OFF ERROR")

    #db.close()

    return event_list

