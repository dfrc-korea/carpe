# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
import binascii

class MSOffice_Recent_Information:
    par_id = ''
    case_id = ''
    evd_id = ''
    file_name = ''
    file_path = ''
    modified_time = ''
    useraccount = ''
    backup_flag = ''
    source_location = ''

def MSOFFICERECENT(reg_nt):
    msoffice_recent_docs_list = []
    msoffice_recent_docs_count = 0

    ms_version = ['12.0', '14.0', '15.0', '16.0', '17.0']  # 2007, 2010, 2014, 2016, 2019

    for i in range(0, 5):
        reg_key = reg_nt.find_key(r"SOFTWARE\Microsoft\Office" + '\\' + ms_version[i])

        try:
            if reg_key is not None:
                excel_mru = reg_key.subkey('Excel').subkey('File MRU')
                word_mru = reg_key.subkey('Word').subkey('File MRU')
                ppt_mru = reg_key.subkey('Powerpoint').subkey('File MRU')
                if excel_mru is not None:
                    for reg_value in excel_mru.values():
                        if len(str(reg_value.data())) > 10:
                            msoffice_recent_information = MSOffice_Recent_Information()
                            msoffice_recent_docs_list.append(msoffice_recent_information)
                            msoffice_recent_docs_list[msoffice_recent_docs_count].file_name = reg_value.data().split('*')[1].replace('\\', '/').split('/')[-1][:-1]
                            msoffice_recent_docs_list[msoffice_recent_docs_count].file_path = reg_value.data().split('*')[1].replace('\\', '/')[:-1]
                            us = int(reg_value.data()[14:29], 16) / 10
                            msoffice_recent_docs_list[msoffice_recent_docs_count].modified_time = datetime(1601, 1, 1) + timedelta(microseconds=us)
                            msoffice_recent_docs_list[msoffice_recent_docs_count].source_location = "SOFTWARE/Microsoft/Office/"+ms_version[i]+"/Excel/File MRU"
                            msoffice_recent_docs_count = msoffice_recent_docs_count + 1
                if word_mru is not None:
                    for reg_value in word_mru.values():
                        if len(str(reg_value.data())) > 10:
                            msoffice_recent_information = MSOffice_Recent_Information()
                            msoffice_recent_docs_list.append(msoffice_recent_information)
                            msoffice_recent_docs_list[msoffice_recent_docs_count].file_name = reg_value.data().split('*')[1].replace('\\', '/').split('/')[-1][:-1]
                            msoffice_recent_docs_list[msoffice_recent_docs_count].file_path = reg_value.data().split('*')[1].replace('\\', '/')[:-1]
                            us = int(reg_value.data()[14:29], 16) / 10
                            msoffice_recent_docs_list[msoffice_recent_docs_count].modified_time = datetime(1601, 1, 1) + timedelta(microseconds=us)
                            msoffice_recent_docs_list[msoffice_recent_docs_count].source_location = "SOFTWARE/Microsoft/Office/"+ms_version[i]+"/Word/File MRU"
                            msoffice_recent_docs_count = msoffice_recent_docs_count + 1
                if ppt_mru is not None:
                    for reg_value in ppt_mru.values():
                        if len(str(reg_value.data())) > 10:
                            msoffice_recent_information = MSOffice_Recent_Information()
                            msoffice_recent_docs_list.append(msoffice_recent_information)
                            msoffice_recent_docs_list[msoffice_recent_docs_count].file_name = reg_value.data().split('*')[1].replace('\\', '/').split('/')[-1][:-1]
                            msoffice_recent_docs_list[msoffice_recent_docs_count].file_path = reg_value.data().split('*')[1].replace('\\', '/')[:-1]
                            us = int(reg_value.data()[14:29], 16) / 10
                            msoffice_recent_docs_list[msoffice_recent_docs_count].modified_time = datetime(1601, 1, 1) + timedelta(microseconds=us)
                            msoffice_recent_docs_list[msoffice_recent_docs_count].source_location = "SOFTWARE/Microsoft/Office/"+ms_version[i]+"/Powerpoint/File MRU"
                            msoffice_recent_docs_count = msoffice_recent_docs_count + 1
        except:
            print('-----MSOFFICE Recent Error')

    return msoffice_recent_docs_list

