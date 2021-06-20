from datetime import datetime, timedelta
import binascii
from modules import logger

class Network_Interface_Information:
    par_id = ''
    case_id = ''
    evd_id = ''
    enable_dhcp = ''
    ipaddress = ''
    dhcp_ipaddress = ''
    dhcp_subnetmask = ''
    dhcp_server = ''
    dhcp_connforcebroadcastflag = ''
    dhcp_domain = ''
    dhcp_name_server = ''
    dhcp_default_gateway = ''
    dhcp_subnetmaskopt = ''
    dhcp_interfaceoptions = ''
    dhcp_gatewayhardware = ''
    dhcp_gatewayhardwarecount = ''
    lease = ''
    lease_obtained_time = ''
    lease_terminate_time = ''
    t1 = ''
    t2 = ''
    address_type = ''
    isservernapaware = ''
    registeradaptername = ''
    registrationenabled = ''
    backup_flag = ''
    source_location = []

def NETWORKINTERFACE(reg_system):
    network_interface_list = []
    network_interface_count = 0
    try:
        reg_key = reg_system.find_key(r"ControlSet001\Services\Tcpip\Parameters\Interfaces")
    except Exception as exception:
        logger.error(exception)
    try:
        for reg_subkey in reg_key.subkeys():
            if len(list(reg_subkey.values())) > 0:
                network_interface_information = Network_Interface_Information()
                network_interface_list.append(network_interface_information)
                network_interface_list[network_interface_count].source_location = []
                network_interface_list[network_interface_count].source_location.append('SYSTEM-ControlSet001/Services/Tcpip/Parameters/Interfaces')
                for reg_subkey_value in reg_subkey.values():
                    if reg_subkey_value.name() == 'EnableDHCP':
                        # 1: True, 0: False
                        network_interface_list[network_interface_count].enable_dhcp = reg_subkey_value.data()
                    elif reg_subkey_value.name() == 'DhcpIPAddress':
                        network_interface_list[network_interface_count].dhcp_ipaddress = reg_subkey_value.data().replace('\x00','')
                    elif reg_subkey_value.name() == 'DhcpSubnetMask':
                        network_interface_list[network_interface_count].dhcp_subnetmask = reg_subkey_value.data().replace('\x00','')
                    elif reg_subkey_value.name() == 'DhcpServer':
                        network_interface_list[network_interface_count].dhcp_server = reg_subkey_value.data().replace('\x00','')
                    elif reg_subkey_value.name() == 'Lease':
                        network_interface_list[network_interface_count].lease = reg_subkey_value.data()
                    elif reg_subkey_value.name() == 'LeaseObtainedTime':
                        network_interface_list[network_interface_count].lease_obtained_time = datetime.fromtimestamp(reg_subkey_value.data()).isoformat()+'Z'
                    elif reg_subkey_value.name() == 'T1':
                        network_interface_list[network_interface_count].t1 = datetime.fromtimestamp(reg_subkey_value.data()).isoformat()+'Z'
                    elif reg_subkey_value.name() == 'T2':
                        network_interface_list[network_interface_count].t2 = datetime.fromtimestamp(reg_subkey_value.data()).isoformat()+'Z'
                    elif reg_subkey_value.name() == 'LeaseTerminatesTime':
                        network_interface_list[network_interface_count].lease_terminate_time = datetime.fromtimestamp(reg_subkey_value.data()).isoformat()+'Z'
                    elif reg_subkey_value.name() == 'AddressType':
                        network_interface_list[network_interface_count].address_type = reg_subkey_value.data()
                    elif reg_subkey_value.name() == 'IsServerNapAware':
                        network_interface_list[network_interface_count].isservernapaware = reg_subkey_value.data()
                    elif reg_subkey_value.name() == 'DhcpConnForceBroadcastFlag':
                        network_interface_list[network_interface_count].dhcp_connforcebroadcastflag = reg_subkey_value.data()
                    elif reg_subkey_value.name() == 'DhcpDomain':
                        network_interface_list[network_interface_count].dhcp_domain = reg_subkey_value.data().replace('\x00','')
                    elif reg_subkey_value.name() == 'DhcpNameServer':
                        network_interface_list[network_interface_count].dhcp_name_server = reg_subkey_value.data().replace('\x00','')
                    elif reg_subkey_value.name() == 'DhcpDefaultGateway':
                        network_interface_list[network_interface_count].dhcp_default_gateway = reg_subkey_value.data()[0].replace('\x00','')
                    elif reg_subkey_value.name() == 'DhcpSubnetMaskOpt':
                        network_interface_list[network_interface_count].dhcp_subnetmaskopt = reg_subkey_value.data()[0].replace('\x00','')
                    #elif reg_subkey_value.name() == 'DhcpInterfaceOptions':
                        #network_interface_list[network_interface_count].dhcp_interfaceoptions = reg_subkey_value.data()
                    #elif reg_subkey_value.name() == 'DhcpGatewayHardware':
                        #network_interface_list[network_interface_count].dhcp_gatewayhardware = reg_subkey_value.data()
                    elif reg_subkey_value.name() == 'DhcpGatewayHardwareCount':
                        network_interface_list[network_interface_count].dhcp_gatewayhardwarecount = reg_subkey_value.data()
                    elif reg_subkey_value.name() == 'IPAddress':
                        network_interface_list[network_interface_count].ipaddress = reg_subkey_value.data()[0].replace('\x00','')
                    elif reg_subkey_value.name() == 'RegisterAdapterName':
                        network_interface_list[network_interface_count].registeradaptername = reg_subkey_value.data()
                    elif reg_subkey_value.name() == 'RegistrationEnabled':
                        network_interface_list[network_interface_count].registrationenabled = reg_subkey_value.data()
                network_interface_count = network_interface_count + 1
    except Exception as exception:
        logger.error(exception)
    return network_interface_list