# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import os, sys, re
from datetime import datetime

from utility import database

class MS_Alerts_Information:
    par_id = ''
    case_id = ''
    evd_id = ''
    task = ''
    time = ''
    program_name = ''
    message = ''
    error_type = ''
    program_version = ''
    user_sid = ''
    event_id = ''
    source = ''
    event_id_description = ''

def EVENTLOGMSALERTS(configuration):
    #db = database.Database()
    #db.open()

    ms_alerts_list = []
    ms_alerts_count = 0
    query = r"SELECT data, event_id, time_created, source, user_sid FROM lv1_os_win_evt_total where event_id like '300' and source like '%OAlerts.evtx%'"
    #result_query = db.execute_query_mul(query)
    result_query = configuration.cursor.execute_query_mul(query)
    for result_data in result_query:
        ms_alerts_information = MS_Alerts_Information()
        try:
            ms_alerts_list.append(ms_alerts_information)
            ms_alerts_list[ms_alerts_count].event_id = result_data[1]
            ms_alerts_list[ms_alerts_count].time = result_data[2]
            ms_alerts_list[ms_alerts_count].source = result_data[3]
            ms_alerts_list[ms_alerts_count].user_sid = result_data[4]
            ms_alerts_list[ms_alerts_count].task = 'Alert'
            ms_alerts_list[ms_alerts_count].event_id_description = 'MS office program usage alert'
            try:
                ms_alerts_list[ms_alerts_count].program_name = result_data[0].split('<Data>')[1].replace('<string>', '').split('</string>')[0]
                ms_alerts_list[ms_alerts_count].message = result_data[0].split('<Data>')[1].replace('<string>', '').split('</string>')[1]
                ms_alerts_list[ms_alerts_count].error_type = result_data[0].split('<Data>')[1].replace('<string>', '').split('</string>')[2]
                ms_alerts_list[ms_alerts_count].program_version = result_data[0].split('<Data>')[1].replace('<string>', '').split('</string>')[3]
            except:
                print("Eventlog_ms_alerts_parsing_error")
            ms_alerts_count = ms_alerts_count + 1
        except:
            print("EVENT LOG MS ALERTS ERROR")

    #db.close()

    return ms_alerts_list
