# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import os, sys, re
from datetime import datetime

from utility import database

class File_Handling_Information:
    par_id = ''
    case_id = ''
    evd_id = ''
    task = ''
    time = ''
    file_name = ''
    user_sid = ''
    event_id = ''
    source = ''
    event_id_description = ''

def EVENTLOGFILEHANDLING(configuration):

    #db = database.Database()
    #db.open()

    file_handling_list = []
    file_handling_count = 0
    query = f"SELECT data, event_id, time_created, source, user_sid FROM lv1_os_win_evt_total WHERE (evd_id='{configuration.evidence_id}') and (event_id like '4663' and source like '%Security.evtx%')"
    #result_query = db.execute_query_mul(query)
    result_query = configuration.cursor.execute_query_mul(query)
    for result_data in result_query:
        file_handling_information = File_Handling_Information()
        try:
            if result_data[1] == '4663':
                if '%%1537' in result_data[0]:
                    file_handling_list.append(file_handling_information)
                    file_handling_list[file_handling_count].task = 'Deleted'
                    file_handling_list[file_handling_count].event_id = result_data[1]
                    file_handling_list[file_handling_count].time = result_data[2]
                    file_handling_list[file_handling_count].source = result_data[3]
                    file_handling_list[file_handling_count].user_sid = result_data[4]
                    file_handling_list[file_handling_count].event_id_description = 'An attempt was made to access an object'
                    if 'SubjectUserName' in result_data[0]:
                        dataInside = r"SubjectUserName\">(.*)<"
                        m = re.search(dataInside, result_data[0])
                        file_handling_list[file_handling_count].user = m.group(1)
                    if 'ObjectName' in result_data[0]:
                        dataInside = r"ObjectName\">(.*)<"
                        m = re.search(dataInside, result_data[0])
                        file_handling_list[file_handling_count].file_name = m.group(1)
                    file_handling_count = file_handling_count + 1
                elif '%%4417 %%4418' in result_data[0]:
                    file_handling_list.append(file_handling_information)
                    file_handling_list[file_handling_count].task = 'Modified'
                    file_handling_list[file_handling_count].event_id = result_data[1]
                    file_handling_list[file_handling_count].time = result_data[2]
                    file_handling_list[file_handling_count].source = result_data[3]
                    file_handling_list[file_handling_count].user_sid = result_data[4]
                    file_handling_list[
                        file_handling_count].event_id_description = 'An attempt was made to access an object'
                    if 'SubjectUserName' in result_data[0]:
                        dataInside = r"SubjectUserName\">(.*)<"
                        m = re.search(dataInside, result_data[0])
                        file_handling_list[file_handling_count].user = m.group(1)
                    if 'ObjectName' in result_data[0]:
                        dataInside = r"ObjectName\">(.*)<"
                        m = re.search(dataInside, result_data[0])
                        file_handling_list[file_handling_count].file_name = m.group(1)
                    file_handling_count = file_handling_count + 1
        except:
            print("EVENT LOG FILE HANDLING ERROR")

    #db.close()

    return file_handling_list
