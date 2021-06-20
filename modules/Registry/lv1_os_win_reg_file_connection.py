from modules import logger

class File_Connection_Information:
    par_id = ''
    case_id = ''
    evd_id = ''
    file_name = ''
    file_path = ''
    command = ''
    file_type = ''
    modified_time = ''
    backup_flag = ''
    source_location = []

def FILECCONNECTION(reg_software):
    file_connection_list = []
    file_connection_count = 0

    try:
        reg_key = reg_software.find_key(r"Classes")
    except Exception as exception:
        logger.error(exception)
    for reg_subkey in reg_key.subkeys():
        try:
            if reg_subkey.name()[0] != '.':
                for reg_subkey_subkey in reg_subkey.subkeys():
                    if reg_subkey_subkey.name() == 'shell':
                        for open in reg_subkey_subkey.subkeys():
                            for command in open.subkeys():
                                if command.name() == 'command':
                                    for command_value in command.values():
                                        if 'command' not in command_value.name():
                                            if 'exe' in str(command_value.data()).lower():
                                                file_connection_information = File_Connection_Information()
                                                file_connection_list.append(file_connection_information)
                                                file_connection_list[file_connection_count].source_location = []
                                                file_connection_list[file_connection_count].source_location.append('SOFTWARE-Classes')
                                                file_connection_list[file_connection_count].file_type = reg_subkey.name()
                                                if type(command_value.data()) == str:
                                                    file_connection_list[file_connection_count].command = command_value.data().replace("'","").replace('"','').replace("\\","/").replace('\x00','')
                                                    file_connection_list[file_connection_count].file_path = (str(command_value.data()).lower().split('exe')[0]+'exe').replace("\\","/").replace('"','')
                                                    file_connection_list[file_connection_count].file_name = str(command_value.data()).lower().split('exe')[0].split('\\')[-1]+'exe'
                                                else:
                                                    file_connection_list[file_connection_count].command = command_value.data()[:-1].decode('utf-16').replace("'",'').replace("\\","/").replace('"','').replace('\x00','')
                                                    file_connection_list[file_connection_count].file_path = (command_value.data()[:-1].decode('utf-16').lower().split('exe')[0]+'exe').replace("\\","/").replace('"','')
                                                    file_connection_list[file_connection_count].file_name = command_value.data()[:-1].decode('utf-16').lower().split('exe')[0].split('\\')[-1]+'exe'
                                                file_connection_list[file_connection_count].modified_time = command.last_written_timestamp().isoformat()+'Z'
                                                file_connection_count = file_connection_count + 1
                                            else:
                                                file_connection_information = File_Connection_Information()
                                                file_connection_list.append(file_connection_information)
                                                file_connection_list[file_connection_count].source_location = []
                                                file_connection_list[file_connection_count].source_location.append('SOFTWARE-Classes')
                                                file_connection_list[file_connection_count].file_type = reg_subkey.name()
                                                if type(command_value.data()) == str:
                                                    file_connection_list[file_connection_count].command = command_value.data().replace("'",'').replace("\\","/").replace('"','').replace('\x00','')
                                                    file_connection_list[file_connection_count].file_path = str(command_value.data()).lower().split(' ')[0].replace("\\","/").replace('"','')
                                                    file_connection_list[file_connection_count].file_name = str(command_value.data()).lower().split(' ')[0]
                                                else:
                                                    file_connection_list[file_connection_count].command = command_value.data()[:-1].decode('utf-16').replace("'",'').replace("\\","/").replace('"','').replace('\x00','')
                                                    file_connection_list[file_connection_count].file_path = command_value.data()[:-1].decode('utf-16').lower().split(' ')[0].replace("\\","/").replace('"','')
                                                    file_connection_list[file_connection_count].file_name = command_value.data()[:-1].decode('utf-16').lower().split(' ')[0]
                                                file_connection_list[file_connection_count].modified_time = command.last_written_timestamp().isoformat()+'Z'
                                                file_connection_count = file_connection_count + 1
        except Exception as exception:
            logger.error(exception)
    return file_connection_list