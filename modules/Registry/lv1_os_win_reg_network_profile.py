from datetime import datetime, timedelta
import binascii
from modules import logger

class Network_Profile_Information:
    par_id = ''
    case_id = ''
    evd_id = ''
    profile_name = ''
    profile_guid = ''
    description = ''
    datecreated = ''
    datelstconnected = ''
    dns = ''
    default_gateway_mac = ''
    backup_flag = ''
    source_location = []


def NETWORKPROFILE(reg_software):
    network_profile_list = []
    network_profile_count = 0

    try:
        reg_key = reg_software.find_key(r"Microsoft\Windows NT\CurrentVersion\NetworkList\Profiles")
    except Exception as exception:
        logger.error(exception)
    try:
        for reg_subkey in reg_key.subkeys():
            network_profile_information = Network_Profile_Information()
            network_profile_list.append(network_profile_information)
            network_profile_list[network_profile_count].source_location = []
            network_profile_list[network_profile_count].source_location.append('SOFTWARE-Microsoft/Windows NT/CurrentVersion/NetworkList/Profiles')
            network_profile_list[network_profile_count].profile_guid = reg_subkey.name()
            for reg_subkey_value in reg_subkey.values():
                if reg_subkey_value.name() == 'ProfileName':
                    network_profile_list[network_profile_count].profile_name = reg_subkey_value.data().replace('\x00','')
                elif reg_subkey_value.name() == 'Description':
                    network_profile_list[network_profile_count].description = reg_subkey_value.data().replace('\x00','')
                # 128bit... 어떻게 바꾸는지 확인 필요
                '''
                elif reg_subkey_value.name() == 'DateCreated':
                    network_profile_list[network_profile_count].datecreated = reg_subkey_value.data()
                elif reg_subkey_value.name() == 'DateLastConnected':
                    network_profile_list[network_profile_count].datelstconnected = reg_subkey_value.data()
                '''
            network_profile_count = network_profile_count + 1

        reg_key = reg_software.find_key(r"Microsoft\Windows NT\CurrentVersion\NetworkList\Signatures\Unmanaged")
        for reg_subkey in reg_key.subkeys():
            for network_profile in network_profile_list:
                if reg_subkey.value(name='ProfileGuid').data()[:-1] == network_profile.profile_guid:
                    for reg_subkey_value in reg_subkey.values():
                        if reg_subkey_value.name() == 'DnsSuffix':
                            network_profile.dns = reg_subkey_value.data().replace('\x00','')
                        elif reg_subkey_value.name() == 'DefaultGatewayMac':
                            network_profile.default_gateway_mac = binascii.b2a_hex(reg_subkey_value.data()).decode()
    except Exception as exception:
        logger.error(exception)
    return network_profile_list