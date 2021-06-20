from datetime import datetime, timedelta
import binascii
from modules import logger

class Start_Information:
    par_id = ''
    case_id = ''
    evd_id = ''
    program_name = ''
    path = ''
    modified_time = ''
    type = ''
    backup_flag = ''
    source_location = []

def START(reg_software, reg_nt):
    start_list = []
    start_count = 0

    try:
        if reg_software != '':
            reg_key = reg_software.find_key(r"Wow6432Node\Microsoft\Windows\CurrentVersion\Run")
            if reg_key is not None:
                for reg_value in reg_key.values():
                    start_information = Start_Information()
                    start_list.append(start_information)
                    start_list[start_count].source_location = []
                    start_list[start_count].source_location.append('SOFTWARE-Wow6432Node/Microsoft/Windows/CurrentVersion/Run')
                    start_list[start_count].program_name = reg_value.name()
                    if len(reg_value.data()) != 0:
                        start_list[start_count].path = reg_value.data().replace('\x00','')
                    else:
                        start_list[start_count].path = ''
                    start_list[start_count].modified_time = reg_key.last_written_timestamp().isoformat()+'Z'
                    start_list[start_count].type = 'Run'
                    start_count = start_count + 1

            reg_key = reg_software.find_key(r"Microsoft\Windows\CurrentVersion\Run")
            if reg_key is not None:
                for reg_value in reg_key.values():
                    start_information = Start_Information()
                    start_list.append(start_information)
                    start_list[start_count].source_location = []
                    start_list[start_count].source_location.append('SOFTWARE-Microsoft/Windows/CurrentVersion/Run')
                    start_list[start_count].program_name = reg_value.name()
                    if len(reg_value.data()) != 0:
                        start_list[start_count].path = reg_value.data().replace('\x00', '')
                    else:
                        start_list[start_count].path = ''
                    start_list[start_count].modified_time = reg_key.last_written_timestamp().isoformat() + 'Z'
                    start_list[start_count].type = 'Run'
                    start_count = start_count + 1

        reg_key = reg_nt.find_key(r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run")
        if reg_key is not None:
            for reg_value in reg_key.values():
                start_information = Start_Information()
                start_list.append(start_information)
                start_list[start_count].source_location = []
                start_list[start_count].source_location.append('NUTSER-SOFTWARE/Microsoft/Windows/CurrentVersion/Run')
                start_list[start_count].program_name = reg_value.name()
                # TODO: bytes 일 때와 str일 때 나눠서 처리 필요 
                if len(reg_value.data()) != 0 and type(reg_value.data()) == str:
                    start_list[start_count].path = reg_value.data().replace('\x00', '')
                else:
                    start_list[start_count].path = ''
                start_list[start_count].modified_time = reg_key.last_written_timestamp().isoformat() + 'Z'
                start_list[start_count].type = 'Run'
                start_count = start_count + 1
    except Exception as exception:
        logger.error(exception)

    return start_list