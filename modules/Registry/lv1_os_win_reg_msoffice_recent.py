# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from modules import logger

# Changed Registry Key by Jeongyoon
# TODO: ADAL Key listing

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

def parseRegOffice(msoffice_recent_docs_list, msoffice_recent_docs_count, reg_value, ms_version, i, app, adalkey):
    msoffice_recent_information = MSOffice_Recent_Information()
    msoffice_recent_docs_list.append(msoffice_recent_information)
    msoffice_recent_docs_list[msoffice_recent_docs_count].file_name = reg_value.data().split('*')[1].replace('\\', '/').replace('\x00', '').split('/')[-1][:-1]
    msoffice_recent_docs_list[msoffice_recent_docs_count].file_path = reg_value.data().split('*')[1].replace('\\', '/').replace('\x00', '')[:-1]
    us = int(reg_value.data()[14:29], 16) / 10
    msoffice_recent_docs_list[msoffice_recent_docs_count].modified_time = datetime(1601, 1, 1) + timedelta(microseconds=us)
    msoffice_recent_docs_list[msoffice_recent_docs_count].source_location = "SOFTWARE/Microsoft/Office/" + ms_version[i] + "//" + app + "/User MRU/" + adalkey + "/File MRU"

def MSOFFICERECENT(reg_nt):
    msoffice_recent_docs_list = []
    msoffice_recent_docs_count = 0

    ms_version = ['12.0', '14.0', '15.0', '16.0', '17.0']  # 2007, 2010, 2014, 2016, 2019

    for i in range(0, 5):
        try:
            reg_key = reg_nt.find_key(r"SOFTWARE\Microsoft\Office" + '\\' + ms_version[i])
        except Exception as exception:
            logger.error(exception)

        try:
            app = ''
            if reg_key is not None:
                print("subkeys", reg_key.subkey('Excel').subkey('User MRU').subkeys_count())
                adalkey = 'ADAL_46241D702D34078EA8017B8719188D251AE64511755F5D9A022E800AC76CFB2D'
                for a in ['Excel', 'Word', 'Powerpoint']:
                    if reg_key.subkey(a).subkey('User MRU').subkey(adalkey).subkey('File MRU') is not None:
                        mru = reg_key.subkey(a).subkey('User MRU').subkey(adalkey).subkey('File MRU')
                        for reg_value in mru.values():
                            # if len(str(reg_value.data())) > 10:
                            if 'Item' in str(reg_value.name()):
                                parseRegOffice(msoffice_recent_docs_list, msoffice_recent_docs_count, reg_value,
                                               ms_version, i, app, adalkey)
                                msoffice_recent_docs_count += 1

                #     for reg_value in word_mru.values():
                #         if len(str(reg_value.data())) > 10:
                #             msoffice_recent_information = MSOffice_Recent_Information()
                #             msoffice_recent_docs_list.append(msoffice_recent_information)
                #             msoffice_recent_docs_list[msoffice_recent_docs_count].file_name = reg_value.data().split('*')[1].replace('\\', '/').split('/')[-1][:-1]
                #             msoffice_recent_docs_list[msoffice_recent_docs_count].file_path = reg_value.data().split('*')[1].replace('\\', '/')[:-1]
                #             us = int(reg_value.data()[14:29], 16) / 10
                #             msoffice_recent_docs_list[msoffice_recent_docs_count].modified_time = datetime(1601, 1, 1) + timedelta(microseconds=us)
                #             msoffice_recent_docs_list[msoffice_recent_docs_count].source_location = "SOFTWARE/Microsoft/Office/"+ms_version[i]+"/Word/File MRU"
                #             msoffice_recent_docs_count = msoffice_recent_docs_count + 1
                # if ppt_mru is not None:
                #     for reg_value in ppt_mru.values():
                #         if len(str(reg_value.data())) > 10:
                #             msoffice_recent_information = MSOffice_Recent_Information()
                #             msoffice_recent_docs_list.append(msoffice_recent_information)
                #             msoffice_recent_docs_list[msoffice_recent_docs_count].file_name = reg_value.data().split('*')[1].replace('\\', '/').split('/')[-1][:-1]
                #             msoffice_recent_docs_list[msoffice_recent_docs_count].file_path = reg_value.data().split('*')[1].replace('\\', '/')[:-1]
                #             us = int(reg_value.data()[14:29], 16) / 10
                #             msoffice_recent_docs_list[msoffice_recent_docs_count].modified_time = datetime(1601, 1, 1) + timedelta(microseconds=us)
                #             msoffice_recent_docs_list[msoffice_recent_docs_count].source_location = "SOFTWARE/Microsoft/Office/"+ms_version[i]+"/Powerpoint/File MRU"
                #             msoffice_recent_docs_count = msoffice_recent_docs_count + 1
        except Exception as exception:
            logger.error(exception)
    return msoffice_recent_docs_list

