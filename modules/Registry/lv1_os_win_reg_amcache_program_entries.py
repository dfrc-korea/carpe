

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
    amacache_count = 0

    amcahce_key = reg_am.find_key(r"Root\InventoryApplication")
    for amcache_subkey in amcahce_key.subkeys():
        try:
            amcache_file_information = Amcache_Program_Information()
            amcache_list.append(amcache_file_information)
            amcache_list[amacache_count].source_location = []
            amcache_list[amacache_count].source_location.append('AmCache.hve-Root/InventoryApplication')
            amcache_list[amacache_count].key_last_updated_time = amcache_subkey.last_written_timestamp().isoformat()+'Z'
            for amcache_subkey_value in amcache_subkey.values():
                if amcache_subkey_value.name() == 'Name':
                    amcache_list[amacache_count].file_name = amcache_subkey_value.data().replace('\x00','')
                elif amcache_subkey_value.name() == 'InstallDate':
                    if amcache_subkey_value.data() != '\x00':
                        amcache_list[amacache_count].installed_date = amcache_subkey_value.data().split(' ')[0].split('/')[2] + '-' + amcache_subkey_value.data().split(' ')[0].split('/')[1] + '-' + amcache_subkey_value.data().split(' ')[0].split('/')[0]+'T'+amcache_subkey_value.data().split(' ')[1].replace('\x00','')+'Z'
                elif amcache_subkey_value.name() == 'Version':
                    amcache_list[amacache_count].version = amcache_subkey_value.data().replace('\x00','')
                elif amcache_subkey_value.name() == 'Publisher':
                    amcache_list[amacache_count].publisher = amcache_subkey_value.data().replace('\x00','')
                elif amcache_subkey_value.name() == 'UninstallDate':
                    if amcache_subkey_value.data() != '\x00':
                        amcache_list[amacache_count].uninstall_date = amcache_subkey_value.data().split(' ')[0].split('/')[2] + '-' + amcache_subkey_value.data().split(' ')[0].split('/')[1] + '-' + amcache_subkey_value.data().split(' ')[0].split('/')[0]+'T'+amcache_subkey_value.data().split(' ')[1].replace('\x00','')+'Z'
                elif amcache_subkey_value.name() == 'OSVersionAtInstallTime':
                    amcache_list[amacache_count].os_version_at_install_time = amcache_subkey_value.data().replace('\x00','')
                elif amcache_subkey_value.name() == 'BundleManifestPath':
                    amcache_list[amacache_count].bundle_manifest_path = amcache_subkey_value.data().replace('\\','/').replace('\x00','')
                elif amcache_subkey_value.name() == 'HiddenArp':
                    # 1: True, 0: False
                    amcache_list[amacache_count].hide_in_control_panel_flag = amcache_subkey_value.data()
                elif amcache_subkey_value.name() == 'InboxModernApp':
                    # 1: True, 0: False
                    amcache_list[amacache_count].inboxmodernapp = amcache_subkey_value.data()
                elif amcache_subkey_value.name() == 'Language':
                    amcache_list[amacache_count].language_code = amcache_subkey_value.data()
                elif amcache_subkey_value.name() == 'ManifestPath':
                    amcache_list[amacache_count].manifest_path = amcache_subkey_value.data().replace('\\','/').replace('\x00','')
                elif amcache_subkey_value.name() == 'MsiPackageCode':
                    amcache_list[amacache_count].msi_package_code = amcache_subkey_value.data().replace('\x00','')
                elif amcache_subkey_value.name() == 'MsiProductCode':
                    amcache_list[amacache_count].msi_product_code = amcache_subkey_value.data().replace('\x00','')
                elif amcache_subkey_value.name() == 'PackageFullName':
                    amcache_list[amacache_count].package_full_name = amcache_subkey_value.data().replace('\x00','')
                elif amcache_subkey_value.name() == 'ProgramId':
                    amcache_list[amacache_count].program_id = amcache_subkey_value.data().replace('\x00','')
                elif amcache_subkey_value.name() == 'ProgramInstanceId':
                    amcache_list[amacache_count].program_instance_id = amcache_subkey_value.data().replace('\x00','')
                elif amcache_subkey_value.name() == 'RegistryKeyPath':
                    amcache_list[amacache_count].uninstall_registry_key_path = amcache_subkey_value.data().replace('\\','/').replace('\x00','')
                elif amcache_subkey_value.name() == 'RootDirPath':
                    amcache_list[amacache_count].root_dir_path = amcache_subkey_value.data().replace('\\','/').replace('\x00','')
                elif amcache_subkey_value.name() == 'Type':
                    amcache_list[amacache_count].type = amcache_subkey_value.data().replace('\x00','')
                elif amcache_subkey_value.name() == 'Source':
                    amcache_list[amacache_count].program_source = amcache_subkey_value.data().replace('\x00','')
                elif amcache_subkey_value.name() == 'StoreAppType':
                    amcache_list[amacache_count].store_app_type = amcache_subkey_value.data().replace('\x00','')
                elif amcache_subkey_value.name() == 'UninstallString':
                    amcache_list[amacache_count].uninstall_string = amcache_subkey_value.data().replace('\\','/').replace('\x00','')
            amacache_count = amacache_count + 1
        except:
            print('-----Amcache program Error')

    return amcache_list