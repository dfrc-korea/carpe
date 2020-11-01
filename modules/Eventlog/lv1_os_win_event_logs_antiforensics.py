# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import os, sys, re
from datetime import datetime

from utility import database

class Antiforensics_Information:
    par_id = ''
    case_id = ''
    evd_id = ''
    task = ''
    time = ''
    user_sid = ''
    event_id = ''
    source = ''
    event_id_description = ''

def EVENTLOGANTIFORENSICS(configuration):

    #db = database.Database()
    #db.open()

    antiforensics_list = []
    antiforensics_list_count = 0
    query = f"SELECT data, event_id, time_created, source, user_sid FROM lv1_os_win_evt_total WHERE (evd_id='{configuration.evidence_id}') and (event_id like '1100' or event_id like '1102' or event_id like '104') and (source like '%System%' or source like '%Security%')"
    #result_query = db.execute_query_mul(query)
    result_query = configuration.cursor.execute_query_mul(query)
    for result_data in result_query:
        antiforensics_information = Antiforensics_Information()
        try:
            if result_data[1] == '1100':
                antiforensics_list.append(antiforensics_information)
                antiforensics_list[antiforensics_list_count].task = 'Event Logging Service End'
                antiforensics_list[antiforensics_list_count].event_id = result_data[1]
                antiforensics_list[antiforensics_list_count].time = result_data[2]
                antiforensics_list[antiforensics_list_count].source = result_data[3]
                antiforensics_list[antiforensics_list_count].user_sid = result_data[4]
                antiforensics_list[antiforensics_list_count].event_id_description = 'Event Logging Service End'
                antiforensics_list_count = antiforensics_list_count + 1
            elif result_data[1] == '1102':
                antiforensics_list.append(antiforensics_information)
                antiforensics_list[antiforensics_list_count].task = 'Event Log Deleted'
                antiforensics_list[antiforensics_list_count].event_id = result_data[1]
                antiforensics_list[antiforensics_list_count].time = result_data[2]
                antiforensics_list[antiforensics_list_count].source = result_data[3]
                antiforensics_list[antiforensics_list_count].user_sid = result_data[4]
                antiforensics_list[
                    antiforensics_list_count].event_id_description = 'System log file was cleared'
                antiforensics_list_count = antiforensics_list_count + 1
            elif result_data[1] == '104':
                antiforensics_list.append(antiforensics_information)
                antiforensics_list[antiforensics_list_count].task = 'Event Log Deleted'
                antiforensics_list[antiforensics_list_count].event_id = result_data[1]
                antiforensics_list[antiforensics_list_count].time = result_data[2]
                antiforensics_list[antiforensics_list_count].source = result_data[3]
                antiforensics_list[antiforensics_list_count].user_sid = result_data[4]
                antiforensics_list[
                    antiforensics_list_count].event_id_description = 'Audit log was cleared'
                antiforensics_list_count = antiforensics_list_count + 1
        except:
            print("EVENT LOG ANTIFORENSICS ERROR")

    #db.close()

    return antiforensics_list
