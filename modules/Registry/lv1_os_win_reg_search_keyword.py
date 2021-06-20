from datetime import datetime, timedelta
import binascii
from modules import logger

class Search_Keyword_Information:
    par_id = ''
    case_id = ''
    evd_id = ''
    keyword = ''
    modified_time = ''
    ordering = ''
    useraccount = ''
    backup_flag = ''
    source_location = []

def SEARCHKEYWORD(reg_nt):
    search_keyword_list = []
    search_keyword_count = 0
    search_keyword_order = []

    try:
        reg_key = reg_nt.find_key(r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\WordWheelQuery")
    except Exception as exception:
        logger.error(exception)
    try:
        if reg_key != None:
            for reg_value in reg_key.values():
                if reg_value.name() == 'MRUListEx':
                    for i in range(0, len(list(reg_key.values()))-2):
                        search_keyword_order.append(int(binascii.b2a_hex(reg_value.data()[4*i:4*i+4][::-1]), 16))

            for order in search_keyword_order:
                for reg_value in reg_key.values():
                    if reg_value.name() == str(order):
                        search_keyword_information = Search_Keyword_Information()
                        search_keyword_list.append(search_keyword_information)
                        search_keyword_list[search_keyword_count].source_location = []
                        search_keyword_list[search_keyword_count].source_location.append('NTUSER-SOFTWARE/Microsoft/Windows/CurrentVersion/Explorer/WordWheelQuery')
                        search_keyword_list[search_keyword_count].keyword = reg_value.data().decode('utf-16').replace('\x00','')
                        if search_keyword_count == 0:
                            search_keyword_list[search_keyword_count].modified_time = reg_key.last_written_timestamp().isoformat()+'Z'
                        search_keyword_list[search_keyword_count].ordering = search_keyword_count+1
                        search_keyword_count = search_keyword_count + 1
    except Exception as exception:
        logger.error(exception)
    return search_keyword_list

