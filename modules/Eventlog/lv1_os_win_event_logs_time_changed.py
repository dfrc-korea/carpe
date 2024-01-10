# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import os, sys, re
from datetime import datetime

from utility import database

class Time_Information:
    par_id = ''
    case_id = ''
    evd_id = ''
    task = ''
    time_old = ''
    time_new = ''
    user_sid = ''
    event_id = ''
    source = ''
    event_id_description = ''

def EVENTLOGTIMECHANGED(configuration):

    #db = database.Database()
    #db.open()

    time_list = []
    time_count = 0
    query = f"SELECT data, event_id, time_created, source, user_sid FROM lv1_os_win_evt_total WHERE (evd_id='{configuration.evidence_id}') and ((event_id like '4616' and source like '%Security%') or (event_id like '1') or (event_id like '20000' and source like '%DateTimeControlPanel%') or (event_id like '20001' and source like '%DateTimeControlPanel%'))"
    #result_query = db.execute_query_mul(query)
    result_query = configuration.cursor.execute_query_mul(query)
    for result_data in result_query:
        time_information = Time_Information()
        try:
            if result_data[1] == '4616':
                time_list.append(time_information)
                if 'PreviousTime' in result_data[0]:
                    dataInside = r"PreviousTime\">(.*)<"
                    m = re.search(dataInside, result_data[0])
                    time_list[time_count].time_old = m.group(1).replace(' ','T')+'Z'
                    time_list[time_count].task = 'Time Chanaged'
                    time_list[time_count].event_id = result_data[1]
                    time_list[time_count].source = result_data[3]
                    time_list[time_count].user_sid = result_data[4]
                    time_list[time_count].event_id_description = 'The system time was changed'
                if 'NewTime' in result_data[0]:
                    dataInside = r"NewTime\">(.*)<"
                    m = re.search(dataInside, result_data[0])
                    time_list[time_count].time_new = m.group(1).replace(' ','T')+'Z'
                    time_list[time_count].task = 'Time Chanaged'
                    time_list[time_count].event_id = result_data[1]
                    time_list[time_count].source = result_data[3]
                    time_list[time_count].user_sid = result_data[4]
                    time_list[time_count].event_id_description = 'The system time was changed'
                time_count = time_count + 1
            elif result_data[1] == '1':
                if 'Kernel-Genral' in result_data[0]:
                    time_list.append(time_information)
                    time_list[time_count].event_id_description = 'The system time has changed'
                    time_list[time_count].event_id = result_data[1]
                    time_list[time_count].source = result_data[3]
                    time_list[time_count].user_sid = result_data[4]
                    time_count = time_count + 1
            elif result_data[1] == '20000':
                time_list.append(time_information)
                time_list[time_count].event_id_description = 'Changed time information'
                time_list[time_count].event_id = result_data[1]
                time_list[time_count].source = result_data[3]
                time_list[time_count].user_sid = result_data[4]
                time_count = time_count + 1
            elif result_data[1] == '20001':
                time_list.append(time_information)
                time_list[time_count].event_id_description = 'Changed time zone information'
                time_list[time_count].event_id = result_data[1]
                time_list[time_count].source = result_data[3]
                time_list[time_count].user_sid = result_data[4]
                time_count = time_count + 1
        except:
            print("EVENT LOG TIME CHANGED ERROR")

    #db.close()

    return time_list
