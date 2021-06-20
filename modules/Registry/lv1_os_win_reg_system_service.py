from datetime import datetime, timedelta
import binascii
from modules import logger

class System_Service_Information:
    par_id = ''
    case_id = ''
    evd_id = ''
    service_name = ''
    service_type = ''
    start_type = ''
    service_location = ''
    groups = ''
    display_name = ''
    dependancy = ''
    user_account =''
    description = ''
    service_detail_information = ''
    host_flag = 'No'
    host_service = ''
    hosted_service_parameter = ''
    modified_time = ''
    error_control = ''
    tag = ''
    backup_flag = ''
    source_location = []

def SYSTEMSERVICE(reg_system):
    system_service_list = []
    system_service_count = 0

    try:
        reg_key = reg_system.find_key(r"ControlSet001\Services")
    except Exception as exception:
        logger.error(exception)
    try:
        for reg_subkey in reg_key.subkeys():
            if reg_subkey.name().startswith('.') is not True:
                system_service_information = System_Service_Information()
                system_service_list.append(system_service_information)
                system_service_list[system_service_count].source_location = []
                system_service_list[system_service_count].source_location.append('SYSTEM-ControlSet001/Services')
                system_service_list[system_service_count].modified_time = reg_subkey.last_written_timestamp().isoformat()+'Z'
                for reg_subkey_values in reg_subkey.values():
                    if reg_subkey_values.name() == 'ImagePath':
                        system_service_list[system_service_count].service_location = reg_subkey_values.data().replace('\x00','')
                        if 'exe' in reg_subkey_values.data():
                            system_service_list[system_service_count].service_name = reg_subkey_values.data().split('exe')[0].split('\\')[-1]+'exe'
                        else:
                            system_service_list[system_service_count].service_name = reg_subkey_values.data().split('\\')[-1].replace('\x00', '')
                    elif reg_subkey_values.name() == 'Type':
                        if reg_subkey_values.data() == 1:
                            system_service_list[system_service_count].service_type = 'KernelDriver'
                        elif reg_subkey_values.data() == 2:
                            system_service_list[system_service_count].service_type = 'FileSystemDriver'
                        elif reg_subkey_values.data() == 16:
                            system_service_list[system_service_count].service_type = 'Win32OwnProcess'
                        elif reg_subkey_values.data() == 32:
                            system_service_list[system_service_count].service_type = 'Win32ShareProcess'
                    elif reg_subkey_values.name() == 'Start':
                        if reg_subkey_values.data() == 0:
                            system_service_list[system_service_count].start_type = 'Boot'
                        elif reg_subkey_values.data() == 1:
                            system_service_list[system_service_count].start_type = 'System'
                        elif reg_subkey_values.data() == 2:
                            system_service_list[system_service_count].start_type = 'Automatic'
                        elif reg_subkey_values.data() == 3:
                            system_service_list[system_service_count].start_type = 'Manual'
                        elif reg_subkey_values.data() == 4:
                            system_service_list[system_service_count].start_type = 'Disabled'
                    elif reg_subkey_values.name() == 'DisplayName':
                        system_service_list[system_service_count].display_name = \
                            str(reg_subkey_values.data()).replace("'", '"').replace('\x00', '')
                    elif reg_subkey_values.name() == 'ImagePath':
                        system_service_list[system_service_count].service_detail_information = reg_subkey_values.data()
                    elif reg_subkey_values.name() == 'ErrorControl':
                        if reg_subkey_values.data() == 0:
                            system_service_list[system_service_count].error_control = 'Ignore'
                        elif reg_subkey_values.data() == 1:
                            system_service_list[system_service_count].error_control = 'Normal'
                        elif reg_subkey_values.data() == 2:
                            system_service_list[system_service_count].error_control = 'Severe'
                        elif reg_subkey_values.data() == 3:
                            system_service_list[system_service_count].error_control = 'Critical'
                    elif reg_subkey_values.name() == 'Group':
                        system_service_list[system_service_count].groups = reg_subkey_values.data().replace('\x00','')
                    elif reg_subkey_values.name() == 'ObjectName':
                        system_service_list[system_service_count].user_account = reg_subkey_values.data().replace('\x00','')
                    elif reg_subkey_values.name() == 'Description':
                        system_service_list[system_service_count].description = reg_subkey_values.data().replace("'",'"').replace('\x00','')
                    elif reg_subkey_values.name() == 'DependOnService':
                        if type(reg_subkey_subkey_value.data()) == list:
                            system_service_list[system_service_count].dependancy = ','.join(reg_subkey_subkey_value.data())
                        elif type(reg_subkey_subkey_value.data()) == bytes:
                            system_service_list[system_service_count].dependancy = ''
                        else:
                            system_service_list[system_service_count].dependancy = reg_subkey_subkey_value.data()
                    elif reg_subkey_values.name() == 'Tag':
                        system_service_list[system_service_count].tag = reg_subkey_values.data()

                temp_array = []
                for reg_subkey_subkey in reg_subkey.subkeys():
                    if reg_subkey_subkey.name() == 'Parameters':
                        for reg_subkey_subkey_value in reg_subkey_subkey.values():
                            if reg_subkey_subkey_value.name() == 'ServiceDll':
                                system_service_list[system_service_count].host_service = reg_subkey_subkey_value.data().replace('\x00','')
                            else:
                                if type(reg_subkey_subkey_value.data()) == int or type(reg_subkey_subkey_value.data()) == str:
                                    temp_array.append(reg_subkey_subkey_value.name() + ': ' + str(reg_subkey_subkey_value.data()))
                                elif type(reg_subkey_subkey_value.data()) == list:
                                    if len(reg_subkey_subkey_value.data()) != 0:
                                        temp_array.append(reg_subkey_subkey_value.name() + ': ' + ','.join(reg_subkey_subkey_value.data()))
                                    else:
                                        temp_array.append(reg_subkey_subkey_value.name())
                                else:
                                    try:
                                        temp_array.append(reg_subkey_subkey_value.name() + ': ' +
                                                          str(int(binascii.b2a_hex(reg_subkey_subkey_value.data()[::-1]).decode(), 16)))
                                    except:
                                        pass
                system_service_list[system_service_count].host_service = ','.join(temp_array).replace('\x00','')
                system_service_count = system_service_count + 1
    except Exception as exception:
        logger.error(exception)
    return system_service_list