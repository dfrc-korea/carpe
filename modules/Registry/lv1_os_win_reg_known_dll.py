from modules import logger

class Known_dll_Information:
    par_id = ''
    case_id = ''
    evd_id = ''
    file_name = ''
    dll_directory = ''
    dll_directory_32 = ''
    modified_time = ''
    backup_flag = ''
    source_location = []

def KNOWNDLL(reg_system):
    known_dll_list = []
    known_dll_count = 0

    try:
        known_dll_key = reg_system.find_key(r"ControlSet001\Control\Session Manager\KnownDLLs")
    except Exception as exception:
        logger.error(exception)
    for known_value in known_dll_key.values():
        try:
            known_dll_information = Known_dll_Information()
            known_dll_list.append(known_dll_information)
            known_dll_list[known_dll_count].source_location = []
            known_dll_list[known_dll_count].source_location.append('SYSTEM-ControlSet001/Control/Session Manager/KnownDLLs')
            known_dll_list[known_dll_count].file_name = known_value.data().replace('\x00','')
            known_dll_list[known_dll_count].dll_directory = '\\system32'
            known_dll_list[known_dll_count].dll_directory_32 = '\\syswow64'
            known_dll_list[known_dll_count].modified_time = known_dll_key.last_written_timestamp().isoformat()+'Z'
            known_dll_count = known_dll_count + 1
        except Exception as exception:
            logger.error(exception)
    return known_dll_list