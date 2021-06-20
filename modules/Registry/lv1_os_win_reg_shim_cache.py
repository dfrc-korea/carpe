from datetime import datetime, timedelta
import binascii
import struct
from modules import logger

class Shim_Cache_Information:
    par_id = ''
    case_id = ''
    evd_id = ''
    file_name = ''
    file_path = ''
    modified_time = ''
    backup_flag = ''
    source_location = []

def convettime(dwLowDateTime,dwHighDateTime):
    try:
        date = datetime(1601, 1, 1, 0, 0, 0)
        temp_time = dwHighDateTime
        temp_time <<= 32
        temp_time |= dwLowDateTime
        return date + timedelta(microseconds=temp_time / 10)
    except:
        return None

def SHIMCACHE(reg_system):
    shim_cache_list = []
    shim_cache_count = 0

    try:
        reg_key = reg_system.find_key(r"ControlSet001\Control\Session Manager\AppCompatCache")
    except Exception as exception:
        logger.error(exception)
    try:
        for reg_value in reg_key.values():
            if reg_value.name() == 'AppCompatCache':
                for i in reg_value.data().split(b'10ts')[1:]:
                    if len(i.split(b'\x00e\x00x\x00e')) > 1:
                        shim_cache_information = Shim_Cache_Information()
                        shim_cache_list.append(shim_cache_information)
                        shim_cache_list[shim_cache_count].source_location = []
                        shim_cache_list[shim_cache_count].source_location.append('SYSTEM-SOFTWARE/ControlSet001/Control/Session Manager/AppCompatCache')
                        shim_cache_list[shim_cache_count].file_path = i[10:i[8]+10].decode('utf-16').replace('\\','/')
                        shim_cache_list[shim_cache_count].file_name = i[10:i[8]+10].decode('utf-16').split('\\')[-1]
                        dwLowDateTime, dwHighDateTime = struct.unpack('<LL',i[i[8]+10:i[8]+18])
                        if convettime(dwLowDateTime, dwHighDateTime) != None:
                            shim_cache_list[shim_cache_count].modified_time = convettime(dwLowDateTime, dwHighDateTime).isoformat()+'Z'
                        shim_cache_count = shim_cache_count + 1
    except Exception as exception:
        logger.error(exception)
    return shim_cache_list