# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import os, sys, re
from datetime import datetime

sys.path.append(os.path.join(os.path.abspath(os.path.dirname(__file__)), "parsers"))

import parser_interface
from utility import carpe_db

class Device_information:
    def __init__(self):
        self.par_id = ''
        self.case_id = ''
        self.evd_id = ''
        self.device_class_id = ''
        self.serial_number = ''
        self.type = ''
        self.last_connected_time = '' #Enum
        self.device_description = ''
        self.friendly_name = ''
        self.manufacturer = ''
        self.last_assigned_drive_letter = ''
        self.volume_GUID = ''
        self.volume_serial_number_decimal = ''
        self.volume_serial_number_hex = ''
        self.associated_user_accounts = ''
        self.first_connected_time = '' #setupapi
        self.first_connected_since_reboot_time = '' #deviceClasses
        self.driver_install_time = '' #64
        self.first_install_time = '' #65
        self.last_insertion_time ='' #66
        self.last_removal_time = '' #67



class USBDEVICES(parser_interface.ParserInterface):
    """
      USB All device Parser.
    """

    def __init__(self):
        # Initialize Formatter Interface
        super().__init__()

    def Parse(self, case_id, evd_id, par_list):
        """
          Analyzes records related to usb all device
          in Psort result.
        """
        # Check Table
        if not self.CheckTable():
            self.CreateTable()

        db = carpe_db.Mariadb()
        db.open()

        for par in par_list:
            for art in self.ARTIFACTS:
                name = art['Name']
                desc = art['Desc']
                values = art['Values']

                if name == "USB_all_device":
                    # TODO : Fix a Chorme Cache plugin -> lack information

                    query = r"SELECT description, datetime FROM log2timeline WHERE (description like '%0064%' or description like '%0065%' or description like '%0066%' or description like '%0067%') and (description like '%SCSI#\%' escape '#' or description like '%USB#\%' escape '#' or description like '%USBSTOR#\%' escape '#' or description like '%STORAGE#\%' escape '#' or description like '%WPDBUSENUM#\%' escape '#')"
                    result_final = db.execute_query_mul(query)

                    device_list = []
                    device_count = 0

                    query = "SELECT description, datetime FROM log2timeline WHERE (description like '%SCSI#\%' escape '#' or description like '%WPDBUSENUM#\%' escape '#' or description like '%USB#\%' escape '#' or description like '%USBSTOR#\%' escape '#' or description like '%STORAGE#\%' escape '#' or description like '%Windows Portable Devices#\\Devices#\\SWD%' escape '#') and description like '%Mfg:%' or description like '%USB#\%' escape '#' and description like '%label:%'"
                    #query2 = "SELECT description, datetime FROM log2timeline WHERE (description like '%SCSI#\%' escape '#' or description like '%WPDBUSENUM#\%' escape '#' or description like '%USB#\%' escape '#' or description like '%USBSTOR#\%' escape '#' or description like '%STORAGE#\%' escape '#' or description like '%Windows Portable Devices#\\Devices#\\SWD%' escape '#') and description like '%Mfg:%'"
                    #result = db.execute_query_mul(query2)
                    result = db.execute_query_mul(query)
                    if len(result) < 1:
                        break
                    else:
                        for result_data in result:
                            device_information = Device_information()
                            try:
                                if 'SCSI\\' in result_data[0].decode('utf-8'):
                                    if 'Address:' not in result_data[0].decode('utf-8'):
                                        dataInside = r"SCSI\\(.*)\\(.*)\] Cap(.*) DeviceDesc: \[REG_SZ\] (.*) (.*) Driver: (.*)FriendlyName: \[REG_SZ\] (.*) Hard(.*) Mfg: \[REG_SZ\] (.*) Service:"
                                        m = re.search(dataInside, result_data[0].decode('utf-8'))
                                        device_list.append(device_information)
                                        device_list[device_count].device_class_id = m.group(1)
                                        device_list[device_count].serial_number = m.group(2)
                                        device_list[device_count].device_description = m.group(4)
                                        device_list[device_count].friendly_name = m.group(7)
                                        device_list[device_count].manufacturer = m.group(9)
                                        device_list[device_count].type = 'SCSI'
                                        device_list[device_count].last_connected_time = result_data[1]
                                    else:
                                        dataInside = r"SCSI\\(.*)\\(.*)\] Address(.*) DeviceDesc: \[REG_SZ\] (.*) (.*) Driver: (.*)FriendlyName: \[REG_SZ\] (.*) Hard(.*) Mfg: \[REG_SZ\] (.*) Service:"
                                        m = re.search(dataInside, result_data[0].decode('utf-8'))
                                        device_list.append(device_information)
                                        device_list[device_count].device_class_id = m.group(1)
                                        device_list[device_count].serial_number = m.group(2)
                                        device_list[device_count].device_description = m.group(4)
                                        device_list[device_count].friendly_name = m.group(7)
                                        device_list[device_count].manufacturer = m.group(9)
                                        device_list[device_count].type = 'SCSI'
                                        device_list[device_count].last_connected_time = result_data[1]
                                elif 'WPDBUSENUM\\' in result_data[0].decode('utf-8'):
                                    dataInside = r"WPDBUSENUM\\(.*)\] Cap(.*) DeviceDesc: \[REG_SZ\] (.*) Driver: (.*)FriendlyName: \[REG_SZ\] (.*) Mfg: \[REG_SZ\] (.*) Service:"
                                    m = re.search(dataInside, result_data[0].decode('utf-8'))
                                    device_list.append(device_information)
                                    device_list[device_count].device_class_id = m.group(1)
                                    device_list[device_count].serial_number = m.group(1)
                                    device_list[device_count].device_description = m.group(3)
                                    if '\\' in m.group(5):
                                        device_list[device_count].friendly_name = m.group(5) + "\\"
                                    else:
                                        device_list[device_count].friendly_name = m.group(5)
                                    device_list[device_count].manufacturer = m.group(6)
                                    device_list[device_count].type = 'SWD'
                                    device_list[device_count].last_connected_time = result_data[1]
                                elif 'USB\\' in result_data[0].decode('utf-8'):
                                    if 'Address:' in result_data[0].decode('utf-8'):
                                        if 'FriendlyName' in result_data[0].decode('utf-8'):
                                            dataInside = r"USB\\(.*)\\(.*)\] Address(.*) DeviceDesc: \[REG_SZ\] (.*) Driver: (.*) FriendlyName: \[REG_SZ\] (.*) Hard(.*) Mfg: \[REG_SZ\] (.*) Service:"
                                            m = re.search(dataInside, result_data[0].decode('utf-8'))
                                            device_list.append(device_information)
                                            device_list[device_count].device_class_id = m.group(1)
                                            device_list[device_count].serial_number = m.group(2)
                                            device_list[device_count].device_description = m.group(4)
                                            device_list[device_count].friendly_name = m.group(6)
                                            device_list[device_count].manufacturer = m.group(8)
                                            device_list[device_count].type = 'USB'
                                            device_list[device_count].last_connected_time = result_data[1]
                                        else:
                                            dataInside = r"USB\\(.*)\\(.*)\] Address(.*) DeviceDesc: \[REG_SZ\] (.*) Driver: (.*) Hard(.*) Mfg: \[REG_SZ\] (.*) Service:"
                                            m = re.search(dataInside, result_data[0].decode('utf-8'))
                                            device_list.append(device_information)
                                            device_list[device_count].device_class_id = m.group(1)
                                            device_list[device_count].serial_number = m.group(2)
                                            device_list[device_count].device_description = m.group(4)
                                            device_list[device_count].manufacturer = m.group(7)
                                            device_list[device_count].type = 'USB'
                                            device_list[device_count].last_connected_time = result_data[1]
                                    else:
                                        dataInside1 = r"USB\\(.*)\\(.*)\] Cap(.*) DeviceDesc: \[REG_SZ\] (.*) Driver: (.*) Mfg: \[REG_SZ\] (.*) P"
                                        dataInside2 = r"USB\\(.*)\\(.*)\] Cap(.*) DeviceDesc: \[REG_SZ\] (.*) Driver: (.*) FriendlyName: \[REG_SZ\] (.*) HardwareID: (.*) Mfg: \[REG_SZ\] (.*) S"
                                        dataInside3 = r"USB\\(.*)\\(.*)\] Cap(.*) DeviceDesc: \[REG_SZ\] (.*) Driver: (.*) Mfg: \[REG_SZ\] (.*) S"
                                        for d in range(0, 3):
                                            m = re.search(dataInside1, result_data[0].decode('utf-8'))
                                            if m == None:
                                                m = re.search(dataInside2, result_data[0].decode('utf-8'))
                                                if m == None:
                                                    m = re.search(dataInside3, result_data[0].decode('utf-8'))
                                                    device_list.append(device_information)
                                                    device_list[device_count].device_class_id = m.group(1)
                                                    device_list[device_count].serial_number = m.group(2)
                                                    device_list[device_count].device_description = m.group(4)
                                                    device_list[device_count].manufacturer = m.group(6)
                                                    device_list[device_count].type = 'USB'
                                                    device_list[device_count].last_connected_time = result_data[1]
                                                    break
                                                else:
                                                    device_list.append(device_information)
                                                    device_list[device_count].device_class_id = m.group(1)
                                                    device_list[device_count].serial_number = m.group(2)
                                                    device_list[device_count].device_description = m.group(4)
                                                    device_list[device_count].friendly_name = m.group(6)
                                                    device_list[device_count].manufacturer = m.group(8)
                                                    device_list[device_count].type = 'USB'
                                                    device_list[device_count].last_connected_time = result_data[1]
                                                    break
                                            else:
                                                device_list.append(device_information)
                                                device_list[device_count].device_class_id = m.group(1)
                                                device_list[device_count].serial_number = m.group(2)
                                                device_list[device_count].device_description = m.group(4)
                                                device_list[device_count].manufacturer = m.group(6)
                                                device_list[device_count].type = 'USB'
                                                device_list[device_count].last_connected_time = result_data[1]
                                                break
                                elif 'USBSTOR\\' in result_data[0].decode('utf-8'):
                                    if 'Address:' in result_data[0].decode('utf-8'):
                                        dataInside = r"USBSTOR\\(.*)\\(.*)\] Address(.*) DeviceDesc: \[REG_SZ\] (.*) (.*) Driver: (.*)FriendlyName: \[REG_SZ\] (.*) Hard(.*) Mfg: \[REG_SZ\] (.*) Service:"
                                        m = re.search(dataInside, result_data[0].decode('utf-8'))
                                        device_list.append(device_information)
                                        device_list[device_count].device_class_id = m.group(1)
                                        device_list[device_count].serial_number = m.group(2)
                                        device_list[device_count].device_description = m.group(4)
                                        device_list[device_count].friendly_name = m.group(7)
                                        device_list[device_count].manufacturer = m.group(9)
                                        device_list[device_count].type = 'USBSTOR'
                                        device_list[device_count].last_connected_time = result_data[1]
                                    else:
                                        dataInside = r"USBSTOR\\(.*)\\(.*)\] Cap(.*) DeviceDesc: \[REG_SZ\] (.*) (.*) Driver: (.*)FriendlyName: \[REG_SZ\] (.*) Hard(.*) Mfg: \[REG_SZ\] (.*) Service:"
                                        m = re.search(dataInside, result_data[0].decode('utf-8'))
                                        device_list.append(device_information)
                                        device_list[device_count].device_class_id = m.group(1)
                                        device_list[device_count].serial_number = m.group(2)
                                        device_list[device_count].device_description = m.group(4)
                                        device_list[device_count].friendly_name = m.group(7)
                                        device_list[device_count].manufacturer = m.group(9)
                                        device_list[device_count].type = 'USBSTOR'
                                        device_list[device_count].last_connected_time = result_data[1]
                                elif 'STORAGE\\' in result_data[0].decode('utf-8'):
                                    if 'Address:' in result_data[0].decode('utf-8'):
                                        dataInside = r"STORAGE\\(.*)\\(.*)\] Address(.*) DeviceDesc: \[REG_SZ\] (.*) Driver: (.*)Hard(.*) Mfg: \[REG_SZ\] (.*) Service:"
                                        m = re.search(dataInside, result_data[0].decode('utf-8'))
                                        device_list.append(device_information)
                                        device_list[device_count].device_class_id = m.group(2)
                                        device_list[device_count].serial_number = m.group(2)
                                        device_list[device_count].device_description = m.group(4)
                                        device_list[device_count].manufacturer = m.group(7)
                                        device_list[device_count].type = 'STORAGE'
                                        device_list[device_count].last_connected_time = result_data[1]
                                    else:
                                        dataInside1 = r"STORAGE\\(.*)\\(.*)\] Cap(.*) DeviceDesc: \[REG_SZ\] (.*) Driver: (.*)Hard(.*) Mfg: \[REG_SZ\] (.*) Service:"
                                        dataInside2 = r"STORAGE\\(.*)\\(.*)\] Cap(.*) DeviceDesc: \[REG_SZ\] (.*) Driver: (.*)Hard(.*) Mfg: \[REG_SZ\] (.*)"
                                        for d in range(0, 2):
                                            m = re.search(dataInside1, result_data[0].decode('utf-8'))
                                            if m == None:
                                                m = re.search(dataInside2, result_data[0].decode('utf-8'))
                                                device_list.append(device_information)
                                                device_list[device_count].device_class_id = m.group(2)
                                                device_list[device_count].serial_number = m.group(2)
                                                device_list[device_count].device_description = m.group(4)
                                                device_list[device_count].manufacturer = m.group(7)
                                                device_list[device_count].type = 'STORAGE'
                                                device_list[device_count].last_connected_time = result_data[1]
                                                break
                                            else:
                                                device_list.append(device_information)
                                                device_list[device_count].device_class_id = m.group(2)
                                                device_list[device_count].serial_number = m.group(2)
                                                device_list[device_count].device_description = m.group(4)
                                                device_list[device_count].manufacturer = m.group(7)
                                                device_list[device_count].type = 'STORAGE'
                                                device_list[device_count].last_connected_time = result_data[1]
                                                break
                                device_count = device_count + 1
                            except:
                                print("MAX-USB-error")

                    for result_data in result:
                        try:
                            if 'Windows Portable Devices\\Devices\\SWD' in result_data[0].decode('utf-8'):
                                dataInside = r"SWD#WPDBUSENUM#(.*)\] FriendlyName: \[REG_SZ\] (.*)"
                                m = re.search(dataInside, result_data[0].decode('utf-8'))
                                for device in device_list:
                                    if m.group(1).lower() == device.device_class_id:
                                        device.last_assigned_drive_letter = m.group(2) + "\\"
                                        break
                        except:
                            print("MAX-USB"+device.device_class_id + "-error")

                    for result_data in result:
                        try:
                            if 'USB\\' in result_data[0].decode('utf-8') and 'Label:' in result_data[0].decode('utf-8'):
                                dataInside = r"Enum\\USB\\(.*)\\(.*)\\Device Parameters(.*)Label: \[REG_SZ\] (.*) PortableDeviceType:"
                                m = re.search(dataInside, result_data[0].decode('utf-8'))
                                for device in device_list:
                                    if m.group(1) == device.device_class_id and m.group(2) == device.serial_number:
                                        device.friendly_name = m.group(4)
                                        break
                        except:
                            print(device.device_class_id + "result_labe_error")

                    for device in device_list:
                        for time_loop in result_final:
                            if '0064]' in time_loop[0].decode('utf-8'):
                                if device.device_class_id in time_loop[0].decode('utf-8') and device.serial_number in time_loop[0].decode('utf-8') and device.type in time_loop[0].decode('utf-8'):
                                    device.driver_install_time = time_loop[1]

                            elif '0065]' in time_loop[0].decode('utf-8'):
                                if device.device_class_id in time_loop[0].decode('utf-8') and device.serial_number in time_loop[0].decode('utf-8') and device.type in time_loop[0].decode('utf-8'):
                                    device.first_install_time  = time_loop[1]

                            elif '0066]' in time_loop[0].decode('utf-8'):
                                if device.device_class_id in time_loop[0].decode('utf-8') and device.serial_number in time_loop[0].decode('utf-8') and device.type in time_loop[0].decode('utf-8'):
                                    device.last_insertion_time = time_loop[1]

                            elif '0067]' in time_loop[0].decode('utf-8'):
                                if device.device_class_id in time_loop[0].decode('utf-8') and device.serial_number in time_loop[0].decode('utf-8') and device.type in time_loop[0].decode('utf-8'):
                                    device.last_removal_time = time_loop[1]

            for device in device_list:
                insert_values = (par[0], case_id, evd_id, str(device.device_class_id), str(device.serial_number), str(device.type),
                                 str(device.last_connected_time), str(device.device_description), str(device.friendly_name),
                                 str(device.manufacturer), str(device.last_assigned_drive_letter), str(device.volume_GUID),
                                 str(device.volume_serial_number_decimal), str(device.volume_serial_number_hex),
                                 str(device.associated_user_accounts), str(device.first_connected_time),
                                 str(device.first_connected_since_reboot_time),
                                 str(device.driver_install_time), str(device.first_install_time),
                                 str(device.last_insertion_time), str(device.last_removal_time))

                self.InsertQuery(db, insert_values)

        db.close()
        now = datetime.now()
        print('[%s-%s-%s %s:%s:%s] USB DEVICES DONE' % (now.year, now.month, now.day, now.hour, now.minute, now.second))

    def InsertQuery(self, _db, _insert_values_tuple):
        query = self.GetQuery('I', _insert_values_tuple)
        _db.execute_query(query)

