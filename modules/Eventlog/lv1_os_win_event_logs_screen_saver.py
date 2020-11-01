# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import os, sys, re
from datetime import datetime

from utility import database

class Screen_Saver_Information:
    par_id = ''
    case_id = ''
    evd_id = ''
    task = ''
    time = ''
    user_sid = ''
    event_id = ''
    source = ''
    event_id_description = ''

def EVENTLOGSCREENSAVER(configuration):

    #db = database.Database()
    #db.open()

    screen_saver_list = []
    screen_saver_count = 0
    query = f"SELECT data, event_id, time_created, source, user_sid FROM lv1_os_win_evt_total WHERE (evd_id='{configuration.evidence_id}') and (event_id like '4802' and source like '%Security.evtx%')"
    #result_query = db.execute_query_mul(query)
    result_query = configuration.cursor.execute_query_mul(query)
    for result_data in result_query:
        screen_saver_information = Screen_Saver_Information()
        try:
            screen_saver_list.append(screen_saver_information)
            screen_saver_list[screen_saver_count].task = 'Activate'
            screen_saver_list[screen_saver_count].event_id = result_data[1]
            screen_saver_list[screen_saver_count].time = result_data[2]
            screen_saver_list[screen_saver_count].source = result_data[3]
            screen_saver_list[screen_saver_count].user_sid = result_data[4]
            screen_saver_list[screen_saver_count].event_id_description = 'The screen saver was invoked'
            screen_saver_count = screen_saver_count + 1
        except:
            print("EVENT LOG SCREEN SAVER ERROR")

    #db.close()

    return screen_saver_list
