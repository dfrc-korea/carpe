# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import os, sys, re
from datetime import datetime

from utility import database

class Others_Information:
    par_id = ''
    case_id = ''
    evd_id = ''
    task = ''
    time = ''
    name = ''
    user_sid = ''
    event_id = ''
    source = ''
    event_id_description = ''

def EVENTLOGOTHERS(configuration):

    #db = database.Database()
    #db.open()

    others_list = []
    others_count = 0
    query = f"SELECT data, event_id, time_created, source, user_sid FROM lv1_os_win_evt_total WHERE (evd_id='{configuration.evidence_id}') and (source like '%System%') and (event_id like '7000' or event_id like '6' or event_id like '19' or event_id like '7045')"
    #result_query = db.execute_query_mul(query)
    result_query = configuration.cursor.execute_query_mul(query)
    for result_data in result_query:
        others_information = Others_Information()
        try:
            if result_data[1] == '6':
                others_list.append(others_information)
                others_list[others_count].task = 'Driver service registered'
                others_list[others_count].event_id = result_data[1]
                others_list[others_count].time = result_data[2]
                others_list[others_count].source = result_data[3]
                others_list[others_count].user_sid = result_data[4]
                others_list[others_count].event_id_description = 'Driver service successfully loaded and registered'
                if 'DeviceName' in result_data[0]:
                    dataInside = r"DeviceName\">(.*)<"
                    m = re.search(dataInside, result_data[0])
                    others_list[others_count].name = m.group(1)
                others_count = others_count + 1
            elif result_data[1] == '19':
                others_list.append(others_information)
                others_list[others_count].task = 'Windows Update'
                others_list[others_count].event_id = result_data[1]
                others_list[others_count].time = result_data[2]
                others_list[others_count].source = result_data[3]
                others_list[others_count].user_sid = result_data[4]
                others_list[
                    others_count].event_id_description = 'Windows version updated'
                if 'updateTitle' in result_data[0]:
                    dataInside = r"updateTitle\">(.*)<"
                    m = re.search(dataInside, result_data[0])
                    others_list[others_count].name = m.group(1)
                others_count = others_count + 1
            elif result_data[1] == '7000':
                others_list.append(others_information)
                others_list[others_count].task = 'Service Start Failed'
                others_list[others_count].event_id = result_data[1]
                others_list[others_count].time = result_data[2]
                others_list[others_count].source = result_data[3]
                others_list[others_count].user_sid = result_data[4]
                others_list[
                    others_count].event_id_description = 'Service failed with error'
                if 'Param1' in result_data[0]:
                    dataInside = r"Param1\">(.*)<"
                    m = re.search(dataInside, result_data[0])
                    others_list[others_count].name = m.group(1)
                others_count = others_count + 1
            elif result_data[1] == '7045':
                others_list.append(others_information)
                others_list[others_count].task = 'Service Installed'
                others_list[others_count].event_id = result_data[1]
                others_list[others_count].time = result_data[2]
                others_list[others_count].source = result_data[3]
                others_list[others_count].user_sid = result_data[4]
                others_list[
                    others_count].event_id_description = 'A service was installed in the system'
                if 'ServiceName' in result_data[0]:
                    dataInside = r"ServiceName\">(.*)<"
                    m = re.search(dataInside, result_data[0])
                    others_list[others_count].name = m.group(1)
                others_count = others_count + 1
        except:
            print("EVENT LOG OTHERS ON OFF ERROR")

    #db.close()

    return others_list
