# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import os, sys, re
from datetime import datetime

from utility import database

class Remote_Information:
    par_id = ''
    case_id = ''
    evd_id = ''
    task = ''
    time = ''
    connection = ''
    address = ''
    user_sid = ''
    event_id = ''
    source = ''
    event_id_description = ''

def EVENTLOGREMOTEONOFF(configuration):

    #db = database.Database()
    #db.open()

    remote_list = []
    remote_count = 0
    query = f"SELECT data, event_id, time_created, source, user_sid FROM lv1_os_win_evt_total WHERE (evd_id='{configuration.evidence_id}') and ((source like '%TerminalServices-LocalSessionmanager%' and event_id like '24') or (source like '%TerminalServices-LocalSessionmanager%' and event_id like '25') or (source like '%TerminalServices-LocalSessionmanager%' and event_id like '42') or (source like '%TerminalServices-RemoteConnectionManager%' and event_id like '261') or (source like '%TerminalServices-RemoteConnectionManager%' and event_id like '1149') or (source like '%TerminalServices-RemoteConnectionManager%' and event_id like '41') or (source like '%TerminalServices-RDPClient%' and event_id like '1024') or (source like '%TerminalServices-RDPClient%' and event_id like '1102') or (source like '%TerminalServices-RDPClient%' and event_id like '1027') or (source like '%TerminalServices-RDPClient%' and event_id like '1105') or (source like '%TerminalServices-RDPClient%' and event_id like '1026') or (source like '%Security.evtx%' and event_id like '4689'))"
    #result_query = db.execute_query_mul(query)
    result_query = configuration.cursor.execute_query_mul(query)
    for result_data in result_query:
        remote_information = Remote_Information()
        try:
            if result_data[1] == '24':
                remote_list.append(remote_information)
                remote_list[remote_count].connection = 'Guest PC -> Host PC'
                remote_list[remote_count].task = 'Remote Disconnection'
                remote_list[remote_count].event_id_description = 'Session has been disconnected'
                remote_list[remote_count].event_id = result_data[1]
                remote_list[remote_count].time = result_data[2]
                remote_list[remote_count].source = result_data[3]
                remote_list[remote_count].user_sid = result_data[4]
                if '<User>' in result_data[0]:
                    dataInside = r"<User>(.*)\\(.*)<"
                    m = re.search(dataInside, result_data[0])
                    remote_list[remote_count].user = m.group(1)
                if 'Address' in result_data[0]:
                    dataInside = r"Address>(.*)<"
                    m = re.search(dataInside, result_data[0])
                    remote_list[remote_count].address = m.group(1)
                remote_count = remote_count + 1
            elif result_data[1] == '25':
                remote_list.append(remote_information)
                remote_list[remote_count].connection = 'Guest PC -> Host PC'
                remote_list[remote_count].task = 'Remote Reconnection'
                remote_list[remote_count].event_id_description = 'Session reconnection succeeded'
                remote_list[remote_count].event_id = result_data[1]
                remote_list[remote_count].time = result_data[2]
                remote_list[remote_count].source = result_data[3]
                remote_list[remote_count].user_sid = result_data[4]
                if '<User>' in result_data[0]:
                    dataInside = r"<User>(.*)\\(.*)<"
                    m = re.search(dataInside, result_data[0])
                    remote_list[remote_count].user = m.group(1)
                if '<Address>' in result_data[0]:
                    dataInside = r"<Address>(.*)<"
                    m = re.search(dataInside, result_data[0])
                    remote_list[remote_count].address = m.group(1)
                remote_count = remote_count + 1
            elif result_data[1] == '42':
                remote_list.append(remote_information)
                remote_list[remote_count].connection = 'Guest PC -> Host PC'
                remote_list[remote_count].task = 'Remote Disconnection'
                remote_list[remote_count].event_id_description = 'End session arbitration'
                remote_list[remote_count].event_id = result_data[1]
                remote_list[remote_count].time = result_data[2]
                remote_list[remote_count].source = result_data[3]
                remote_list[remote_count].user_sid = result_data[4]
                if '<User>' in result_data[0]:
                    dataInside = r"<User>(.*)\\(.*)<"
                    m = re.search(dataInside, result_data[0])
                    remote_list[remote_count].user = m.group(2)
                if '<Address>' in result_data[0]:
                    dataInside = r"<Address>(.*)<"
                    m = re.search(dataInside, result_data[0])
                    remote_list[remote_count].address = m.group(1)
                remote_count = remote_count + 1
            elif result_data[1] == '261':
                remote_list.append(remote_information)
                remote_list[remote_count].connection = 'Guest PC -> Host PC'
                remote_list[remote_count].task = 'Remote Connection'
                remote_list[remote_count].event_id_description = 'Listener RDP-Tcp received a connection'
                remote_list[remote_count].event_id = result_data[1]
                remote_list[remote_count].time = result_data[2]
                remote_list[remote_count].source = result_data[3]
                remote_list[remote_count].user_sid = result_data[4]
                remote_count = remote_count + 1
            elif result_data[1] == '1149':
                remote_list.append(remote_information)
                remote_list[remote_count].connection = 'Guest PC -> Host PC'
                remote_list[remote_count].task = 'Remote Connection'
                remote_list[remote_count].event_id_description = 'User authentication succeeded'
                remote_list[remote_count].event_id = result_data[1]
                remote_list[remote_count].time = result_data[2]
                remote_list[remote_count].source = result_data[3]
                remote_list[remote_count].user_sid = result_data[4]
                if 'Param1' in result_data[0]:
                    dataInside = r"Param1>(.*)<"
                    m = re.search(dataInside, result_data[0])
                    remote_list[remote_count].user = m.group(1)
                if 'Param3' in result_data[0]:
                    dataInside = r"Param3>(.*)<"
                    m = re.search(dataInside, result_data[0])
                    remote_list[remote_count].address = m.group(1)
                remote_count = remote_count + 1
            elif result_data[1] == '41':
                remote_list.append(remote_information)
                remote_list[remote_count].connection = 'Guest PC -> Host PC'
                remote_list[remote_count].task = 'Remote Connection'
                remote_list[remote_count].event_id_description = 'Start session arbitration'
                remote_list[remote_count].event_id = result_data[1]
                remote_list[remote_count].time = result_data[2]
                remote_list[remote_count].source = result_data[3]
                remote_list[remote_count].user_sid = result_data[4]
                if '<User>' in result_data[0]:
                    dataInside = r"<User>(.*)\\(.*)<"
                    m = re.search(dataInside, result_data[0])
                    remote_list[remote_count].user = m.group(1)
                if '<Address>' in result_data[0]:
                    dataInside = r"<Address>(.*)<"
                    m = re.search(dataInside, result_data[0])
                    remote_list[remote_count].address = m.group(1)
                remote_count = remote_count + 1
            elif result_data[1] == '1024' or result_data[1] == '1102' or result_data[1] == '1027':
                remote_list.append(remote_information)
                remote_list[remote_count].connection = 'Host PC -> Guest PC'
                remote_list[remote_count].task = 'Remote Connection'
                if result_data[1] == '1024':
                    remote_list[remote_count].event_id_description = 'RDP ClientActiveX is trying to connect to the server'
                elif result_data[1] == '1102':
                    remote_list[remote_count].event_id_description = 'The client has initiated a multi-transport connection to the server'
                elif result_data[1] == '1027':
                    remote_list[remote_count].event_id_description = 'Connected to domain'
                remote_list[remote_count].event_id = result_data[1]
                remote_list[remote_count].time = result_data[2]
                remote_list[remote_count].source = result_data[3]
                remote_list[remote_count].user_sid = result_data[4]
                remote_count = remote_count + 1
            elif result_data[1] == '4689' or result_data[1] == '1105' or result_data[1] == '1026':
                remote_list.append(remote_information)
                remote_list[remote_count].connection = 'Host PC -> Guest PC'
                remote_list[remote_count].task = 'Remote Disconnection'
                if result_data[1] == '4689':
                    remote_list[remote_count].event_id_description = 'A process has exited'
                elif result_data[1] == '1105':
                    remote_list[remote_count].event_id_description = 'The multi-transport connection has been disconnected'
                elif result_data[1] == '1026':
                    remote_list[remote_count].event_id_description = 'RDP ClientActiveX has been disconnected'
                remote_list[remote_count].event_id = result_data[1]
                remote_list[remote_count].time = result_data[2]
                remote_list[remote_count].source = result_data[3]
                remote_list[remote_count].user_sid = result_data[4]
                remote_count = remote_count + 1
        except:
            print("EVENT LOG REMOTE ON OFF ERROR")

    #db.close()

    return remote_list
