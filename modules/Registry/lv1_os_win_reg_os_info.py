from datetime import datetime, timedelta
import binascii

import modules.Registry.convert_util as cu
from modules import logger


class OS_Information:
    par_id = ''
    case_id = ''
    evd_id = ''
    operating_system = ''
    release_id = ''
    version_number = ''
    install_time = ''
    product_key = ''
    owner = ''
    display_computer_name = ''
    computer_name = ''
    dhcp_dns_server = ''
    operating_system_version = ''
    build_number = ''
    product_id = ''
    last_service_pack = ''
    organization = ''
    last_shutdown_time = ''
    system_root = ''
    path = ''
    last_access_time_flag = ''
    timezone_utc = ''
    display_timezone_name = ''
    backup_flag = ''
    source_location = []

def decode_key(rpk):
    rpk_offset = 52

    is_win8 = (rpk[66]/6) and 1
    rpk[66] = (rpk[66] & 0xf7) | ((is_win8 & 2) * 4)
    i = 24
    sz_possible_chars = "BCDFGHJKMPQRTVWXY2346789"
    sz_product_key = ""
    while i >= 0:
        dw_accumulator = 0
        j = 14
        while j >= 0:
            dw_accumulator = dw_accumulator * 256
            d = rpk[j+rpk_offset]
            dw_accumulator = d + dw_accumulator
            rpk[j+rpk_offset] = int(dw_accumulator / 24)
            dw_accumulator = dw_accumulator % 24
            j = j - 1
        i = i - 1
        sz_product_key = sz_possible_chars[dw_accumulator] + sz_product_key
        last = dw_accumulator

    keypart1 = sz_product_key[1:1 + last]
    insert = 'N'
    sz_product_key = sz_product_key[1:].replace(keypart1, keypart1 + insert, 1)
    if last == 0:
        sz_product_key = insert + sz_product_key
    sz_product_key = '{0}-{1}-{2}-{3}-{4}'.format(sz_product_key[1:6], sz_product_key[6:11], sz_product_key[11:16],
                                                sz_product_key[16:21], sz_product_key[21:26])

    return sz_product_key

def OSINFO(reg_software, reg_system):
    os_list = []
    os_count = 0
    os_key_list = []

    try:
        os_key_list.append(reg_software.find_key(r"Microsoft\Windows NT\CurrentVersion"))
        os_key_list.append(reg_system.find_key(r"ControlSet001\Control\ComputerName\ComputerName"))
        os_key_list.append(reg_system.find_key(r"ControlSet001\Control\FileSystem"))
        os_key_list.append(reg_system.find_key(r"ControlSet001\Control\TimeZoneInformation"))
        os_key_list.append(reg_system.find_key(r"ControlSet001\Services\Tcpip\Parameters"))
        os_key_list.append(reg_system.find_key(r"ControlSet001\Control\Windows"))
        os_information = OS_Information()
        os_list.append(os_information)
        os_list[os_count].source_location = []
        os_list[os_count].source_location.append('SOFTWARE-Microsoft/Windows NT/CurrentVersion')
        os_list[os_count].source_location.append('SYSTEM-ControlSet001/Control/ComputerName/ComputerName')
        os_list[os_count].source_location.append('SYSTEM-ControlSet001/Control/FileSystem')
        os_list[os_count].source_location.append('SYSTEM-ControlSet001/Control/TimeZoneInformation')
        os_list[os_count].source_location.append('SYSTEM-ControlSet001/Services/Tcpip/Parameters')
        os_list[os_count].source_location.append('SYSTEM-ControlSet001/Control/Windows')

        for os_key in os_key_list:
            for os_value in os_key.values():
                if os_value.name() == 'ProductName':
                    os_list[os_count].operating_system = os_value.data().replace('\x00', '')
                elif os_value.name()  == 'DigitalProductId':
                    value = []
                    for data in os_value.data():
                        value.append(data)
                    os_list[os_count].product_key = decode_key(value)
                elif os_value.name() == 'ReleaseId':
                    os_list[os_count].release_id = os_value.data().replace('\x00', '')
                elif os_value.name() == 'CSDVersion':
                    os_list[os_count].last_service_pack = os_value.data()
                elif os_value.name() == 'SystemRoot':
                    os_list[os_count].system_root = os_value.data().replace('\x00', '')
                elif os_value.name() == 'PathName':
                    os_list[os_count].path = os_value.data().replace('\x00', '')
                elif os_value.name() == 'EditionID':
                    os_list[os_count].operating_system_version = os_value.data().replace('\x00', '')
                elif os_value.name() == 'RegisteredOrganization':
                    os_list[os_count].organization = os_value.data().replace('\x00', '')
                elif os_value.name() == 'CurrentVersion':
                    os_list[os_count].version_number = os_value.data().replace('\x00', '')
                elif os_value.name() == 'CurrentBuildNumber':
                    os_list[os_count].build_number = os_value.data().replace('\x00', '')
                elif os_value.name() == 'ProductId':
                    os_list[os_count].product_id = os_value.data().replace('\x00', '')
                elif os_value.name() == 'RegisteredOwner':
                    os_list[os_count].owner = os_value.data().replace('\x00', '')
                elif os_value.name() == 'InstallDate':
                    os_list[os_count].install_time = cu.from_unix_timestamp(os_value.data())
                elif os_value.name() == 'ComputerName':
                    os_list[os_count].computer_name = os_value.data().replace('\x00', '')
                elif os_value.name() == 'NtfsDisableLastAccessUpdate':
                    # 0: True, 1: False
                    os_list[os_count].last_access_time_flag = os_value.data()
                elif os_value.name() == 'TimeZoneKeyName':
                    os_list[os_count].display_timezone_name = os_value.data().replace('\x00', '')
                    for j in reg_software.find_key(r"Microsoft\Windows NT\CurrentVersion\Time Zones").subkeys():
                        if j.name() == os_list[os_count].display_timezone_name:
                            for k in j.values():
                                if k.name() == 'Display':
                                    os_list[os_count].timezone_utc = k.data().replace('\x00', '')
                elif os_value.name() == 'HostName':
                    os_list[os_count].display_computer_name = os_value.data().replace('\x00', '')
                elif os_value.name() == 'Hostname':
                    os_list[os_count].display_computer_name = os_value.data().replace('\x00', '')
                elif os_value.name() == 'DhcpNameServer':
                    os_list[os_count].dhcp_dns_server = os_value.data().replace('\x00', '')
                elif os_value.name() == 'ShutdownTime':
                    os_list[os_count].last_shutdown_time = (datetime(1601, 1, 1) + timedelta(microseconds=int(binascii.b2a_hex(os_value.data()[::-1]), 16) / 10)).isoformat()+'Z'
    except Exception as exception:
        logger.error(exception)
    return os_list