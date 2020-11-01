from __future__ import unicode_literals
import os, sys, re
from datetime import datetime, timedelta
from utility import database


class Usage_Day_Detail_Information:
    seq = ''
    regdate = ''
    evdnc_type = ''
    artifact_type = ''
    information = ''
    case_id = ''

def USAGEDAYDETAIL(configuration):
    db = configuration.cursor

    usage_history_list = []
    usage_history_count = 0

    par_list = []
    for i in (configuration.partition_list.values()):
        # 문서파일 생성
        query = f"SELECT name, from_unixtime(ctime,'%Y-%m-%d %H:%i:%s') as created_time, from_unixtime(mtime,'%Y-%m-%d %H:%i:%s') as modified_time, from_unixtime(atime,'%Y-%m-%d %H:%i:%s') as accessed_time FROM file_info where (extension like 'doc%' or extension like 'ppt%' or extension like 'xls%' or extension like 'pdf' or extension like 'hwp') AND (par_id='{i}')"
        result_query = db.execute_query_mul(query)
        if len(result_query) != 0:
            for result_data in result_query:
                try:
                    if result_data[0] == 'document.doc' or result_data[0] == 'hancom.hwp':
                        pass
                    else:
                        usage_day_detail_information = Usage_Day_Detail_Information()
                        usage_history_list.append(usage_day_detail_information)
                        usage_history_list[usage_history_count].regdate = datetime.strptime(result_data[1], '%Y-%m-%d %H:%M:%S')-timedelta(hours=9)
                        usage_history_list[usage_history_count].evdnc_type = 'Created Time'
                        usage_history_list[usage_history_count].artifact_type = 'File Info'
                        usage_history_list[usage_history_count].information = result_data[0]
                        usage_history_count = usage_history_count + 1
                        usage_day_detail_information = Usage_Day_Detail_Information()
                        usage_history_list.append(usage_day_detail_information)
                        usage_history_list[usage_history_count].regdate = datetime.strptime(result_data[2], '%Y-%m-%d %H:%M:%S')-timedelta(hours=9)
                        usage_history_list[usage_history_count].evdnc_type = 'Modified Time'
                        usage_history_list[usage_history_count].artifact_type = 'File Info'
                        usage_history_list[usage_history_count].information = result_data[0]
                        usage_history_count = usage_history_count + 1
                        usage_day_detail_information = Usage_Day_Detail_Information()
                        usage_history_list.append(usage_day_detail_information)
                        usage_history_list[usage_history_count].regdate = datetime.strptime(result_data[3], '%Y-%m-%d %H:%M:%S')-timedelta(hours=9)
                        usage_history_list[usage_history_count].evdnc_type = 'Accessed Time'
                        usage_history_list[usage_history_count].artifact_type = 'File Info'
                        usage_history_list[usage_history_count].information = result_data[0]
                        usage_history_count = usage_history_count + 1
                except:
                    print('-----Document Error')

    # 이벤트로그 -  로그온/로그오프
    query = f"SELECT task, time, user_sid FROM lv1_os_win_event_logs_logonoff WHERE (evd_id='{configuration.evidence_id}')"
    result_query = db.execute_query_mul(query)

    for result_data in result_query:
        try:
            usage_day_detail_information = Usage_Day_Detail_Information()
            if result_data[0] == 'LogOn - Success':
                usage_history_list.append(usage_day_detail_information)
                usage_history_list[usage_history_count].regdate = result_data[1].replace('T',' ').replace('Z','')
                usage_history_list[usage_history_count].evdnc_type = 'Log On'
                usage_history_list[usage_history_count].artifact_type = 'EventLog'
                usage_history_list[usage_history_count].information = result_data[2]
                usage_history_count = usage_history_count + 1
            elif result_data[0] == 'LogOff':
                usage_history_list.append(usage_day_detail_information)
                usage_history_list[usage_history_count].regdate = result_data[1].replace('T',' ').replace('Z','')
                usage_history_list[usage_history_count].evdnc_type = 'Log Off'
                usage_history_list[usage_history_count].artifact_type = 'EventLog'
                usage_history_list[usage_history_count].information = result_data[2]
                usage_history_count = usage_history_count + 1
        except:
            print('-----Log On/Off Error')

    # 이벤트로그 -  시스템 시작/시스템 종료 (12,13은 뻇음)
    query = f"SELECT task, time, user_sid FROM lv1_os_win_event_logs_pconoff WHERE (evd_id='{configuration.evidence_id}')"
    result_query = db.execute_query_mul(query)

    for result_data in result_query:
        try:
            usage_day_detail_information = Usage_Day_Detail_Information()
            if result_data[0] == 'System On':
                usage_history_list.append(usage_day_detail_information)
                usage_history_list[usage_history_count].regdate = result_data[1].replace('T',' ').replace('Z','')
                usage_history_list[usage_history_count].evdnc_type = 'System On'
                usage_history_list[usage_history_count].artifact_type = 'EventLog'
                usage_history_list[usage_history_count].information = result_data[2]
                usage_history_count = usage_history_count + 1
            elif result_data[0] == 'System Off':
                usage_history_list.append(usage_day_detail_information)
                usage_history_list[usage_history_count].regdate = result_data[1].replace('T',' ').replace('Z','')
                usage_history_list[usage_history_count].evdnc_type = 'System Off'
                usage_history_list[usage_history_count].artifact_type = 'EventLog'
                usage_history_list[usage_history_count].information = result_data[2]
                usage_history_count = usage_history_count + 1
        except:
            print('-----System On/Off Error')

    # 이벤트로그 -  외부 저장 장치 연결 / 연결 해제
    query = f"SELECT task, time, device_instance_id, description, manufacturer, model, revision, serial_number, user_sid FROM lv1_os_win_event_logs_usb_devices  WHERE (evd_id='{configuration.evidence_id}')"
    result_query = db.execute_query_mul(query)

    for result_data in result_query:
        try:
            usage_day_detail_information = Usage_Day_Detail_Information()
            if result_data[0] == 'Connected':
                usage_history_list.append(usage_day_detail_information)
                usage_history_list[usage_history_count].regdate = result_data[1].replace('T',' ').replace('Z','')
                usage_history_list[usage_history_count].evdnc_type = 'USB Connected'
                usage_history_list[usage_history_count].artifact_type = 'EventLog'
                usage_history_list[usage_history_count].information = result_data[2]+'|'+result_data[3]+'|'+result_data[4]+'|'+result_data[5]+'|'+result_data[6]+'|'+result_data[7]+'|'+result_data[8]
                usage_history_count = usage_history_count + 1
            elif result_data[0] == 'Disconnected':
                usage_history_list.append(usage_day_detail_information)
                usage_history_list[usage_history_count].regdate = result_data[1].replace('T',' ').replace('Z','')
                usage_history_list[usage_history_count].evdnc_type = 'USB Disonnected'
                usage_history_list[usage_history_count].artifact_type = 'EventLog'
                usage_history_list[usage_history_count].information = result_data[2]+'|'+result_data[3]+'|'+result_data[4]+'|'+result_data[5]+'|'+result_data[6]+'|'+result_data[7]+'|'+result_data[8]
                usage_history_count = usage_history_count + 1
        except:
            print('-----EVT - USB Connected/Disconneccted Error')

    # 레지스트리 -  외부 저장 장치 연결 / 연결 해제 등
    query = f"SELECT last_connected_time, first_connected_time, first_connected_since_reboot_time, driver_install_time, first_install_time, last_insertion_time, last_removal_time, device_class_id, serial_number, device_description, friendly_name, manufacturer, last_assigned_drive_letter, volume_GUID FROM lv1_os_win_reg_usb_device WHERE (evd_id='{configuration.evidence_id}')"
    result_query = db.execute_query_mul(query)

    for result_data in result_query:
        try:
            if result_data[0] != '':
                usage_day_detail_information = Usage_Day_Detail_Information()
                usage_history_list.append(usage_day_detail_information)
                usage_history_list[usage_history_count].regdate = result_data[0].replace('T',' ').replace('Z','')
                usage_history_list[usage_history_count].evdnc_type = 'USB Last Connected'
                usage_history_list[usage_history_count].artifact_type = 'Registry'
                usage_history_list[usage_history_count].information = result_data[7]+'|'+result_data[8]+'|'+result_data[9]+'|'+result_data[10]+'|'+result_data[11]+'|'+result_data[12]+'|'+result_data[13]
                usage_history_count = usage_history_count + 1
            if result_data[1] != '':
                usage_day_detail_information = Usage_Day_Detail_Information()
                usage_history_list.append(usage_day_detail_information)
                usage_history_list[usage_history_count].regdate = result_data[1].replace('T',' ').replace('Z','')
                usage_history_list[usage_history_count].evdnc_type = 'USB First Connected'
                usage_history_list[usage_history_count].artifact_type = 'Registry'
                usage_history_list[usage_history_count].information = result_data[7]+'|'+result_data[8]+'|'+result_data[9]+'|'+result_data[10]+'|'+result_data[11]+'|'+result_data[12]+'|'+result_data[13]
                usage_history_count = usage_history_count + 1
            if result_data[2] != '':
                usage_day_detail_information = Usage_Day_Detail_Information()
                usage_history_list.append(usage_day_detail_information)
                usage_history_list[usage_history_count].regdate = result_data[2].replace('T',' ').replace('Z','')
                usage_history_list[usage_history_count].evdnc_type = 'USB First Connected Since Reboot'
                usage_history_list[usage_history_count].artifact_type = 'Registry'
                usage_history_list[usage_history_count].information = result_data[7]+'|'+result_data[8]+'|'+result_data[9]+'|'+result_data[10]+'|'+result_data[11]+'|'+result_data[12]+'|'+result_data[13]
                usage_history_count = usage_history_count + 1
            if result_data[3] != '':
                usage_day_detail_information = Usage_Day_Detail_Information()
                usage_history_list.append(usage_day_detail_information)
                usage_history_list[usage_history_count].regdate = result_data[3].replace('T',' ').replace('Z','')
                usage_history_list[usage_history_count].evdnc_type = 'USB Driver Installed'
                usage_history_list[usage_history_count].artifact_type = 'Registry'
                usage_history_list[usage_history_count].information = result_data[7]+'|'+result_data[8]+'|'+result_data[9]+'|'+result_data[10]+'|'+result_data[11]+'|'+result_data[12]+'|'+result_data[13]
                usage_history_count = usage_history_count + 1
            if result_data[4] != '':
                usage_day_detail_information = Usage_Day_Detail_Information()
                usage_history_list.append(usage_day_detail_information)
                usage_history_list[usage_history_count].regdate = result_data[4].replace('T',' ').replace('Z','')
                usage_history_list[usage_history_count].evdnc_type = 'USB First Installed'
                usage_history_list[usage_history_count].artifact_type = 'Registry'
                usage_history_list[usage_history_count].information = result_data[7]+'|'+result_data[8]+'|'+result_data[9]+'|'+result_data[10]+'|'+result_data[11]+'|'+result_data[12]+'|'+result_data[13]
                usage_history_count = usage_history_count + 1
            if result_data[5] != '':
                usage_day_detail_information = Usage_Day_Detail_Information()
                usage_history_list.append(usage_day_detail_information)
                usage_history_list[usage_history_count].regdate = result_data[5].replace('T',' ').replace('Z','')
                usage_history_list[usage_history_count].evdnc_type = 'USB Last Insertion'
                usage_history_list[usage_history_count].artifact_type = 'Registry'
                usage_history_list[usage_history_count].information = result_data[7]+'|'+result_data[8]+'|'+result_data[9]+'|'+result_data[10]+'|'+result_data[11]+'|'+result_data[12]+'|'+result_data[13]
                usage_history_count = usage_history_count + 1
            if result_data[6] != '':
                usage_day_detail_information = Usage_Day_Detail_Information()
                usage_history_list.append(usage_day_detail_information)
                usage_history_list[usage_history_count].regdate = result_data[6].replace('T',' ').replace('Z','')
                usage_history_list[usage_history_count].evdnc_type = 'USB Last Removal'
                usage_history_list[usage_history_count].artifact_type = 'Registry'
                usage_history_list[usage_history_count].information = result_data[7]+'|'+result_data[8]+'|'+result_data[9]+'|'+result_data[10]+'|'+result_data[11]+'|'+result_data[12]+'|'+result_data[13]
                usage_history_count = usage_history_count + 1
        except:
            print('-----REG - USB Connected/Disconneccted Error')

    # 웹 아티팩트 - IE - 접근시간
    query = f"SELECT AccessedTime, Url FROM lv1_os_win_esedb_ie_content WHERE (evd_id='{configuration.evidence_id}')"
    result_query = db.execute_query_mul(query)
    if result_query == -1:
        print('-----WEB - IE - Cache Error')
    else:
        for result_data in result_query:
            try:
                usage_day_detail_information = Usage_Day_Detail_Information()
                usage_history_list.append(usage_day_detail_information)
                usage_history_list[usage_history_count].regdate = result_data[0].replace('T', ' ').replace('Z', '')
                usage_history_list[usage_history_count].evdnc_type = 'IE Accessed Time - Cache'
                usage_history_list[usage_history_count].artifact_type = 'Web Artifact'
                usage_history_list[usage_history_count].information = result_data[1]
                usage_history_count = usage_history_count + 1
            except:
                print('-----WEB - IE - Cache Error')

    query = f"SELECT AccessedTime, Url FROM lv1_os_win_esedb_ie_cookies WHERE (evd_id='{configuration.evidence_id}')"
    result_query = db.execute_query_mul(query)
    if result_query == -1:
        print('-----WEB - IE - Cookie Error')
    else:
        for result_data in result_query:
            try:
                usage_day_detail_information = Usage_Day_Detail_Information()
                usage_history_list.append(usage_day_detail_information)
                usage_history_list[usage_history_count].regdate = result_data[0].replace('T', ' ').replace('Z', '')
                usage_history_list[usage_history_count].evdnc_type = 'IE Accessed Time - Cookie'
                usage_history_list[usage_history_count].artifact_type = 'Web Artifact'
                usage_history_list[usage_history_count].information = result_data[1]
                usage_history_count = usage_history_count + 1
            except:
                print('-----WEB - IE - Cookie Error')

    query = f"SELECT AccessedTime, Url FROM lv1_os_win_esedb_ie_download WHERE (evd_id='{configuration.evidence_id}')"
    result_query = db.execute_query_mul(query)
    if result_query == -1:
        print('-----WEB - IE - Download Error')
    else:
        for result_data in result_query:
            try:
                usage_day_detail_information = Usage_Day_Detail_Information()
                usage_history_list.append(usage_day_detail_information)
                usage_history_list[usage_history_count].regdate = result_data[0].replace('T', ' ').replace('Z', '')
                usage_history_list[usage_history_count].evdnc_type = 'IE Accessed Time - Download'
                usage_history_list[usage_history_count].artifact_type = 'Web Artifact'
                usage_history_list[usage_history_count].information = result_data[1]
                usage_history_count = usage_history_count + 1
            except:
                print('-----WEB - IE - Download Error')

    query = f"SELECT AccessedTime, Url FROM lv1_os_win_esedb_ie_history WHERE (evd_id='{configuration.evidence_id}')"
    result_query = db.execute_query_mul(query)
    if result_query == -1:
        print('-----WEB - IE - History Error')
    else:
        for result_data in result_query:
            try:
                usage_day_detail_information = Usage_Day_Detail_Information()
                usage_history_list.append(usage_day_detail_information)
                usage_history_list[usage_history_count].regdate = result_data[0].replace('T', ' ').replace('Z', '')
                usage_history_list[usage_history_count].evdnc_type = 'IE Accessed Time - History'
                usage_history_list[usage_history_count].artifact_type = 'Web Artifact'
                usage_history_list[usage_history_count].information = result_data[1]
                usage_history_count = usage_history_count + 1
            except:
                print('-----WEB - IE - History Error')

    # 웹 아티팩트 - Chrome - 접근시간
    query = f"SELECT last_access_utc, host_key FROM lv1_app_web_chrome_cookies WHERE (evd_id='{configuration.evidence_id}')"
    result_query = db.execute_query_mul(query)
    for result_data in result_query:
        try:
            usage_day_detail_information = Usage_Day_Detail_Information()
            usage_history_list.append(usage_day_detail_information)
            usage_history_list[usage_history_count].regdate = result_data[0].replace('T', ' ').replace('Z', '')
            usage_history_list[usage_history_count].evdnc_type = 'Chrome Accessed Time - Cookies'
            usage_history_list[usage_history_count].artifact_type = 'Web Artifact'
            usage_history_list[usage_history_count].information = result_data[1]
            usage_history_count = usage_history_count + 1
        except:
            print('-----WEB - Chrome - Cookies Error')

    query = f"SELECT start_time, file_name, download_tab_url FROM lv1_app_web_chrome_download WHERE (evd_id='{configuration.evidence_id}')"
    result_query = db.execute_query_mul(query)
    for result_data in result_query:
        try:
            usage_day_detail_information = Usage_Day_Detail_Information()
            usage_history_list.append(usage_day_detail_information)
            usage_history_list[usage_history_count].regdate = result_data[0].replace('T', ' ').replace('Z', '')
            usage_history_list[usage_history_count].evdnc_type = 'Chrome Started Time - Download'
            usage_history_list[usage_history_count].artifact_type = 'Web Artifact'
            usage_history_list[usage_history_count].information = result_data[1]+' | '+ result_data[2].replace('\\','/')
            usage_history_count = usage_history_count + 1
        except:
            print('-----WEB - Chrome - Download Error')

    query = f"SELECT last_updated, icon_url FROM lv1_app_web_chrome_favicons WHERE (evd_id='{configuration.evidence_id}')"
    result_query = db.execute_query_mul(query)
    for result_data in result_query:
        try:
            usage_day_detail_information = Usage_Day_Detail_Information()
            usage_history_list.append(usage_day_detail_information)
            usage_history_list[usage_history_count].regdate = result_data[0].replace('T', ' ').replace('Z', '')
            usage_history_list[usage_history_count].evdnc_type = 'Chrome Updated Time - Favicons'
            usage_history_list[usage_history_count].artifact_type = 'Web Artifact'
            usage_history_list[usage_history_count].information = result_data[1].replace('\\','/')
            usage_history_count = usage_history_count + 1
        except:
            print('-----WEB - Chrome - Favicons Error')

    query = f"SELECT searched_time, search_term FROM lv1_app_web_chrome_search_terms WHERE (evd_id='{configuration.evidence_id}')"
    result_query = db.execute_query_mul(query)
    for result_data in result_query:
        try:
            usage_day_detail_information = Usage_Day_Detail_Information()
            usage_history_list.append(usage_day_detail_information)
            usage_history_list[usage_history_count].regdate = result_data[0].replace('T', ' ').replace('Z', '')
            usage_history_list[usage_history_count].evdnc_type = 'Chrome Updated Time - Search Term'
            usage_history_list[usage_history_count].artifact_type = 'Web Artifact'
            usage_history_list[usage_history_count].information = result_data[1]
            usage_history_count = usage_history_count + 1
        except:
            print('-----WEB - Chrome - Search Term Error')

    query = f"SELECT last_access_time, url FROM lv1_app_web_chrome_shortcuts WHERE (evd_id='{configuration.evidence_id}')"
    result_query = db.execute_query_mul(query)
    for result_data in result_query:
        try:
            usage_day_detail_information = Usage_Day_Detail_Information()
            usage_history_list.append(usage_day_detail_information)
            usage_history_list[usage_history_count].regdate = result_data[0].replace('T', ' ').replace('Z', '')
            usage_history_list[usage_history_count].evdnc_type = 'Chrome Accessed Time - Shortcut'
            usage_history_list[usage_history_count].artifact_type = 'Web Artifact'
            usage_history_list[usage_history_count].information = result_data[1].replace('\\','/')
            usage_history_count = usage_history_count + 1
        except:
            print('-----WEB - Chrome - Shortcut Error')

    query = f"SELECT last_visited_time, title, url  FROM lv1_app_web_chrome_visit_urls WHERE (evd_id='{configuration.evidence_id}')"
    result_query = db.execute_query_mul(query)
    for result_data in result_query:
        try:
            if '1601-01' not in result_data[0]:
                usage_day_detail_information = Usage_Day_Detail_Information()
                usage_history_list.append(usage_day_detail_information)
                usage_history_list[usage_history_count].regdate = result_data[0].replace('T', ' ').replace('Z', '')
                usage_history_list[usage_history_count].evdnc_type = 'Chrome Accessed Time - Visit URL'
                usage_history_list[usage_history_count].artifact_type = 'Web Artifact'
                usage_history_list[usage_history_count].information = result_data[1] + '|' + result_data[2].replace('\\','/')
                usage_history_count = usage_history_count + 1
        except:
            print('-----WEB - Chrome - Visit URL Error')


    # 프로그램 실행시간
    query = f"SELECT execution_time, process_name, source FROM lv2_os_app_history WHERE (evd_id='{configuration.evidence_id}')"
    result_query = db.execute_query_mul(query)
    for result_data in result_query:
        try:
            usage_day_detail_information = Usage_Day_Detail_Information()
            usage_history_list.append(usage_day_detail_information)
            usage_history_list[usage_history_count].regdate = result_data[0].replace('T', ' ').replace('Z', '')
            usage_history_list[usage_history_count].information = result_data[1]
            usage_history_list[usage_history_count].evdnc_type = 'Application Execution Time'
            usage_history_list[usage_history_count].artifact_type = result_data[2]
            usage_history_count = usage_history_count + 1
        except:
            print('-----Application - Execution Time - Error')

    # AmCache 프로그램 실행시간
    query = f"SELECT key_last_updated_time, file_name FROM lv1_os_win_reg_amcache_program WHERE (evd_id='{configuration.evidence_id}')"
    result_query = db.execute_query_mul(query)
    for result_data in result_query:
        try:
            usage_day_detail_information = Usage_Day_Detail_Information()
            usage_history_list.append(usage_day_detail_information)
            usage_history_list[usage_history_count].regdate = result_data[0].replace('T', ' ').replace('Z', '')
            usage_history_list[usage_history_count].information = result_data[1]
            usage_history_list[usage_history_count].evdnc_type = 'Application Execution Time'
            usage_history_list[usage_history_count].artifact_type = 'Amcache'
            usage_history_count = usage_history_count + 1
        except:
            print('-----AmCache - Execution Time - Error')

    # 레지스트리 프로그램 설치 시간
    query = f"SELECT key_last_updated_time, program_name FROM lv1_os_win_reg_installed_program WHERE (evd_id='{configuration.evidence_id}')"
    result_query = db.execute_query_mul(query)
    for result_data in result_query:
        try:
            usage_day_detail_information = Usage_Day_Detail_Information()
            usage_history_list.append(usage_day_detail_information)
            usage_history_list[usage_history_count].regdate = result_data[0].replace('T', ' ').replace('Z', '')
            usage_history_list[usage_history_count].information = result_data[1]
            usage_history_list[usage_history_count].evdnc_type = 'Application Installed Time'
            usage_history_list[usage_history_count].artifact_type = 'Registry'
            usage_history_count = usage_history_count + 1
        except:
            print('-----Registry - Installed program Time - Error')

    # 레지스트리 프로그램 설치 시간
    query = f"SELECT key_last_updated_time, program_name FROM lv1_os_win_reg_installed_program WHERE (evd_id='{configuration.evidence_id}')"
    result_query = db.execute_query_mul(query)
    for result_data in result_query:
        try:
            usage_day_detail_information = Usage_Day_Detail_Information()
            usage_history_list.append(usage_day_detail_information)
            usage_history_list[usage_history_count].regdate = result_data[0].replace('T', ' ').replace('Z', '')
            usage_history_list[usage_history_count].information = result_data[1]
            usage_history_list[usage_history_count].evdnc_type = 'Application Installed Time'
            usage_history_list[usage_history_count].artifact_type = 'Registry'
            usage_history_count = usage_history_count + 1
        except:
            print('-----Registry - Installed program Time - Error')

    # 이벤트로그 프로그램 설치 시간
    query = f"SELECT time, application_name FROM lv1_os_win_event_logs_applications WHERE (evd_id='{configuration.evidence_id}')"
    result_query = db.execute_query_mul(query)
    for result_data in result_query:
        try:
            usage_day_detail_information = Usage_Day_Detail_Information()
            usage_history_list.append(usage_day_detail_information)
            usage_history_list[usage_history_count].regdate = result_data[0].replace('T', ' ').replace('Z', '')
            usage_history_list[usage_history_count].information = result_data[1]
            usage_history_list[usage_history_count].evdnc_type = 'Application Installed Time'
            usage_history_list[usage_history_count].artifact_type = 'Eventlog'
            usage_history_count = usage_history_count + 1
        except:
            print('-----Eventlog - Installed program Time - Error')

    return usage_history_list