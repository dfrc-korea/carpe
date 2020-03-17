# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import os, sys, re
from datetime import datetime, timedelta

sys.path.append(os.path.join(os.path.abspath(os.path.dirname(__file__)), "parsers"))

import parser_interface
from utility import carpe_db

class OS_Information:
    def __init__(self):
        self.par_id = ''
        self.case_id = ''
        self.evd_id = ''
        self.operating_system = ''
        self.version_number = ''
        self.install_time = ''
        self.product_key = ''
        self.owner = ''
        self.display_computer_name = ''
        self.computer_name = ''
        self.dhcp_dns_server = ''
        self.operating_system_version = ''
        self.build_number = ''
        self.product_id = ''
        self.last_service_pack = ''
        self.organization = ''
        self.last_shutdown_time = ''
        self.system_root = ''
        self.path = ''
        self.last_access_time_flag = ''
        self.timezone_utc = ''
        self.display_timezone_name = ''

class OSINFO(parser_interface.ParserInterface):
    """
      OS Information Parser.
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

                if name == "os_info":
                    # TODO : Fix a Chorme Cache plugin -> lack information
                    OS_list = []
                    OS_count = 0

                    #Select Default OS
                    query = r"SELECT description, filename, datetime FROM log2timeline WHERE description like '%#[HKEY_LOCAL_MACHINE#\\Software#\\Microsoft#\\Windows NT#\\CurrentVersion#]%' escape '#' or description like '%#[HKEY_LOCAL_MACHINE#\\System#\\ControlSet001#\\Control#\\ComputerName#\\ComputerName#]%' escape '#' or description like '%#[HKEY_LOCAL_MACHINE#\\System#\\ControlSet001#\\Control#\\FileSystem#]%' escape '#' or description like '%#[HKEY_LOCAL_MACHINE#\\System#\\ControlSet001#\\Control#\\TimeZoneInformation#]%' escape '#' or description like '%#[HKEY_LOCAL_MACHINE#\\System#\\ControlSet001#\\Services#\\Tcpip#\\Parameters#]%' escape '#' or description like '%#[HKEY_LOCAL_MACHINE#\\System#\\ControlSet001#\\Control#\\Windows#]%' escape '#'"
                    result_query = db.execute_query_mul(query)
                    os_information = OS_Information()
                    try:
                        OS_list.append(os_information)
                        for result_data in result_query:
                            if 'SafeOS' in result_data[1] or 'Windows.old' in result_data[1]:
                                if 'CurrentVersion]' in result_data[0].decode('utf-8'):
                                    if 'ProductName' in result_data[0].decode('utf-8'):
                                        if 'RegisteredOwner' in result_data[0].decode('utf-8'):
                                            dataInside = r"ProductName: \[REG_SZ\] (.*) RegisteredOrganization: (.*) ReleaseId: \[REG_SZ\] (.*) SoftwareType:"
                                            m = re.search(dataInside, result_data[0].decode('utf-8'))
                                            OS_list[OS_count].operating_system = m.group(1)+'('+m.group(3)+')'
                                        else:
                                            dataInside = r"ProductName: \[REG_SZ\] (.*) ReleaseId: \[REG_SZ\] (.*) SoftwareType:"
                                            m = re.search(dataInside, result_data[0].decode('utf-8'))
                                            OS_list[OS_count].operating_system = m.group(1)+'('+m.group(2)+')'
                                    if 'CurrentVersion' in result_data[0].decode('utf-8'):
                                        dataInside = r" CurrentVersion: \[REG_SZ\] ([\d\W]*)"
                                        m = re.search(dataInside, result_data[0].decode('utf-8'))
                                        OS_list[OS_count].version_number = m.group(1)
                                    if 'InstallTime' in result_data[0].decode('utf-8'):
                                        dataInside = r"InstallTime: \[REG_QWORD\] ([\d]*)"
                                        m = re.search(dataInside, result_data[0].decode('utf-8'))
                                        OS_list[OS_count].install_time = datetime(1601, 1, 1) + timedelta(microseconds=int(m.group(1))/10)
                                    if 'RegisteredOwner' in result_data[0].decode('utf-8'):
                                        dataInside = r"RegisteredOwner: \[REG_SZ\] (.*) ReleaseId:"
                                        m = re.search(dataInside, result_data[0].decode('utf-8'))
                                        OS_list[OS_count].owner = m.group(1)
                                    if 'EditionID' in result_data[0].decode('utf-8'):
                                        if 'InstallTime' in result_data[0].decode('utf-8'):
                                            dataInside = r"EditionID: \[REG_SZ\] (.*) InstallTime:"
                                            m = re.search(dataInside, result_data[0].decode('utf-8'))
                                            OS_list[OS_count].operating_system_version = m.group(1)
                                        else:
                                            dataInside = r"EditionID: \[REG_SZ\] (.*) InstallationType:"
                                            m = re.search(dataInside, result_data[0].decode('utf-8'))
                                            OS_list[OS_count].operating_system_version = m.group(1)
                                    if 'CurrentBuildNumber' in result_data[0].decode('utf-8'):
                                        dataInside = r"CurrentBuildNumber: \[REG_SZ\] ([\d]*)"
                                        m = re.search(dataInside, result_data[0].decode('utf-8'))
                                        OS_list[OS_count].build_number = m.group(1)
                                    if 'ProductId' in result_data[0].decode('utf-8'):
                                        dataInside = r"ProductId: \[REG_SZ\] (.*) ProductName:"
                                        m = re.search(dataInside, result_data[0].decode('utf-8'))
                                        OS_list[OS_count].product_id = m.group(1)
                                    if 'RegisteredOrganizations' in result_data[0].decode('utf-8'):
                                        dataInside = r"RegisteredOrganizations: \[REG_SZ\] (.*) RegisteredOwner:"
                                        m = re.search(dataInside, result_data[0].decode('utf-8'))
                                        OS_list[OS_count].Organization = m.group(1)
                                    if 'SystemRoot' in result_data[0].decode('utf-8'):
                                        dataInside = r"SystemRoot: \[REG_SZ\] (.*) UBR:"
                                        m = re.search(dataInside, result_data[0].decode('utf-8'))
                                        OS_list[OS_count].system_root = m.group(1)
                                    if 'PathName' in result_data[0].decode('utf-8'):
                                        if 'ProductId' in result_data[0].decode('utf-8'):
                                            dataInside = r"PathName: \[REG_SZ\] (.*) ProductId:"
                                            m = re.search(dataInside, result_data[0].decode('utf-8'))
                                            OS_list[OS_count].path = m.group(1)
                                        else:
                                            dataInside = r"PathName: \[REG_SZ\] (.*) ProductName:"
                                            m = re.search(dataInside, result_data[0].decode('utf-8'))
                                            OS_list[OS_count].path = m.group(1)
                                if 'ComputerName\ComputerName]' in result_data[0].decode('utf-8'):
                                    dataInside = r"ComputerName: \[REG_SZ\] (.*)"
                                    m = re.search(dataInside, result_data[0].decode('utf-8'))
                                    OS_list[OS_count].computer_name = m.group(1)
                                if 'FileSystem]' in result_data[0].decode('utf-8'):
                                    dataInside = r"NtfsDisableLastAccessUpdate: \[REG_DWORD_LE\] ([\d])"
                                    m = re.search(dataInside, result_data[0].decode('utf-8'))
                                    if m.group(1) == '1':
                                        OS_list[OS_count].last_access_time_flag = 'No'
                                    else:
                                        OS_list[OS_count].last_access_time_flag = 'Yes'
                                if 'TimeZoneInformation]' in result_data[0].decode('utf-8'):
                                    dataInside = r"TimeZoneKeyName: (.*)"
                                    m = re.search(dataInside, result_data[0].decode('utf-8'))
                                    OS_list[OS_count].display_timezone_name = m.group(1)
                                if 'Tcpip\Parameters]' in result_data[0].decode('utf-8'):
                                    if 'Hostname' in result_data[0].decode('utf-8'):
                                        dataInside = r"Hostname: \[REG_SZ\] (.*) ICSDomain:"
                                        m = re.search(dataInside, result_data[0].decode('utf-8'))
                                        OS_list[OS_count].display_computer_name = m.group(1)
                                        dataInside = r"DhcpNameServer: \[REG_SZ\] (.*) Domain:"
                                        m = re.search(dataInside, result_data[0].decode('utf-8'))
                                        OS_list[OS_count].dhcp_dns_server = m.group(1)
                                    elif 'HostName' in result_data[0].decode('utf-8'):
                                        dataInside = r"HostName: \[REG_SZ\] (.*) ICSDomain:"
                                        m = re.search(dataInside, result_data[0].decode('utf-8'))
                                        OS_list[OS_count].display_computer_name = m.group(1)
                                        dataInside = r"DhcpNameServer: \[REG_SZ\] (.*) Domain:"
                                        m = re.search(dataInside, result_data[0].decode('utf-8'))
                                        OS_list[OS_count].dhcp_dns_server = m.group(1)
                                if 'Control\Windows]' in result_data[0].decode('utf-8'):
                                    OS_list[OS_count].last_shutdown_time = str(result_data[2])
                        OS_count = OS_count + 1
                        os_information = OS_Information()
                        OS_list.append(os_information)
                        for result_data in result_query:
                            if 'SafeOS' not in result_data[1] and 'Windows.old' not in result_data[1]:
                                if 'CurrentVersion]' in result_data[0].decode('utf-8'):
                                    if 'ProductName' in result_data[0].decode('utf-8'):
                                        if 'RegisteredOwner' in result_data[0].decode('utf-8'):
                                            dataInside = r"ProductName: \[REG_SZ\] (.*) RegisteredOrganization: (.*) ReleaseId: \[REG_SZ\] (.*) SoftwareType:"
                                            m = re.search(dataInside, result_data[0].decode('utf-8'))
                                            OS_list[OS_count].operating_system = m.group(1)+'('+m.group(3)+')'
                                        else:
                                            dataInside = r"ProductName: \[REG_SZ\] (.*) ReleaseId: \[REG_SZ\] (.*) SoftwareType:"
                                            m = re.search(dataInside, result_data[0].decode('utf-8'))
                                            OS_list[OS_count].operating_system = m.group(1)+'('+m.group(2)+')'
                                    if 'CurrentVersion' in result_data[0].decode('utf-8'):
                                        dataInside = r" CurrentVersion: \[REG_SZ\] ([\d\W]*)"
                                        m = re.search(dataInside, result_data[0].decode('utf-8'))
                                        OS_list[OS_count].version_number = m.group(1)
                                    if 'InstallTime' in result_data[0].decode('utf-8'):
                                        dataInside = r"InstallTime: \[REG_QWORD\] ([\d]*)"
                                        m = re.search(dataInside, result_data[0].decode('utf-8'))
                                        OS_list[OS_count].install_time = datetime(1601, 1, 1) + timedelta(microseconds=int(m.group(1))/10)
                                    if 'RegisteredOwner' in result_data[0].decode('utf-8'):
                                        dataInside = r"RegisteredOwner: \[REG_SZ\] (.*) ReleaseId:"
                                        m = re.search(dataInside, result_data[0].decode('utf-8'))
                                        OS_list[OS_count].owner = m.group(1)
                                    if 'EditionID' in result_data[0].decode('utf-8'):
                                        if 'InstallTime' in result_data[0].decode('utf-8'):
                                            if 'EditionSubManufacturer' in result_data[0].decode('utf-8'):
                                                dataInside = r" EditionID: \[REG_SZ\] (.*) EditionSubManufacturer:"
                                                m = re.search(dataInside, result_data[0].decode('utf-8'))
                                                OS_list[OS_count].operating_system_version = m.group(1)
                                            else:
                                                dataInside = r" EditionID: \[REG_SZ\] (.*) InstallTime:"
                                                m = re.search(dataInside, result_data[0].decode('utf-8'))
                                                OS_list[OS_count].operating_system_version = m.group(1)
                                        else:
                                            dataInside = r" EditionID: \[REG_SZ\] (.*) InstallationType:"
                                            m = re.search(dataInside, result_data[0].decode('utf-8'))
                                            OS_list[OS_count].operating_system_version = m.group(1)
                                    if 'CurrentBuildNumber' in result_data[0].decode('utf-8'):
                                        dataInside = r"CurrentBuildNumber: \[REG_SZ\] ([\d]*)"
                                        m = re.search(dataInside, result_data[0].decode('utf-8'))
                                        OS_list[OS_count].build_number = m.group(1)
                                    if 'ProductId' in result_data[0].decode('utf-8'):
                                        dataInside = r"ProductId: \[REG_SZ\] (.*) ProductName:"
                                        m = re.search(dataInside, result_data[0].decode('utf-8'))
                                        OS_list[OS_count].product_id = m.group(1)
                                    if 'RegisteredOrganizations' in result_data[0].decode('utf-8'):
                                        dataInside = r"RegisteredOrganizations: \[REG_SZ\] (.*) RegisteredOwner:"
                                        m = re.search(dataInside, result_data[0].decode('utf-8'))
                                        OS_list[OS_count].Organization = m.group(1)
                                    if 'SystemRoot' in result_data[0].decode('utf-8'):
                                        dataInside = r"SystemRoot: \[REG_SZ\] (.*) UBR:"
                                        m = re.search(dataInside, result_data[0].decode('utf-8'))
                                        OS_list[OS_count].system_root = m.group(1)
                                    if 'PathName' in result_data[0].decode('utf-8'):
                                        dataInside = r"PathName: \[REG_SZ\] (.*) ProductId:"
                                        m = re.search(dataInside, result_data[0].decode('utf-8'))
                                        OS_list[OS_count].path = m.group(1)
                                if 'ComputerName\ComputerName]' in result_data[0].decode('utf-8'):
                                    dataInside = r"ComputerName: \[REG_SZ\] (.*)"
                                    m = re.search(dataInside, result_data[0].decode('utf-8'))
                                    OS_list[OS_count].computer_name = m.group(1)
                                if 'FileSystem]' in result_data[0].decode('utf-8'):
                                    dataInside = r"NtfsDisableLastAccessUpdate: \[REG_DWORD_LE\] (.*) NtfsDisableLfsDowngrade:"
                                    m = re.search(dataInside, result_data[0].decode('utf-8'))
                                    if m.group(1) == '1':
                                        OS_list[OS_count].last_access_time_flag = 'No'
                                    elif m.group(1) == '0':
                                        OS_list[OS_count].last_access_time_flag = 'Yes'
                                    else:
                                        OS_list[OS_count].last_access_time_flag = m.group(1) + '(not parsed)'
                                if 'TimeZoneInformation]' in result_data[0].decode('utf-8'):
                                    dataInside = r"TimeZoneKeyName: (.*)"
                                    m = re.search(dataInside, result_data[0].decode('utf-8'))
                                    OS_list[OS_count].display_timezone_name = m.group(1)
                                if 'Tcpip\Parameters]' in result_data[0].decode('utf-8'):
                                    if 'HostName' in result_data[0].decode('utf-8'):
                                        dataInside = r"HostName: \[REG_SZ\] (.*) ICSDomain:"
                                        m = re.search(dataInside, result_data[0].decode('utf-8'))
                                        OS_list[OS_count].display_computer_name = m.group(1)
                                        dataInside = r"DhcpNameServer: \[REG_SZ\] (.*) Domain:"
                                        m = re.search(dataInside, result_data[0].decode('utf-8'))
                                        OS_list[OS_count].dhcp_dns_server = m.group(1)
                                    elif 'Hostname' in result_data[0].decode('utf-8'):
                                        dataInside = r"Hostname: \[REG_SZ\] (.*) ICSDomain:"
                                        m = re.search(dataInside, result_data[0].decode('utf-8'))
                                        OS_list[OS_count].display_computer_name = m.group(1)
                                        dataInside = r"DhcpNameServer: \[REG_SZ\] (.*) Domain:"
                                        m = re.search(dataInside, result_data[0].decode('utf-8'))
                                        OS_list[OS_count].dhcp_dns_server = m.group(1)

                                if 'Control\Windows]' in result_data[0].decode('utf-8'):
                                    OS_list[OS_count].last_shutdown_time = str(result_data[2])
                    except:
                        print("MAX-OS_INFO" + result_data[0].decode('utf-8')+"error")

                    try:
                        query1 = r"SELECT description, filename FROM log2timeline WHERE description like '%#Windows NT#\\CurrentVersion#\\Time Zones#\\" + \
                                 OS_list[0].display_timezone_name + "%' escape '#' and (filename like '%SafeOS%' or filename like '%Windows.old%')"
                        query2 = r"SELECT description, filename FROM log2timeline WHERE description like '%#Windows NT#\\CurrentVersion#\\Time Zones#\\" + \
                                 OS_list[1].display_timezone_name + "%' escape '#' and (filename not like '%SafeOS%' and filename not like '%Windows.old%')"
                        result_data = db.execute_query_mul(query1)
                        result_data2 = db.execute_query_mul(query2)

                        dataInside = r" Display: \[REG_SZ\] (.*) Dlt:"
                        m = re.search(dataInside, result_data[0][0].decode('utf-8'))
                        OS_list[0].timezone_utc = m.group(1)
                        m = re.search(dataInside, result_data2[0][0].decode('utf-8'))
                        OS_list[1].timezone_utc = m.group(1)
                    except:
                        print("MAX-OSINFO-Timezone_error")

            for os in OS_list:
                insert_values = (par[0], case_id, evd_id,
                                 str(os.operating_system), str(os.version_number), str(os.install_time),
                                 str(os.product_key), str(os.owner), str(os.display_computer_name),
                                 str(os.computer_name), str(os.dhcp_dns_server), str(os.operating_system_version),
                                 str(os.build_number), str(os.product_id), str(os.last_service_pack),
                                 str(os.organization), str(os.last_shutdown_time), str(os.system_root),
                                 str(os.path), str(os.last_access_time_flag), str(os.timezone_utc),
                                 str(os.display_timezone_name))
                self.InsertQuery(db, insert_values)
        db.close()
        now = datetime.now()
        print('[%s-%s-%s %s:%s:%s] OS INFO DONE' % (now.year, now.month, now.day, now.hour, now.minute, now.second))

    def InsertQuery(self, _db, _insert_values_tuple):
        query = self.GetQuery('I', _insert_values_tuple)
        _db.execute_query(query)


