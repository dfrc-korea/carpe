# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import os, sys, re
from datetime import datetime

from utility import database

class Printer_Information:
    par_id = ''
    case_id = ''
    evd_id = ''
    task = ''
    time = ''
    location = ''
    size = ''
    pages = ''
    user_sid = ''
    event_id = ''
    source = ''
    event_id_description = ''

def EVENTLOGPRINTER(configuration):
    #db = database.Database()
    #db.open()

    printer_list = []
    printer_count = 0
    query = f"SELECT data, event_id, time_created, source, user_sid FROM lv1_os_win_evt_total WHERE (evd_id='{configuration.evidence_id}') and (source like '%PrintService%' and (event_id like '307' or event_id like '801' or event_id like '801' or event_id like '802'))"
    #result_query = db.execute_query_mul(query)
    result_query = configuration.cursor.execute_query_mul(query)
    for result_data in result_query:
        printer_information = Printer_Information()
        try:
            if result_data[1] == '307':
                printer_list.append(printer_information)
                printer_list[printer_count].task = 'Printing'
                printer_list[printer_count].event_id_description = 'Complete document printing'
                printer_list[printer_count].event_id = result_data[1]
                printer_list[printer_count].time = result_data[2]
                printer_list[printer_count].source = result_data[3]
                printer_list[printer_count].user_sid = result_data[4]
                printer_count = printer_count + 1
            elif result_data[1] == '801' or result_data[1] == '842':
                printer_list.append(printer_information)
                printer_list[printer_count].task = 'Printing'
                if result_data[1] == '801':
                    printer_list[printer_count].event_id_description = 'Printing job'
                elif result_data[1] == '842':
                    printer_list[printer_count].event_id_description = 'The print job was sent through the print processor on printer'
                printer_list[printer_count].event_id = result_data[1]
                printer_list[printer_count].time = result_data[2]
                printer_list[printer_count].source = result_data[3]
                printer_list[printer_count].user_sid = result_data[4]
                printer_count = printer_count + 1
            elif result_data[1] == '802':
                printer_list.append(printer_information)
                printer_list[printer_count].task = 'Deleting'
                printer_list[printer_count].event_id_description = 'Deleting job'
                printer_list[printer_count].event_id = result_data[1]
                printer_list[printer_count].time = result_data[2]
                printer_list[printer_count].source = result_data[3]
                printer_list[printer_count].user_sid = result_data[4]
                printer_count = printer_count + 1
        except:
            print("EVENT LOG PRINTER ERROR")

    #db.close()

    return printer_list
