# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import os, sys, re, numpy
from datetime import datetime

from utility import database

class USB_Information:
    par_id = ''
    case_id = ''
    evd_id = ''
    task = ''
    time = ''
    device_instance_id = ''
    description = ''
    manufacturer = ''
    model = ''
    revision = ''
    serial_number = ''
    parentid = ''
    user_sid = ''
    event_id = ''
    source = ''
    event_id_description = ''

def EVENTLOGUSBDEVICES(configuration):
    #db = database.Database()
    #db.open()
    usb_list = []
    usb_count = 0
    query = f"SELECT data, event_id, time_created, source, user_sid FROM lv1_os_win_evt_total WHERE (evd_id='{configuration.evidence_id}') and ((event_id like '1006' and source like '%Partition%') or (event_id like '507' and source like '%Storage%') or (event_id like '504'and source like '%Storage%') or (event_id like '10000'and source like '%System.evtx%') or (event_id like '20001'and source like '%System.evtx%') or (event_id like '20003'and source like '%System.evtx%') or (event_id like '2003'and source like '%DriverFrameworks%') or (event_id like '2101'and source like '%DriverFrameworks%') or (event_id like '2102'and source like '%DriverFrameworks%') or (event_id like '2901'and source like '%DriverFrameworks%'))"
    #result_query = db.execute_query_mul(query)
    result_query = configuration.cursor.execute_query_mul(query)
    for result_data in result_query:
        usb_information = USB_Information()
        try:
            if result_data[1] == '1006':
                usb_list.append(usb_information)
                usb_list[usb_count].event_id = result_data[1]
                usb_list[usb_count].time = result_data[2]
                usb_list[usb_count].source = result_data[3]
                usb_list[usb_count].user_sid = result_data[4]
                usb_list[usb_count].event_id_description = 'Device Connected or disconnected events'
                if 'Capacity">0<' in result_data[0]:
                    usb_list[usb_count].task = 'Disconnected'
                else:
                    usb_list[usb_count].task = 'Connected'
                if 'Manufacturer' in result_data[0]:
                    dataInside = r"Manufacturer\">(.*)<"
                    m = re.search(dataInside, result_data[0])
                    usb_list[usb_count].manufacturer = m.group(1)
                if 'Model' in result_data[0]:
                    dataInside = r"Model\">(.*)<"
                    m = re.search(dataInside, result_data[0])
                    usb_list[usb_count].model = m.group(1)
                if 'Revision' in result_data[0]:
                    dataInside = r"Revision\">(.*)<"
                    m = re.search(dataInside, result_data[0])
                    usb_list[usb_count].revision = m.group(1)
                if 'SerialNumber' in result_data[0]:
                    dataInside = r"SerialNumber\">(.*)<"
                    m = re.search(dataInside, result_data[0])
                    usb_list[usb_count].serial_number = m.group(1)
                if 'ParentId' in result_data[0]:
                    dataInside = r"ParentId\">(.*)<"
                    m = re.search(dataInside, result_data[0])
                    usb_list[usb_count].parentid = m.group(1)
                usb_count = usb_count + 1

            elif result_data[1] == '507':
                usb_list.append(usb_information)
                usb_list[usb_count].event_id = result_data[1]
                usb_list[usb_count].time = result_data[2]
                usb_list[usb_count].source = result_data[3]
                usb_list[usb_count].user_sid = result_data[4]
                usb_list[usb_count].task = 'Connected'
                usb_list[usb_count].event_id_description = 'Completing a failed non-ReadWrite SCSI SRB request'
                if 'Vendor' in result_data[0]:
                    dataInside = r"Vendor\">(.*)<"
                    m = re.search(dataInside, result_data[0])
                    usb_list[usb_count].manufacturer = m.group(1)
                if 'Model' in result_data[0]:
                    dataInside = r"Model\">(.*)<"
                    m = re.search(dataInside, result_data[0])
                    usb_list[usb_count].model = m.group(1)
                if 'FirmwareVersion' in result_data[0]:
                    dataInside = r"FirmwareVersion\">(.*)<"
                    m = re.search(dataInside, result_data[0])
                    usb_list[usb_count].revision = m.group(1)
                if 'SerialNumber' in result_data[0]:
                    dataInside = r"SerialNumber\">(.*)<"
                    m = re.search(dataInside, result_data[0])
                    usb_list[usb_count].serial_number = m.group(1)
                if 'ParentId' in result_data[0]:
                    dataInside = r"ParentId\">(.*)<"
                    m = re.search(dataInside, result_data[0])
                    usb_list[usb_count].parentid = m.group(1)
                usb_count = usb_count + 1

            elif result_data[1] == '10000' or result_data[1] == '20001' or result_data[1] == '20003':
                usb_list.append(usb_information)
                usb_list[usb_count].event_id = result_data[1]
                usb_list[usb_count].time = result_data[2]
                usb_list[usb_count].source = result_data[3]
                usb_list[usb_count].user_sid = result_data[4]
                usb_list[usb_count].task = 'Connected'
                if result_data[1] == '10000':
                    usb_list[usb_count].event_id_description = 'Install driver package'
                elif result_data[1] == '20001':
                    usb_list[usb_count].event_id_description = 'End the driver installation process'
                elif result_data[1] == '20003':
                    usb_list[usb_count].event_id_description = 'End the service addition process'
                if 'DeviceInstanceID' in result_data[0]:
                    dataInside = r"DeviceInstanceID>(.*)<"
                    m = re.search(dataInside, result_data[0])
                    usb_list[usb_count].device_instance_id = m.group(1)
                elif 'DriverDescription' in result_data[0]:
                    dataInside = r"DriverDescription>(.*)<"
                    m = re.search(dataInside, result_data[0])
                    usb_list[usb_count].description = m.group(1)
                elif 'DeviceId' in result_data[0]:
                    dataInside = r"DeviceId>(.*)<"
                    m = re.search(dataInside, result_data[0])
                    usb_list[usb_count].device_instance_id = m.group(1)
                usb_count = usb_count + 1
        except:
            print("EVENT LOG USB DEVICES ERROR")
    #db.close()

    return usb_list
