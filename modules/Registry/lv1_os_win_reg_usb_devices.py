import datetime
from modules import logger


class Device_information:
    par_id = ''
    case_id = ''
    evd_id = ''
    device_class_id = ''
    serial_number = ''
    type = ''
    last_connected_time = ''  # Enum
    device_description = ''
    friendly_name = ''
    manufacturer = ''
    last_assigned_drive_letter = ''
    volume_GUID = ''
    volume_serial_number_decimal = ''
    volume_serial_number_hex = ''
    associated_user_accounts = ''
    first_connected_time = ''  # setupapi
    first_connected_since_reboot_time = ''  # deviceClasses
    driver_install_time = ''  # 64
    first_install_time = ''  # 65
    last_insertion_time = ''  # 66
    last_removal_time = ''  # 67
    backup_flag = ''
    source_location = []


def USBDEVICES(reg_software, reg_system, text_data):
    device_list = []
    device_key_list1 = []
    device_key_list2 = []
    device_count = 0

    try:
        device_key_list1.append(reg_system.find_key(r"ControlSet001\Enum\USBSTOR"))
        device_key_list1.append(reg_system.find_key(r"ControlSet001\Enum\USB"))
        device_key_list1.append(reg_system.find_key(r"ControlSet001\Enum\SCSI"))

        for device_key in device_key_list1:
            if device_key is None:
                continue
            for device_class_id in device_key.subkeys():
                for serial_number in device_class_id.subkeys():
                    device_information = Device_information()
                    device_list.append(device_information)
                    if device_key == device_key_list1[0]:
                        device_list[device_count].source_location = []
                        device_list[device_count].source_location.append('SYSTEM-ControlSet001/Enum/USBSTOR')
                    elif device_key == device_key_list1[1]:
                        device_list[device_count].source_location = []
                        device_list[device_count].source_location.append('SYSTEM-ControlSet001/Enum/USB')
                    elif device_key == device_key_list1[2]:
                        device_list[device_count].source_location = []
                        device_list[device_count].source_location.append('SYSTEM-ControlSet001/Enum/SCSI')

                    device_list[device_count].device_class_id = device_class_id.name()
                    device_list[device_count].serial_number = serial_number.name()
                    device_list[
                        device_count].last_connected_time = serial_number.last_written_timestamp().isoformat() + 'Z'
                    for serial_number_value in serial_number.values():
                        if serial_number_value.name() == 'DeviceDesc':
                            device_list[device_count].device_description = serial_number_value.data().replace('\x00',
                                                                                                              '')
                        elif serial_number_value.name() == 'Mfg':
                            device_list[device_count].manufacturer = serial_number_value.data().replace('\x00', '')
                        elif serial_number_value.name() == 'FriendlyName':
                            device_list[device_count].friendly_name = serial_number_value.data().replace('\x00', '')
                    for properties in serial_number.subkeys():
                        for properties_subkey in properties.subkeys():
                            if '83da6326' in properties_subkey.name():
                                for properties_time_data in properties_subkey.subkeys():
                                    if properties_time_data.name() == '0064':
                                        device_list[
                                            device_count].driver_install_time = properties_time_data.last_written_timestamp().isoformat() + 'Z'
                                    elif properties_time_data.name() == '0065':
                                        device_list[
                                            device_count].first_install_time = properties_time_data.last_written_timestamp().isoformat() + 'Z'
                                    elif properties_time_data.name() == '0066':
                                        device_list[
                                            device_count].last_insertion_time = properties_time_data.last_written_timestamp().isoformat() + 'Z'
                                    elif properties_time_data.name() == '0067':
                                        device_list[
                                            device_count].last_removal_time = properties_time_data.last_written_timestamp().isoformat() + 'Z'
                    device_count = device_count + 1

        try:
            device_key_list2.append(reg_system.find_key(r"ControlSet001\Enum\STORAGE\Volume"))
            device_key_list2.append(reg_system.find_key(r"ControlSet001\Enum\STORAGE\VolumeSnapshot"))
            device_key_list2.append(reg_system.find_key(r"ControlSet001\Enum\SWD\WPDBUSENUM"))

            for device_key in device_key_list2:
                if device_key != None:
                    for device_class_id in device_key.subkeys():
                        device_information = Device_information()
                        device_list.append(device_information)
                        if device_key == device_key_list2[0]:
                            device_list[device_count].source_location = []
                            device_list[device_count].source_location.append('SYSTEM-ControlSet001/Enum/STORAGE/Volume')
                        elif device_key == device_key_list2[1]:
                            device_list[device_count].source_location = []
                            device_list[device_count].source_location.append(
                                'SYSTEM-ControlSet001/Enum/STORAGE/VolumeSnapshot')
                        elif device_key == device_key_list2[2]:
                            device_list[device_count].source_location = []
                            device_list[device_count].source_location.append('SYSTEM-ControlSet001/Enum/SWD/WPDBUSENUM')
                        if '??' in device_class_id.name():
                            device_list[device_count].device_class_id = device_class_id.name().split('#')[1]
                            device_list[device_count].serial_number = device_class_id.name().split('#')[2]
                            device_list[
                                device_count].first_connected_since_reboot_time = device_class_id.last_written_timestamp().isoformat() + 'Z'
                        elif '??' not in device_class_id.name() and '#' in device_class_id.name():
                            device_list[device_count].device_class_id = device_class_id.name().split('#')[0][1:-1]
                            device_list[device_count].serial_number = device_class_id.name().split('#')[1]
                            device_list[
                                device_count].first_connected_since_reboot_time = device_class_id.last_written_timestamp().isoformat() + 'Z'
                        else:
                            device_list[device_count].device_class_id = device_class_id.name()
                        for device_class_id_value in device_class_id.values():
                            if device_class_id_value.name() == 'DeviceDesc':
                                device_list[device_count].device_description = device_class_id_value.data().replace(
                                    '\x00', '')
                            elif device_class_id_value.name() == 'Mfg':
                                device_list[device_count].manufacturer = device_class_id_value.data().replace('\x00',
                                                                                                              '')
                            elif device_class_id_value.name() == 'FriendlyName':
                                device_list[device_count].friendly_name = device_class_id_value.data().replace('\x00',
                                                                                                               '')
                        for properties in device_class_id.subkeys():
                            for properties_subkey in properties.subkeys():
                                if '83da6326' in properties_subkey.name():
                                    for properties_time_data in properties_subkey.subkeys():
                                        if properties_time_data.name() == '0064':
                                            device_list[
                                                device_count].driver_install_time = properties_time_data.last_written_timestamp().isoformat() + 'Z'
                                        elif properties_time_data.name() == '0065':
                                            device_list[
                                                device_count].first_install_time = properties_time_data.last_written_timestamp().isoformat() + 'Z'
                                        elif properties_time_data.name() == '0066':
                                            device_list[
                                                device_count].last_insertion_time = properties_time_data.last_written_timestamp().isoformat() + 'Z'
                                        elif properties_time_data.name() == '0067':
                                            device_list[
                                                device_count].last_removal_time = properties_time_data.last_written_timestamp().isoformat() + 'Z'
                        device_count = device_count + 1
        except Exception as exception:
            logger.error(exception)
        # last_assigned_drive_letter
        reg_key = reg_system.find_key(r"MountedDevices")
        for reg_value in reg_key.values():
            if 'Volume' in reg_value.name():
                if reg_value.data()[2] == 63:
                    for device in device_list:
                        if device.serial_number == reg_value.data().decode('utf-16').split('#')[2]:
                            device.volume_GUID = reg_value.name().split('Volume')[1][1:-1]
                            for reg_value_drive_letter in reg_key.values():
                                if 'DosDevices' in reg_value_drive_letter.name():
                                    if reg_value.data() == reg_value_drive_letter.data():
                                        device.last_assigned_drive_letter = reg_value_drive_letter.name().split('\\')[
                                            2].replace('\x00', '')
                                        device.source_location.append('SYSTEM-MountedDevices')

        # VSN (volume Serial Number) - emdMgmt
        reg_key = reg_software.find_key(r"Microsoft\Windows NT\CurrentVersion\EMDMgmt")
        if reg_key is not None:
            for reg_subkey in reg_key.subkeys():
                for device in device_list:
                    if device.serial_number == reg_subkey.name().decode('utf-16').split('#')[2]:
                        device.volume_serial_number_decimal = reg_subkey.name().split('_')[-1]
                        device.source_location.append('SOFTWARE-Microsoft/Windows NT/CurrentVersion/EMDMgmt')

        # first_connected_time - SETUPAPI
        for device_class_id in str(text_data).split(
                ">>>  [Device Install (Hardware initiated) - SWD\\\\WPDBUSENUM\\\\"):
            if device_class_id.startswith('_'):
                for device in device_list:
                    if device.serial_number == device_class_id.split('\\r\\n')[0].split('#')[2]:
                        temp_date = datetime.datetime.strptime(device_class_id.split('\\r\\n')[1].split('start ')[1],
                                                               "%Y/%m/%d %H:%M:%S.%f")
                        temp_date2 = temp_date - datetime.timedelta(hours=9)
                        device.first_connected_time = str(temp_date2).replace(' ', 'T') + 'Z'
                        device.source_location.append('setupapi.dev.log')

    except Exception as exception:
        logger.error(exception)

    return device_list