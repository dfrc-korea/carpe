# -*- coding: utf-8 -*-
"""module for Registry."""
import os
from modules import manager
from modules import interface
from yarp import Registry
from modules.Registry import lv1_os_win_reg_os_info as oi
from modules.Registry import lv1_os_win_reg_installed_programs as ip
from modules.Registry import lv1_os_win_reg_user_accounts as ua
from modules.Registry import lv1_os_win_reg_usb_devices as ud
from modules.Registry import lv1_os_win_reg_userassist as u
from modules.Registry import lv1_os_win_reg_amcache_file_entries as afe
from modules.Registry import lv1_os_win_reg_amcache_program_entries as ape
from modules.Registry import lv1_os_win_reg_known_dll as kd
from modules.Registry import lv1_os_win_reg_file_connection as fc
from modules.Registry import lv1_os_win_reg_mru_folder as mf
from modules.Registry import lv1_os_win_reg_mru_opened_file as mof
from modules.Registry import lv1_os_win_reg_start as s
from modules.Registry import lv1_os_win_reg_system_service as ss
from modules.Registry import lv1_os_win_reg_shim_cache as sc
from modules.Registry import lv1_os_win_reg_mui_cache as mc
from modules.Registry import lv1_os_win_reg_recent_docs as rd
from modules.Registry import lv1_os_win_reg_run_command as rc
from modules.Registry import lv1_os_win_reg_search_keyword as sk
from modules.Registry import lv1_os_win_reg_mac_address as ma
from modules.Registry import lv1_os_win_reg_network_drive as nd
from modules.Registry import lv1_os_win_reg_network_interface as ni
from modules.Registry import lv1_os_win_reg_network_profile as np


class RegistryConnector(interface.ModuleConnector):
    NAME = 'registry_connector'
    DESCRIPTION = 'Module for Registry'

    _plugin_classes = {}

    def __init__(self):
        super(RegistryConnector, self).__init__()

    def Connect(self, par_id, configuration, source_path_spec, knowledge_base):

        this_file_path = os.path.dirname(
            os.path.abspath(__file__)) + os.sep + 'schema' + os.sep + 'registry' + os.sep
        # 모든 yaml 파일 리스트
        yaml_list = [this_file_path + 'lv1_os_win_reg_amcache_file_entries.yaml',
                     this_file_path + 'lv1_os_win_reg_amcache_program_entries.yaml',
                     this_file_path + 'lv1_os_win_reg_installed_programs.yaml',
                     this_file_path + 'lv1_os_win_reg_os_info.yaml',
                     this_file_path + 'lv1_os_win_reg_usb_devices.yaml',
                     this_file_path + 'lv1_os_win_reg_user_accounts.yaml',
                     this_file_path + 'lv1_os_win_reg_userassist.yaml',
                     this_file_path + 'lv1_os_win_reg_file_connection.yaml',
                     this_file_path + 'lv1_os_win_reg_known_dll.yaml',
                     this_file_path + 'lv1_os_win_reg_mac_address.yaml',
                     this_file_path + 'lv1_os_win_reg_mui_cache.yaml',
                     this_file_path + 'lv1_os_win_reg_shim_cache.yaml',
                     this_file_path + 'lv1_os_win_reg_network_drive.yaml',
                     this_file_path + 'lv1_os_win_reg_network_interface.yaml',
                     this_file_path + 'lv1_os_win_reg_network_profile.yaml',
                     this_file_path + 'lv1_os_win_reg_recent_docs.yaml',
                     this_file_path + 'lv1_os_win_reg_run_command.yaml',
                     this_file_path + 'lv1_os_win_reg_search_keyword.yaml',
                     this_file_path + 'lv1_os_win_reg_start_list.yaml',
                     this_file_path + 'lv1_os_win_reg_system_service.yaml',
                     this_file_path + 'lv1_os_win_reg_mru_folder.yaml',
                     this_file_path + 'lv1_os_win_reg_mru_file.yaml']

        # 모든 테이블 리스트
        table_list = ['lv1_os_win_reg_amcache_file',
                      'lv1_os_win_reg_amcache_program',
                      'lv1_os_win_reg_installed_program',
                      'lv1_os_win_reg_os_information',
                      'lv1_os_win_reg_usb_device',
                      'lv1_os_win_reg_user_account',
                      'lv1_os_win_reg_user_assist',
                      'lv1_os_win_reg_file_connection',
                      'lv1_os_win_reg_known_dll',
                      'lv1_os_win_reg_mac_address',
                      'lv1_os_win_reg_mui_cache',
                      'lv1_os_win_reg_shim_cache',
                      'lv1_os_win_reg_network_drive',
                      'lv1_os_win_reg_network_interface',
                      'lv1_os_win_reg_network_profile',
                      'lv1_os_win_reg_recent_docs',
                      'lv1_os_win_reg_run_command',
                      'lv1_os_win_reg_search_keyword',
                      'lv1_os_win_reg_start_list',
                      'lv1_os_win_reg_system_service',
                      'lv1_os_win_reg_mru_folder',
                      'lv1_os_win_reg_mru_file']

        if not self.check_table_from_yaml(configuration, yaml_list, table_list):
            return False

        ### 계정 불러오기 ###
        useraccount_list = []
        for user_accounts in knowledge_base._user_accounts.values():
            for hostname in user_accounts.values():
                if hostname.identifier.find('S-1-5-21') == -1:
                    continue
                useraccount_list.append(hostname.username)

        query_separator = self.GetQuerySeparator(source_path_spec, configuration)
        path_separator = self.GetPathSeparator(source_path_spec)

        config_path = f"root{query_separator}Windows{query_separator}System32{query_separator}config"
        appcompat_path = f"root{query_separator}Windows{query_separator}appcompat{query_separator}Programs"
        INF_path = f"root{query_separator}Windows{query_separator}INF"
        query = f"SELECT name, parent_path, extension FROM file_info WHERE (par_id='{par_id}') and " \
                f"((name = 'SYSTEM' and parent_path like '{config_path}') or " \
                f"(name = 'SOFTWARE' and parent_path like '{config_path}') or " \
                f"(name = 'SAM' and parent_path like '{config_path}') or " \
                f"(name = 'Amcache.hve' and parent_path like '{appcompat_path}') or " \
                f"(name = 'setupapi.dev.log' and parent_path like '{INF_path}')  or " \
                f"(name = 'SYSTEM.LOG1' and parent_path like '{config_path}') or " \
                f"(name = 'SYSTEM.LOG2' and parent_path like '{config_path}') or " \
                f"(name = 'SOFTWARE.LOG1' and parent_path like '{config_path}') or " \
                f"(name = 'SOFTWARE.LOG2' and parent_path like '{config_path}') or " \
                f"(name = 'SAM.LOG1' and parent_path like '{config_path}') or " \
                f"(name = 'SAM.LOG2' and parent_path like '{config_path}') or " \
                f"(name = 'Amcache.hve.LOG1' and parent_path like '{appcompat_path}') or " \
                f"(name = 'Amcache.hve.LOG2' and parent_path like '{appcompat_path}'))"

        # query = query.replace('/', query_separator)

        registry_files = configuration.cursor.execute_query_mul(query)

        if len(registry_files) == 0:
            print("There are no registry files")
            return False

        registry_files2 = []
        for useraccount in useraccount_list:
            query2 = f"SELECT name, parent_path, extension FROM file_info WHERE (par_id='{par_id}') and " \
                     f"((name = 'UsrClass.dat' and parent_path like '%{useraccount}%') or " \
                     f"(name = 'NTUSER.DAT' and parent_path like '%{useraccount}%') or " \
                     f"(name = 'UsrClass.dat.LOG1' and parent_path like '%{useraccount}%') or " \
                     f"(name = 'UsrClass.dat.LOG2' and parent_path like '%{useraccount}%') or " \
                     f"(name = 'ntuser.dat.LOG1' and parent_path like '%{useraccount}%') or " \
                     f"(name = 'ntuser.dat.LOG2' and parent_path like '%{useraccount}%'))"
            # query2 = query2.replace('/', query_separator)
            registry_files2.append(configuration.cursor.execute_query_mul(query2))

        old_config_path = f"root{query_separator}Windows.old{query_separator}Windows{query_separator}System32{query_separator}config"
        old_appcompat_path = f"root{query_separator}Windows.old{query_separator}Windows{query_separator}appcompat{query_separator}Programs"
        old_INF_path = f"root{query_separator}Windows.old{query_separator}Windows{query_separator}INF"

        query3 = f"SELECT name, parent_path, extension FROM file_info WHERE (par_id='{par_id}') and " \
                 f"((name = 'SYSTEM' and parent_path like '{old_config_path}') or " \
                 f"(name = 'SOFTWARE' and parent_path like '{old_config_path}') or " \
                 f"(name = 'SAM' and parent_path like '{old_config_path}') or " \
                 f"(name = 'Amcache.hve' and parent_path like '{old_appcompat_path}') or " \
                 f"(name = 'setupapi.dev.log' and parent_path like '{old_INF_path}') or " \
                 f"(name = 'SYSTEM.LOG1' and parent_path like '{old_config_path}') or " \
                 f"(name = 'SYSTEM.LOG2' and parent_path like '{old_config_path}') or " \
                 f"(name = 'SOFTWARE.LOG1' and parent_path like '{old_config_path}') or " \
                 f"(name = 'SOFTWARE.LOG2' and parent_path like '{old_config_path}') or " \
                 f"(name = 'SAM.LOG1' and parent_path like '{old_config_path}') or " \
                 f"(name = 'SAM.LOG2' and parent_path like '{old_config_path}') or " \
                 f"(name = 'Amcache.hve.LOG1' and parent_path like '{old_appcompat_path}') or " \
                 f"(name = 'Amcache.hve.LOG2' and parent_path like '{old_appcompat_path}'))"
        # query3 = query3.replace('/', query_separator)
        regback_path = f"root{query_separator}Windows{query_separator}System32{query_separator}config{query_separator}RegBack"
        query4 = f"SELECT name, parent_path, extension FROM file_info WHERE (par_id='{par_id}') and " \
                 f"((name = 'SYSTEM' and parent_path like '{regback_path}') or " \
                 f"(name = 'SOFTWARE' and parent_path like '{regback_path}') or " \
                 f"(name = 'SAM' and parent_path like '{regback_path}') or " \
                 f"(name = 'SYSTEM.LOG1' and parent_path like '{regback_path}') or " \
                 f"(name = 'SYSTEM.LOG2' and parent_path like '{regback_path}') or " \
                 f"(name = 'SOFTWARE.LOG1' and parent_path like '{regback_path}') or " \
                 f"(name = 'SOFTWARE.LOG2' and parent_path like '{regback_path}') or " \
                 f"(name = 'SAM.LOG1' and parent_path like '{regback_path}') or " \
                 f"(name = 'SAM.LOG2' and parent_path like '{regback_path}'))"
        # query4 = query4.replace('/', query_separator)

        old_regback_path = f"root{query_separator}Windows.old{query_separator}Windows{query_separator}System32{query_separator}config{query_separator}RegBack"

        query5 = f"SELECT name, parent_path, extension FROM file_info WHERE (par_id='{par_id}') and " \
                 f"((name = 'SYSTEM' and parent_path like '{old_regback_path}') or " \
                 f"(name = 'SOFTWARE' and parent_path like '{old_regback_path}') or " \
                 f"(name = 'SAM' and parent_path like '{old_regback_path}') or " \
                 f"(name = 'SYSTEM.LOG1' and parent_path like '{old_regback_path}') or " \
                 f"(name = 'SYSTEM.LOG2' and parent_path like '{old_regback_path}') or " \
                 f"(name = 'SOFTWARE.LOG1' and parent_path like '{old_regback_path}') or " \
                 f"(name = 'SOFTWARE.LOG2' and parent_path like '{old_regback_path}') or " \
                 f"(name = 'SAM.LOG1' and parent_path like '{old_regback_path}') or " \
                 f"(name = 'SAM.LOG2' and parent_path like '{old_regback_path}'))"
        # query5 = query5.replace('/', query_separator)

        registry_files3 = configuration.cursor.execute_query_mul(query3)
        registry_files4 = configuration.cursor.execute_query_mul(query4)
        registry_files5 = configuration.cursor.execute_query_mul(query5)

        registry_file_list = [registry_files]

        if len(registry_files3) != 0:
            registry_file_list.append(registry_files3)
        elif len(registry_files4) != 0:
            registry_file_list.append(registry_files4)
        elif len(registry_files5) != 0:
            registry_file_list.append(registry_files5)

        setupapi_data = None
        for registry_file in registry_file_list:
            reg_am = ''
            reg_am_log1 = ''
            reg_am_log2 = ''
            reg_system = ''
            reg_system_log1 = ''
            reg_system_log2 = ''
            reg_software = ''
            reg_software_log1 = ''
            reg_software_log2 = ''
            reg_sam = ''
            reg_sam_log1 = ''
            reg_sam_log2 = ''
            reg_usrclass_list = []
            reg_usr = ''
            reg_usr_log1 = ''
            reg_usr_log2 = ''
            reg_nt_list = []
            reg_nt = ''
            reg_nt_log1 = ''
            reg_nt_log2 = ''
            if registry_file == registry_files:
                backup_flag = 'Local'
            elif registry_file == registry_files3:
                registry_files = registry_files3
                backup_flag = 'Backup-Windows.old'
            elif registry_file == registry_files4:
                registry_files = registry_files4
                backup_flag = 'Backup-RegBack'
            elif registry_file == registry_files5:
                registry_files = registry_files5
                backup_flag = 'Backup-Windows.old, Backup-RegBack'

            for registry in registry_files:
                registry_path = registry[1][registry[1].find(path_separator):] + path_separator + registry[0]
                fileName = registry[0]

                file_object = self.LoadTargetFileToMemory(
                    source_path_spec=source_path_spec,
                    configuration=configuration,
                    file_path=registry_path)

                if file_object is None:
                    return

                if fileName == 'Amcache.hve':
                    reg_am = Registry.RegistryHive(file_object)
                    for registry in registry_files:
                        if registry[0] == 'Amcache.hve.LOG1':
                            registry_path = registry[1][registry[1].find(path_separator):] + path_separator + registry[
                                0]
                            reg_am_log1 = self.LoadTargetFileToMemory(
                                source_path_spec=source_path_spec,
                                configuration=configuration,
                                file_path=registry_path)
                        elif registry[0] == 'Amcache.hve.LOG2':
                            registry_path = registry[1][registry[1].find(path_separator):] + path_separator + registry[
                                0]
                            reg_am_log2 = self.LoadTargetFileToMemory(
                                source_path_spec=source_path_spec,
                                configuration=configuration,
                                file_path=registry_path)
                    reg_am.recover_auto(None, reg_am_log1, reg_am_log2)

                if fileName == 'SYSTEM':
                    try:
                        reg_system = Registry.RegistryHive(file_object)
                    except:
                        reg_system = ''
                        print("SYSTEM - ERROR")
                    if reg_system != '':
                        for registry in registry_files:
                            if registry[0] == 'SYSTEM.LOG1':
                                registry_path = registry[1][registry[1].find(path_separator):] + path_separator + \
                                                registry[0]
                                reg_system_log1 = self.LoadTargetFileToMemory(
                                    source_path_spec=source_path_spec,
                                    configuration=configuration,
                                    file_path=registry_path)
                            elif registry[0] == 'SYSTEM.LOG2':
                                registry_path = registry[1][registry[1].find(path_separator):] + path_separator + \
                                                registry[0]
                                reg_system_log2 = self.LoadTargetFileToMemory(
                                    source_path_spec=source_path_spec,
                                    configuration=configuration,
                                    file_path=registry_path)
                        reg_system.recover_auto(None, reg_system_log1, reg_system_log2)

                if fileName == 'SOFTWARE':
                    try:
                        reg_software = Registry.RegistryHive(file_object)
                    except:
                        reg_software = ''
                        print("SOFTWARE - ERROR")
                    if reg_software != '':
                        for registry in registry_files:
                            if registry[0] == 'SOFTWARE.LOG1':
                                registry_path = registry[1][registry[1].find(path_separator):] + path_separator + \
                                                registry[0]
                                reg_software_log1 = self.LoadTargetFileToMemory(
                                    source_path_spec=source_path_spec,
                                    configuration=configuration,
                                    file_path=registry_path)
                            elif registry[0] == 'SOFTWARE.LOG2':
                                registry_path = registry[1][registry[1].find(path_separator):] + path_separator + \
                                                registry[0]
                                reg_software_log2 = self.LoadTargetFileToMemory(
                                    source_path_spec=source_path_spec,
                                    configuration=configuration,
                                    file_path=registry_path)
                        reg_software.recover_auto(None, reg_software_log1, reg_software_log2)

                elif fileName == 'SAM':
                    try:
                        reg_sam = Registry.RegistryHive(file_object)
                    except:
                        reg_sam = ''
                        print("SAM - ERROR")
                    if reg_sam != '':
                        for registry in registry_files:
                            if registry[0] == 'SAM.LOG1':
                                registry_path = registry[1][registry[1].find(path_separator):] + path_separator + \
                                                registry[0]
                                reg_sam_log1 = self.LoadTargetFileToMemory(
                                    source_path_spec=source_path_spec,
                                    configuration=configuration,
                                    file_path=registry_path)
                            elif registry[0] == 'SAM.LOG2':
                                registry_path = registry[1][registry[1].find(path_separator):] + path_separator + \
                                                registry[0]
                                reg_sam_log2 = self.LoadTargetFileToMemory(
                                    source_path_spec=source_path_spec,
                                    configuration=configuration,
                                    file_path=registry_path)
                        reg_sam.recover_auto(None, reg_sam_log1, reg_sam_log2)

                if fileName == 'setupapi.dev.log':
                    setupapi_data = file_object.read()

            if backup_flag != 'Backup-RegBack':
                for registry2 in registry_files2:
                    for registry in registry2:
                        registry_path = registry[1][registry[1].find(path_separator):] + path_separator + registry[0]
                        fileName = registry[0]

                        file_object = self.LoadTargetFileToMemory(
                            source_path_spec=source_path_spec,
                            configuration=configuration,
                            file_path=registry_path)

                        if file_object is None:
                            return

                        if fileName == 'UsrClass.dat':
                            wow = []
                            reg_usr = Registry.RegistryHive(file_object)
                            for registry in registry2:
                                if registry[0] == 'UsrClass.dat.LOG1':
                                    registry_path = registry[1][registry[1].find(path_separator):] + path_separator + \
                                                    registry[0]
                                    reg_usr_log1 = self.LoadTargetFileToMemory(
                                        source_path_spec=source_path_spec,
                                        configuration=configuration,
                                        file_path=registry_path)
                                elif registry[0] == 'UsrClass.dat.LOG2':
                                    registry_path = registry[1][registry[1].find(path_separator):] + path_separator + \
                                                    registry[0]
                                    reg_usr_log2 = self.LoadTargetFileToMemory(
                                        source_path_spec=source_path_spec,
                                        configuration=configuration,
                                        file_path=registry_path)
                            reg_usr.recover_auto(None, reg_usr_log1, reg_usr_log2)

                            wow.append(reg_usr)
                            wow.append(registry[1].split(path_separator)[2])
                            reg_usrclass_list.append(wow)
                        elif fileName == 'NTUSER.DAT':
                            wow = []
                            reg_nt = Registry.RegistryHive(file_object)
                            for registry in registry2:
                                if registry[0] == 'ntuser.dat.LOG1':
                                    registry_path = registry[1][registry[1].find(path_separator):] + path_separator + \
                                                    registry[0]
                                    reg_nt_log1 = self.LoadTargetFileToMemory(
                                        source_path_spec=source_path_spec,
                                        configuration=configuration,
                                        file_path=registry_path)
                                elif registry[0] == 'ntuser.dat.LOG2':
                                    registry_path = registry[1][registry[1].find(path_separator):] + path_separator + \
                                                    registry[0]
                                    reg_nt_log2 = self.LoadTargetFileToMemory(
                                        source_path_spec=source_path_spec,
                                        configuration=configuration,
                                        file_path=registry_path)
                            reg_nt.recover_auto(None, reg_nt_log1, reg_nt_log2)

                            wow.append(reg_nt)
                            wow.append(registry[1].split(path_separator)[2])
                            reg_nt_list.append(wow)

            # Amcache File
            if backup_flag != 'Backup-RegBack' and reg_am != '':
                print(f'[{self.print_now_time()}] [MODULE]: Registry - Amcache File')
                insert_data = []
                for amcache in afe.AMCACHEFILEENTRIES(reg_am):
                    key_last_updated_time = configuration.apply_time_zone(str(amcache.key_last_updated_time),
                                                                          knowledge_base.time_zone)
                    link_date = configuration.apply_time_zone(str(amcache.link_date), knowledge_base.time_zone)
                    insert_data.append(
                        tuple([par_id, configuration.case_id, configuration.evidence_id, str(amcache.file_name),
                               key_last_updated_time, str(amcache.file_extension), str(amcache.program_id),
                               str(amcache.key_id), str(amcache.related_programname),
                               str(amcache.sha1_hash), str(amcache.os_component_flag),
                               str(amcache.full_path), link_date, str(amcache.product_name), str(amcache.size),
                               str(amcache.version), str(amcache.product_version), str(amcache.long_path_hash),
                               str(amcache.binary_type), str(amcache.pe_file_flag), str(amcache.binary_file_version),
                               str(amcache.binary_product_version),
                               str(amcache.language_code), str(amcache.usn), str(amcache.publisher), backup_flag,
                               ', '.join(amcache.source_location)]))
                query = "Insert into lv1_os_win_reg_amcache_file values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"
                if len(insert_data) > 0:
                    configuration.cursor.bulk_execute(query, insert_data)

            # Amcache Program
            if backup_flag != 'Backup-RegBack' and reg_am != '':
                print(f'[{self.print_now_time()}] [MODULE]: Registry - Amcache Program')
                insert_data = []
                for amcache in ape.AMCACHEPROGRAMENTRIES(reg_am):
                    key_last_updated_time = configuration.apply_time_zone(str(amcache.key_last_updated_time),
                                                                          knowledge_base.time_zone)
                    try:
                        installed_date = configuration.apply_time_zone(str(amcache.installed_date),
                                                                       knowledge_base.time_zone)
                    except Exception:
                        installed_date = None
                    uninstall_date = configuration.apply_time_zone(str(amcache.uninstall_date),
                                                                   knowledge_base.time_zone)
                    insert_data.append(
                        tuple([par_id, configuration.case_id, configuration.evidence_id, str(amcache.file_name),
                               key_last_updated_time, installed_date, str(amcache.version),
                               str(amcache.publisher), uninstall_date,
                               str(amcache.os_version_at_install_time), str(amcache.bundle_manifest_path),
                               str(amcache.hide_in_control_panel_flag), str(amcache.inboxmodernapp),
                               str(amcache.language_code), str(amcache.manifest_path),
                               str(amcache.msi_package_code), str(amcache.msi_product_code),
                               str(amcache.package_full_name), str(amcache.program_id),
                               str(amcache.program_instance_id), str(amcache.uninstall_registry_key_path),
                               str(amcache.root_dir_path), str(amcache.type), str(amcache.program_source),
                               str(amcache.store_app_type),
                               str(amcache.uninstall_string), backup_flag, ', '.join(amcache.source_location)]))
                query = "Insert into lv1_os_win_reg_amcache_program values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"
                if len(insert_data) > 0:
                    configuration.cursor.bulk_execute(query, insert_data)

            # Installed Program
            if backup_flag != 'Backup-RegBack' and reg_software != '':
                print(f'[{self.print_now_time()}] [MODULE]: Registry - Installed Program')
                count = 0
                for reg_nt in reg_nt_list:
                    insert_data = []
                    if count == 0:
                        for program in ip.INSTALLEDPROGRAMS(reg_software, reg_nt[0]):
                            key_last_updated_time = configuration.apply_time_zone(str(program.key_last_updated_time),
                                                                                  knowledge_base.time_zone)
                            insert_data.append(tuple(
                                [par_id, configuration.case_id, configuration.evidence_id, str(program.program_name),
                                 str(program.company), str(program.created_date), key_last_updated_time,
                                 str(program.install_size), str(program.version),
                                 str(program.potential_location), str(reg_nt[1]), backup_flag,
                                 ', '.join(program.source_location)]))
                        query = "Insert into lv1_os_win_reg_installed_program values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"
                        if len(insert_data) > 0:
                            configuration.cursor.bulk_execute(query, insert_data)
                        count = count + 1
                    else:
                        for program in ip.INSTALLEDPROGRAMS('', reg_nt[0]):
                            key_last_updated_time = configuration.apply_time_zone(str(program.key_last_updated_time),
                                                                                  knowledge_base.time_zone)
                            insert_data.append(tuple(
                                [par_id, configuration.case_id, configuration.evidence_id, str(program.program_name),
                                 str(program.company), str(program.created_date), key_last_updated_time,
                                 str(program.install_size), str(program.version),
                                 str(program.potential_location), str(reg_nt[1]), backup_flag,
                                 ', '.join(program.source_location)]))
                        query = "Insert into lv1_os_win_reg_installed_program values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"
                        if len(insert_data) > 0:
                            configuration.cursor.bulk_execute(query, insert_data)
                        count = count + 1

            # OS Information
            if reg_software != '' and reg_system != '':
                print(f'[{self.print_now_time()}] [MODULE]: Registry - OS Information')
                insert_data = []
                for op_system in oi.OSINFO(reg_software, reg_system):
                    install_time = configuration.apply_time_zone(str(op_system.install_time), knowledge_base.time_zone)
                    last_shutdown_time = configuration.apply_time_zone(str(op_system.last_shutdown_time),
                                                                       knowledge_base.time_zone)
                    insert_data.append(
                        tuple([par_id, configuration.case_id, configuration.evidence_id,
                               str(op_system.operating_system),
                               str(op_system.release_id), str(op_system.version_number),
                               install_time, str(op_system.product_key), str(op_system.owner),
                               str(op_system.display_computer_name), str(op_system.computer_name),
                               str(op_system.dhcp_dns_server),
                               str(op_system.operating_system_version), str(op_system.build_number),
                               str(op_system.product_id),
                               str(op_system.last_service_pack), str(op_system.organization), last_shutdown_time,
                               str(op_system.system_root), str(op_system.path), str(op_system.last_access_time_flag),
                               str(op_system.timezone_utc), str(op_system.display_timezone_name), backup_flag,
                               ', '.join(op_system.source_location)]))
                query = "Insert into lv1_os_win_reg_os_information values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"
                if len(insert_data) > 0:
                    configuration.cursor.bulk_execute(query, insert_data)

            # USB Device
            if reg_software != '' and reg_system != '':
                print(f'[{self.print_now_time()}] [MODULE]: Registry - USB Device')
                insert_data = []
                for usb in ud.USBDEVICES(reg_software, reg_system, setupapi_data):
                    last_connected_time = configuration.apply_time_zone(str(usb.last_connected_time),
                                                                        knowledge_base.time_zone)
                    first_connected_time = configuration.apply_time_zone(str(usb.first_connected_time),
                                                                         knowledge_base.time_zone)
                    first_connected_since_reboot_time = configuration.apply_time_zone(
                        str(usb.first_connected_since_reboot_time),
                        knowledge_base.time_zone)
                    driver_install_time = configuration.apply_time_zone(str(usb.driver_install_time),
                                                                        knowledge_base.time_zone)
                    first_install_time = configuration.apply_time_zone(str(usb.first_install_time),
                                                                       knowledge_base.time_zone)
                    last_insertion_time = configuration.apply_time_zone(str(usb.last_insertion_time),
                                                                        knowledge_base.time_zone)
                    last_removal_time = configuration.apply_time_zone(str(usb.last_removal_time),
                                                                      knowledge_base.time_zone)
                    insert_data.append(
                        tuple([par_id, configuration.case_id, configuration.evidence_id, str(usb.device_class_id),
                               str(usb.serial_number), str(usb.type), last_connected_time,
                               str(usb.device_description), str(usb.friendly_name),
                               str(usb.manufacturer), str(usb.last_assigned_drive_letter), str(usb.volume_GUID),
                               str(usb.volume_serial_number_decimal), str(usb.volume_serial_number_hex),
                               str(usb.associated_user_accounts), first_connected_time,
                               first_connected_since_reboot_time, driver_install_time,
                               first_install_time, last_insertion_time, last_removal_time,
                               backup_flag, ', '.join(usb.source_location)]))
                query = "Insert into lv1_os_win_reg_usb_device values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"
                if len(insert_data) > 0:
                    configuration.cursor.bulk_execute(query, insert_data)

            # User Account
            if reg_sam != '' and reg_software != '':
                print(f'[{self.print_now_time()}] [MODULE]: Registry - User Account')
                insert_data = []
                for user in ua.USERACCOUNTS(reg_sam, reg_software):
                    account_created_time = configuration.apply_time_zone(str(user.account_created_time),
                                                                         knowledge_base.time_zone)
                    last_login_time = configuration.apply_time_zone(str(user.last_login_time), knowledge_base.time_zone)
                    last_password_change_time = configuration.apply_time_zone(str(user.last_password_change_time),
                                                                              knowledge_base.time_zone)
                    last_incorrect_password_login_time = configuration.apply_time_zone(
                        str(user.last_incorrect_password_login_time), knowledge_base.time_zone)
                    insert_data.append(
                        tuple([par_id, configuration.case_id, configuration.evidence_id, str(user.user_name),
                               str(user.full_name), str(user.type_of_user), str(user.account_description),
                               str(user.security_identifier), str(user.user_group),
                               str(user.login_script), str(user.profile_path), account_created_time, last_login_time,
                               last_password_change_time, last_incorrect_password_login_time, str(user.login_count),
                               str(user.account_disabled), str(user.password_required), str(user.password_hint),
                               str(user.lm_hash), str(user.ntlm_hash), backup_flag, ', '.join(user.source_location)]))
                query = "Insert into lv1_os_win_reg_user_account values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"
                if len(insert_data) > 0:
                    configuration.cursor.bulk_execute(query, insert_data)

            # Known DLL
            if reg_system != '':
                print(f'[{self.print_now_time()}] [MODULE]: Registry - Known DLL')
                insert_data = []
                for dll in kd.KNOWNDLL(reg_system):
                    modified_time = configuration.apply_time_zone(str(dll.modified_time), knowledge_base.time_zone)
                    insert_data.append(
                        tuple([par_id, configuration.case_id, configuration.evidence_id, str(dll.file_name),
                               str(dll.dll_directory), str(dll.dll_directory_32), modified_time, backup_flag,
                               ', '.join(dll.source_location)]))
                query = "Insert into lv1_os_win_reg_known_dll values (%s, %s, %s, %s, %s, %s, %s, %s, %s);"
                if len(insert_data) > 0:
                    configuration.cursor.bulk_execute(query, insert_data)

            # MAC Address
            if reg_system != '':
                print(f'[{self.print_now_time()}] [MODULE]: Registry - MAC Address')
                if len(ma.MACADDRESS(reg_system)) != 0:
                    insert_data = []
                    for address in ma.MACADDRESS(reg_system):
                        insert_data.append(
                            tuple([par_id, configuration.case_id, configuration.evidence_id, str(address.mac_address),
                                   str(address.description), backup_flag, ', '.join(address.source_location)]))
                    query = "Insert into lv1_os_win_reg_mac_address values (%s, %s, %s, %s, %s, %s, %s);"
                    if len(insert_data) > 0:
                        configuration.cursor.bulk_execute(query, insert_data)

            # Shim Cache
            if reg_system != '':
                print(f'[{self.print_now_time()}] [MODULE]: Registry - Shim Cache')
                insert_data = []
                for cache in sc.SHIMCACHE(reg_system):
                    modified_time = configuration.apply_time_zone(str(cache.modified_time), knowledge_base.time_zone)
                    insert_data.append(
                        tuple([par_id, configuration.case_id, configuration.evidence_id, str(cache.file_name),
                               str(cache.file_path), modified_time, backup_flag,
                               ', '.join(cache.source_location)]))
                query = "Insert into lv1_os_win_reg_shim_cache values (%s, %s, %s, %s, %s, %s, %s, %s);"
                if len(insert_data) > 0:
                    configuration.cursor.bulk_execute(query, insert_data)

            # Network Interface
            if reg_system != '':
                print(f'[{self.print_now_time()}] [MODULE]: Registry - Network Interface')
                insert_data = []
                for network in ni.NETWORKINTERFACE(reg_system):
                    lease_obtained_time = configuration.apply_time_zone(str(network.lease_obtained_time),
                                                                        knowledge_base.time_zone)
                    lease_terminate_time = configuration.apply_time_zone(str(network.lease_terminate_time),
                                                                         knowledge_base.time_zone)
                    t1 = configuration.apply_time_zone(str(network.t1), knowledge_base.time_zone)
                    t2 = configuration.apply_time_zone(str(network.t2), knowledge_base.time_zone)
                    insert_data.append(
                        tuple([par_id, configuration.case_id, configuration.evidence_id, str(network.enable_dhcp),
                               str(network.ipaddress), str(network.dhcp_ipaddress),
                               str(network.dhcp_subnetmask), str(network.dhcp_server),
                               str(network.dhcp_connforcebroadcastflag), str(network.dhcp_domain),
                               str(network.dhcp_name_server), str(network.dhcp_default_gateway),
                               str(network.dhcp_subnetmaskopt), str(network.dhcp_interfaceoptions),
                               str(network.dhcp_gatewayhardware), str(network.dhcp_gatewayhardwarecount),
                               str(network.lease), lease_obtained_time, lease_terminate_time, t1, t2,
                               str(network.address_type),
                               str(network.isservernapaware), str(network.registeradaptername),
                               str(network.registrationenabled), backup_flag, ', '.join(network.source_location)]))
                query = "Insert into lv1_os_win_reg_network_interface values " \
                        "(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"
                if len(insert_data) > 0:
                    configuration.cursor.bulk_execute(query, insert_data)

            # Network Profile
            if reg_software != '':
                print(f'[{self.print_now_time()}] [MODULE]: Registry - Network Profile')
                insert_data = []
                for network in np.NETWORKPROFILE(reg_software):
                    date_created = configuration.apply_time_zone(str(network.datecreated), knowledge_base.time_zone)
                    date_lst_connected = configuration.apply_time_zone(str(network.datelstconnected),
                                                                       knowledge_base.time_zone)
                    insert_data.append(
                        tuple([par_id, configuration.case_id, configuration.evidence_id, str(network.profile_name),
                               str(network.profile_guid), str(network.description),
                               date_created, date_lst_connected, str(network.dns),
                               str(network.default_gateway_mac), backup_flag, ', '.join(network.source_location)]))
                query = "Insert into lv1_os_win_reg_network_profile values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"
                if len(insert_data) > 0:
                    configuration.cursor.bulk_execute(query, insert_data)

            # File Connection
            if reg_software != '':
                print(f'[{self.print_now_time()}] [MODULE]: Registry - File Connection')
                insert_data = []
                for file in fc.FILECCONNECTION(reg_software):
                    modified_time = configuration.apply_time_zone(str(file.modified_time), knowledge_base.time_zone)
                    insert_data.append(
                        tuple([par_id, configuration.case_id, configuration.evidence_id, str(file.file_name),
                               str(file.file_path), str(file.command), str(file.file_type), modified_time,
                               backup_flag, ', '.join(file.source_location)]))
                query = "Insert into lv1_os_win_reg_file_connection values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"
                if len(insert_data) > 0:
                    configuration.cursor.bulk_execute(query, insert_data)

            # System service
            if reg_system != '':
                print(f'[{self.print_now_time()}] [MODULE]: Registry - System service')
                insert_data = []
                for service in ss.SYSTEMSERVICE(reg_system):
                    modified_time = configuration.apply_time_zone(str(service.modified_time), knowledge_base.time_zone)
                    insert_data.append(
                        tuple([par_id, configuration.case_id, configuration.evidence_id, str(service.service_name),
                               str(service.service_type), str(service.start_type),
                               str(service.service_location), str(service.groups), str(service.display_name),
                               str(service.dependancy), str(service.user_account), str(service.description),
                               str(service.service_detail_information), str(service.host_flag),
                               str(service.host_service), str(service.hosted_service_parameter), modified_time,
                               str(service.error_control),
                               str(service.tag), backup_flag, ', '.join(service.source_location)]))
                query = "Insert into lv1_os_win_reg_system_service values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"
                if len(insert_data) > 0:
                    configuration.cursor.bulk_execute(query, insert_data)

            # User Assist
            if backup_flag != 'Backup-RegBack' and len(reg_nt_list) != 0:
                print(f'[{self.print_now_time()}] [MODULE]: Registry - User Assist')
                for reg_nt in reg_nt_list:
                    insert_data = []
                    for user in u.USERASSIST(reg_nt[0]):
                        last_run_time = configuration.apply_time_zone(str(user.last_run_time), knowledge_base.time_zone)
                        insert_data.append(
                            tuple([par_id, configuration.case_id, configuration.evidence_id, str(user.file_name),
                                   str(user.type), str(user.userassist_entry_number), str(user.program_run_count),
                                   last_run_time, str(user.focus_count), str(user.focus_seconds), str(reg_nt[1]),
                                   backup_flag, ', '.join(user.source_location)]))
                    query = "Insert into lv1_os_win_reg_user_assist values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"
                    if len(insert_data) > 0:
                        configuration.cursor.bulk_execute(query, insert_data)

            # MUI Cache
            if backup_flag != 'Backup-RegBack' and len(reg_usrclass_list) != 0:
                print(f'[{self.print_now_time()}] [MODULE]: Registry - MUI Cache')
                for reg_usrclass in reg_usrclass_list:
                    insert_data = []
                    for cache in mc.MUICACHE(reg_usrclass[0]):
                        insert_data.append(
                            tuple([par_id, configuration.case_id, configuration.evidence_id, str(cache.file_name),
                                   str(cache.file_path), str(cache.data), str(reg_usrclass[1]), backup_flag,
                                   ', '.join(cache.source_location)]))
                    query = "Insert into lv1_os_win_reg_mui_cache values (%s, %s, %s, %s, %s, %s, %s, %s, %s);"
                    if len(insert_data) > 0:
                        configuration.cursor.bulk_execute(query, insert_data)

            # Network Drive
            if backup_flag != 'Backup-RegBack' and len(reg_nt_list) != 0:
                print(f'[{self.print_now_time()}] [MODULE]: Registry - Network Drive')
                for reg_nt in reg_nt_list:
                    insert_data = []
                    for drive in nd.NETWORKDRIVE(reg_nt[0]):
                        modified_time = configuration.apply_time_zone(str(drive.modified_time),
                                                                      knowledge_base.time_zone)
                        insert_data.append(
                            tuple([par_id, configuration.case_id, configuration.evidence_id,
                                   str(drive.network_drive_name), modified_time, str(drive.ordering), str(reg_nt[1]),
                                   backup_flag, ', '.join(drive.source_location)]))
                    query = "Insert into lv1_os_win_reg_network_drive values (%s, %s, %s, %s, %s, %s, %s, %s, %s);"
                    if len(insert_data) > 0:
                        configuration.cursor.bulk_execute(query, insert_data)

            # Recent Docs
            if backup_flag != 'Backup-RegBack' and len(reg_nt_list) != 0:
                print(f'[{self.print_now_time()}] [MODULE]: Registry - Recent Docs')
                for reg_nt in reg_nt_list:
                    insert_data = []
                    for doc in rd.RECENTDOCS(reg_nt[0]):
                        modified_time = configuration.apply_time_zone(str(doc.modified_time), knowledge_base.time_zone)
                        insert_data.append(
                            tuple([par_id, configuration.case_id, configuration.evidence_id, str(doc.file_folder_name),
                                   str(doc.file_folder_link), modified_time, str(doc.registry_order), str(doc.value),
                                   str(reg_nt[1]), backup_flag, ', '.join(doc.source_location)]))
                    query = "Insert into lv1_os_win_reg_recent_docs values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"
                    if len(insert_data) > 0:
                        configuration.cursor.bulk_execute(query, insert_data)

            # Run command
            if backup_flag != 'Backup-RegBack' and len(reg_nt_list) != 0:
                print(f'[{self.print_now_time()}] [MODULE]: Registry - Run command')
                for reg_nt in reg_nt_list:
                    insert_data = []
                    for command in rc.RUNCOMMAND(reg_nt[0]):
                        modified_time = configuration.apply_time_zone(str(command.modified_time),
                                                                      knowledge_base.time_zone)
                        insert_data.append(
                            tuple([par_id, configuration.case_id, configuration.evidence_id, str(command.command),
                                   modified_time, str(command.ordering), str(reg_nt[1]), backup_flag,
                                   ', '.join(command.source_location)]))
                    query = "Insert into lv1_os_win_reg_run_command values (%s, %s, %s, %s, %s, %s, %s, %s, %s);"
                    if len(insert_data) > 0:
                        configuration.cursor.bulk_execute(query, insert_data)

            # Search keyword
            if backup_flag != 'Backup-RegBack' and len(reg_nt_list) != 0:
                print(f'[{self.print_now_time()}] [MODULE]: Registry - Search keyword')
                for reg_nt in reg_nt_list:
                    insert_data = []
                    for keyword in sk.SEARCHKEYWORD(reg_nt[0]):
                        modified_time = configuration.apply_time_zone(str(keyword.modified_time),
                                                                      knowledge_base.time_zone)
                        insert_data.append(
                            tuple([par_id, configuration.case_id, configuration.evidence_id, str(keyword.keyword),
                                   modified_time, str(keyword.ordering), str(reg_nt[1]), backup_flag,
                                   ', '.join(keyword.source_location)]))
                    query = "Insert into lv1_os_win_reg_search_keyword values (%s, %s, %s, %s, %s, %s, %s, %s, %s);"
                    if len(insert_data) > 0:
                        configuration.cursor.bulk_execute(query, insert_data)

            # Start list
            if backup_flag != 'Backup-RegBack' and reg_software != '' and len(reg_nt_list) != 0:
                print(f'[{self.print_now_time()}] [MODULE]: Registry - Start list')
                count = 0
                for reg_nt in reg_nt_list:
                    insert_data = []
                    if count == 0:
                        for start in s.START(reg_software, reg_nt[0]):
                            modified_time = configuration.apply_time_zone(str(start.modified_time),
                                                                          knowledge_base.time_zone)
                            insert_data.append(
                                tuple(
                                    [par_id, configuration.case_id, configuration.evidence_id, str(start.program_name),
                                     str(start.path), modified_time, str(start.type), str(reg_nt[1]),
                                     backup_flag, ', '.join(start.source_location)]))
                        query = "Insert into lv1_os_win_reg_start_list values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"
                        if len(insert_data) > 0:
                            configuration.cursor.bulk_execute(query, insert_data)
                        count = count + 1
                    else:
                        for start in s.START('', reg_nt[0]):
                            modified_time = configuration.apply_time_zone(str(start.modified_time),
                                                                          knowledge_base.time_zone)
                            insert_data.append(
                                tuple(
                                    [par_id, configuration.case_id, configuration.evidence_id, str(start.program_name),
                                     str(start.path), modified_time, str(start.type), str(reg_nt[1]),
                                     backup_flag, ', '.join(start.source_location)]))
                        query = "Insert into lv1_os_win_reg_start_list values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"
                        if len(insert_data) > 0:
                            configuration.cursor.bulk_execute(query, insert_data)
                        count = count + 1

            # MRU Foloder
            if backup_flag != 'Backup-RegBack' and len(reg_nt_list) != 0:
                print(f'[{self.print_now_time()}] [MODULE]: Registry - MRU Folder')
                for reg_nt in reg_nt_list:
                    insert_data = []
                    for mru in mf.MRUFOLDER(reg_nt[0]):
                        modified_time = configuration.apply_time_zone(str(mru.modified_time), knowledge_base.time_zone)
                        insert_data.append(
                            tuple([par_id, configuration.case_id, configuration.evidence_id, str(mru.program_name),
                                   str(mru.accessed_folder), modified_time, str(mru.registry_order),
                                   str(mru.value), str(reg_nt[1]), backup_flag,
                                   ', '.join(mru.source_location)]))
                    query = "Insert into lv1_os_win_reg_mru_folder values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"
                    if len(insert_data) > 0:
                        configuration.cursor.bulk_execute(query, insert_data)

            # MRU Open File
            if backup_flag != 'Backup-RegBack' and len(reg_nt_list) != 0:
                print(f'[{self.print_now_time()}] [MODULE]: Registry - MRU File')
                for reg_nt in reg_nt_list:
                    insert_data = []
                    for mru in mof.MRUOPENEDFILE(reg_nt[0]):
                        modified_time = configuration.apply_time_zone(str(mru.modified_time), knowledge_base.time_zone)
                        insert_data.append(
                            tuple([par_id, configuration.case_id, configuration.evidence_id, str(mru.file_name),
                                   str(mru.file_path), modified_time,
                                   str(mru.extension), str(mru.value), str(reg_nt[1]), backup_flag,
                                   ', '.join(mru.source_location)]))
                    query = "Insert into lv1_os_win_reg_mru_file values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"
                    if len(insert_data) > 0:
                        configuration.cursor.bulk_execute(query, insert_data)

            if reg_am is not '':
                reg_am.registry_file.file_object.close()
            if reg_am_log1 is not '':
                reg_am_log1.close()
            if reg_am_log2 is not '':
                reg_am_log2.close()
            if reg_system is not '':
                reg_system.registry_file.file_object.close()
            if reg_system_log1 is not '':
                reg_system_log1.close()
            if reg_system_log2 is not '':
                reg_system_log2.close()
            if reg_software is not '':
                reg_software.registry_file.file_object.close()
            if reg_software_log1 is not '':
                reg_software_log1.close()
            if reg_software_log2 is not '':
                reg_software_log2.close()
            if reg_sam is not '':
                reg_sam.registry_file.file_object.close()
            if reg_sam_log1 is not '':
                reg_sam_log1.close()
            if reg_sam_log2 is not '':
                reg_sam_log2.close()
            if reg_usrclass_list is not '':
                for reg_usrclass in reg_usrclass_list:
                    reg_usrclass[0].registry_file.file_object.close()
            if reg_usr_log1 is not '':
                reg_usr_log1.close()
            if reg_usr_log2 is not '':
                reg_usr_log2.close()
            if reg_nt_list is not '':
                for reg_nt in reg_nt_list:
                    reg_nt[0].registry_file.file_object.close()
            if reg_nt_log1 is not '':
                reg_nt_log1.close()
            if reg_nt_log2 is not '':
                reg_nt_log2.close()


manager.ModulesManager.RegisterModule(RegistryConnector)
