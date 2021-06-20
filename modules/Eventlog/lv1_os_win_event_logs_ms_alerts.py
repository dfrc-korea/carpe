# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import os, sys, re
from datetime import datetime

from utility import database
from modules import logger
from xml.etree import ElementTree

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
    query = f"SELECT data, event_id, time_created, source, user_sid FROM lv1_os_win_evt_total WHERE (evd_id='{configuration.evidence_id}') and (event_id like '300' and source like '%OAlerts.evtx%')"
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
                root = ElementTree.fromstring(result_data[0])
                results = root.iter('{http://schemas.microsoft.com/win/2004/08/events/event}Data')
                data = []
                message = ''
                for result in results:
                    for txt in result.iter('{http://schemas.microsoft.com/win/2004/08/events/event}string'):
                        if txt.text != '\n':
                            data.append(txt.text)
                ms_alerts_list[ms_alerts_count].program_name = data[0]
                for i in range(1, len(data)-2):
                     message += data[i]
                ms_alerts_list[ms_alerts_count].message = message
                ms_alerts_list[ms_alerts_count].error_type = data[len(data)-2]
                ms_alerts_list[ms_alerts_count].program_version = data[len(data)-1]
            except Exception as exception:
                logger.error('EVENTLOGS MS Alerts Parsing Error: {0!s}'.format(exception))
            ms_alerts_count = ms_alerts_count + 1
        except Exception as exception:
            logger.error('EVENTLOGS MS Alerts Error: {0!s}'.format(exception))

    #db.close()

    return ms_alerts_list
