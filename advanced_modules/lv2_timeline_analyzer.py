
import datetime
import os

from advanced_modules import manager
from advanced_modules import interface
from advanced_modules import logger
from dfvfs.lib import definitions as dfvfs_definitions


class LV2TIMELINEAnalyzer(interface.AdvancedModuleAnalyzer):

    NAME = 'lv2_timeline_analyzer'
    DESCRIPTION = 'Module for LV2 Timeline'

    _plugin_classes = {}

    def _convert_timestamp(self, timestamp):
        time = datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%dT%H:%M:%S')
        return time
    def _convert_secs(self, seconds):
        time = datetime.timedelta(seconds=seconds)
        return time
    def _convert_millisecs(self, milliseconds):
        time = datetime.timedelta(milliseconds=milliseconds)
        return time

    def __init__(self):
        super(LV2TIMELINEAnalyzer, self).__init__()

    def Analyze(self, par_id, configuration, source_path_spec, knowledge_base):

        # if par_id is None or par_id == '':
        #     return False
        # else:
        #     if source_path_spec.parent.type_indicator != dfvfs_definitions.TYPE_INDICATOR_TSK_PARTITION:
        #         par_id = configuration.partition_list['p1']
        #     else:
        #         par_id = configuration.partition_list[getattr(source_path_spec.parent, 'location', None)[1:]]

        this_file_path = os.path.dirname(os.path.abspath(__file__)) + os.sep + 'schema' + os.sep
        # 모든 yaml 파일 리스트
        yaml_list = [this_file_path + 'lv2_timeline.yaml']

        # 모든 테이블 리스트
        table_list = ['lv2_timeline']

        # 모든 테이블 생성
        if not self.check_table_from_yaml(configuration, yaml_list, table_list):
            return False

        # todo : 쿼리
        call_log_query = f"SELECT call_date, duration_in_secs, phone_account_address, partner, type " \
                         f"FROM lv1_os_and_basic_app_call_logs" \
                         f" WHERE par_id='{par_id}';"
        mms_query = f"SELECT * FROM lv1_os_and_basic_app_mms" \
                    f" WHERE par_id='{par_id}';"
        sms_query = f"SELECT date, address, body, type, service_center FROM lv1_os_and_basic_app_sms" \
                    f" WHERE par_id='{par_id}';"
        usagestats_query = f"SELECT last_time_active, time_active_in_msecs, package, source " \
                           f"FROM lv1_os_and_basic_app_usagestats_0"\
                           f" WHERE par_id='{par_id}';"
        chrome_download_query = f"SELECT start_time, end_time, download_tab_url, download_path, file_name, os_account, chrome_profile " \
                                f"FROM lv1_app_web_chrome_download"\
                                f" WHERE par_id='{par_id}';"
        chromium_edge_download_query = f"SELECT start_time, end_time, download_tab_url, download_path, file_name, os_account, edge_profile " \
                                       f"FROM lv1_app_web_chromium_edge_download"\
                                       f" WHERE par_id='{par_id}';"
        whale_download_query = f"SELECT start_time, end_time, download_tab_url, download_path, file_name, os_account, whale_profile " \
                               f"FROM lv1_app_web_whale_download"\
                               f" WHERE par_id='{par_id}';"
        opera_download_query = f"SELECT start_time, end_time, download_tab_url, download_path, file_name, os_account, opera_profile " \
                               f"FROM lv1_app_web_opera_download"\
                               f" WHERE par_id='{par_id}';"
        firefox_download_query = f"SELECT start_time, end_time, url, download_path, os_account, firefox_profile_id " \
                                 f"FROM lv1_app_web_firefox_download"\
                                 f" WHERE par_id='{par_id}';"
        reg_usb_query = f"SELECT last_insertion_time, source_location, friendly_name, serial_number, device_description, last_assigned_drive_letter " \
                        f"FROM lv1_os_win_reg_usb_device" \
                        f" WHERE par_id='{par_id}';"
        evt_usb_query = f"SELECT time, manufacturer, model, serial_number, event_id, event_id_description, source " \
                        f"FROM lv1_os_win_event_logs_usb_devices"\
                        f" WHERE par_id='{par_id}';"

        table_query_list = [
            ['lv1_os_and_basic_app_call_logs', call_log_query],
            ['lv1_os_and_basic_app_mms', mms_query],
            ['lv1_os_and_basic_app_sms', sms_query],
            ['lv1_os_and_basic_app_usagestats_0', usagestats_query],
            ['lv1_app_web_chrome_download', chrome_download_query],
            ['lv1_app_web_chromium_edge_download', chromium_edge_download_query],
            ['lv1_app_web_whale_download', whale_download_query],
            ['lv1_app_web_opera_download', opera_download_query],
            ['lv1_app_web_firefox_download', firefox_download_query],
            ['lv1_os_win_reg_usb_device', reg_usb_query],
            ['lv1_os_win_event_logs_usb_devices', evt_usb_query]
        ]

        insert_data = []
        for row in table_query_list:
            if configuration.cursor.check_table_exist(row[0]): # table 있는지 체크
                query = row[1]
                result = configuration.cursor.execute_query_mul(query)

                if len(result) != 0:    # table은 있지만 레코드 없는 경우 체크
                    # print("not yet")

                    if row[0] == 'lv1_os_and_basic_app_call_logs':
                        for value in result:
                            event_type = "Call"
                            event_time = value[0]
                            duration = self._convert_secs(int(value[1]))
                            description = "from:%s, to:%s, call_type:%s" % (value[2], value[3], value[4])

                            insert_data.append(tuple([par_id, configuration.case_id, configuration.evidence_id,
                                                      event_type, str(event_time), str(duration), description]))

                    if row[0] == 'lv1_os_and_basic_app_mms':
                        for value in result:
                            event_type = "Message(MMS)"
                            event_time = value[5]
                            duration = "00:00:00"
                            description = "from:%s, to:%s, content:%s" % (value[8], value[9], value[12])

                            insert_data.append(tuple([par_id, configuration.case_id, configuration.evidence_id,
                                                      event_type, str(event_time), str(duration), description]))

                    if row[0] == 'lv1_os_and_basic_app_sms':
                        for value in result:
                            event_type = "Message(SMS)"

                            if value[3] == 'Sent':
                                from_num = '' # Todo : service_center 컬럼 뭔지 확인해서 추가하기
                                to_num = value[1]
                            else:
                                from_num = value[1]
                                to_num = '' # Todo : service_center 컬럼 뭔지 확인해서 추가하기

                            event_time = value[0]
                            duration = "00:00:00"
                            description = "from:%s, to:%s, content:%s" % (from_num, to_num, value[2])

                            insert_data.append(tuple([par_id, configuration.case_id, configuration.evidence_id,
                                                      event_type, str(event_time), str(duration), description]))

                    if row[0] == 'lv1_os_and_basic_app_usagestats_0':
                        for value in result:
                            event_type = "Android App"
                            event_time = value[0]
                            duration = self._convert_millisecs(int(value[1]))
                            description = "package:%s, source:%s" % (value[2], value[3])

                            insert_data.append(tuple([par_id, configuration.case_id, configuration.evidence_id,
                                                      event_type, str(event_time), str(duration), description]))

                    if row[0] == 'lv1_app_web_chrome_download':
                        for value in result:
                            event_type = "Web Download"
                            event_time = value[0]

                            if len(value[1]) != 0:
                                start_time = datetime.datetime.strptime(value[0][:-6], '%Y-%m-%dT%H:%M:%S.%f')
                                end_time = datetime.datetime.strptime(value[1][:-6], '%Y-%m-%dT%H:%M:%S.%f')
                                duration = str(end_time - start_time)
                            else:
                                duration = "00:00:00"

                            description = "browser:Chrome, source:%s, file_path:%s, os_account:%s, chrome profile:%s" \
                                          % (value[2], value[3] + value[4], value[5], value[6])

                            insert_data.append(tuple([par_id, configuration.case_id, configuration.evidence_id,
                                                      event_type, str(event_time), str(duration), description]))

                    if row[0] == 'lv1_app_web_chromium_edge_download':
                        for value in result:
                            event_type = "Web Download"
                            event_time = value[0]

                            if len(value[1]) != 0:
                                start_time = datetime.datetime.strptime(value[0][:-6], '%Y-%m-%dT%H:%M:%S.%f')
                                end_time = datetime.datetime.strptime(value[1][:-6], '%Y-%m-%dT%H:%M:%S.%f')
                                duration = str(end_time - start_time)
                            else:
                                duration = "00:00:00"

                            description = "browser:Chromium Edge, source:%s, file_path:%s, os_account:%s, " \
                                          "edge profile:%s" % (value[2], value[3] + value[4], value[5], value[6])

                            insert_data.append(tuple([par_id, configuration.case_id, configuration.evidence_id,
                                                      event_type, str(event_time), str(duration), description]))

                    if row[0] == 'lv1_app_web_whale_download':
                        for value in result:
                            event_type = "Web Download"
                            event_time = value[0]

                            if len(value[1]) != 0:
                                start_time = datetime.datetime.strptime(value[0][:-6], '%Y-%m-%dT%H:%M:%S.%f')
                                end_time = datetime.datetime.strptime(value[1][:-6], '%Y-%m-%dT%H:%M:%S.%f')
                                duration = str(end_time - start_time)
                            else:
                                duration = "00:00:00"

                            description = "browser:Whale, source:%s, file_path:%s, os_account:%s, whale profile:%s" \
                                          % (value[2], value[3]+value[4], value[5], value[6])

                            insert_data.append(tuple([par_id, configuration.case_id, configuration.evidence_id,
                                                      event_type, str(event_time), str(duration), description]))

                    if row[0] == 'lv1_app_web_opera_download':
                        for value in result:
                            event_type = "Web Download"
                            event_time = value[0]

                            if len(value[1]) != 0:
                                start_time = datetime.datetime.strptime(value[0][:-6], '%Y-%m-%dT%H:%M:%S.%f')
                                end_time = datetime.datetime.strptime(value[1][:-6], '%Y-%m-%dT%H:%M:%S.%f')
                                duration = str(end_time - start_time)
                            else:
                                duration = "00:00:00"

                            description = "browser:Opera, source:%s, file_path:%s, os_account:%s, opera profile:%s" \
                                          % (value[2], value[3]+value[4], value[5], value[6])

                            insert_data.append(tuple([par_id, configuration.case_id, configuration.evidence_id,
                                                      event_type, str(event_time), str(duration), description]))

                    if row[0] == 'lv1_app_web_firefox_download':
                        for value in result:
                            event_type = "Web Download"
                            event_time = value[0]

                            if len(value[1]) != 0:
                                start_time = datetime.datetime.strptime(value[0][:-6], '%Y-%m-%dT%H:%M:%S.%f')
                                end_time = datetime.datetime.strptime(value[1][:-6], '%Y-%m-%dT%H:%M:%S.%f')
                                duration = str(end_time - start_time)
                            else:
                                duration = "00:00:00"

                            description = "browser:Firefox, source:%s, file_path:%s, os_account:%s, " \
                                          "firefox profile:%s" % (value[2], value[3], value[4], value[5])

                            insert_data.append(tuple([par_id, configuration.case_id, configuration.evidence_id,
                                                      event_type, str(event_time), str(duration), description]))

                    if row[0] == 'lv1_os_win_reg_usb_device':
                        for value in result:
                            event_type = "USB Connection"
                            event_time = value[0]
                            duration = "00:00:00"

                            description = "source:%s, friendly_name:%s, serial_number:%s, device_description:%s, " \
                                          "last_assigned_drive_letter:%s" \
                                          % (value[1], value[2], value[3], value[4], value[5])

                            insert_data.append(tuple([par_id, configuration.case_id, configuration.evidence_id,
                                                      event_type, str(event_time), str(duration), description]))

                    if row[0] == 'lv1_os_win_event_logs_usb_devices':
                        for value in result:
                            event_type = "USB Connection"
                            event_time = value[0]
                            duration = "00:00:00"

                            description = "manufacturer:%s, model:%s, serial_number:%s, event_id:%s, " \
                                          "event_id_description:%s, source:%s"\
                                          % (value[1], value[2], value[3], value[4], value[5], value[6])

                            insert_data.append(tuple([par_id, configuration.case_id, configuration.evidence_id,
                                                      event_type, str(event_time), str(duration), description]))
                    else:
                        pass
                else:
                    pass
            else:
                pass

        query = "Insert into lv2_timeline values (%s, %s, %s, %s, %s, %s, %s);"
        configuration.cursor.bulk_execute(query, insert_data)



manager.AdvancedModulesManager.RegisterModule(LV2TIMELINEAnalyzer)