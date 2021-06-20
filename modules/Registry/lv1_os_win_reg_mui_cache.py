from modules import logger

class Mui_Cache_Information:
    par_id = ''
    case_id = ''
    evd_id = ''
    file_name = ''
    file_path = ''
    data = ''
    useraccount = ''
    backup_flag = ''
    source_location = []

def MUICACHE(reg_usrclass):
    mui_cache_list = []
    mui_cache_count = 0

    try:
        reg_key = reg_usrclass.find_key(r"Local Settings")
        if reg_key != None:
            for reg_value_temp in reg_key.subkey(name='MuiCache').subkeys():
                for reg_value_subkey in reg_value_temp.subkeys():
                    for reg_value in reg_value_subkey.values():
                        if reg_value.name() != 'LanguageList':
                            mui_cahce_information = Mui_Cache_Information()
                            mui_cache_list.append(mui_cahce_information)
                            mui_cache_list[mui_cache_count].source_location = []
                            mui_cache_list[mui_cache_count].source_location.append('USRCLASS-Software/Classes/Local Settings/MuiCache')
                            mui_cache_list[mui_cache_count].file_name = reg_value.name().split('\\')[-1].split(',')[0]
                            mui_cache_list[mui_cache_count].file_path = reg_value.name()
                            mui_cache_list[mui_cache_count].data = reg_value.data().replace('\x00','')
                            mui_cache_count = mui_cache_count + 1

            if reg_key.subkey(name='Software').subkey(name='Microsoft').subkey(name='Windows').subkey(name='Shell') != None:
                for reg_value in reg_key.subkey(name='Software').subkey(name='Microsoft').subkey(name='Windows').subkey(name='Shell').subkey(name='MuiCache').values():
                    if reg_value.name() != 'LangID':
                        mui_cahce_information = Mui_Cache_Information()
                        mui_cache_list.append(mui_cahce_information)
                        mui_cache_list[mui_cache_count].source_location = []
                        mui_cache_list[mui_cache_count].source_location.append('USRCLASS-Software/Microsoft/Windows/Shell/MuiCache')
                        mui_cache_list[mui_cache_count].file_name = reg_value.name().split('\\')[-1]
                        mui_cache_list[mui_cache_count].file_path = reg_value.name()
                        mui_cache_list[mui_cache_count].data = reg_value.data().replace('\x00','')
                        mui_cache_count = mui_cache_count + 1

    except Exception as exception:
        logger.error(exception)

    return mui_cache_list