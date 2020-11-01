# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import os, sys, re
from datetime import datetime

from utility import database

class Task_Scheduler_Information:
    par_id = ''
    case_id = ''
    evd_id = ''
    task = ''
    time = ''
    action_name = ''
    user_sid = ''
    event_id = ''
    source = ''
    event_id_description = ''

def EVENTLOGTASKSCHEDULER(configuration):

    #db = database.Database()
    #db.open()

    task_scheduler_list = []
    task_scheduler_count = 0
    query = f"SELECT data, event_id, time_created, source, user_sid FROM lv1_os_win_evt_total WHERE (evd_id='{configuration.evidence_id}') and (event_id like '200' or event_id like '201') and source like '%TaskScheduler%'"
    #result_query = db.execute_query_mul(query)
    result_query = configuration.cursor.execute_query_mul(query)
    for result_data in result_query:
        screen_saver_information = Task_Scheduler_Information()
        try:
            if result_data[1] == '200':
                task_scheduler_list.append(screen_saver_information)
                task_scheduler_list[task_scheduler_count].task = 'Executed'
                task_scheduler_list[task_scheduler_count].event_id = result_data[1]
                task_scheduler_list[task_scheduler_count].time = result_data[2]
                task_scheduler_list[task_scheduler_count].source = result_data[3]
                task_scheduler_list[task_scheduler_count].user_sid = result_data[4]
                task_scheduler_list[task_scheduler_count].event_id_description = 'Action executed'
                dataInside = r"ActionName\">(.*)<"
                m = re.search(dataInside, result_data[0])
                task_scheduler_list[task_scheduler_count].action_name = m.group(1)
                task_scheduler_count = task_scheduler_count + 1
            elif result_data[1] == '201':
                task_scheduler_list.append(screen_saver_information)
                task_scheduler_list[task_scheduler_count].task = 'Completed'
                task_scheduler_list[task_scheduler_count].event_id = result_data[1]
                task_scheduler_list[task_scheduler_count].time = result_data[2]
                task_scheduler_list[task_scheduler_count].source = result_data[3]
                task_scheduler_list[task_scheduler_count].user_sid = result_data[4]
                task_scheduler_list[task_scheduler_count].event_id_description = 'Action completed'
                dataInside = r"ActionName\">(.*)<"
                m = re.search(dataInside, result_data[0])
                task_scheduler_list[task_scheduler_count].action_name = m.group(1)
                task_scheduler_count = task_scheduler_count + 1
        except:
            print("EVENT LOG TASK SCHEDULER ERROR")

    #db.close()

    return task_scheduler_list
