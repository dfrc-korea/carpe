# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import os, sys, re
from datetime import datetime

from utility import database

class Shared_Folder_Information:
    par_id = ''
    case_id = ''
    evd_id = ''
    task = ''
    time = ''
    user_sid = ''
    event_id = ''
    source = ''
    event_id_description = ''

def EVENTLOGSHAREDFOLDER(configuration):

    #db = database.Database()
    #db.open()

    shared_folder_list = []
    shared_folder_count = 0
    query = f"SELECT data, event_id, time_created, source, user_sid FROM lv1_os_win_evt_total WHERE (evd_id='{configuration.evidence_id}') and ((event_id like '4656' and source like '%Security.evtx%') or (event_id like '4663' and source like '%Security.evtx%') or (event_id like '5140' and source like '%Security.evtx%') or (event_id like '30804' and source like '%SMBClient%') or (event_id like '30805' and source like '%SMBClient%') or (event_id like '30806' and source like '%SMBClient%') or (event_id like '30807' and source like '%SMBClient%') or (event_id like '30808' and source like '%SMBClient%'))"
    #result_query = db.execute_query_mul(query)
    result_query = configuration.cursor.execute_query_mul(query)
    for result_data in result_query:
        shared_folder_information = Shared_Folder_Information()
        try:
            shared_folder_list.append(shared_folder_information)
            shared_folder_list[shared_folder_count].event_id = result_data[1]
            shared_folder_list[shared_folder_count].time = result_data[2]
            shared_folder_list[shared_folder_count].source = result_data[3]
            shared_folder_list[shared_folder_count].user_sid = result_data[4]
            shared_folder_list[shared_folder_count].task = 'File Shared'
            if result_data[1] == '4656':
                shared_folder_list[shared_folder_count].event_id_description = 'Request a handle to an object'
            elif result_data[1] == '4663':
                shared_folder_list[
                    shared_folder_count].event_id_description = 'Attempt to access an object'
            elif result_data[1] == '5140':
                shared_folder_list[
                    shared_folder_count].event_id_description = 'A network share object was accessed'
            elif result_data[1] == '30804':
                shared_folder_list[
                    shared_folder_count].event_id_description = 'A network connection was disconnected'
            elif result_data[1] == '30805':
                shared_folder_list[
                    shared_folder_count].event_id_description = 'The client lost its session to the server'
            elif result_data[1] == '30806':
                shared_folder_list[
                    shared_folder_count].event_id_description = 'The client re-established its session to the server'
            elif result_data[1] == '30807':
                shared_folder_list[
                    shared_folder_count].event_id_description = 'The connection to the share was lost'
            elif result_data[1] == '30808':
                shared_folder_list[
                    shared_folder_count].event_id_description = 'The connection to the share was re-established'
            shared_folder_count = shared_folder_count + 1
        except:
            print("EVENT LOG SHARED FOLDER ERROR")

    #db.close()

    return shared_folder_list
