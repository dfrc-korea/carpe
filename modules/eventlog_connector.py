# -*- coding: utf-8 -*-
"""module for Eventlog."""
import os
from modules import manager
from modules import interface

from modules.Eventlog import lv1_os_win_evt_total as et
from modules.Eventlog import lv1_os_win_event_logs_usb_devices as ud
from modules.Eventlog import lv1_os_win_event_logs_antiforensics as af
from modules.Eventlog import lv1_os_win_event_logs_applications as app
from modules.Eventlog import lv1_os_win_event_logs_dns as dn
from modules.Eventlog import lv1_os_win_event_logs_file_handling as fh
from modules.Eventlog import lv1_os_win_event_logs_logonoff as logon
from modules.Eventlog import lv1_os_win_event_logs_ms_alerts as ms
from modules.Eventlog import lv1_os_win_event_logs_msi_installer as msi
from modules.Eventlog import lv1_os_win_event_logs_network as nt
from modules.Eventlog import lv1_os_win_event_logs_others as ot
from modules.Eventlog import lv1_os_win_event_logs_pconoff as pc
from modules.Eventlog import lv1_os_win_event_logs_printer as pr
from modules.Eventlog import lv1_os_win_event_logs_process as pro
from modules.Eventlog import lv1_os_win_event_logs_registry_handling as reg
from modules.Eventlog import lv1_os_win_event_logs_remoteonoff as rem
from modules.Eventlog import lv1_os_win_event_logs_screen_saver as ss
from modules.Eventlog import lv1_os_win_event_logs_shared_folder as sf
from modules.Eventlog import lv1_os_win_event_logs_sleeponoff as sle
from modules.Eventlog import lv1_os_win_event_logs_task_scheduler as ts
from modules.Eventlog import lv1_os_win_event_logs_telemetry as tele
from modules.Eventlog import lv1_os_win_event_logs_time_changed as tc


class EventlogConnector(interface.ModuleConnector):
    NAME = 'eventlog_connector'
    DESCRIPTION = 'Module for Eventlog'

    _plugin_classes = {}

    def __init__(self):
        super(EventlogConnector, self).__init__()

    def Connect(self, par_id, configuration, source_path_spec, knowledge_base):
        try:
            this_file_path = os.path.dirname(
                os.path.abspath(__file__)) + os.sep + 'schema' + os.sep + 'eventlog' + os.sep

            # Total yaml 파일 리스트
            total_yaml_list = [this_file_path + 'lv1_os_win_evt_total.yaml']
            # Total 테이블 리스트
            total_table_list = ['lv1_os_win_evt_total']

            if not self.check_table_from_yaml(configuration, total_yaml_list, total_table_list):
                return False

            # 모든 yaml 파일 리스트
            yaml_list = [this_file_path + 'lv1_os_win_event_logs_antiforensics.yaml',
                         this_file_path + 'lv1_os_win_event_logs_applications.yaml',
                         this_file_path + 'lv1_os_win_event_logs_dns.yaml',
                         this_file_path + 'lv1_os_win_event_logs_file_handling.yaml',
                         this_file_path + 'lv1_os_win_event_logs_logonoff.yaml',
                         this_file_path + 'lv1_os_win_event_logs_ms_alerts.yaml',
                         this_file_path + 'lv1_os_win_event_logs_msi_installer.yaml',
                         this_file_path + 'lv1_os_win_event_logs_network.yaml',
                         this_file_path + 'lv1_os_win_event_logs_others.yaml',
                         this_file_path + 'lv1_os_win_event_logs_pconoff.yaml',
                         this_file_path + 'lv1_os_win_event_logs_printer.yaml',
                         this_file_path + 'lv1_os_win_event_logs_process.yaml',
                         this_file_path + 'lv1_os_win_event_logs_registry_handling.yaml',
                         this_file_path + 'lv1_os_win_event_logs_remoteonoff.yaml',
                         this_file_path + 'lv1_os_win_event_logs_screen_saver.yaml',
                         this_file_path + 'lv1_os_win_event_logs_shared_folder.yaml',
                         this_file_path + 'lv1_os_win_event_logs_task_scheduler.yaml',
                         this_file_path + 'lv1_os_win_event_logs_telemetry.yaml',
                         this_file_path + 'lv1_os_win_event_logs_time_changed.yaml',
                         this_file_path + 'lv1_os_win_event_logs_usb_devices.yaml',
                         this_file_path + 'lv1_os_win_event_logs_sleeponoff.yaml'
                         ]

            # 모든 테이블 리스트
            table_list = ['lv1_os_win_event_logs_antiforensics',
                          'lv1_os_win_event_logs_applications',
                          'lv1_os_win_event_logs_dns',
                          'lv1_os_win_event_logs_file_handling',
                          'lv1_os_win_event_logs_logonoff',
                          'lv1_os_win_event_logs_ms_alerts',
                          'lv1_os_win_event_logs_msi_installer',
                          'lv1_os_win_event_logs_network',
                          'lv1_os_win_event_logs_others',
                          'lv1_os_win_event_logs_pconoff',
                          'lv1_os_win_event_logs_printer',
                          'lv1_os_win_event_logs_process',
                          'lv1_os_win_event_logs_registry_handling',
                          'lv1_os_win_event_logs_remoteonoff',
                          'lv1_os_win_event_logs_screen_saver',
                          'lv1_os_win_event_logs_shared_folder',
                          'lv1_os_win_event_logs_task_scheduler',
                          'lv1_os_win_event_logs_telemetry',
                          'lv1_os_win_event_logs_time_changed',
                          'lv1_os_win_event_logs_usb_devices',
                          'lv1_os_win_event_logs_sleeponoff'
                          ]

            if not self.check_table_from_yaml(configuration, yaml_list, table_list):
                return False

            #query_separator = "/" if source_path_spec.location == "/" else source_path_spec.location * 2
            query_separator = self.GetQuerySeparator(source_path_spec, configuration)
            path_separator = self.GetPathSeparator(source_path_spec)

            if configuration.source_type == 'directory' or 'file':
                query = f"SELECT name, parent_path, extension FROM file_info WHERE (par_id='{par_id}') " \
                        f"and sig_type = 'evtx' " \

            else:
                query = f"SELECT name, parent_path, extension FROM file_info WHERE (par_id='{par_id}') " \
                        f"and extension = 'evtx' " \
                        f"and parent_path like 'root{query_separator}Windows{query_separator}" \
                        f"System32{query_separator}winevt{query_separator}Logs'"

            eventlog_files = configuration.cursor.execute_query_mul(query)

            if len(eventlog_files) == 0:
                # print("There are no eventlog files")
                return False

            eventlog_file_list = ['Security.evtx', 'System.evtx', 'Application.evtx',
                                  'Microsoft-Windows-Application-Experience%4Program-Compatibility-Assistant.evtx',
                                  'Microsoft-Windows-DNS-Client%4Operational.evtx',
                                  'Microsoft-Windows-User Profile Service%4Operational.evtx',
                                  'OAlerts.evtx', 'Microsoft-Windows-NetworkProfile%4Operational.evtx',
                                  'Microsoft-Windows-PrintService%4Operational.evtx',
                                  'Microsoft-Windows-TerminalServices-LocalSessionManager%4Operational.evtx',
                                  'Microsoft-Windows-SmbClient%4Connectivity.evtx',
                                  'Microsoft-Windows-TaskScheduler%4Operational.evtx',
                                  'Microsoft-Windows-Application-Experience%4Program-Telemetry.evtx',
                                  'Microsoft-Windows-DateTimeControlPanel%4Operational.evtx',
                                  'Microsoft-Windows-Partition%4Diagnostic.evtx',
                                  'Microsoft-Windows-Storage-ClassPnP%4Operational.evtx']
            insert_data = []
            for eventlog in eventlog_files:
                if eventlog[0] in eventlog_file_list:
                    eventlog_path = eventlog[1][eventlog[1].find(path_separator):] + path_separator + eventlog[0]  # document full path
                    fileName = eventlog[0]

                    if configuration.source_type == 'directory' or 'file':
                        fn = eventlog_path
                    else:
                        output_path = configuration.root_tmp_path + os.sep + configuration.case_id + os.sep + \
                                      configuration.evidence_id + os.sep + par_id

                        if not os.path.exists(output_path):
                            os.mkdir(output_path)

                        self.ExtractTargetFileToPath(
                            source_path_spec=source_path_spec,
                            configuration=configuration,
                            file_path=eventlog_path,
                            output_path=output_path)

                        fn = output_path + os.path.sep + fileName

                    # Eventlog Total
                    print(f'[{self.print_now_time()}] [MODULE]: Eventlog - Total - ' + fn.split(os.sep)[-1])
                    for eventlog in et.EventlogTotal(eventlog_path, fn):
                        insert_data.append(tuple(
                            [par_id, configuration.case_id, configuration.evidence_id, str(eventlog.event_id),
                             configuration.apply_time_zone(str(eventlog.time_created), knowledge_base.time_zone),
                             str(eventlog.source), str(eventlog.data),
                             str(eventlog.user_sid)]))
            query = "Insert into lv1_os_win_evt_total values (%s, %s, %s, %s, %s, %s, %s, %s);"
            if len(insert_data) > 0:
                configuration.cursor.bulk_execute(query, insert_data)
            # EVENTLOGUSBDEVICES
            print(f'[{self.print_now_time()}] [MODULE]: Eventlog - EVENTLOGUSBDEVICES')
            insert_data = []
            for usb in ud.EVENTLOGUSBDEVICES(configuration):
                insert_data.append(tuple(
                    [par_id, configuration.case_id, configuration.evidence_id, str(usb.task),
                     str(usb.time),
                     str(usb.device_instance_id), str(usb.description), str(usb.manufacturer), str(usb.model),
                     str(usb.revision), str(usb.serial_number), str(usb.parentid), str(usb.user_sid),
                     str(usb.event_id), str(usb.source), str(usb.event_id_description)]))
            query = "Insert into lv1_os_win_event_logs_usb_devices values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"
            if len(insert_data) > 0:
                configuration.cursor.bulk_execute(query, insert_data)

            # EVENTLOGANTIFORENSICS
            print(f'[{self.print_now_time()}] [MODULE]: Eventlog - EVENTLOGANTIFORENSICS')
            insert_data = []
            for antiforensics in af.EVENTLOGANTIFORENSICS(configuration):
                insert_data.append(tuple(
                    [par_id, configuration.case_id, configuration.evidence_id, str(antiforensics.task),
                     str(antiforensics.time),
                     str(antiforensics.user_sid), str(antiforensics.event_id),
                     str(antiforensics.source), str(antiforensics.event_id_description)]))
            query = "Insert into lv1_os_win_event_logs_antiforensics values (%s, %s, %s, %s, %s, %s, %s, %s, %s);"
            if len(insert_data) > 0:
                configuration.cursor.bulk_execute(query, insert_data)

            # EVENTLOGAPPLICATIONS
            print(f'[{self.print_now_time()}] [MODULE]: Eventlog - EVENTLOGAPPLICATIONS')
            insert_data = []
            for applications in app.EVENTLOGAPPLICATIONS(configuration):
                insert_data.append(tuple(
                    [par_id, configuration.case_id, configuration.evidence_id, str(applications.task),
                     str(applications.time),
                     str(applications.application_name), str(applications.path),
                     str(applications.resolver_name), str(applications.user_sid), str(applications.event_id),
                     str(applications.source), str(applications.event_id_description)]))
            query = "Insert into lv1_os_win_event_logs_applications values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"
            if len(insert_data) > 0:
                configuration.cursor.bulk_execute(query, insert_data)

            # EVENTLOGDNS
            print(f'[{self.print_now_time()}] [MODULE]: Eventlog - EVENTLOGDNS')
            insert_data = []
            for dns in dn.EVENTLOGDNS(configuration):
                insert_data.append(tuple(
                    [par_id, configuration.case_id, configuration.evidence_id, str(dns.task),
                     str(dns.time),
                     str(dns.query_name), str(dns.user_sid), str(dns.event_id), str(dns.source),
                     str(dns.event_id_description)]))
            query = "Insert into lv1_os_win_event_logs_dns values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"
            if len(insert_data) > 0:
                configuration.cursor.bulk_execute(query, insert_data)

            # EVENTLOGFILEHANDLING
            print(f'[{self.print_now_time()}] [MODULE]: Eventlog - EVENTLOGFILEHANDLING')
            insert_data = []
            for file_handling in fh.EVENTLOGFILEHANDLING(configuration):
                insert_data.append(tuple(
                    [par_id, configuration.case_id, configuration.evidence_id, str(file_handling.task),
                     str(file_handling.time),
                     str(file_handling.file_name), str(file_handling.user_sid),
                     str(file_handling.event_id), str(file_handling.source), str(file_handling.event_id_description)]))
            query = "Insert into lv1_os_win_event_logs_file_handling values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"
            if len(insert_data) > 0:
                configuration.cursor.bulk_execute(query, insert_data)

            # EVENTLOGONOFF
            print(f'[{self.print_now_time()}] [MODULE]: Eventlog - EVENTLOGONOFF')
            insert_data = []
            for event in logon.EVENTLOGONOFF(configuration):
                insert_data.append(tuple(
                    [par_id, configuration.case_id, configuration.evidence_id, str(event.task),
                     str(event.time),
                     str(event.user_sid), str(event.event_id), str(event.source), str(event.event_id_description)]))
            query = "Insert into lv1_os_win_event_logs_logonoff values (%s, %s, %s, %s, %s, %s, %s, %s, %s);"
            if len(insert_data) > 0:
                configuration.cursor.bulk_execute(query, insert_data)

            # EVENTLOGMSALERTS
            print(f'[{self.print_now_time()}] [MODULE]: Eventlog - EVENTLOGMSALERTS')
            insert_data = []
            for ms_alerts in ms.EVENTLOGMSALERTS(configuration):
                insert_data.append(tuple(
                    [par_id, configuration.case_id, configuration.evidence_id, str(ms_alerts.task),
                     str(ms_alerts.time),
                     str(ms_alerts.program_name), str(ms_alerts.message), str(ms_alerts.error_type),
                     str(ms_alerts.program_version), str(ms_alerts.user_sid), str(ms_alerts.event_id),
                     str(ms_alerts.source), str(ms_alerts.event_id_description)]))
            query = "Insert into lv1_os_win_event_logs_ms_alerts values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"
            if len(insert_data) > 0:
                configuration.cursor.bulk_execute(query, insert_data)

            # EVENTLOGMSIINSTALLER
            print(f'[{self.print_now_time()}] [MODULE]: Eventlog - EVENTLOGMSIINSTALLER')
            insert_data = []
            for msi_installer in msi.EVENTLOGMSIINSTALLER(configuration):
                insert_data.append(tuple(
                    [par_id, configuration.case_id, configuration.evidence_id, str(msi_installer.task),
                     str(msi_installer.time),
                     str(msi_installer.product_name), str(msi_installer.product_version),
                     str(msi_installer.manufacturer), str(msi_installer.user_sid), str(msi_installer.event_id),
                     str(msi_installer.source), str(msi_installer.event_id_description)]))
            query = "Insert into lv1_os_win_event_logs_msi_installer values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"
            if len(insert_data) > 0:
                configuration.cursor.bulk_execute(query, insert_data)

            # EVENTLOGNETWORK
            print(f'[{self.print_now_time()}] [MODULE]: Eventlog - EVENTLOGNETWORK')
            insert_data = []
            for network in nt.EVENTLOGNETWORK(configuration):
                insert_data.append(tuple(
                    [par_id, configuration.case_id, configuration.evidence_id, str(network.task),
                     str(network.time),
                     str(network.network_name), str(network.description), str(network.category), str(network.user_sid),
                     str(network.event_id), str(network.source), str(network.event_id_description)]))
            query = "Insert into lv1_os_win_event_logs_network values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"
            if len(insert_data) > 0:
                configuration.cursor.bulk_execute(query, insert_data)

            # EVENTLOGOTHERS
            print(f'[{self.print_now_time()}] [MODULE]: Eventlog - EVENTLOGOTHERS')
            insert_data = []
            for others in ot.EVENTLOGOTHERS(configuration):
                insert_data.append(tuple(
                    [par_id, configuration.case_id, configuration.evidence_id, str(others.task),
                     str(others.time),
                     str(others.name), str(others.user_sid), str(others.event_id), str(others.source),
                     str(others.event_id_description)]))
            query = "Insert into lv1_os_win_event_logs_others values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"
            if len(insert_data) > 0:
                configuration.cursor.bulk_execute(query, insert_data)

            # EVENTLOGPCONOFF
            print(f'[{self.print_now_time()}] [MODULE]: Eventlog - EVENTLOGPCONOFF')
            insert_data = []
            for event in pc.EVENTLOGPCONOFF(configuration):
                insert_data.append(tuple(
                    [par_id, configuration.case_id, configuration.evidence_id, str(event.task),
                     str(event.time),
                     str(event.user_sid), str(event.event_id), str(event.source), str(event.event_id_description)]))
            query = "Insert into lv1_os_win_event_logs_pconoff values (%s, %s, %s, %s, %s, %s, %s, %s, %s);"
            if len(insert_data) > 0:
                configuration.cursor.bulk_execute(query, insert_data)

            # EVENTLOGPRINTER
            print(f'[{self.print_now_time()}] [MODULE]: Eventlog - EVENTLOGPRINTER')
            insert_data = []
            for printer in pr.EVENTLOGPRINTER(configuration):
                insert_data.append(tuple(
                    [par_id, configuration.case_id, configuration.evidence_id, str(printer.task),
                     str(printer.time),
                     str(printer.location), str(printer.size), str(printer.pages), str(printer.user_sid),
                     str(printer.event_id), str(printer.source), str(printer.event_id_description)]))
            query = "Insert into lv1_os_win_event_logs_printer values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"
            if len(insert_data) > 0:
                configuration.cursor.bulk_execute(query, insert_data)

            # EVENTLOGPROCESS
            print(f'[{self.print_now_time()}] [MODULE]: Eventlog - EVENTLOGPROCESS')
            insert_data = []
            for process in pro.EVENTLOGPROCESS(configuration):
                insert_data.append(tuple(
                    [par_id, configuration.case_id, configuration.evidence_id, str(process.task),
                     str(process.time),
                     str(process.process_name), str(process.user_sid), str(process.event_id), str(process.source),
                     str(process.event_id_description)]))
            query = "Insert into lv1_os_win_event_logs_process values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"
            if len(insert_data) > 0:
                configuration.cursor.bulk_execute(query, insert_data)

            # EVENTLOGREGISTRYHANDLING
            print(f'[{self.print_now_time()}] [MODULE]: Eventlog - EVENTLOGREGISTRYHANDLING')
            insert_data = []
            for registry in reg.EVENTLOGREGISTRYHANDLING(configuration):
                insert_data.append(tuple(
                    [par_id, configuration.case_id, configuration.evidence_id, str(registry.task),
                     str(registry.time),
                     str(registry.registry_path), str(registry.registry_value_name), str(registry.old_value),
                     str(registry.new_value), str(registry.user_sid), str(registry.event_id), str(registry.source),
                     str(registry.event_id_description)]))
            query = "Insert into lv1_os_win_event_logs_registry_handling values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"
            if len(insert_data) > 0:
                configuration.cursor.bulk_execute(query, insert_data)

            # EVENTLOGREMOTEONOFF
            print(f'[{self.print_now_time()}] [MODULE]: Eventlog - EVENTLOGREMOTEONOFF')
            insert_data = []
            for remote in rem.EVENTLOGREMOTEONOFF(configuration):
                insert_data.append(tuple(
                    [par_id, configuration.case_id, configuration.evidence_id, str(remote.task),
                     str(remote.time),
                     str(remote.connection), str(remote.address), str(remote.user_sid), str(remote.event_id),
                     str(remote.source), str(remote.event_id_description)]))
            query = "Insert into lv1_os_win_event_logs_remoteonoff values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"
            if len(insert_data) > 0:
                configuration.cursor.bulk_execute(query, insert_data)

            # EVENTLOGSCREENSAVER
            print(f'[{self.print_now_time()}] [MODULE]: Eventlog - EVENTLOGSCREENSAVER')
            insert_data = []
            for screen_saver in ss.EVENTLOGSCREENSAVER(configuration):
                insert_data.append(tuple(
                    [par_id, configuration.case_id, configuration.evidence_id, str(screen_saver.task),
                     str(screen_saver.time),
                     str(screen_saver.user_sid), str(screen_saver.event_id),
                     str(screen_saver.source), str(screen_saver.event_id_description)]))
            query = "Insert into lv1_os_win_event_logs_screen_saver values (%s, %s, %s, %s, %s, %s, %s, %s, %s);"
            if len(insert_data) > 0:
                configuration.cursor.bulk_execute(query, insert_data)

            # EVENTLOGSHAREDFOLDER
            print(f'[{self.print_now_time()}] [MODULE]: Eventlog - EVENTLOGSHAREDFOLDER')
            insert_data = []
            for shared_folder in sf.EVENTLOGSHAREDFOLDER(configuration):
                insert_data.append(tuple(
                    [par_id, configuration.case_id, configuration.evidence_id, str(shared_folder.task),
                     str(shared_folder.time),
                     str(shared_folder.user_sid), str(shared_folder.event_id),
                     str(shared_folder.source), str(shared_folder.event_id_description)]))
            query = "Insert into lv1_os_win_event_logs_shared_folder values (%s, %s, %s, %s, %s, %s, %s, %s, %s);"
            if len(insert_data) > 0:
                configuration.cursor.bulk_execute(query, insert_data)

            # EVENTLOGSLEEPONOFF
            print(f'[{self.print_now_time()}] [MODULE]: Eventlog - EVENTLOGSLEEPONOFF')
            insert_data = []
            for sleep in sle.EVENTLOGSLEEPONOFF(configuration):
                insert_data.append(tuple(
                    [par_id, configuration.case_id, configuration.evidence_id, str(sleep.task),
                     str(sleep.time_sleep),
                     str(sleep.time_wake),
                     str(sleep.user_sid), str(sleep.event_id), str(sleep.source),
                     str(sleep.event_id_description)]))
            query = "Insert into lv1_os_win_event_logs_sleeponoff values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"
            if len(insert_data) > 0:
                configuration.cursor.bulk_execute(query, insert_data)

            # EVENTLOGTASKSCHEDULER
            print(f'[{self.print_now_time()}] [MODULE]: Eventlog - EVENTLOGTASKSCHEDULER')
            insert_data = []
            for task_scheduler in ts.EVENTLOGTASKSCHEDULER(configuration):
                insert_data.append(tuple(
                    [par_id, configuration.case_id, configuration.evidence_id, str(task_scheduler.task),
                     str(task_scheduler.time),
                     str(task_scheduler.action_name), str(task_scheduler.user_sid),
                     str(task_scheduler.event_id), str(task_scheduler.source),
                     str(task_scheduler.event_id_description)]))
            query = "Insert into lv1_os_win_event_logs_task_scheduler values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"
            if len(insert_data) > 0:
                configuration.cursor.bulk_execute(query, insert_data)

            # EVENTLOGTELEMETRY
            print(f'[{self.print_now_time()}] [MODULE]: Eventlog - EVENTLOGTELEMETRY')
            insert_data = []
            for telemetry in tele.EVENTLOGTELEMETRY(configuration):
                insert_data.append(tuple(
                    [par_id, configuration.case_id, configuration.evidence_id, str(telemetry.task),
                     str(telemetry.time),
                     str(telemetry.program_name), str(telemetry.program_path), str(telemetry.user_sid),
                     str(telemetry.event_id), str(telemetry.source), str(telemetry.event_id_description)]))
            query = "Insert into lv1_os_win_event_logs_telemetry values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"
            if len(insert_data) > 0:
                configuration.cursor.bulk_execute(query, insert_data)

            # EVENTLOGTIMECHANGED
            print(f'[{self.print_now_time()}] [MODULE]: Eventlog - EVENTLOGTIMECHANGED')
            insert_data = []
            for time in tc.EVENTLOGTIMECHANGED(configuration):
                insert_data.append(tuple(
                    [par_id, configuration.case_id, configuration.evidence_id, str(time.task),
                     str(time.time_old),
                     str(time.time_new),
                     str(time.user_sid), str(time.event_id), str(time.source),
                     str(time.event_id_description)]))
            query = "Insert into lv1_os_win_event_logs_time_changed values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"
            if len(insert_data) > 0:
                configuration.cursor.bulk_execute(query, insert_data)

        except Exception as e:
            print(f"[{self.print_now_time()}] Eventlog Connector Error: {e}")


manager.ModulesManager.RegisterModule(EventlogConnector)
