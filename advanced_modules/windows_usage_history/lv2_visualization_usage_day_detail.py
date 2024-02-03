from __future__ import unicode_literals
import os, sys, re
from datetime import datetime, timedelta

import dateutil

from utility import database


class Usage_Day_Detail_Information:
    seq = ''
    regdate = ''
    evdnc_type = ''
    artifact_type = ''
    information = ''
    case_id = ''

def USAGEDAYDETAIL(configuration, time_zone):
    db = configuration.cursor

    usage_history_list = []
    usage_history_count = 0

    # par_list = []
    for i in (configuration.partition_list.values()):
        query = f"SELECT name, ctime, mtime, atime, ctime_nano, mtime_nano, atime_nano " \
                f"FROM file_info " \
                f"where (extension like 'doc%' or extension like 'ppt%' or extension like 'xls%' or extension like 'pdf' or extension like 'hwp') " \
                f"AND (par_id='{i}')"
        result_query = db.execute_query_mul(query)
        if result_query != -1 and len(result_query) != 0:
            for result_data in result_query:
                try:
                    if result_data[0] == 'document.doc' or result_data[0] == 'hancom.hwp':
                        pass
                    else:
                        # UTC 0
                        creation_time = str(datetime.utcfromtimestamp(int(
                            str(result_data[1]).zfill(11) + str(result_data[4]).zfill(
                                7)) / 10000000 - 11644473600)).replace(' ', 'T') + 'Z'

                        write_time = str(datetime.utcfromtimestamp(int(
                            str(result_data[2]).zfill(11) + str(result_data[5]).zfill(
                                7)) / 10000000 - 11644473600)).replace(' ', 'T') + 'Z'

                        insert_creation_time = str(configuration.apply_time_zone(creation_time, time_zone))
                        insert_write_time = str(configuration.apply_time_zone(write_time, time_zone))

                        usage_day_detail_information = Usage_Day_Detail_Information()
                        usage_history_list.append(usage_day_detail_information)
                        usage_history_list[usage_history_count].regdate = insert_creation_time
                        usage_history_list[usage_history_count].evdnc_type = 'Created Time'
                        usage_history_list[usage_history_count].artifact_type = 'File Info'
                        usage_history_list[usage_history_count].information = result_data[0]
                        usage_history_count = usage_history_count + 1

                        if dateutil.parser.parse(creation_time) < dateutil.parser.parse(write_time):
                            usage_day_detail_information = Usage_Day_Detail_Information()
                            usage_history_list.append(usage_day_detail_information)
                            usage_history_list[usage_history_count].regdate = insert_write_time
                            usage_history_list[usage_history_count].evdnc_type = 'Modified Time'
                            usage_history_list[usage_history_count].artifact_type = 'File Info'
                            usage_history_list[usage_history_count].information = result_data[0]
                            usage_history_count = usage_history_count + 1

                except:
                    print('-----Document not found')

    # 링크 - 실행 시간
    query = f"SELECT file_name, file_path, lnk_creation_time, lnk_write_time FROM lv1_os_win_link WHERE (evd_id='{configuration.evidence_id}')"
    result_query = db.execute_query_mul(query)
    if result_query != -1 and len(result_query) != 0:
        for result_data in result_query:
            try:
                usage_day_detail_information = Usage_Day_Detail_Information()
                usage_history_list.append(usage_day_detail_information)
                usage_history_list[usage_history_count].regdate = result_data[2]
                usage_history_list[usage_history_count].evdnc_type = 'File/Folder Open'
                usage_history_list[usage_history_count].artifact_type = 'Link'
                usage_history_list[usage_history_count].information = result_data[1]
                usage_history_count = usage_history_count + 1

                usage_day_detail_information = Usage_Day_Detail_Information()
                usage_history_list.append(usage_day_detail_information)
                usage_history_list[usage_history_count].regdate = result_data[3]
                usage_history_list[usage_history_count].evdnc_type = 'File/Folder Open'
                usage_history_list[usage_history_count].artifact_type = 'Link'
                usage_history_list[usage_history_count].information = result_data[1]
                usage_history_count = usage_history_count + 1

            except:
                print('-----Link not found')

    # 이벤트로그 -  로그온/로그오프
    query = f"SELECT task, time, event_id_description FROM lv1_os_win_event_logs_logonoff WHERE (evd_id='{configuration.evidence_id}') ORDER BY time ASC"
    result_query = db.execute_query_mul(query)
    if result_query != -1 and len(result_query) != 0:
        for result_data in result_query:
            try:
                usage_day_detail_information = Usage_Day_Detail_Information()
                if result_data[0] == 'LogOn - Success':
                    usage_history_list.append(usage_day_detail_information)
                    usage_history_list[usage_history_count].regdate = result_data[1]
                    usage_history_list[usage_history_count].evdnc_type = 'Log On'
                    usage_history_list[usage_history_count].artifact_type = 'EventLog'
                    usage_history_list[usage_history_count].information = result_data[2]
                    usage_history_count = usage_history_count + 1
                elif result_data[0] == 'LogOff':
                    usage_history_list.append(usage_day_detail_information)
                    usage_history_list[usage_history_count].regdate = result_data[1]
                    usage_history_list[usage_history_count].evdnc_type = 'Log Off'
                    usage_history_list[usage_history_count].artifact_type = 'EventLog'
                    usage_history_list[usage_history_count].information = result_data[2]
                    usage_history_count = usage_history_count + 1
            except:
                print('-----Log On/Off not found')

    # 이벤트로그 -  시스템 시작/시스템 종료 (12,13은 뻇음)
    query = f"SELECT task, time, event_id_description FROM lv1_os_win_event_logs_pconoff WHERE (evd_id='{configuration.evidence_id}') ORDER BY time ASC"
    result_query = db.execute_query_mul(query)
    if result_query != -1 and len(result_query) != 0:
        for result_data in result_query:
            try:
                usage_day_detail_information = Usage_Day_Detail_Information()
                if result_data[0] == 'System On':
                    usage_history_list.append(usage_day_detail_information)
                    usage_history_list[usage_history_count].regdate = result_data[1]
                    usage_history_list[usage_history_count].evdnc_type = 'System On'
                    usage_history_list[usage_history_count].artifact_type = 'EventLog'
                    usage_history_list[usage_history_count].information = result_data[2]
                    usage_history_count = usage_history_count + 1
                elif result_data[0] == 'System Off':
                    usage_history_list.append(usage_day_detail_information)
                    usage_history_list[usage_history_count].regdate = result_data[1]
                    usage_history_list[usage_history_count].evdnc_type = 'System Off'
                    usage_history_list[usage_history_count].artifact_type = 'EventLog'
                    usage_history_list[usage_history_count].information = result_data[2]
                    usage_history_count = usage_history_count + 1
            except:
                print('-----System On/Off not found')

    # 이벤트로그 - Sleep Start End (1번으로만 구별)
    query = f"SELECT task, time_sleep, time_wake, event_id_description FROM lv1_os_win_event_logs_sleeponoff WHERE (evd_id='{configuration.evidence_id}' and event_id = '1') ORDER BY time_sleep ASC"
    result_query = db.execute_query_mul(query)
    if result_query != -1 and len(result_query) != 0:
        for result_data in result_query:
            try:
                usage_day_detail_information = Usage_Day_Detail_Information()
                usage_history_list.append(usage_day_detail_information)
                usage_history_list[usage_history_count].regdate = result_data[1]
                usage_history_list[usage_history_count].evdnc_type = 'Sleep Start'
                usage_history_list[usage_history_count].artifact_type = 'EventLog'
                usage_history_list[usage_history_count].information = result_data[3]
                usage_history_count = usage_history_count + 1

                usage_day_detail_information = Usage_Day_Detail_Information()
                usage_history_list.append(usage_day_detail_information)
                usage_history_list[usage_history_count].regdate = result_data[2]
                usage_history_list[usage_history_count].evdnc_type = 'Sleep End'
                usage_history_list[usage_history_count].artifact_type = 'EventLog'
                usage_history_list[usage_history_count].information = result_data[3]
                usage_history_count = usage_history_count + 1

            except:
                print('-----Sleep Start/End not found')

    # 이벤트로그 -  외부 저장 장치 연결 / 연결 해제
    query = f"SELECT task, time, device_instance_id, description, manufacturer, model, revision, serial_number, user_sid " \
            f"FROM lv1_os_win_event_logs_usb_devices  WHERE (evd_id='{configuration.evidence_id}') ORDER BY time ASC"
    result_query = db.execute_query_mul(query)
    if result_query != -1 and len(result_query) != 0:
        for result_data in result_query:
            try:
                usage_day_detail_information = Usage_Day_Detail_Information()
                if result_data[0] == 'Connected':
                    usage_history_list.append(usage_day_detail_information)
                    usage_history_list[usage_history_count].regdate = result_data[1]
                    usage_history_list[usage_history_count].evdnc_type = 'USB Connected'
                    usage_history_list[usage_history_count].artifact_type = 'EventLog'
                    usage_history_list[usage_history_count].information = result_data[2]+'|'+result_data[3]+'|'+result_data[4]+'|'+result_data[5]+'|'+result_data[6]+'|'+result_data[7]+'|'+result_data[8]
                    usage_history_count = usage_history_count + 1
                elif result_data[0] == 'Disconnected':
                    usage_history_list.append(usage_day_detail_information)
                    usage_history_list[usage_history_count].regdate = result_data[1]
                    usage_history_list[usage_history_count].evdnc_type = 'USB Disonnected'
                    usage_history_list[usage_history_count].artifact_type = 'EventLog'
                    usage_history_list[usage_history_count].information = result_data[2]+'|'+result_data[3]+'|'+result_data[4]+'|'+result_data[5]+'|'+result_data[6]+'|'+result_data[7]+'|'+result_data[8]
                    usage_history_count = usage_history_count + 1
            except:
                print('-----EVT - USB Connected/Disconneccted not found')

    # 레지스트리 -  외부 저장 장치 연결 / 연결 해제 등
    query = f"SELECT last_connected_time, first_connected_time, first_connected_since_reboot_time, " \
            f"driver_install_time, first_install_time, last_insertion_time, last_removal_time, " \
            f"device_class_id, serial_number, device_description, friendly_name, manufacturer, " \
            f"last_assigned_drive_letter, volume_GUID " \
            f"FROM lv1_os_win_reg_usb_device WHERE (evd_id='{configuration.evidence_id}')"
    result_query = db.execute_query_mul(query)
    if result_query != -1 and len(result_query) != 0:
        for result_data in result_query:
            try:
                if result_data[0] != '':
                    usage_day_detail_information = Usage_Day_Detail_Information()
                    usage_history_list.append(usage_day_detail_information)
                    usage_history_list[usage_history_count].regdate = result_data[0]
                    usage_history_list[usage_history_count].evdnc_type = 'USB Last Connected'
                    usage_history_list[usage_history_count].artifact_type = 'Registry'
                    usage_history_list[usage_history_count].information = result_data[7]+'|'+result_data[8]+'|'+result_data[9]+'|'+result_data[10]+'|'+result_data[11]+'|'+result_data[12]+'|'+result_data[13]
                    usage_history_count = usage_history_count + 1
                if result_data[1] != '':
                    usage_day_detail_information = Usage_Day_Detail_Information()
                    usage_history_list.append(usage_day_detail_information)
                    usage_history_list[usage_history_count].regdate = result_data[1]
                    usage_history_list[usage_history_count].evdnc_type = 'USB First Connected'
                    usage_history_list[usage_history_count].artifact_type = 'Registry'
                    usage_history_list[usage_history_count].information = result_data[7]+'|'+result_data[8]+'|'+result_data[9]+'|'+result_data[10]+'|'+result_data[11]+'|'+result_data[12]+'|'+result_data[13]
                    usage_history_count = usage_history_count + 1
                if result_data[2] != '':
                    usage_day_detail_information = Usage_Day_Detail_Information()
                    usage_history_list.append(usage_day_detail_information)
                    usage_history_list[usage_history_count].regdate = result_data[2]
                    usage_history_list[usage_history_count].evdnc_type = 'USB First Connected Since Reboot'
                    usage_history_list[usage_history_count].artifact_type = 'Registry'
                    usage_history_list[usage_history_count].information = result_data[7]+'|'+result_data[8]+'|'+result_data[9]+'|'+result_data[10]+'|'+result_data[11]+'|'+result_data[12]+'|'+result_data[13]
                    usage_history_count = usage_history_count + 1
                if result_data[3] != '':
                    usage_day_detail_information = Usage_Day_Detail_Information()
                    usage_history_list.append(usage_day_detail_information)
                    usage_history_list[usage_history_count].regdate = result_data[3]
                    usage_history_list[usage_history_count].evdnc_type = 'USB Driver Installed'
                    usage_history_list[usage_history_count].artifact_type = 'Registry'
                    usage_history_list[usage_history_count].information = result_data[7]+'|'+result_data[8]+'|'+result_data[9]+'|'+result_data[10]+'|'+result_data[11]+'|'+result_data[12]+'|'+result_data[13]
                    usage_history_count = usage_history_count + 1
                if result_data[4] != '':
                    usage_day_detail_information = Usage_Day_Detail_Information()
                    usage_history_list.append(usage_day_detail_information)
                    usage_history_list[usage_history_count].regdate = result_data[4]
                    usage_history_list[usage_history_count].evdnc_type = 'USB First Installed'
                    usage_history_list[usage_history_count].artifact_type = 'Registry'
                    usage_history_list[usage_history_count].information = result_data[7]+'|'+result_data[8]+'|'+result_data[9]+'|'+result_data[10]+'|'+result_data[11]+'|'+result_data[12]+'|'+result_data[13]
                    usage_history_count = usage_history_count + 1
                if result_data[5] != '':
                    usage_day_detail_information = Usage_Day_Detail_Information()
                    usage_history_list.append(usage_day_detail_information)
                    usage_history_list[usage_history_count].regdate = result_data[5]
                    usage_history_list[usage_history_count].evdnc_type = 'USB Last Insertion'
                    usage_history_list[usage_history_count].artifact_type = 'Registry'
                    usage_history_list[usage_history_count].information = result_data[7]+'|'+result_data[8]+'|'+result_data[9]+'|'+result_data[10]+'|'+result_data[11]+'|'+result_data[12]+'|'+result_data[13]
                    usage_history_count = usage_history_count + 1
                if result_data[6] != '':
                    usage_day_detail_information = Usage_Day_Detail_Information()
                    usage_history_list.append(usage_day_detail_information)
                    usage_history_list[usage_history_count].regdate = result_data[6]
                    usage_history_list[usage_history_count].evdnc_type = 'USB Last Removal'
                    usage_history_list[usage_history_count].artifact_type = 'Registry'
                    usage_history_list[usage_history_count].information = result_data[7]+'|'+result_data[8]+'|'+result_data[9]+'|'+result_data[10]+'|'+result_data[11]+'|'+result_data[12]+'|'+result_data[13]
                    usage_history_count = usage_history_count + 1
            except:
                print('-----REG - USB Connected/Disconneccted not found')

    # 웹 아티팩트 - IE - 접근시간
    # query = f"SELECT ModifiedTime, Url FROM lv1_os_win_esedb_ie_content WHERE (evd_id='{configuration.evidence_id}')"
    # result_query = db.execute_query_mul(query)
    # if result_query == -1:
    #     pass
    # else:
    #     for result_data in result_query:
    #         try:
    #             usage_day_detail_information = Usage_Day_Detail_Information()
    #             usage_history_list.append(usage_day_detail_information)
    #             usage_history_list[usage_history_count].regdate = result_data[0]
    #             usage_history_list[usage_history_count].evdnc_type = 'IE Accessed Time - Cache'
    #             usage_history_list[usage_history_count].artifact_type = 'Web Artifact'
    #             usage_history_list[usage_history_count].information = result_data[1]
    #             usage_history_count = usage_history_count + 1
    #         except:
    #             print('-----WEB - IE - Cache Error')

    # query = f"SELECT ModifiedTime, Url FROM lv1_os_win_esedb_ie_cookies WHERE (evd_id='{configuration.evidence_id}')"
    # result_query = db.execute_query_mul(query)
    # if result_query == -1:
    #     pass
    # else:
    #     for result_data in result_query:
    #         try:
    #             usage_day_detail_information = Usage_Day_Detail_Information()
    #             usage_history_list.append(usage_day_detail_information)
    #             usage_history_list[usage_history_count].regdate = result_data[0]
    #             usage_history_list[usage_history_count].evdnc_type = 'IE Accessed Time - Cookie'
    #             usage_history_list[usage_history_count].artifact_type = 'Web Artifact'
    #             usage_history_list[usage_history_count].information = result_data[1]
    #             usage_history_count = usage_history_count + 1
    #         except:
    #             print('-----WEB - IE - Cookie Error')

    query = f"SELECT ModifiedTime, Url FROM lv1_os_win_esedb_ie_download WHERE (evd_id='{configuration.evidence_id}')"
    result_query = db.execute_query_mul(query)
    if result_query != -1 and len(result_query) != 0:
        for result_data in result_query:
            try:
                usage_day_detail_information = Usage_Day_Detail_Information()
                usage_history_list.append(usage_day_detail_information)
                usage_history_list[usage_history_count].regdate = result_data[0]
                usage_history_list[usage_history_count].evdnc_type = 'IE Accessed Time - Download'
                usage_history_list[usage_history_count].artifact_type = 'Web Artifact'
                usage_history_list[usage_history_count].information = result_data[1]
                usage_history_count = usage_history_count + 1
            except:
                print('-----WEB - IE - Download not found')

    query = f"SELECT ModifiedTime, Url FROM lv1_os_win_esedb_ie_history WHERE (evd_id='{configuration.evidence_id}')"
    result_query = db.execute_query_mul(query)
    if result_query != -1 and len(result_query) != 0:
        for result_data in result_query:
            try:
                usage_day_detail_information = Usage_Day_Detail_Information()
                usage_history_list.append(usage_day_detail_information)
                usage_history_list[usage_history_count].regdate = result_data[0]
                usage_history_list[usage_history_count].evdnc_type = 'IE Accessed Time - History'
                usage_history_list[usage_history_count].artifact_type = 'Web Artifact'
                usage_history_list[usage_history_count].information = result_data[1]
                usage_history_count = usage_history_count + 1
            except:
                print('-----WEB - IE - History not found')

    # 웹 아티팩트 - Chrome - 접근시간
    # query = f"SELECT last_access_utc, host_key FROM lv1_app_web_chrome_cookies WHERE (evd_id='{configuration.evidence_id}')"
    # result_query = db.execute_query_mul(query)
    # for result_data in result_query:
    #     try:
    #         usage_day_detail_information = Usage_Day_Detail_Information()
    #         usage_history_list.append(usage_day_detail_information)
    #         usage_history_list[usage_history_count].regdate = result_data[0]
    #         usage_history_list[usage_history_count].evdnc_type = 'Chrome Accessed Time - Cookies'
    #         usage_history_list[usage_history_count].artifact_type = 'Web Artifact'
    #         usage_history_list[usage_history_count].information = result_data[1]
    #         usage_history_count = usage_history_count + 1
    #     except:
    #         print('-----WEB - Chrome - Cookies Error')

    query = f"SELECT start_time, file_name, download_tab_url FROM lv1_app_web_chrome_download WHERE (evd_id='{configuration.evidence_id}')"
    result_query = db.execute_query_mul(query)
    if result_query != -1 and len(result_query) != 0:
        for result_data in result_query:
            try:
                usage_day_detail_information = Usage_Day_Detail_Information()
                usage_history_list.append(usage_day_detail_information)
                usage_history_list[usage_history_count].regdate = result_data[0]
                usage_history_list[usage_history_count].evdnc_type = 'Chrome Started Time - Download'
                usage_history_list[usage_history_count].artifact_type = 'Web Artifact'
                usage_history_list[usage_history_count].information = result_data[1]+' | '+ result_data[2].replace('\\','/')
                usage_history_count = usage_history_count + 1
            except:
                print('-----WEB - Chrome - Download not found')

    # query = f"SELECT last_updated, icon_url FROM lv1_app_web_chrome_favicons WHERE (evd_id='{configuration.evidence_id}')"
    # result_query = db.execute_query_mul(query)
    # for result_data in result_query:
    #     try:
    #         usage_day_detail_information = Usage_Day_Detail_Information()
    #         usage_history_list.append(usage_day_detail_information)
    #         usage_history_list[usage_history_count].regdate = result_data[0]
    #         usage_history_list[usage_history_count].evdnc_type = 'Chrome Updated Time - Favicons'
    #         usage_history_list[usage_history_count].artifact_type = 'Web Artifact'
    #         usage_history_list[usage_history_count].information = result_data[1].replace('\\','/')
    #         usage_history_count = usage_history_count + 1
    #     except:
    #         print('-----WEB - Chrome - Favicons Error')
    #
    query = f"SELECT searched_time, search_term FROM lv1_app_web_chrome_search_terms WHERE (evd_id='{configuration.evidence_id}')"
    result_query = db.execute_query_mul(query)
    if result_query != -1 and len(result_query) != 0:
        for result_data in result_query:
            try:
                usage_day_detail_information = Usage_Day_Detail_Information()
                usage_history_list.append(usage_day_detail_information)
                usage_history_list[usage_history_count].regdate = result_data[0]
                usage_history_list[usage_history_count].evdnc_type = 'Chrome Updated Time - Search Term'
                usage_history_list[usage_history_count].artifact_type = 'Web Artifact'
                usage_history_list[usage_history_count].information = result_data[1]
                usage_history_count = usage_history_count + 1
            except:
                print('-----WEB - Chrome - Search Term not found')
    #
    # query = f"SELECT last_access_time, url FROM lv1_app_web_chrome_shortcuts WHERE (evd_id='{configuration.evidence_id}')"
    # result_query = db.execute_query_mul(query)
    # for result_data in result_query:
    #     try:
    #         usage_day_detail_information = Usage_Day_Detail_Information()
    #         usage_history_list.append(usage_day_detail_information)
    #         usage_history_list[usage_history_count].regdate = result_data[0]
    #         usage_history_list[usage_history_count].evdnc_type = 'Chrome Accessed Time - Shortcut'
    #         usage_history_list[usage_history_count].artifact_type = 'Web Artifact'
    #         usage_history_list[usage_history_count].information = result_data[1].replace('\\','/')
    #         usage_history_count = usage_history_count + 1
    #     except:
    #         print('-----WEB - Chrome - Shortcut Error')
    #
    query = f"SELECT last_visited_time, title, url  FROM lv1_app_web_chrome_visit_urls WHERE (evd_id='{configuration.evidence_id}')"
    result_query = db.execute_query_mul(query)
    if result_query != -1 and len(result_query) != 0:
        for result_data in result_query:
            try:
                if '1601-01' not in result_data[0]:
                    usage_day_detail_information = Usage_Day_Detail_Information()
                    usage_history_list.append(usage_day_detail_information)
                    usage_history_list[usage_history_count].regdate = result_data[0]
                    usage_history_list[usage_history_count].evdnc_type = 'Chrome Accessed Time - Visit URL'
                    usage_history_list[usage_history_count].artifact_type = 'Web Artifact'
                    usage_history_list[usage_history_count].information = result_data[1] + '|' + result_data[2].replace('\\','/')
                    usage_history_count = usage_history_count + 1
            except:
                print('-----WEB - Chrome - Visit URL not found')


    # 프로그램 실행시간
    query = f"SELECT execution_time, process_name, source FROM lv2_os_app_history WHERE (evd_id='{configuration.evidence_id}' and source='Prefetch')"
    result_query = db.execute_query_mul(query)
    if result_query != -1 and len(result_query) != 0:
        for result_data in result_query:
            try:
                usage_day_detail_information = Usage_Day_Detail_Information()
                usage_history_list.append(usage_day_detail_information)
                usage_history_list[usage_history_count].regdate = result_data[0]
                usage_history_list[usage_history_count].information = result_data[1]
                usage_history_list[usage_history_count].evdnc_type = 'Application Execution Time'
                usage_history_list[usage_history_count].artifact_type = result_data[2]
                usage_history_count = usage_history_count + 1
            except:
                print('-----Application - Execution Time - not found')
    #
    # # AmCache 프로그램 실행시간
    # query = f"SELECT key_last_updated_time, file_name FROM lv1_os_win_reg_amcache_program WHERE (evd_id='{configuration.evidence_id}')"
    # result_query = db.execute_query_mul(query)
    # for result_data in result_query:
    #     try:
    #         usage_day_detail_information = Usage_Day_Detail_Information()
    #         usage_history_list.append(usage_day_detail_information)
    #         usage_history_list[usage_history_count].regdate = result_data[0]
    #         usage_history_list[usage_history_count].information = result_data[1]
    #         usage_history_list[usage_history_count].evdnc_type = 'Application Execution Time'
    #         usage_history_list[usage_history_count].artifact_type = 'Amcache'
    #         usage_history_count = usage_history_count + 1
    #     except:
    #         print('-----AmCache - Execution Time - Error')

    # # 레지스트리 프로그램 설치 시간
    # query = f"SELECT key_last_updated_time, program_name FROM lv1_os_win_reg_installed_program WHERE (evd_id='{configuration.evidence_id}')"
    # result_query = db.execute_query_mul(query)
    # for result_data in result_query:
    #     try:
    #         usage_day_detail_information = Usage_Day_Detail_Information()
    #         usage_history_list.append(usage_day_detail_information)
    #         usage_history_list[usage_history_count].regdate = result_data[0]
    #         usage_history_list[usage_history_count].information = result_data[1]
    #         usage_history_list[usage_history_count].evdnc_type = 'Application Installed Time'
    #         usage_history_list[usage_history_count].artifact_type = 'Registry'
    #         usage_history_count = usage_history_count + 1
    #     except:
    #         print('-----Registry - Installed program Time - Error')
    #
    # # 이벤트로그 프로그램 설치 시간
    # query = f"SELECT time, application_name FROM lv1_os_win_event_logs_applications WHERE (evd_id='{configuration.evidence_id}')"
    # result_query = db.execute_query_mul(query)
    # for result_data in result_query:
    #     try:
    #         usage_day_detail_information = Usage_Day_Detail_Information()
    #         usage_history_list.append(usage_day_detail_information)
    #         usage_history_list[usage_history_count].regdate = result_data[0]
    #         usage_history_list[usage_history_count].information = result_data[1]
    #         usage_history_list[usage_history_count].evdnc_type = 'Application Installed Time'
    #         usage_history_list[usage_history_count].artifact_type = 'Eventlog'
    #         usage_history_count = usage_history_count + 1
    #     except:
    #         print('-----Eventlog - Installed program Time - Error')

    return usage_history_list