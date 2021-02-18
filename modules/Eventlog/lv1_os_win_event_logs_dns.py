# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import os, sys, re
from datetime import datetime

from utility import database

class DNS_Information:
    par_id = ''
    case_id = ''
    evd_id = ''
    task = ''
    time = ''
    query_name = ''
    user_sid = ''
    event_id = ''
    source = ''
    event_id_description = ''

def EVENTLOGDNS(configuration):

    #db = database.Database()
    #db.open()

    dns_list = []
    dns_count = 0
    query = f"SELECT data, event_id, time_created, source, user_sid FROM lv1_os_win_evt_total WHERE (evd_id='{configuration.evidence_id}') and (event_id like '1001' or event_id like '3006' or event_id like '3008' or event_id like '3010' or event_id like '3019' or event_id like '3020') and source like '%DNS%'"
    #result_query = db.execute_query_mul(query)
    result_query = configuration.cursor.execute_query_mul(query)
    for result_data in result_query:
        dns_information = DNS_Information()
        try:
            if result_data[1] == '1001':
                dns_list.append(dns_information)
                dns_list[dns_count].event_id = result_data[1]
                dns_list[dns_count].time = result_data[2]
                dns_list[dns_count].source = result_data[3]
                dns_list[dns_count].user_sid = result_data[4]
                dns_list[dns_count].task = 'Interface'
                dns_count = dns_count + 1
                dns_list[dns_count].event_id_description = 'Interface, total DNS'
            elif result_data[1] == '3006':
                dns_list.append(dns_information)
                dns_list[dns_count].event_id = result_data[1]
                dns_list[dns_count].time = result_data[2]
                dns_list[dns_count].source = result_data[3]
                dns_list[dns_count].user_sid = result_data[4]
                dns_list[dns_count].task = 'Called'
                dns_list[dns_count].event_id_description = 'DNS query is called'
                dns_count = dns_count + 1
            elif result_data[1] == '3008':
                dns_list.append(dns_information)
                dns_list[dns_count].event_id = result_data[1]
                dns_list[dns_count].time = result_data[2]
                dns_list[dns_count].source = result_data[3]
                dns_list[dns_count].user_sid = result_data[4]
                dns_list[dns_count].task = 'Completed'
                dns_list[dns_count].event_id_description = 'DNS query is completed'
                dns_count = dns_count + 1
            elif result_data[1] == '3010':
                dns_list.append(dns_information)
                dns_list[dns_count].event_id = result_data[1]
                dns_list[dns_count].time = result_data[2]
                dns_list[dns_count].source = result_data[3]
                dns_list[dns_count].user_sid = result_data[4]
                dns_list[dns_count].task = 'Sent'
                dns_list[dns_count].event_id_description = 'DNS query sent to DNS Server'
                dns_count = dns_count + 1
            elif result_data[1] == '3019':
                dns_list.append(dns_information)
                dns_list[dns_count].event_id = result_data[1]
                dns_list[dns_count].time = result_data[2]
                dns_list[dns_count].source = result_data[3]
                dns_list[dns_count].user_sid = result_data[4]
                dns_list[dns_count].task = 'Called'
                dns_list[dns_count].event_id_description = 'DNS wire called'
                dns_count = dns_count + 1
            elif result_data[1] == '3020':
                dns_list.append(dns_information)
                dns_list[dns_count].event_id = result_data[1]
                dns_list[dns_count].time = result_data[2]
                dns_list[dns_count].source = result_data[3]
                dns_list[dns_count].user_sid = result_data[4]
                dns_list[dns_count].task = 'Response'
                dns_list[dns_count].event_id_description = 'DNS response'
                dns_count = dns_count + 1
        except:
            print("EVENT LOG DNS ERROR")

    #db.close()

    return dns_list

