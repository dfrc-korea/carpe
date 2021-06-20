from datetime import datetime, timedelta
import binascii
import codecs
from modules import logger

class Userassist_information:
    par_id = ''
    case_id = ''
    evd_id = ''
    file_name = ''
    type = ''
    userassist_entry_number = ''
    program_run_count = ''
    last_run_time = ''
    focus_count = ''
    focus_seconds = ''
    backup_flag = ''
    source_location = []

def USERASSIST(reg_nt):
    user_list = []
    user_count = 0

    try:
        user_key = reg_nt.find_key(r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\UserAssist\{CEBFF5CD-ACE2-4F4F-9178-9926F41749EA}\Count")
        if user_key != None:
            for user_value in user_key.values():
                userassist_information = Userassist_information()
                user_list.append(userassist_information)
                user_list[user_count].source_location = []
                user_list[user_count].source_location.append('NTUSER-SOFTWARE/Microsoft/Windows/CurrentVersion/Explorer/UserAssist/{CEBFF5CD-ACE2-4F4F-9178-9926F41749EA}/Count')
                user_list[user_count].type = 'File'
                user_list[user_count].file_name = codecs.encode(user_value.name(), "rot13").replace('\\','/')
                user_list[user_count].userassist_entry_number = int(binascii.b2a_hex(user_value.data()[0:4][::-1]), 16)
                user_list[user_count].program_run_count = int(binascii.b2a_hex(user_value.data()[4:8][::-1]), 16)
                user_list[user_count].focus_count = int(binascii.b2a_hex(user_value.data()[8:12][::-1]), 16)
                user_list[user_count].focus_seconds = int(binascii.b2a_hex(user_value.data()[12:16][::-1]), 16)/10000
                user_list[user_count].last_run_time = (datetime(1601, 1, 1) + timedelta(microseconds=int(binascii.b2a_hex(user_value.data()[60:68][::-1]), 16) / 10)).isoformat()+'Z'
                user_count = user_count + 1

        user_key = reg_nt.find_key(r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\UserAssist\{F4E57C4B-2036-45F0-A9AB-443BCFE33D9F}\Count")
        if user_key != None:
            for user_value in user_key.values():
                userassist_information = Userassist_information()
                user_list.append(userassist_information)
                user_list[user_count].source_location = []
                user_list[user_count].source_location.append('NTUSER-SOFTWARE/Microsoft/Windows/CurrentVersion/Explorer/UserAssist/{F4E57C4B-2036-45F0-A9AB-443BCFE33D9F}/Count')
                user_list[user_count].type = 'ShortCut'
                user_list[user_count].file_name = codecs.encode(user_value.name(), "rot13").replace('\\','/')
                user_list[user_count].userassist_entry_number = int(binascii.b2a_hex(user_value.data()[0:4][::-1]), 16)
                user_list[user_count].program_run_count = int(binascii.b2a_hex(user_value.data()[4:8][::-1]), 16)
                user_list[user_count].focus_count = int(binascii.b2a_hex(user_value.data()[8:12][::-1]), 16)
                user_list[user_count].focus_seconds = int(binascii.b2a_hex(user_value.data()[12:16][::-1]), 16)/10000
                user_list[user_count].last_run_time = (datetime(1601, 1, 1) + timedelta(microseconds=int(binascii.b2a_hex(user_value.data()[60:68][::-1]), 16) / 10)).isoformat()+'Z'
                user_count = user_count + 1
    except Exception as exception:
        logger.error(exception)
    return user_list