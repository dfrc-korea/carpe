# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import os, sys, re
from datetime import datetime

from utility import database

class Sleep_Information:
    par_id = ''
    case_id = ''
    evd_id = ''
    task = ''
    time_sleep = ''
    time_wake = ''
    user_sid = ''
    event_id = ''
    source = ''
    event_id_description = ''

def EVENTLOGSLEEPONOFF(configuration, knowledge_base):

    #db = database.Database()
    #db.open()

    sleep_list = []
    sleep_count = 0
    query = f"SELECT data, event_id, time_created, source, user_sid FROM lv1_os_win_evt_total WHERE (evd_id='{configuration.evidence_id}') and (source like '%System%') and (event_id like '107' or event_id like '42' or event_id like '1')"
    #result_query = db.execute_query_mul(query)
    result_query = configuration.cursor.execute_query_mul(query)
    for result_data in result_query:
        sleep_information = Sleep_Information()
        try:
            if 'Kernel-Power' in result_data[0] or 'Power-Troubleshooter' in result_data[0]:
                if result_data[1] == '42':
                    sleep_list.append(sleep_information)
                    sleep_list[sleep_count].task = 'Sleep Start'
                    sleep_list[sleep_count].event_id_description = 'The system is entering sleep'
                    sleep_list[sleep_count].event_id = result_data[1]
                    sleep_list[sleep_count].time_sleep = result_data[2]
                    sleep_list[sleep_count].source = result_data[3]
                    sleep_list[sleep_count].user_sid = result_data[4]
                    sleep_count = sleep_count + 1
                elif result_data[1] == '107':
                    sleep_list.append(sleep_information)
                    sleep_list[sleep_count].task = 'Sleep End'
                    sleep_list[sleep_count].event_id_description = 'The system has resumed from sleep'
                    sleep_list[sleep_count].event_id = result_data[1]
                    sleep_list[sleep_count].time_wake = result_data[2]
                    sleep_list[sleep_count].source = result_data[3]
                    sleep_list[sleep_count].user_sid = result_data[4]
                    sleep_count = sleep_count + 1
                elif result_data[1] == '1':
                    sleep_list.append(sleep_information)
                    sleep_list[sleep_count].task = 'Sleep End'
                    sleep_list[sleep_count].event_id_description = 'The system has resumed from sleep'
                    sleep_list[sleep_count].event_id = result_data[1]
                    sleep_list[sleep_count].time_wake = result_data[2]
                    sleep_list[sleep_count].source = result_data[3]
                    sleep_list[sleep_count].user_sid = result_data[4]
                    if 'SleepTime' in result_data[0]:
                        dataInside = r"SleepTime\">(.*)<"
                        m = re.search(dataInside, result_data[0])
                        # evt_total에는 Timezone 처리해주는데 여기선 못해줘서 추가.
                        sleep_list[sleep_count].time_sleep = m.group(1).replace(' ', 'T') + 'Z'
                        sleep_list[sleep_count].time_sleep = configuration.apply_time_zone(str(sleep_list[sleep_count].time_sleep), knowledge_base.time_zone)
                    if 'WakeTime' in result_data[0]:
                        dataInside = r"WakeTime\">(.*)<"
                        m = re.search(dataInside, result_data[0])
                        # evt_total에는 Timezone 처리해주는데 여기선 못해줘서 추가.
                        sleep_list[sleep_count].time_wake = m.group(1).replace(' ', 'T') + 'Z'
                        sleep_list[sleep_count].time_wake = configuration.apply_time_zone(str(sleep_list[sleep_count].time_wake), knowledge_base.time_zone)
                    sleep_count = sleep_count + 1

        except:
            print("EVENT LOG SLEEP ON OFF ERROR")

    #db.close()

    return sleep_list
