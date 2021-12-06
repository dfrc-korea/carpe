# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import os, sys, re
from datetime import datetime

from utility import database

class Account_Information:
    par_id = ''
    case_id = ''
    evd_id = ''
    time = ''
    event_log_file = ''
    target_name = ''
    subject_name = ''
    user_sid = ''
    event_id = ''
    source = ''
    event_id_description = ''


def EVENTLOGACCOUNTCHANGED(configuration):

    #db = database.Database()
    #db.open()

    account_list = []
    account_count = 0
    query = f"SELECT data, event_id, time_created, source, user_sid FROM lv1_os_win_evt_total " \
            f"WHERE (evd_id='{configuration.evidence_id}') " \
            f"and (event_id = '4720' or event_id = '4723' or event_id = '4726' or event_id = '4738')"
    #result_query = db.execute_query_mul(query)
    result_query = configuration.cursor.execute_query_mul(query)
    for result_data in result_query:
        account_information = Account_Information()
        try:
            if result_data[1] == '4720':
                account_list.append(account_information)
                account_list[account_count].event_id = result_data[1]
                account_list[account_count].event_id_description = 'Create user account'
                account_list[account_count].event_log_file = result_data[3][-13:]
                account_list[account_count].time = result_data[2]
                account_list[account_count].source = result_data[3]
                account_list[account_count].user_sid = result_data[4]
                if 'TargetUserName' in result_data[0]:
                    dataInside = r"TargetUserName\">(.*)<"
                    m = re.search(dataInside, result_data[0])
                    account_list[account_count].target_name = m.group(1)
                if 'SubjectUserName' in result_data[0]:
                    dataInside = r"SubjectUserName\">(.*)<"
                    m = re.search(dataInside, result_data[0])
                    account_list[account_count].subject_name = m.group(1)
                account_count = account_count + 1
            elif result_data[1] == '4723':
                account_list.append(account_information)
                account_list[account_count].event_id = result_data[1]
                account_list[account_count].event_id_description = 'Attempt to change the account password'
                account_list[account_count].event_log_file = result_data[3][-13:]
                account_list[account_count].time = result_data[2]
                account_list[account_count].source = result_data[3]
                account_list[account_count].user_sid = result_data[4]
                if 'TargetUserName' in result_data[0]:
                    dataInside = r"TargetUserName\">(.*)<"
                    m = re.search(dataInside, result_data[0])
                    account_list[account_count].target_name = m.group(1)
                if 'SubjectUserName' in result_data[0]:
                    dataInside = r"SubjectUserName\">(.*)<"
                    m = re.search(dataInside, result_data[0])
                    account_list[account_count].subject_name = m.group(1)
                account_count = account_count + 1
            elif result_data[1] == '4726':
                account_list.append(account_information)
                account_list[account_count].event_id = result_data[1]
                account_list[account_count].event_id_description = 'Delete user account'
                account_list[account_count].event_log_file = result_data[3][-13:]
                account_list[account_count].time = result_data[2]
                account_list[account_count].source = result_data[3]
                account_list[account_count].user_sid = result_data[4]
                if 'TargetUserName' in result_data[0]:
                    dataInside = r"TargetUserName\">(.*)<"
                    m = re.search(dataInside, result_data[0])
                    account_list[account_count].target_name = m.group(1)
                if 'SubjectUserName' in result_data[0]:
                    dataInside = r"SubjectUserName\">(.*)<"
                    m = re.search(dataInside, result_data[0])
                    account_list[account_count].subject_name = m.group(1)
                account_count = account_count + 1
            elif result_data[1] == '4738':
                account_list.append(account_information)
                account_list[account_count].event_id = result_data[1]
                account_list[account_count].event_id_description = 'Change user account'
                account_list[account_count].event_log_file = result_data[3][-13:]
                account_list[account_count].time = result_data[2]
                account_list[account_count].source = result_data[3]
                account_list[account_count].user_sid = result_data[4]
                if 'TargetUserName' in result_data[0]:
                    dataInside = r"TargetUserName\">(.*)<"
                    m = re.search(dataInside, result_data[0])
                    account_list[account_count].target_name = m.group(1)
                if 'SubjectUserName' in result_data[0]:
                    dataInside = r"SubjectUserName\">(.*)<"
                    m = re.search(dataInside, result_data[0])
                    account_list[account_count].subject_name = m.group(1)
                account_count = account_count + 1

        except:
            print("EVENT LOG ACCOUNT CHANGED ERROR")

    #db.close()

    return account_list
