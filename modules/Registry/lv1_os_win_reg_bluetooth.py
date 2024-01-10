from modules import logger

class Bluetooth_Information:
    par_id = ''
    case_id = ''
    evd_id = ''
    name = ''
    key_last_updated_time = ''
    lastconnectedtime = ''
    backup_flag = ''
    source = ''

def Bluetooth(reg_system):
    bluetooth_list = []
    bluetooth_count = 0
    try:
        bluetooth_key = reg_system.find_key(r"ControlSet001\Services\BTHPORT\Parameters\Devices") ####
    except Exception as exception:
        logger.error(exception)
        return bluetooth_list

    if bluetooth_key == None:
        return bluetooth_list

    for bluetooth_subkey in bluetooth_key.subkeys():
        try:
            bluetooth_information = Bluetooth_Information()
            bluetooth_list.append(bluetooth_information)
            bluetooth_list[bluetooth_count].source = r"ControlSet001\Services\BTHPORT\Parameters\Devices"+'/'+bluetooth_subkey.name()
            bluetooth_list[bluetooth_count].key_last_updated_time = bluetooth_subkey.last_written_timestamp().isoformat()+'Z'
            for bluetooth_subkey_value in bluetooth_subkey.values():
                if bluetooth_subkey_value.name() == 'Name':
                    if str(type(bluetooth_subkey_value.data()))=="<class 'bytes'>":
                        bluetooth_list[bluetooth_count].name = bluetooth_subkey_value.data().decode('utf-8')[:-1]
                    else:
                        bluetooth_list[bluetooth_count].name = bluetooth_subkey_value.data().replace('\x00','')
                elif bluetooth_subkey_value.name() == 'LastConnceted':
                    bluetooth_list[bluetooth_count].lastconnectedtime = bluetooth_subkey_value.data().replace('\x00','')

            bluetooth_count = bluetooth_count + 1
        except Exception as exception:
            logger.error(exception)

    return bluetooth_list

