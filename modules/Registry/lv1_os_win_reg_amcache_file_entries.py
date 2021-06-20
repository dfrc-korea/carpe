from modules import logger

class Amcache_File_Information:
    par_id = ''
    case_id = ''
    evd_id = ''
    file_name = ''
    key_last_updated_time = ''
    file_extension = ''
    program_id = ''
    key_id = ''
    related_programname = ''
    sha1_hash = ''
    os_component_flag = ''
    full_path = ''
    link_date = ''
    product_name = ''
    size = ''
    version = ''
    product_version = ''
    long_path_hash = ''
    binary_type = ''
    pe_file_flag = ''
    binary_file_version = ''
    binary_product_version = ''
    language_code = ''
    usn = ''
    publisher = ''
    backup_flag = ''
    source_location = []

def AMCACHEFILEENTRIES(reg_am):
    amcache_list = []
    amacache_count = 0
    try:
        amcache_key = reg_am.find_key(r"Root\InventoryApplicationFile")
    except Exception as exception:
        logger.error(exception)
    for amcache_subkey in amcache_key.subkeys():
        try:
            amcache_file_information = Amcache_File_Information()
            amcache_list.append(amcache_file_information)
            amcache_list[amacache_count].source_location = []
            amcache_list[amacache_count].source_location.append('AmCache.hve-Root/InventoryApplicationFile')
            amcache_list[amacache_count].key_id = amcache_subkey.name()
            amcache_list[amacache_count].key_last_updated_time = amcache_subkey.last_written_timestamp().isoformat()+'Z'
            for amcache_subkey_value in amcache_subkey.values():
                if amcache_subkey_value.name() == 'Name':
                    amcache_list[amacache_count].file_name = amcache_subkey_value.data().replace('\x00','')
                    amcache_list[amacache_count].file_extension = amcache_subkey_value.data().split('.')[-1].replace('\x00','')
                elif amcache_subkey_value.name() == 'ProgramId':
                    amcache_list[amacache_count].program_id = amcache_subkey_value.data().replace('\x00','')
                elif amcache_subkey_value.name() == 'FileId':
                    amcache_list[amacache_count].sha1_hash = amcache_subkey_value.data().replace('\x00','')
                elif amcache_subkey_value.name() == 'LowerCaseLongPath':
                    amcache_list[amacache_count].full_path = amcache_subkey_value.data().replace('\\','/').replace('\x00','')
                elif amcache_subkey_value.name() == 'LongPathHash':
                    amcache_list[amacache_count].long_path_hash = amcache_subkey_value.data().replace('\x00','')
                elif amcache_subkey_value.name() == 'Publisher':
                    amcache_list[amacache_count].publisher = amcache_subkey_value.data().replace('\x00','')
                elif amcache_subkey_value.name() == 'Version':
                    amcache_list[amacache_count].version = amcache_subkey_value.data().replace('\x00','')
                elif amcache_subkey_value.name() == 'BinFileVersion':
                    amcache_list[amacache_count].binary_file_version = amcache_subkey_value.data().replace('\x00','')
                elif amcache_subkey_value.name() == 'BinaryType':
                    amcache_list[amacache_count].binary_type = amcache_subkey_value.data().replace('\x00','')
                elif amcache_subkey_value.name() == 'ProductName':
                    amcache_list[amacache_count].product_name = amcache_subkey_value.data().replace('\x00','')
                elif amcache_subkey_value.name() == 'ProductVersion':
                    amcache_list[amacache_count].product_version = amcache_subkey_value.data().replace('\x00','')
                elif amcache_subkey_value.name() == 'LinkDate':
                    if amcache_subkey_value.data() != '\x00':
                        amcache_list[amacache_count].link_date = amcache_subkey_value.data().split(' ')[0].split('/')[2] \
                                                                 + '-' + amcache_subkey_value.data().split(' ')[0].split('/')[0] \
                                                                 + '-' + amcache_subkey_value.data().split(' ')[0].split('/')[1] + 'T' \
                                                                 + amcache_subkey_value.data().split(' ')[1].replace('\x00', '')+'Z'
                elif amcache_subkey_value.name() == 'BinProductVersion':
                    amcache_list[amacache_count].binary_product_version = amcache_subkey_value.data().replace('\x00','')
                elif amcache_subkey_value.name() == 'Size':
                    amcache_list[amacache_count].size = amcache_subkey_value.data()
                elif amcache_subkey_value.name() == 'Language':
                    amcache_list[amacache_count].language_code = amcache_subkey_value.data()
                elif amcache_subkey_value.name() == 'IsPeFile':
                    # 1: True, 0: False
                    amcache_list[amacache_count].pe_file_flag = amcache_subkey_value.data()
                elif amcache_subkey_value.name() == 'IsOsComponent':
                    # 1: True, 0: False
                    amcache_list[amacache_count].os_component_flag = amcache_subkey_value.data()
                elif amcache_subkey_value.name() == 'Usn':
                    amcache_list[amacache_count].usn = amcache_subkey_value.data()
            amacache_count = amacache_count + 1
        except Exception as exception:
            logger.error(exception)

    amcahce_key = reg_am.find_key(r"Root\InventoryApplication")
    try:
        for amcache in amcache_list:
            for amcache_subkey in amcahce_key.subkeys():
                if amcache_subkey.name() == amcache.program_id:
                    for amcache_subkey_value in amcache_subkey.values():
                        if amcache_subkey_value.name() == 'Name':
                            amcache.related_programname = amcache_subkey_value.data().replace('\x00','')
                            amcache.source_location.append('AmCache.hve-Root/InventoryApplication')
    except Exception as exception:
        logger.error(exception)
    return amcache_list

