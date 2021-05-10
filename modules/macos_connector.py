# -*- coding: utf-8 -*-
"""module for MAC OS."""
import os, sys, time
from modules import manager
from modules import interface
from modules import logger
import plistlib

import subprocess
import io
import shutil
import logging

# class list
class InstalledProgram:
    par_id=''
    case_id=''
    evd_id=''
    date = ''
    filename=''
    version=''
class SystemInformation:
    par_id=''
    case_id=''
    evd_id=''
    product_name = ''
    version=''
    ios_support_version=''
class SystemLog:
    par_id=''
    case_id=''
    evd_id=''
    data=''
class InstallLog:
    par_id=''
    case_id=''
    evd_id=''
    data=''

class MacosConnector(interface.ModuleConnector):
    NAME = 'macos_connector'
    DESCRIPTION = 'Module for MacOS'

    _plugin_classes = {}

    def __init__(self):
        super(MacosConnector, self).__init__()

    def Connect(self, par_id, configuration, source_path_spec, knowledge_base):

        if source_path_spec.TYPE_INDICATOR != 'APFS':
            # print('No MacOS')
            return False

        this_file_path = os.path.dirname(
            os.path.abspath(__file__)) + os.sep + 'schema' + os.sep + 'macos' + os.sep
        # 모든 yaml 파일 리스트
        yaml_list = [this_file_path + 'lv1_os_mac_installed_program.yaml',
                     this_file_path + 'lv1_os_mac_system_information.yaml',
                     this_file_path + 'lv1_os_mac_installed_log.yaml',
                     this_file_path + 'lv1_os_mac_system_log.yaml',
                    ]

        # 모든 테이블 리스트
        table_list = ['lv1_os_mac_installed_program',
                      'lv1_os_mac_system_information',
                      'lv1_os_mac_installed_log',
                      'lv1_os_mac_system_log'
                      ]

        if not self.check_table_from_yaml(configuration, yaml_list, table_list):
            return False

        if sys.platform == 'win32':
            cmd = "..\\modules\\apfs\\pstat.exe " + '"' + configuration.source_path + '"'
        else:
            cmd = "/usr/local/bin/pstat " + '"' + configuration.source_path + '"'
        ret = subprocess.Popen(cmd, shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        time.sleep(30)
        ret_code = ret.stdout.read()
        apsb_block_number = str(ret_code)[str(ret_code).find('APSB Block Number') + 19:].split('\\')[0]

        # Installed program
        installed_program_list = []
        try:
            if sys.platform == 'win32':
                cmd = "..\\modules\\apfs\\fcat.exe -B " + apsb_block_number + " /Library/Receipts/InstallHistory.plist " + '"' + configuration.source_path + '"'
            else:
                cmd = "/usr/local/bin/fcat -B " + apsb_block_number + " /Library/Receipts/InstallHistory.plist " + '"' + configuration.source_path + '"'
            ret = subprocess.Popen(cmd, shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
            time.sleep(10)
            ret_code = ret.stdout.read()

            f = open("temp.plist", 'wb')
            f.write(ret_code)
            f.close()

            with open("temp.plist", 'rb') as fp1:
                pl = plistlib.load(fp1)
            fp1.close()

            os.remove("temp.plist")

            installed_program_count = 0
            for program_info in pl:
                installed_program = InstalledProgram()
                installed_program_list.append(installed_program)
                installed_program_list[installed_program_count].date = str(program_info['date']).replace(' ', 'T') + 'Z'
                installed_program_list[installed_program_count].filename = program_info['displayName']
                installed_program_list[installed_program_count].version = program_info['displayVersion']
                installed_program_count = installed_program_count + 1
        except:
            print("macOS - installed program error")

        insert_data = []
        for installed_program in installed_program_list:
            insert_data.append(
                tuple([par_id, configuration.case_id, configuration.evidence_id, str(installed_program.date),
                       str(installed_program.filename), str(installed_program.version)]))
        query = "Insert into lv1_os_mac_installed_program values (%s, %s, %s, %s, %s, %s)"
        if len(insert_data) > 0:
            configuration.cursor.bulk_execute(query, insert_data)

        # System Information
        system_information_list = []
        try:
            if sys.platform == 'win32':
                cmd = "..\\modules\\apfs\\fcat.exe -B " + apsb_block_number + " /System/Library/CoreServices/SystemVersion.plist " + '"' + configuration.source_path + '"'
            else:
                cmd = "/usr/local/bin/fcat -B " + apsb_block_number + " /System/Library/CoreServices/SystemVersion.plist " + '"' + configuration.source_path + '"'
            ret = subprocess.Popen(cmd, shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
            time.sleep(10)
            ret_code = ret.stdout.read()

            f = open("temp.plist", 'wb')
            f.write(ret_code)
            f.close()

            with open("temp.plist", 'rb') as fp2:
                system_info = plistlib.load(fp2)
            fp2.close()

            os.remove("temp.plist")

            system_information = SystemInformation()
            system_information_list.append(system_information)
            system_information_list[0].product_name = system_info['ProductName']
            system_information_list[0].version = system_info['ProductVersion']
            system_information_list[0].ios_support_version = system_info['iOSSupportVersion']
        except:
            print("macOS - System Informaiton error")

        insert_data = []
        insert_data.append(
            tuple([par_id, configuration.case_id, configuration.evidence_id, str(system_information_list[0].product_name),
                   str(system_information_list[0].version), str(system_information_list[0].ios_support_version)]))
        query = "Insert into lv1_os_mac_system_information values (%s, %s, %s, %s, %s, %s)"
        if len(insert_data) > 0:
            configuration.cursor.bulk_execute(query, insert_data)

        # System Log
        system_log_list = []
        try:
            if sys.platform == 'win32':
                cmd = "..\\modules\\apfs\\fcat.exe -B " + apsb_block_number + " /private/var/log/system.log " + '"' + configuration.source_path + '"'
            else:
                cmd = "/usr/local/bin/fcat -B " + apsb_block_number + " /private/var/log/system.log " + '"' + configuration.source_path + '"'
            ret = subprocess.Popen(cmd, shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
            time.sleep(10)
            ret_code = ret.stdout.read()

            system_log_count = 0
            for Systemlog_info in str(ret_code).replace("b\'",'').split('\\n'):
                system_log = SystemLog()
                system_log_list.append(system_log)
                if Systemlog_info[0] != '\\':
                    system_log_list[system_log_count].data = Systemlog_info
                else:
                    system_log_count = system_log_count - 1
                    system_log_list[system_log_count].data = system_log_list[system_log_count].data + Systemlog_info
                system_log_count = system_log_count + 1
        except:
            print("macOS - System Log error")

        insert_data = []
        for system_log in system_log_list:
            insert_data.append(
                tuple([par_id, configuration.case_id, configuration.evidence_id, str(system_log.data)]))
        query = "Insert into lv1_os_mac_system_log values (%s, %s, %s, %s)"
        if len(insert_data) > 0:
            configuration.cursor.bulk_execute(query, insert_data)
        '''
        # Install Log
        install_log_list = []
        try:
            cmd = "/usr/local/bin/fcat -B " + apsb_block_number + " /private/var/log/install.log " + '"' + configuration.source_path + '"'
            ret = subprocess.Popen(cmd, shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
            ret_code = ret.stdout.read()

            install_log_count = 0
            for Installlog_info in str(ret_code).replace("b\'", '').split('\\n'):
                install_log = InstallLog()
                install_log_list.append(install_log)
                if Installlog_info[0] != '\\':
                    install_log_list[install_log_count].data = Installlog_info
                else:
                    install_log_count = install_log_count - 1
                    install_log_list[install_log_count].data = install_log_list[
                                                                   install_log_count].data + Installlog_info
                install_log_count = install_log_count + 1
        except:
            print("macOS - Install Log error")

        insert_data = []
        for install_log in install_log_list:
            insert_data.append(
                tuple([par_id, configuration.case_id, configuration.evidence_id, str(install_log.data)]))
        query = "Insert into lv1_os_mac_installed_log values (%s, %s, %s, %s)"
        if len(insert_data) > 0:
            configuration.cursor.bulk_execute(query, insert_data)
        '''
manager.ModulesManager.RegisterModule(MacosConnector)
