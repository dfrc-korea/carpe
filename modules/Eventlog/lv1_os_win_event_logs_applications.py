# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import os, sys, re
from datetime import datetime

from utility import database

class Applications_Information:
    par_id = ''
    case_id = ''
    evd_id = ''
    task = ''
    time = ''
    application_name = ''
    path = ''
    resolver_name = ''
    user_sid = ''
    event_id = ''
    source = ''
    event_id_description = ''

def EVENTLOGAPPLICATIONS(configuration):

    #db = database.Database()
    #db.open()

    applications_list = []
    applications_count = 0
    query = f"SELECT data, event_id, time_created, source, user_sid FROM lv1_os_win_evt_total WHERE (evd_id='{configuration.evidence_id}') and (event_id like '17' and source like '%Program-Compatibility%')"
    #result_query = db.execute_query_mul(query)
    result_query = configuration.cursor.execute_query_mul(query)
    for result_data in result_query:
        applications_information = Applications_Information()
        try:
            applications_list.append(applications_information)
            if result_data[1] == '17':
                applications_list[applications_count].event_id = result_data[1]
                applications_list[applications_count].time = result_data[2]
                applications_list[applications_count].source = result_data[3]
                applications_list[applications_count].user_sid = result_data[4]
                applications_list[applications_count].task = 'Installed'
                applications_list[
                    applications_count].event_id_description = 'Program installed'
                if 'ExePath' in result_data[0]:
                    dataInside = r"<ExePath>(.*)\\(.*)</ExePath>"
                    m = re.search(dataInside, result_data[0])
                    applications_list[applications_count].path = m.group(1).replace('\\','/')
                    applications_list[applications_count].application_name = m.group(2)
                if 'ResolverName' in result_data[0]:
                    dataInside = r"<ResolverName>(.*)</ResolverName>"
                    m = re.search(dataInside, result_data[0])
                    applications_list[applications_count].resolver_name = m.group(1)
                applications_count = applications_count + 1
        except:
            print("EVENT LOG APPLICATIONS ERROR")

    #db.close()

    return applications_list
