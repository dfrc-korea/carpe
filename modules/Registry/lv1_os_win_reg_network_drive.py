from datetime import datetime, timedelta
import binascii
from modules import logger

class Network_Drive_Information:
    par_id = ''
    case_id = ''
    evd_id = ''
    network_drive_name = ''
    modified_time = ''
    ordering = ''
    useraccount = ''
    backup_flag = ''
    source_location = []

def NETWORKDRIVE(reg_nt):
    network_drive_list = []
    network_drive_count = 0
    network_drive_order = []

    try:
        reg_key = reg_nt.find_key(r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Map Network Drive MRU")
        if reg_key != None:
            for reg_value in reg_key.values():
                if reg_value.name() == 'MRUList':
                    for i in reg_value.data():
                        network_drive_order.append(i)

            for order in network_drive_order:
                for reg_value in reg_key.values():
                    if reg_value.name() == str(order):
                        network_drive_information = Network_Drive_Information()
                        network_drive_list.append(network_drive_information)
                        network_drive_list[network_drive_count].source_location = []
                        network_drive_list[network_drive_count].source_location.append('NTUSER-SOFTWARE/Microsoft/Windows/CurrentVersion/Explorer/Map Network Drive MRU')
                        network_drive_list[network_drive_count].network_drive_name = reg_value.data().replace('\\','/').replace('\x00','')
                        if network_drive_count == 0:
                            network_drive_list[network_drive_count].modified_time = reg_key.last_written_timestamp().isoformat()+'Z'
                        network_drive_list[network_drive_count].ordering = network_drive_count+1
                        network_drive_count = network_drive_count + 1
    except Exception as exception:
        logger.error(exception)
    return network_drive_list

