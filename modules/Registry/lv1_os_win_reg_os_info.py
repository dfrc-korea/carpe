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
                    if os_value.data()[:-1] == 'Windows 10 Pro':
                        os_list[os_count].product_key = 'W269N-WFGWX-YVC9B-4J6C9-T83GX'
                    elif os_value.data()[:-1] == 'Windows 10 Pro N':
                        os_list[os_count].product_key = 'MH37W-N47XK-V7XM9-C7227-GCQG9'
                    elif os_value.data()[:-1] == 'Windows 10 Pro for Workstations':
                        os_list[os_count].product_key = 'NRG8B-VKK3Q-CXVCJ-9G2XF-6Q84J'
                    elif os_value.data()[:-1] == 'Windows 10 Pro for Workstations N':
                        os_list[os_count].product_key = '9FNHH-K3HBT-3W4TD-6383H-6XYWF'
                    elif os_value.data()[:-1] == 'Windows 10 Pro Education':
                        os_list[os_count].product_key = '6TP4R-GNPTD-KYYHQ-7B7DP-J447Y'
                    elif os_value.data()[:-1] == 'Windows 10 Pro Education N':
                        os_list[os_count].product_key = 'YVWGF-BXNMC-HTQYQ-CPQ99-66QFC'
                    elif os_value.data()[:-1] == 'Windows 10 Education':
                        os_list[os_count].product_key = 'NW6C2-QMPVW-D7KKK-3GKT6-VCFB2'
                    elif os_value.data()[:-1] == 'Windows 10 Education KN':
                        os_list[os_count].product_key = '2WH4N-8QGBV-H22JP-CT43Q-MDWWJ'
                    elif os_value.data()[:-1] == 'Windows 10 Enterprise':
                        os_list[os_count].product_key = 'NPPR9-FWDCX-D2C8J-H872K-2YT43'
                    elif os_value.data()[:-1] == 'Windows 10 Enterprise KN':
                        os_list[os_count].product_key = 'DPH2V-TTNVB-4X9Q3-TJR4H-KHJW4'
                    elif os_value.data()[:-1] == 'Windows 10 Enterprise G':
                        os_list[os_count].product_key = 'YYVX9-NTFWV-6MDM3-9PT4T-4M68B'
                    elif os_value.data()[:-1] == 'Windows 10 Enterprise G N':
                        os_list[os_count].product_key = '44RPN-FTY23-9VTTB-MP9BX-T84FV'
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
                elif os_value.name() == 'ReleaseId':
                    os_list[os_count].release_id = os_value.data()
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