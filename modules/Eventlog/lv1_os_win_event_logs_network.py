# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import os, sys, re
from datetime import datetime

from utility import database

class Network_Information:
    par_id = ''
    case_id = ''
    evd_id = ''
    task = ''
    time = ''
    network_name = ''
    description = ''
    category = ''
    user_sid = ''
    event_id = ''
    source = ''
    event_id_description = ''

def EVENTLOGNETWORK(configuration):
    #db = database.Database()
    #db.open()

    network_list = []
    network_count = 0
    query = f"SELECT data, event_id, time_created, source, user_sid FROM lv1_os_win_evt_total WHERE (evd_id='{configuration.evidence_id}') and (source like '%NetworkProfile%') and (event_id like '10000' or event_id like '10001')"
    #result_query = db.execute_query_mul(query)
    result_query = configuration.cursor.execute_query_mul(query)
    for result_data in result_query:
        network_information = Network_Information()
        try:
            if result_data[1] == '10000' or result_data[1] == '10001':
                network_list.append(network_information)
                network_list[network_count].event_id = result_data[1]
                network_list[network_count].time = result_data[2]
                network_list[network_count].source = result_data[3]
                network_list[network_count].user_sid = result_data[4]
                if 'Name' in result_data[0]:
                    dataInside = r"Name\">(.*)<"
                    m = re.search(dataInside, result_data[0])
                    network_list[network_count].network_name = m.group(1)
                if 'Description' in result_data[0]:
                    dataInside = r"Description\">(.*)<"
                    m = re.search(dataInside, result_data[0])
                    network_list[network_count].description = m.group(1)
                if 'State' in result_data[0]:
                    dataInside = r"State\">(.*)<"
                    m = re.search(dataInside, result_data[0])
                    if m.group(1) == '1':
                        network_list[network_count].task = 'Connected'
                        network_list[network_count].event_id_description = 'Network connected'
                    elif m.group(1) == '2':
                        network_list[network_count].task = 'Disconnected'
                        network_list[network_count].event_id_description = 'Network disconnected'
                    elif m.group(1) == '9':
                        network_list[network_count].task = 'Connected, IPV4 (Internet)'
                        network_list[network_count].event_id_description = 'Network connected'
                    else:
                        network_list[network_count].task = 'N/A'
                        network_list[network_count].event_id_description = 'N/A'
                if 'Category' in result_data[0]:
                    dataInside = r"Category\">(.*)<"
                    m = re.search(dataInside, result_data[0])
                    if m.group(1) == '0':
                        network_list[network_count].category = 'Public'
                    elif m.group(1) == '1':
                        network_list[network_count].category = 'Private'
                    else:
                        network_list[network_count].category = 'N/A'
            network_count = network_count + 1

        except:
            print("EVENT LOG NETWORK RROR")

    #db.close()

    return network_list
