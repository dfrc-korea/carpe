from modules import logger

class Amcache_Program_Information:
    par_id = ''
    case_id = ''
    evd_id = ''
    file_name = ''
    key_last_updated_time = ''
    installed_date = ''
    version = ''
    publisher = ''
    uninstall_date = ''
    os_version_at_install_time= ''
    bundle_manifest_path = ''
    hide_in_control_panel_flag = ''
    inboxmodernapp = ''
    language_code = ''
    manifest_path = ''
    msi_package_code = ''
    msi_product_code = ''
    package_full_name = ''
    program_id = ''
    program_instance_id = ''
    uninstall_registry_key_path = ''
    root_dir_path = ''
    type = ''
    program_source = ''
    store_app_type = ''
    uninstall_string = ''
    backup_flag = ''
    source_location = []

def AMCACHEPROGRAMENTRIES(reg_am):
    amcache_list = []
    amcache_count = 0
    try:
        amcache_key = reg_am.find_key(r"Root\InventoryApplication")
    except Exception as exception:
        logger.error(exception)
    if amcache_key is None:
        return amcache_list
    for amcache_subkey in amcache_key.subkeys():
        try:
            amcache_file_information = Amcache_Program_Information()
            amcache_list.append(amcache_file_information)
            amcache_list[amcache_count].source_location = []
            amcache_list[amcache_count].source_location.append('AmCache.hve-Root/InventoryApplication')
            amcache_list[amcache_count].key_last_updated_time = amcache_subkey.last_written_timestamp().isoformat()+'Z'
            for amcache_subkey_value in amcache_subkey.values():
                if amcache_subkey_value.name() == 'Name':
                    amcache_list[amcache_count].file_name = amcache_subkey_value.data().replace('\x00','')
                elif amcache_subkey_value.name() == 'InstallDate':
                    if amcache_subkey_value.data() != '\x00':
                        amcache_list[amcache_count].installed_date = amcache_subkey_value.data().split(' ')[0].split('/')[2] + '-' + amcache_subkey_value.data().split(' ')[0].split('/')[0] + '-' + amcache_subkey_value.data().split(' ')[0].split('/')[1]+'T'+amcache_subkey_value.data().split(' ')[1].replace('\x00','')+'Z'
                elif amcache_subkey_value.name() == 'Version':
                    amcache_list[amcache_count].version = amcache_subkey_value.data().replace('\x00','')
                elif amcache_subkey_value.name() == 'Publisher':
                    amcache_list[amcache_count].publisher = amcache_subkey_value.data().replace('\x00','')
                elif amcache_subkey_value.name() == 'UninstallDate':
                    if amcache_subkey_value.data() != '\x00':
                        amcache_list[amcache_count].uninstall_date = amcache_subkey_value.data().split(' ')[0].split('/')[2] + '-' + amcache_subkey_value.data().split(' ')[0].split('/')[0] + '-' + amcache_subkey_value.data().split(' ')[0].split('/')[1]+'T'+amcache_subkey_value.data().split(' ')[1].replace('\x00','')+'Z'
                elif amcache_subkey_value.name() == 'OSVersionAtInstallTime':
                    amcache_list[amcache_count].os_version_at_install_time = amcache_subkey_value.data().replace('\x00','')
                elif amcache_subkey_value.name() == 'BundleManifestPath':
                    amcache_list[amcache_count].bundle_manifest_path = amcache_subkey_value.data().replace('\\','/').replace('\x00','')
                elif amcache_subkey_value.name() == 'HiddenArp':
                    # 1: True, 0: False
                    amcache_list[amcache_count].hide_in_control_panel_flag = amcache_subkey_value.data()
                elif amcache_subkey_value.name() == 'InboxModernApp':
                    # 1: True, 0: False
                    amcache_list[amcache_count].inboxmodernapp = amcache_subkey_value.data()
                elif amcache_subkey_value.name() == 'Language':
                    amcache_list[amcache_count].language_code = amcache_subkey_value.data()
                elif amcache_subkey_value.name() == 'ManifestPath':
                    amcache_list[amcache_count].manifest_path = amcache_subkey_value.data().replace('\\','/').replace('\x00','')
                elif amcache_subkey_value.name() == 'MsiPackageCode':
                    amcache_list[amcache_count].msi_package_code = amcache_subkey_value.data().replace('\x00','')
                elif amcache_subkey_value.name() == 'MsiProductCode':
                    amcache_list[amcache_count].msi_product_code = amcache_subkey_value.data().replace('\x00','')
                elif amcache_subkey_value.name() == 'PackageFullName':
                    amcache_list[amcache_count].package_full_name = amcache_subkey_value.data().replace('\x00','')
                elif amcache_subkey_value.name() == 'ProgramId':
                    amcache_list[amcache_count].program_id = amcache_subkey_value.data().replace('\x00','')
                elif amcache_subkey_value.name() == 'ProgramInstanceId':
                    amcache_list[amcache_count].program_instance_id = amcache_subkey_value.data().replace('\x00','')
                elif amcache_subkey_value.name() == 'RegistryKeyPath':
                    amcache_list[amcache_count].uninstall_registry_key_path = amcache_subkey_value.data().replace('\\','/').replace('\x00','')
                elif amcache_subkey_value.name() == 'RootDirPath':
                    amcache_list[amcache_count].root_dir_path = amcache_subkey_value.data().replace('\\','/').replace('\x00','')
                elif amcache_subkey_value.name() == 'Type':
                    amcache_list[amcache_count].type = amcache_subkey_value.data().replace('\x00','')
                elif amcache_subkey_value.name() == 'Source':
                    amcache_list[amcache_count].program_source = amcache_subkey_value.data().replace('\x00','')
                elif amcache_subkey_value.name() == 'StoreAppType':
                    amcache_list[amcache_count].store_app_type = amcache_subkey_value.data().replace('\x00','')
                elif amcache_subkey_value.name() == 'UninstallString':
                    amcache_list[amcache_count].uninstall_string = amcache_subkey_value.data().replace('\\','/').replace('\x00','')
            amcache_count = amcache_count + 1
        except Exception as exception:
            logger.error(exception)

    return amcache_list