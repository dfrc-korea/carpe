from datetime import datetime, timedelta
import binascii
from modules import logger

class Run_Command_Information:
    par_id = ''
    case_id = ''
    evd_id = ''
    command = ''
    modified_time = ''
    ordering = ''
    useraccount = ''
    backup_flag = ''
    source_location = []

def RUNCOMMAND(reg_nt):
    run_command_list = []
    run_command_count = 0
    run_command_order = []
    try:
        reg_key = reg_nt.find_key(r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\RunMRU")
    except Exception as exception:
        logger.error(exception)
    try:
        if reg_key != None:
            for reg_value in reg_key.values():
                if reg_value.name() == 'MRUList':
                    for i in reg_value.data():
                        run_command_order.append(i)

            for order in run_command_order:
                for reg_value in reg_key.values():
                    if reg_value.name() == str(order):
                        run_command_information = Run_Command_Information()
                        run_command_list.append(run_command_information)
                        run_command_list[run_command_count].source_location = []
                        run_command_list[run_command_count].source_location.append('NTUSER-SOFTWARE/Microsoft/Windows/CurrentVersion/Explorer/RunMRU')
                        run_command_list[run_command_count].command = reg_value.data().replace('\x00','')
                        if run_command_count == 0:
                            run_command_list[run_command_count].modified_time = reg_key.last_written_timestamp().isoformat()+'Z'
                        run_command_list[run_command_count].ordering = run_command_count+1
                        run_command_count = run_command_count + 1
    except Exception as exception:
        logger.error(exception)
    return run_command_list

