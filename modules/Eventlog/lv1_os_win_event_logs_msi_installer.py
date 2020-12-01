# -*- coding: utf-8 -*-

from __future__ import unicode_literals


class MSI_Installer_Information:
    par_id = ''
    case_id = ''
    evd_id = ''
    task = ''
    time = ''
    product_name = ''
    product_version = ''
    manufacturer = ''
    user_sid = ''
    event_id = ''
    source = ''
    event_id_description = ''


def EVENTLOGMSIINSTALLER(configuration):

    msi_installer_list = []
    msi_installer_count = 0
    query = f"SELECT data, event_id, time_created, source, user_sid FROM lv1_os_win_evt_total " \
            f"WHERE (evd_id='{configuration.evidence_id}') " \
            f"and (event_id = '1033' or event_id = '11707' or event_id = '11724')"
    result_query = configuration.cursor.execute_query_mul(query)
    for result_data in result_query:
        msi_installer_information = MSI_Installer_Information()
        try:
            if 'MsiInstaller' in result_data[0]:
                if result_data[1] == '1033':
                    msi_installer_list.append(msi_installer_information)
                    msi_installer_list[msi_installer_count].task = 'Install application'
                    msi_installer_list[msi_installer_count].event_id = result_data[1]
                    msi_installer_list[msi_installer_count].time = result_data[2]
                    msi_installer_list[msi_installer_count].source = result_data[3]
                    msi_installer_list[msi_installer_count].user_sid = result_data[4]
                    msi_installer_list[msi_installer_count].event_id_description = 'Windows Installer installed the product'
                    try:
                        msi_installer_list[msi_installer_count].product_name = result_data[0].split('<Data>')[1].replace('<string>', '').split('</string>')[0].replace('\n','')
                        msi_installer_list[msi_installer_count].product_version = result_data[0].split('<Data>')[1].replace('<string>', '').split('</string>')[1].replace('\n','')
                        msi_installer_list[msi_installer_count].manufacturer = result_data[0].split('<Data>')[1].replace('<string>', '').split('</string>')[5].replace('\n','')
                    except:
                        print("Eventlog_msiinstaller_parsing_error")
                    msi_installer_count = msi_installer_count + 1
                elif result_data[1] == '11707':
                    msi_installer_list.append(msi_installer_information)
                    msi_installer_list[msi_installer_count].task = 'Install application'
                    msi_installer_list[msi_installer_count].event_id = result_data[1]
                    msi_installer_list[msi_installer_count].time = result_data[2]
                    msi_installer_list[msi_installer_count].source = result_data[3]
                    msi_installer_list[msi_installer_count].user_sid = result_data[4]
                    msi_installer_list[msi_installer_count].event_id_description = 'Installation completed successfully'
                    try:
                        msi_installer_list[msi_installer_count].product_name = result_data[0].split('<Data>')[1].replace('<string>', '').split('</string>')[0].split('--')[0].split(': ')[1].split('- 설')[0]
                    except:
                        print("Eventlog_msiinstaller_parsing_error")
                    msi_installer_count = msi_installer_count + 1
                elif result_data[1] == '11724':
                    msi_installer_list.append(msi_installer_information)
                    msi_installer_list[msi_installer_count].task = 'Uninstall application'
                    msi_installer_list[msi_installer_count].event_id = result_data[1]
                    msi_installer_list[msi_installer_count].time = result_data[2]
                    msi_installer_list[msi_installer_count].source = result_data[3]
                    msi_installer_list[msi_installer_count].user_sid = result_data[4]
                    try:
                        msi_installer_list[msi_installer_count].product_name = result_data[0].split('<Data>')[1].replace('<string>', '').split('</string>')[0].split('--')[0].split(': ')[1].split('- 설')[0]
                    except:
                        print("Eventlog_msiinstaller_parsing_error")
                    msi_installer_count = msi_installer_count + 1
        except:
            print("EVENT LOG EVENTLOGMSIINSTALLER ERROR")

    return msi_installer_list
