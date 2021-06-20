from modules import logger

class Mac_Address_Information:
    par_id = ''
    case_id = ''
    evd_id = ''
    mac_address = ''
    description = ''
    backup_flag = ''
    source_location = []

def MACADDRESS(reg_system):
    mac_address_list = []
    mac_address_count = 0

    try:
        reg_key = reg_system.find_key(r"ControlSet001\Control\Class\{4d36e972-e325-11ce-bfc1-08002be10318}")
    except Exception as exception:
        logger.error(exception)
    for reg_subkey in reg_key.subkeys():
        try:
            for reg_subkey_value in reg_subkey.values():
                if reg_subkey_value.name() == 'DeviceInstanceID':
                    if 'FFFF' in reg_subkey_value.data():
                        mac_address_information = Mac_Address_Information()
                        mac_address_list.append(mac_address_information)
                        mac_address_list[mac_address_count].source_location = []
                        mac_address_list[mac_address_count].source_location.append('SYSTEM-ControlSet001/Control/Class/{4d36e972-e325-11ce-bfc1-08002be10318}')
                        mac_address_list[mac_address_count].mac_address = reg_subkey_value.data().split('\\')[-1][0:6] + reg_subkey_value.data().split('\\')[-1][10:16]
                        mac_address_list[mac_address_count].description = reg_subkey.value(name='DriverDesc').data()
                        mac_address_count = mac_address_count + 1
        except Exception as exception:
            logger.error(exception)
    return mac_address_list