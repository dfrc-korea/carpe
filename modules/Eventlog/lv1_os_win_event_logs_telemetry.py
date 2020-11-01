# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import os, sys, re
from datetime import datetime

from utility import database

class Telemetry_Information:
    par_id = ''
    case_id = ''
    evd_id = ''
    task = ''
    time = ''
    program_name = ''
    program_path = ''
    user_sid = ''
    event_id = ''
    source = ''
    event_id_description = ''

def EVENTLOGTELEMETRY(configuration):

    #db = database.Database()
    #db.open()

    telemetry_list = []
    telemetry_count = 0
    query = f"SELECT data, event_id, time_created, source, user_sid FROM lv1_os_win_evt_total WHERE (evd_id='{configuration.evidence_id}') and (event_id like '500' or event_id like '505') and source like '%Telemetry%'"
    #result_query = db.execute_query_mul(query)
    result_query = configuration.cursor.execute_query_mul(query)
    for result_data in result_query:
        telemetry_information = Telemetry_Information()
        try:
            telemetry_list.append(telemetry_information)
            telemetry_list[telemetry_count].task = 'Executed'
            telemetry_list[telemetry_count].event_id = result_data[1]
            telemetry_list[telemetry_count].time = result_data[2]
            telemetry_list[telemetry_count].source = result_data[3]
            telemetry_list[telemetry_count].user_sid = result_data[4]
            telemetry_list[telemetry_count].event_id_description = 'Program executed'
            if 'FixName' in result_data[0]:
                dataInside = r"FixName>(.*)<"
                m = re.search(dataInside, result_data[0])
                telemetry_list[telemetry_count].program_name = m.group(1)
            if 'ExePath' in result_data[0]:
                dataInside = r"ExePath>(.*)<"
                m = re.search(dataInside, result_data[0])
                telemetry_list[telemetry_count].program_path = m.group(1).replace('\\','/')
            telemetry_count = telemetry_count + 1
        except:
            print("EVENT LOG TELEMETRY ERROR")

    #db.close()

    return telemetry_list
