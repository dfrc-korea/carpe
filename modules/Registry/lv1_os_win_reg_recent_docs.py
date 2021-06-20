from datetime import datetime, timedelta
import binascii
from modules import logger

class Recent_Docs_Information:
    par_id = ''
    case_id = ''
    evd_id = ''
    file_folder_name = ''
    file_folder_link = ''
    modified_time = ''
    registry_order = ''
    value = ''
    useraccount = ''
    backup_flag = ''
    source_location = ''

def RECENTDOCS(reg_nt):
    recent_docs_list = []
    recent_docs_order = []
    recent_docs_count = 0
    try:
        reg_key = reg_nt.find_key(r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\RecentDocs")
    except Exception as exception:
        logger.error(exception)

    try:
        if reg_key != None:
            for reg_value in reg_key.values():
                if reg_value.name() == 'MRUListEx':
                    for i in range(0, len(list(reg_key.values()))-1):
                        recent_docs_order.append(int(binascii.b2a_hex(reg_value.data()[4*i:4*i+4][::-1]),16))
                else:
                    for order in recent_docs_order:
                        if reg_value.name() == str(order):
                            recent_docs_information = Recent_Docs_Information()
                            recent_docs_list.append(recent_docs_information)
                            if reg_value.data()[0:reg_value.data().find(b'\x00\x00\x00') + 1].decode('utf-16')[-1] != '6':
                                recent_docs_list[recent_docs_count].file_folder_name = reg_value.data()[0:reg_value.data().find(b'\x00\x00\x00') + 1].decode('utf-16')
                                recent_docs_list[recent_docs_count].file_folder_link = reg_value.data()[0:reg_value.data().find(b'\x00\x00\x00') + 1].decode('utf-16').split('.')[0] + '.lnk'
                            elif reg_value.data()[0:reg_value.data().find(b'\x00\x00\x00') + 1].decode('utf-16')[-1] == '6':
                                recent_docs_list[recent_docs_count].file_folder_name = reg_value.data()[0:reg_value.data().find(b'\x00\x00\x00') + -5].decode('utf-16')
                                recent_docs_list[recent_docs_count].file_folder_link = reg_value.data()[0:reg_value.data().find(b'\x00\x00\x00') + -5].decode('utf-16').split('.')[0] + '.lnk'
                            recent_docs_list[recent_docs_count].modified_time = reg_key.last_written_timestamp().isoformat()+'Z'
                            recent_docs_list[recent_docs_count].registry_order = recent_docs_count + 1
                            recent_docs_list[recent_docs_count].value = reg_value.name()
                            recent_docs_list[recent_docs_count].source_location = "NTUSER-SOFTWARE/Microsoft/Windows/CurrentVersion/Explorer/RecentDocs/"
                            recent_docs_count = recent_docs_count + 1

            for reg_subkey in reg_key.subkeys():
                recent_docs_order = []
                for reg_value in reg_subkey.values():
                    if reg_value.name() == 'MRUListEx':
                        for i in range(0, len(list(reg_subkey.values()))-1):
                            recent_docs_order.append(int(binascii.b2a_hex(reg_value.data()[4*i:4*i+4][::-1]),16))
                for order in recent_docs_order:
                    for reg_value in reg_subkey.values():
                        if reg_value.name() == str(order):
                            recent_docs_information = Recent_Docs_Information()
                            recent_docs_list.append(recent_docs_information)
                            if reg_value.data()[0:reg_value.data().find(b'\x00\x00\x00') + 1].decode('utf-16')[-1] != '6':
                                recent_docs_list[recent_docs_count].file_folder_name = reg_value.data()[0:reg_value.data().find(b'\x00\x00\x00') + 1].decode('utf-16')
                                recent_docs_list[recent_docs_count].file_folder_link = reg_value.data()[0:reg_value.data().find(b'\x00\x00\x00') + 1].decode('utf-16').split('.')[0] + '.lnk'
                            elif reg_value.data()[0:reg_value.data().find(b'\x00\x00\x00') + 1].decode('utf-16')[-1] == '6':
                                recent_docs_list[recent_docs_count].file_folder_name = reg_value.data()[0:reg_value.data().find(b'\x00\x00\x00') + -5].decode('utf-16')
                                recent_docs_list[recent_docs_count].file_folder_link = reg_value.data()[0:reg_value.data().find(b'\x00\x00\x00') + -5].decode('utf-16').split('.')[0] + '.lnk'
                            if recent_docs_count == 0:
                                recent_docs_list[recent_docs_count].modified_time = reg_subkey.last_written_timestamp().isoformat()+'Z'
                            recent_docs_list[recent_docs_count].registry_order = recent_docs_count+1
                            recent_docs_list[recent_docs_count].value = reg_value.name()
                            recent_docs_list[recent_docs_count].source_location = "NTUSER-SOFTWARE/Microsoft/Windows/CurrentVersion/Explorer/RecentDocs/"
                            recent_docs_count = recent_docs_count + 1
    except Exception as exception:
        logger.error(exception)

    return recent_docs_list

