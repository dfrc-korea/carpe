from modules import logger

class Program_Information:
    par_id = ''
    case_id = ''
    evd_id = ''
    program_name = ''
    company = ''
    created_date = ''
    key_last_updated_time = ''
    install_size = ''
    version = ''
    potential_location = ''
    useraccount = ''
    backup_flag = ''
    source_location = []

def INSTALLEDPROGRAMS(reg_software, reg_nt):
    programs_list = []
    program_count = 0
    installed_programs_key_list = []

    try:
        if reg_software != '':
            installed_programs_key_list.append(reg_software.find_key(r"Microsoft\Windows\CurrentVersion\Uninstall"))
            installed_programs_key_list.append(reg_software.find_key(r"WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"))
        installed_programs_key_list.append(reg_nt.find_key(r"Software\Microsoft\Windows\CurrentVersion\Uninstall"))
    except Exception as exception:
        logger.error(exception)

    tmp_installed_programs_key_list = []
    for installed_programs_key in installed_programs_key_list:
        if installed_programs_key != None:
            tmp_installed_programs_key_list.append(installed_programs_key)

    installed_programs_key_list = tmp_installed_programs_key_list

    for installed_programs_key in installed_programs_key_list:
        for installed_programs_subkey in installed_programs_key.subkeys():
            try:
                if 'InstallShield Uninstall Information' not in installed_programs_subkey.name():
                    program_information = Program_Information()
                    programs_list.append(program_information)

                    if reg_software != '':
                        if installed_programs_key == installed_programs_key_list[0]:
                            programs_list[program_count].source_location = []
                            programs_list[program_count].source_location.append('SOFTWARE-Microsoft/Windows/CurrentVersion/Uninstall')
                        elif installed_programs_key == installed_programs_key_list[1]:
                            programs_list[program_count].source_location = []
                            programs_list[program_count].source_location.append('SOFTWARE-WOW6432Node/Microsoft/Windows/CurrentVersion/Uninstall')
                        elif installed_programs_key == installed_programs_key_list[2]:
                            programs_list[program_count].source_location = []
                            programs_list[program_count].source_location.append('NTUSER-Software/Microsoft/Windows/CurrentVersion/Uninstall')
                    else:
                        programs_list[program_count].source_location = []
                        programs_list[program_count].source_location.append('NTUSER-Software/Microsoft/Windows/CurrentVersion/Uninstall')
                    programs_list[program_count].program_name = installed_programs_subkey.name()
                    programs_list[program_count].key_last_updated_time = installed_programs_subkey.last_written_timestamp().isoformat()+'Z'
                    for installed_programs_subkey_value in installed_programs_subkey.values():
                        if installed_programs_subkey_value.name() == 'DisplayName':
                            programs_list[program_count].program_name = installed_programs_subkey_value.data().replace('\x00','')
                        elif installed_programs_subkey_value.name() == 'DisplayVersion':
                            if type(installed_programs_subkey_value.data()) == str:
                                programs_list[program_count].version = installed_programs_subkey_value.data().replace('\x00','')
                            else:
                                programs_list[program_count].version = installed_programs_subkey_value.data()[:-1].decode('utf-16')
                        elif installed_programs_subkey_value.name() == 'Publisher':
                            programs_list[program_count].company = installed_programs_subkey_value.data().replace('\x00','')
                        elif installed_programs_subkey_value.name() == 'EstimatedSize':
                            programs_list[program_count].install_size = installed_programs_subkey_value.data()
                        elif installed_programs_subkey_value.name() == 'InstallDate':
                            if installed_programs_subkey_value.data() != None:
                                programs_list[program_count].created_date = installed_programs_subkey_value.data().replace('\x00','')[0:4]+'-'+installed_programs_subkey_value.data().replace('\x00','')[4:6]+'-'+installed_programs_subkey_value.data().replace('\x00','')[6:8]
                        elif installed_programs_subkey_value.name() == 'InstallLocation':
                            programs_list[program_count].potential_location = installed_programs_subkey_value.data().replace('\\','/').replace('\x00','')
                    program_count = program_count + 1
            except Exception as exception:
                logger.error(exception)

    return programs_list