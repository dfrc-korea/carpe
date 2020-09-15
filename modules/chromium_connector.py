# -*- coding: utf-8 -*-
"""module for Chromium Web Browser."""
import os
import shutil


from dfvfs.lib import definitions as dfvfs_definitions
from modules import logger
from modules import manager
from modules import interface
from modules.app_chromium.chrome import chrome
from modules.app_chromium.whale import whale
from modules.app_chromium.chromium_edge import chromium_edge
from modules.app_chromium.opera import opera
from modules.app_chromium.firefox import firefox


class ChromiumConnector(interface.ModuleConnector):
    NAME = 'chromium_connector'
    DESCRIPTION = 'Module for Chromium'

    _plugin_classes = {}

    def __init__(self):
        super(ChromiumConnector, self).__init__()

    def Connect(self, configuration, source_path_spec, knowledge_base):
        print('[MODULE]: Chromium Connect')

        if source_path_spec.parent.type_indicator != dfvfs_definitions.TYPE_INDICATOR_TSK_PARTITION:
            par_id = configuration.partition_list['p1']
        else:
            par_id = configuration.partition_list[getattr(source_path_spec.parent, 'location', None)[1:]]

        if par_id == None:
            return False

        chrome_query = f"SELECT name, parent_path, extension FROM file_info WHERE par_id='{par_id}' and ("
        whale_query = f"SELECT name, parent_path, extension FROM file_info WHERE par_id='{par_id}' and ("
        chromium_edge_query = f"SELECT name, parent_path, extension FROM file_info WHERE par_id='{par_id}' and ("
        opera_query = f"SELECT name, parent_path, extension FROM file_info WHERE par_id='{par_id}' and ("
        firefox_query = f"SELECT name, parent_path, extension FROM file_info WHERE par_id='{par_id}' and ("

        user_list = []

        if not knowledge_base._user_accounts:
            return False

        for user_accounts in knowledge_base._user_accounts.values():
            for hostname in user_accounts.values():
                if hostname.identifier.find('S-1-5-21') == -1:
                    continue

                chrome_query += f"parent_path= \'root/Users/{hostname.username}/AppData/Local/Google/Chrome/User Data\' or "
                whale_query += f"parent_path= \'root/Users/{hostname.username}/AppData/Local/Naver/Naver Whale/User Data\' or "
                chromium_edge_query += f"parent_path= \'root/Users/{hostname.username}/AppData/Local/Microsoft/Edge/User Data\' or "
                opera_query += f"parent_path= \'root/Users/{hostname.username}/AppData/Roaming/Opera Software/Opera Stable\' or "
                firefox_query += f"parent_path= \'root/Users/{hostname.username}/AppData/Roaming/Mozilla/Firefox/Profiles\' or "
                user_list.append(hostname.username)

        chrome_query = chrome_query[:-4] + ")and not type='7';"
        whale_query = whale_query[:-4] + ")and not type='7';"
        chromium_edge_query = chromium_edge_query[:-4] + ")and not type='7';"
        opera_query = opera_query[:-4] + ")and not type='7';"
        firefox_query = firefox_query[:-4] + ")and not type='7';"

        chrome_artifact = configuration.cursor.execute_query_mul(chrome_query)
        whale_artifact = configuration.cursor.execute_query_mul(whale_query)
        chromium_edge_artifact = configuration.cursor.execute_query_mul(chromium_edge_query)
        opera_artifact = configuration.cursor.execute_query_mul(opera_query)
        firefox_artifact = configuration.cursor.execute_query_mul(firefox_query)

        chrome_file_path = os.path.dirname(os.path.abspath(__file__)) + os.sep + 'schema' + os.sep + 'web' + os.sep \
                           + 'chrome' + os.sep
        whale_file_path = os.path.dirname(os.path.abspath(__file__)) + os.sep + 'schema' + os.sep + 'web' + os.sep \
                          + 'whale' + os.sep
        edge_file_path = os.path.dirname(os.path.abspath(__file__)) + os.sep + 'schema' + os.sep + 'web' + os.sep \
                         + 'chromium_edge' + os.sep
        opera_file_path = os.path.dirname(os.path.abspath(__file__)) + os.sep + 'schema' + os.sep + 'web' + os.sep \
                          + 'opera' + os.sep
        firefox_file_path = os.path.dirname(os.path.abspath(__file__)) + os.sep + 'schema' + os.sep + 'web' + os.sep\
                            + 'firefox' + os.sep

        # Web Browser yaml file list
        chrome_yaml_list = [chrome_file_path + 'lv1_app_web_chrome_search_terms.yaml',
                            chrome_file_path + 'lv1_app_web_chrome_visit_urls.yaml',
                            chrome_file_path + 'lv1_app_web_chrome_download.yaml',
                            chrome_file_path + 'lv1_app_web_chrome_shortcuts.yaml',
                            chrome_file_path + 'lv1_app_web_chrome_favicons.yaml',
                            chrome_file_path + 'lv1_app_web_chrome_cookies.yaml',
                            chrome_file_path + 'lv1_app_web_chrome_autofill.yaml',
                            chrome_file_path + 'lv1_app_web_chrome_logindata.yaml',
                            chrome_file_path + 'lv1_app_web_chrome_bookmarks.yaml',
                            chrome_file_path + 'lv1_app_web_chrome_top_sites.yaml',
                            chrome_file_path + 'lv1_app_web_chrome_domain.yaml',
                            chrome_file_path + 'lv1_app_web_chrome_visit_history.yaml',
                            chrome_file_path + 'lv1_app_web_chrome_google_account.yaml',
                            chrome_file_path + 'lv1_app_web_chrome_zoom_level.yaml']

        whale_yaml_list = [whale_file_path+'lv1_app_web_whale_bookmarks.yaml',
                           whale_file_path+'lv1_app_web_whale_download.yaml',
                           whale_file_path+'lv1_app_web_whale_visit_urls.yaml',
                           whale_file_path+'lv1_app_web_whale_visit_history.yaml',
                           whale_file_path+'lv1_app_web_whale_search_terms.yaml',
                           whale_file_path+'lv1_app_web_whale_cookies.yaml',
                           whale_file_path+'lv1_app_web_whale_top_sites.yaml',
                           whale_file_path+'lv1_app_web_whale_autofill.yaml',
                           whale_file_path+'lv1_app_web_whale_logindata.yaml',
                           whale_file_path+'lv1_app_web_whale_shortcuts.yaml',
                           whale_file_path+'lv1_app_web_whale_favicons.yaml']

        edge_yaml_list = [edge_file_path+'lv1_app_web_chromium_edge_search_terms.yaml',
                          edge_file_path+'lv1_app_web_chromium_edge_visit_urls.yaml',
                          edge_file_path+'lv1_app_web_chromium_edge_visit_history.yaml',
                          edge_file_path+'lv1_app_web_chromium_edge_download.yaml',
                          edge_file_path+'lv1_app_web_chromium_edge_shortcuts.yaml',
                          edge_file_path+'lv1_app_web_chromium_edge_favicons.yaml',
                          edge_file_path+'lv1_app_web_chromium_edge_cookies.yaml',
                          edge_file_path+'lv1_app_web_chromium_edge_autofill.yaml',
                          edge_file_path+'lv1_app_web_chromium_edge_logindata.yaml',
                          edge_file_path+'lv1_app_web_chromium_edge_bookmarks.yaml',
                          edge_file_path+'lv1_app_web_chromium_edge_top_sites.yaml']

        opera_yaml_list = [opera_file_path+'lv1_app_web_opera_search_terms.yaml',
                           opera_file_path+'lv1_app_web_opera_visit_urls.yaml',
                           opera_file_path+'lv1_app_web_opera_visit_history.yaml',
                           opera_file_path+'lv1_app_web_opera_autofill.yaml',
                           opera_file_path+'lv1_app_web_opera_bookmarks.yaml',
                           opera_file_path+'lv1_app_web_opera_cookies.yaml',
                           opera_file_path+'lv1_app_web_opera_favicons.yaml',
                           opera_file_path+'lv1_app_web_opera_logindata.yaml',
                           opera_file_path+'lv1_app_web_opera_shortcuts.yaml',
                           opera_file_path+'lv1_app_web_opera_download.yaml']

        firefox_yaml_list = [firefox_file_path+'lv1_app_web_firefox_visit_history.yaml',
                             firefox_file_path+'lv1_app_web_firefox_visit_urls.yaml',
                             firefox_file_path+'lv1_app_web_firefox_domain.yaml',
                             firefox_file_path+'lv1_app_web_firefox_download.yaml',
                             firefox_file_path+'lv1_app_web_firefox_cookies.yaml',
                             firefox_file_path+'lv1_app_web_firefox_permissions.yaml',
                             firefox_file_path+'lv1_app_web_firefox_formhistory.yaml',
                             firefox_file_path+'lv1_app_web_firefox_favicons.yaml',
                             firefox_file_path+'lv1_app_web_firefox_content_prefs.yaml',
                             firefox_file_path+'lv1_app_web_firefox_bookmarks.yaml']

        # Web Browser table list
        chrome_table_list = ['lv1_app_web_chrome_search_terms',
                             'lv1_app_web_chrome_visit_urls',
                             'lv1_app_web_chrome_download',
                             'lv1_app_web_chrome_shortcuts',
                             'lv1_app_web_chrome_favicons',
                             'lv1_app_web_chrome_cookies',
                             'lv1_app_web_chrome_autofill',
                             'lv1_app_web_chrome_logindata',
                             'lv1_app_web_chrome_bookmarks',
                             'lv1_app_web_chrome_top_sites',
                             'lv1_app_web_chrome_domain',
                             'lv1_app_web_chrome_visit_history',
                             'lv1_app_web_chrome_google_account',
                             'lv1_app_web_chrome_zoom_level']

        whale_table_list = ['lv1_app_web_whale_bookmarks',
                            'lv1_app_web_whale_download',
                            'lv1_app_web_whale_visit_urls',
                            'lv1_app_web_whale_visit_history',
                            'lv1_app_web_whale_search_terms',
                            'lv1_app_web_whale_cookies',
                            'lv1_app_web_whale_top_sites',
                            'lv1_app_web_whale_autofill',
                            'lv1_app_web_whale_logindata',
                            'lv1_app_web_whale_shortcuts',
                            'lv1_app_web_whale_favicons']

        edge_table_list = ['lv1_app_web_chromium_edge_search_terms',
                           'lv1_app_web_chromium_edge_visit_urls',
                           'lv1_app_web_chromium_edge_visit_history',
                           'lv1_app_web_chromium_edge_download',
                           'lv1_app_web_chromium_edge_shortcuts',
                           'lv1_app_web_chromium_edge_favicons',
                           'lv1_app_web_chromium_edge_cookies',
                           'lv1_app_web_chromium_edge_autofill',
                           'lv1_app_web_chromium_edge_logindata',
                           'lv1_app_web_chromium_edge_bookmarks',
                           'lv1_app_web_chromium_edge_top_sites']

        opera_table_list = ['lv1_app_web_opera_search_terms',
                            'lv1_app_web_opera_visit_urls',
                            'lv1_app_web_opera_visit_history',
                            'lv1_app_web_opera_autofill',
                            'lv1_app_web_opera_bookmarks',
                            'lv1_app_web_opera_cookies',
                            'lv1_app_web_opera_favicons',
                            'lv1_app_web_opera_logindata',
                            'lv1_app_web_opera_shortcuts',
                            'lv1_app_web_opera_download']

        firefox_table_list = ['lv1_app_web_firefox_visit_history',
                              'lv1_app_web_firefox_visit_urls',
                              'lv1_app_web_firefox_domain',
                              'lv1_app_web_firefox_download',
                              'lv1_app_web_firefox_cookies',
                              'lv1_app_web_firefox_permissions',
                              'lv1_app_web_firefox_formhistory',
                              'lv1_app_web_firefox_favicons',
                              'lv1_app_web_firefox_content_prefs',
                              'lv1_app_web_firefox_bookmarks']

        # Create Web Browser table
        if not self.check_table_from_yaml(configuration, chrome_yaml_list, chrome_table_list):
            return False
        if not self.check_table_from_yaml(configuration, whale_yaml_list, whale_table_list):
            return False
        if not self.check_table_from_yaml(configuration, edge_yaml_list, edge_table_list):
            return False
        if not self.check_table_from_yaml(configuration, opera_yaml_list, opera_table_list):
            return False
        if not self.check_table_from_yaml(configuration, firefox_yaml_list, firefox_table_list):
            return False

        ################## Chrome ###################
        if len(chrome_artifact) != 0:  # If chrome artifact remain in partition

            # Chrome profile check
            full_path = []
            for i in range(len(chrome_artifact)):

                if 'Default' in chrome_artifact[i][0]:
                    full_path.append(chrome_artifact[i][1] + os.sep + chrome_artifact[i][0])

                if 'Profile' in chrome_artifact[i][0]:
                    full_path.append(chrome_artifact[i][1] + os.sep + chrome_artifact[i][0])

            # print(full_path)

            # Make Chrome artifact ouput dir
            chrome_output_path = configuration.root_tmp_path + os.sep + configuration.case_id + os.sep + \
                                 configuration.evidence_id + os.sep + par_id + os.sep + "web" + os.sep + "chrome" + os.sep

            # Match between os user chrome profile
            os_user_chrome_profile = []

            for f in full_path:
                for user in user_list:
                    if f.find(user) != -1:
                        profile_index = f.rfind(os.sep)
                        os_user_chrome_profile.append([user, f[profile_index + 1:]])

            # print(os_user_chrome_profile)

            # Create profile dir in ouput dir
            if os.path.isdir(chrome_output_path) == False:
                for make_dir_tree in os_user_chrome_profile:
                    os.makedirs(chrome_output_path + make_dir_tree[0] + os.sep + make_dir_tree[1] + os.sep)

            # Extract chrome artifact file
            chromium_artifact_file_list = ['Preferences', 'History', 'Login Data', 'Shortcuts', 'Top Sites', 'Web Data', 'Favicons',
                                         'Cookies', 'Bookmarks']

            for make_dir_tree in os_user_chrome_profile:

                for file in chromium_artifact_file_list:
                    self.ExtractTargetFileToPath(
                        source_path_spec=source_path_spec,
                        configuration=configuration,
                        file_path='/Users/' + make_dir_tree[0] + '/AppData/Local/Google/Chrome/User Data/' +
                                  make_dir_tree[1] + '/' + file,
                        output_path=chrome_output_path + make_dir_tree[0] + os.sep + make_dir_tree[1] + os.sep)

            print("[Web] Chrome artifact files extraction success")

            chrome_search_result = []
            chrome_visit_urls_result = []
            chrome_download_result = []
            chrome_top_sites = []
            chrome_shortcuts = []
            chrome_favicons = []
            chrome_cookies = []
            chrome_autofill = []
            chrome_logindata = []
            chrome_bookmarks = []
            chrome_domain = []
            chrome_visit_history = []
            chrome_google_account = []
            chrome_zoom_level = []

            for file_check in os_user_chrome_profile:

                files = [f for f in os.listdir(chrome_output_path + file_check[0] + os.sep + file_check[1] + os.sep) if
                         os.path.isfile(
                             os.path.join(chrome_output_path + file_check[0] + os.sep + file_check[1] + os.sep, f))]

                if 'Preferences' in files:
                    tmp_file_path = chrome_output_path + file_check[0] + os.sep + file_check[1] + os.sep + 'Preferences'
                    chrome_domain.append(chrome.chrome_domain_analysis(tmp_file_path))
                    chrome_google_account.append(chrome.chrome_google_account(tmp_file_path))
                    chrome_zoom_level.append(chrome.chrome_zoom_level(tmp_file_path))

                if 'History' in files:
                    tmp_file_path = chrome_output_path + file_check[0] + os.sep + file_check[1] + os.sep + 'History'
                    chrome_search_result.append(chrome.chrome_search_terms(tmp_file_path))
                    chrome_visit_urls_result.append(chrome.chrome_visit_urls(tmp_file_path))
                    chrome_download_result.append(chrome.chrome_download(tmp_file_path))
                    chrome_visit_history.append(chrome.chrome_visit_history(tmp_file_path))

                if 'Top Sites' in files:
                    tmp_file_path = chrome_output_path + file_check[0] + os.sep + file_check[1] + os.sep + 'Top Sites'
                    chrome_top_sites.append(chrome.chrome_top_sites(tmp_file_path))

                if 'Shortcuts' in files:
                    tmp_file_path = chrome_output_path + file_check[0] + os.sep + file_check[1] + os.sep + 'Shortcuts'
                    chrome_shortcuts.append(chrome.chrome_shortcuts(tmp_file_path))

                if 'Favicons' in files:
                    tmp_file_path = chrome_output_path + file_check[0] + os.sep + file_check[1] + os.sep + 'Favicons'
                    chrome_favicons.append(chrome.chrome_favicons(tmp_file_path))

                if 'Cookies' in files:
                    tmp_file_path = chrome_output_path + file_check[0] + os.sep + file_check[1] + os.sep + 'Cookies'
                    chrome_cookies.append(chrome.chrome_cookies(tmp_file_path))

                if 'Web Data' in files:
                    tmp_file_path = chrome_output_path + file_check[0] + os.sep + file_check[1] + os.sep + 'Web Data'
                    chrome_autofill.append(chrome.chrome_autofill(tmp_file_path))
                    # ToDo : keywords 테이블 의미 파악 후 반영

                if 'Login Data' in files:
                    tmp_file_path = chrome_output_path + file_check[0] + os.sep + file_check[1] + os.sep + 'Login Data'
                    chrome_logindata.append(chrome.chrome_logindata(tmp_file_path))

                if 'Bookmarks' in files:
                    tmp_file_path = chrome_output_path + file_check[0] + os.sep + file_check[1] + os.sep + 'Bookmarks'
                    chrome_bookmarks.append(chrome.chrome_bookmarks(tmp_file_path))

            # delete chrome output dir
            shutil.rmtree(chrome_output_path)

            info = [par_id, configuration.case_id, configuration.evidence_id]

            # insert data
            for search_terms, profile_match in zip(chrome_search_result, os_user_chrome_profile):
                for row in search_terms:
                    table_name = 'lv1_app_web_chrome_search_terms'

                    row = info + list(row) + profile_match

                    query = f"Insert into {table_name} values ('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s');" % tuple(
                        row)

                    # print(query)
                    configuration.cursor.execute_query(query)
            # print("[chrome] search terms data insert complete")

            for visit_urls, profile_match in zip(chrome_visit_urls_result, os_user_chrome_profile):
                for row in visit_urls:
                    table_name = 'lv1_app_web_chrome_visit_urls'
                    row = info + list(row) + profile_match

                    query = f"Insert into {table_name} values ('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s');" % tuple(
                        row)

                    # print(query)
                    configuration.cursor.execute_query(query)

            for visit_history, profile_match in zip(chrome_visit_history, os_user_chrome_profile):
                for row in visit_history:
                    table_name = 'lv1_app_web_chrome_visit_history'
                    row = info + list(row) + profile_match

                    query = f"Insert into {table_name} values ('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s'," \
                            f"'%s', '%s', '%s', '%s');" % tuple(row)

                    configuration.cursor.execute_query(query)

            for download_files, profile_match in zip(chrome_download_result, os_user_chrome_profile):
                for row in download_files:
                    table_name = 'lv1_app_web_chrome_download'
                    row = info + list(row) + profile_match

                    query = f"Insert into {table_name} values ('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s'" \
                            f", '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s'" \
                            f", '%s', '%s');" % tuple(row)

                    # print(query)
                    configuration.cursor.execute_query(query)

            for top_sites, profile_match in zip(chrome_top_sites, os_user_chrome_profile):
                for row in top_sites:
                    table_name = 'lv1_app_web_chrome_top_sites'
                    row = info + list(row) + profile_match

                    query = f"Insert into {table_name} values ('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s');" % tuple(
                        row)

                    # print(query)
                    configuration.cursor.execute_query(query)

            for shortcuts, profile_match in zip(chrome_shortcuts, os_user_chrome_profile):
                for row in shortcuts:
                    table_name = 'lv1_app_web_chrome_shortcuts'
                    row = info + list(row) + profile_match

                    query = f"Insert into {table_name} values ('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s');" % tuple(
                        row)

                    # print(query)
                    configuration.cursor.execute_query(query)

            for favicons, profile_match in zip(chrome_favicons, os_user_chrome_profile):
                for row in favicons:
                    table_name = 'lv1_app_web_chrome_favicons'
                    row = info + list(row) + profile_match

                    query = f"Insert into {table_name} values ('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', " % tuple(
                        row[0:8]) + \
                            "(UNHEX(\'" + row[8].hex() + "\'))" \
                                                         ", '%s', '%s', '%s', '%s');" % tuple(row[9:])
                    # print(query)
                    configuration.cursor.execute_query(query)

            for cookies, profile_match in zip(chrome_cookies, os_user_chrome_profile):
                for row in cookies:
                    table_name = 'lv1_app_web_chrome_cookies'
                    row = info + list(row) + profile_match

                    query = f"Insert into {table_name} values ('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', " % tuple(
                        row[0:14]) + \
                            "(UNHEX(\'" + row[14].hex() + "\'))" \
                                                          ", '%s', '%s', '%s');" % tuple(row[15:])
                    # print(query)
                    configuration.cursor.execute_query(query)

            for autofill, profile_match in zip(chrome_autofill, os_user_chrome_profile):
                for row in autofill:
                    table_name = 'lv1_app_web_chrome_autofill'
                    row = info + list(row) + profile_match

                    query = f"Insert into {table_name} values ('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s');" % tuple(
                        row)
                    # print(query)
                    configuration.cursor.execute_query(query)

            for logindata, profile_match in zip(chrome_logindata, os_user_chrome_profile):
                for row in logindata:
                    table_name = 'lv1_app_web_chrome_logindata'
                    row = info + list(row) + profile_match


                    query = f"Insert into {table_name} values ('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', " % tuple(
                        row[0:8]) + \
                            "(UNHEX(\'" + row[8].hex() + "\'))" \
                                                         ", '%s', '%s', " % tuple(row[9:11]) + \
                            "(UNHEX(\'" + row[11].hex() + "\'))" \
                                                          ", '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', " % tuple(
                        row[12:22]) + \
                            "(UNHEX(\'" + row[22].hex() + "\'))" \
                                                          ", '%s', '%s', '%s', '%s', '%s');" % tuple(row[23:])
                    # print(query)
                    configuration.cursor.execute_query(query)

            for bookmark, profile_match in zip(chrome_bookmarks, os_user_chrome_profile):
                for row in bookmark:
                    table_name = 'lv1_app_web_chrome_bookmarks'
                    row = info + list(row) + profile_match

                    query = f"Insert into {table_name} values ('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s');" % tuple(
                        row)
                    # print(query)
                    configuration.cursor.execute_query(query)

            for domain, profile_match in zip(chrome_domain, os_user_chrome_profile):
                for row in domain:
                    table_name = 'lv1_app_web_chrome_domain'
                    row = info + list(row) + profile_match

                    query = f"Insert into {table_name} values ('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s');" % tuple(
                        row)
                    # print(query)
                    configuration.cursor.execute_query(query)

            for google_account, profile_match in zip(chrome_google_account, os_user_chrome_profile):
                for row in google_account:
                    table_name = 'lv1_app_web_chrome_google_account'
                    row = info + list(row) + profile_match

                    query = f"Insert into {table_name} values ('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', " \
                            f"'%s', '%s', '%s', '%s', '%s', '%s');" % tuple(row)

                    configuration.cursor.execute_query(query)

            for zoom_level, profile_match in zip(chrome_zoom_level, os_user_chrome_profile):
                for row in zoom_level:
                    table_name = 'lv1_app_web_chrome_zoom_level'
                    row = info + list(row) + profile_match

                    query = f"Insert into {table_name} values ('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s');" % tuple(row)

                    configuration.cursor.execute_query(query)

            print("[Web] "+"\033[32m"+"Chrome Analysis Complete" +"\033[0m")

        else:
            print("[Web] "+"\033[31m"+"No Chrome artifact"+"\033[0m"+" in par_id %s." % (par_id))

        ################## Whale ###################
        if len(whale_artifact) != 0:

            # Whale profile check
            full_path = []
            for i in range(len(whale_artifact)):

                if 'Default' in whale_artifact[i][0]:
                    full_path.append(whale_artifact[i][1] + os.sep + whale_artifact[i][0])

                if 'Profile' in whale_artifact[i][0]:
                    full_path.append(whale_artifact[i][1] + os.sep + whale_artifact[i][0])

            # print(full_path)

            # Make Whale artifact ouput dir
            whale_output_path = configuration.root_tmp_path + os.sep + configuration.case_id + os.sep + \
                                configuration.evidence_id + os.sep + par_id + os.sep + "web" + os.sep + "whale" + os.sep

            # Match between os user whale profile
            os_user_whale_profile = []

            for f in full_path:
                for user in user_list:
                    if f.find(user) != -1:
                        profile_index = f.rfind(os.sep)
                        os_user_whale_profile.append([user, f[profile_index + 1:]])

            # print(os_user_whale_profile)

            # Create profile dir in ouput dir
            if not os.path.isdir(whale_output_path):
                for make_dir_tree in os_user_whale_profile:
                    os.makedirs(whale_output_path + make_dir_tree[0] + os.sep + make_dir_tree[1] + os.sep)

            # Extract whale artifact file
            chromium_artifact_file_list = ['Preferences', 'History', 'Login Data', 'Shortcuts', 'Top Sites', 'Web Data',
                                        'Favicons', 'Cookies', 'Bookmarks']

            for make_dir_tree in os_user_whale_profile:

                for file in chromium_artifact_file_list:
                    self.ExtractTargetFileToPath(
                        source_path_spec=source_path_spec,
                        configuration=configuration,
                        file_path='/Users/' + make_dir_tree[0] + '/AppData/Local/Naver/Naver Whale/User Data/' +
                                  make_dir_tree[1] + '/' + file,
                        output_path=whale_output_path + make_dir_tree[0] + os.sep + make_dir_tree[1] + os.sep)

            print("[Web] Whale artifact files extraction success")

            whale_search_result = []
            whale_visit_urls_result = []
            whale_download_result = []
            whale_top_sites = []
            whale_cookies = []
            whale_autofill = []
            whale_logindata = []
            whale_bookmarks = []
            whale_shortcuts = []
            whale_favicons = []
            whale_visit_history = []

            # Parse artifact
            for file_check in os_user_whale_profile:

                files = [f for f in os.listdir(whale_output_path + file_check[0] + os.sep + file_check[1] + os.sep) if
                         os.path.isfile(
                             os.path.join(whale_output_path + file_check[0] + os.sep + file_check[1] + os.sep, f))]

                if 'History' in files:
                    tmp_file_path = whale_output_path + file_check[0] + os.sep + file_check[1] + os.sep + 'History'
                    whale_search_result.append(whale.whale_search_terms(tmp_file_path))  # fp 대신 dict 자료형으로????
                    whale_visit_urls_result.append(whale.whale_visit_urls(tmp_file_path))
                    whale_download_result.append(whale.whale_download(tmp_file_path))
                    whale_visit_history.append(whale.whale_visit_history(tmp_file_path))

                if 'Bookmarks' in files:
                    tmp_file_path = whale_output_path + file_check[0] + os.sep + file_check[1] + os.sep + 'Bookmarks'
                    whale_bookmarks.append(whale.whale_bookmarks(tmp_file_path))

                if 'Cookies' in files:
                    tmp_file_path = whale_output_path + file_check[0] + os.sep + file_check[1] + os.sep + 'Cookies'
                    whale_cookies.append(whale.whale_cookies(tmp_file_path))

                if 'Top Sites' in files:
                    tmp_file_path = whale_output_path + file_check[0] + os.sep + file_check[1] + os.sep + 'Top Sites'
                    whale_top_sites.append(whale.whale_top_sites(tmp_file_path))

                if 'Web Data' in files:
                    tmp_file_path = whale_output_path + file_check[0] + os.sep + file_check[1] + os.sep + 'Web Data'
                    whale_autofill.append(whale.whale_autofill(tmp_file_path))

                if 'Login Data' in files:
                    tmp_file_path = whale_output_path + file_check[0] + os.sep + file_check[1] + os.sep + 'Login Data'
                    whale_logindata.append(whale.whale_logindata(tmp_file_path))

                if 'Shortcuts' in files:
                    tmp_file_path = whale_output_path + file_check[0] + os.sep + file_check[1] + os.sep + 'Shortcuts'
                    whale_shortcuts.append(whale.whale_shortcuts(tmp_file_path))

                if 'Favicons' in files:
                    tmp_file_path = whale_output_path + file_check[0] + os.sep + file_check[1] + os.sep + 'Favicons'
                    whale_favicons.append(whale.whale_favicons(tmp_file_path))

            # delete chrome output dir
            shutil.rmtree(whale_output_path)

            info = [par_id, configuration.case_id, configuration.evidence_id]

            # insert data
            for bookmark, profile_match in zip(whale_bookmarks, os_user_whale_profile):
                for row in bookmark:
                    table_name = 'lv1_app_web_whale_bookmarks'
                    row = info + list(row) + profile_match

                    query = f"Insert into {table_name} values ('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s');" % tuple(
                        row)

                    # print(query)
                    configuration.cursor.execute_query(query)

            for download, profile_match in zip(whale_download_result, os_user_whale_profile):
                for row in download:
                    table_name = 'lv1_app_web_whale_download'
                    row = info + list(row) + profile_match

                    query = f"Insert into {table_name} values ('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s'" \
                            f", '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s'" \
                            f", '%s', '%s');" % tuple(row)

                    # print(query)
                    configuration.cursor.execute_query(query)

            for visit_urls, profile_match in zip(whale_visit_urls_result, os_user_whale_profile):
                for row in visit_urls:
                    table_name = 'lv1_app_web_whale_visit_urls'
                    row = info + list(row) + profile_match

                    query = f"Insert into {table_name} values ('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s');" % tuple(
                        row)

                    # print(query)
                    configuration.cursor.execute_query(query)

            for visit_history, profile_match in zip(whale_visit_history, os_user_whale_profile):
                for row in visit_history:
                    table_name = 'lv1_app_web_whale_visit_history'
                    row = info + list(row) + profile_match

                    query = f"Insert into {table_name} values ('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s'," \
                            f"'%s', '%s', '%s', '%s');" % tuple(row)

                    configuration.cursor.execute_query(query)

            for search_terms, profile_match in zip(whale_search_result, os_user_whale_profile):
                for row in search_terms:
                    table_name = 'lv1_app_web_whale_search_terms'
                    row = info + list(row) + profile_match

                    query = f"Insert into {table_name} values ('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s');" % tuple(
                        row)

                    # print(query)
                    configuration.cursor.execute_query(query)

            for cookies, profile_match in zip(whale_cookies, os_user_whale_profile):
                for row in cookies:
                    table_name = 'lv1_app_web_whale_cookies'
                    row = info + list(row) + profile_match

                    # query = f"Insert into {table_name} values ('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s');" % tuple(
                    #    row)

                    query = f"Insert into {table_name} values ('%s', '%s', '%s', '%s', '%s', '%s', '%s', " % tuple(
                        row[0:7]) + \
                            "(UNHEX(\'" + row[7].hex() + "\'))" \
                                                         ", '%s', '%s', '%s', '%s', '%s');" % tuple(row[8:])

                    # print(query)
                    configuration.cursor.execute_query(query)

            for top_sites, profile_match in zip(whale_top_sites, os_user_whale_profile):
                for row in top_sites:
                    table_name = 'lv1_app_web_whale_top_sites'
                    row = info + list(row) + profile_match

                    query = f"Insert into {table_name} values ('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s');" % tuple(
                        row)

                    # print(query)
                    configuration.cursor.execute_query(query)

            for autofill, profile_match in zip(whale_autofill, os_user_whale_profile):
                for row in autofill:
                    table_name = 'lv1_app_web_whale_autofill'
                    row = info + list(row) + profile_match

                    query = f"Insert into {table_name} values ('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s');" % tuple(
                        row)

                    # print(query)
                    configuration.cursor.execute_query(query)

            for logindata, profile_match in zip(whale_logindata, os_user_whale_profile):
                for row in logindata:
                    table_name = 'lv1_app_web_whale_logindata'
                    row = info + list(row) + profile_match

                    query = f"Insert into {table_name} values ('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', " % tuple(
                        row[0:8]) + \
                            "(UNHEX(\'" + row[8].hex() + "\'))" \
                                                         ", '%s', '%s', " % tuple(row[9:11]) + \
                            "(UNHEX(\'" + row[11].hex() + "\'))" \
                                                          ", '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', " % tuple(
                        row[12:22]) + \
                            "(UNHEX(\'" + row[22].hex() + "\'))" \
                                                          ", '%s', '%s', '%s', '%s', '%s');" % tuple(row[23:])
                    # print(query)
                    configuration.cursor.execute_query(query)

            for shortcuts, profile_match in zip(whale_shortcuts, os_user_whale_profile):
                for row in shortcuts:
                    table_name = 'lv1_app_web_whale_shortcuts'
                    row = info + list(row) + profile_match

                    query = f"Insert into {table_name} values ('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s');" % tuple(
                        row)

                    # print(query)
                    configuration.cursor.execute_query(query)

            for favicons, profile_match in zip(whale_favicons, os_user_whale_profile):
                for row in favicons:
                    table_name = 'lv1_app_web_whale_favicons'
                    row = info + list(row) + profile_match

                    query = f"Insert into {table_name} values ('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', " % tuple(
                        row[0:8]) + \
                            "(UNHEX(\'" + row[8].hex() + "\'))" \
                                                         ", '%s', '%s', '%s', '%s');" % tuple(row[9:])
                    # print(query)
                    configuration.cursor.execute_query(query)

            print("[Web] " + "\033[32m" + "Whale Analysis Complete" + "\033[0m")

        else:
            print("[Web] " + "\033[31m" + "No Whale artifact" + "\033[0m" + " in par_id %s." % (par_id))

        ################ Chromium Edge ###################
        if len(chromium_edge_artifact) != 0:

            # Profile check
            full_path = []
            for i in range(len(chromium_edge_artifact)):

                if 'Default' in chromium_edge_artifact[i][0]:
                    full_path.append(chromium_edge_artifact[i][1] + os.sep + chromium_edge_artifact[i][0])

                if 'Profile' in chromium_edge_artifact[i][0]:
                    full_path.append(chromium_edge_artifact[i][1] + os.sep + chromium_edge_artifact[i][0])

            # Make Chrome artifact output dir
            edge_output_path = configuration.root_tmp_path + os.sep + configuration.case_id + os.sep + \
                               configuration.evidence_id + os.sep + par_id + os.sep + "web" + os.sep + "chromium_edge" + os.sep

            # Match between os user chrome profile
            os_user_edge_profile = []

            for f in full_path:
                for user in user_list:
                    if f.find(user) != -1:
                        profile_index = f.rfind(os.sep)
                        os_user_edge_profile.append([user, f[profile_index + 1:]])

            # Create profile dir in output dir
            if os.path.isdir(edge_output_path) == False:
                for make_dir_tree in os_user_edge_profile:
                    os.makedirs(edge_output_path + make_dir_tree[0] + os.sep + make_dir_tree[1] + os.sep)

            # Extract chrome artifact file
            chromium_artifact_file_list = ['Preferences', 'History', 'Login Data', 'Shortcuts', 'Top Sites', 'Web Data', 'Favicons',
                                           'Cookies', 'Bookmarks']

            for make_dir_tree in os_user_edge_profile:

                for file in chromium_artifact_file_list:
                    self.ExtractTargetFileToPath(
                        source_path_spec=source_path_spec,
                        configuration=configuration,
                        file_path='/Users/' + make_dir_tree[0] + '/AppData/Local/Microsoft/Edge/User Data/' +
                                  make_dir_tree[1] + '/' + file,
                        output_path=edge_output_path + make_dir_tree[0] + os.sep + make_dir_tree[1] + os.sep)

            print("[Web] Chromium Edge artifact files extraction success")

            edge_search_result = []
            edge_visit_urls_result = []
            edge_download_result = []
            edge_top_sites = []
            edge_shortcuts = []
            edge_favicons = []
            edge_cookies = []
            edge_autofill = []
            edge_logindata = []
            edge_bookmarks = []
            edge_preferences = []
            edge_visit_history = []

            for file_check in os_user_edge_profile:

                files = [f for f in os.listdir(edge_output_path + file_check[0] + os.sep + file_check[1] + os.sep) if
                         os.path.isfile(
                             os.path.join(edge_output_path + file_check[0] + os.sep + file_check[1] + os.sep, f))]

                if 'Preferences' in files:
                    tmp_file_path = edge_output_path + file_check[0] + os.sep + file_check[1] + os.sep + 'Preferences'


                if 'History' in files:
                    tmp_file_path = edge_output_path + file_check[0] + os.sep + file_check[1] + os.sep + 'History'
                    edge_search_result.append(chromium_edge.edge_search_terms(tmp_file_path))  # fp 대신 dict 자료형으로????
                    edge_visit_urls_result.append(chromium_edge.edge_visit_urls(tmp_file_path))
                    edge_download_result.append(chromium_edge.edge_download(tmp_file_path))
                    edge_visit_history.append(chromium_edge.edge_visit_history(tmp_file_path))

                if 'Top Sites' in files:
                    tmp_file_path = edge_output_path + file_check[0] + os.sep + file_check[1] + os.sep + 'Top Sites'
                    edge_top_sites.append(chromium_edge.edge_top_sites(tmp_file_path))

                if 'Shortcuts' in files:
                    tmp_file_path = edge_output_path + file_check[0] + os.sep + file_check[1] + os.sep + 'Shortcuts'
                    edge_shortcuts.append(chromium_edge.edge_shortcuts(tmp_file_path))

                if 'Favicons' in files:
                    tmp_file_path = edge_output_path + file_check[0] + os.sep + file_check[1] + os.sep + 'Favicons'
                    edge_favicons.append(chromium_edge.edge_favicons(tmp_file_path))

                if 'Cookies' in files:
                    tmp_file_path = edge_output_path + file_check[0] + os.sep + file_check[1] + os.sep + 'Cookies'
                    edge_cookies.append(chromium_edge.edge_cookies(tmp_file_path))

                if 'Web Data' in files:
                    tmp_file_path = edge_output_path + file_check[0] + os.sep + file_check[1] + os.sep + 'Web Data'
                    edge_autofill.append(chromium_edge.edge_autofill(tmp_file_path))

                if 'Login Data' in files:
                    tmp_file_path = edge_output_path + file_check[0] + os.sep + file_check[1] + os.sep + 'Login Data'
                    edge_logindata.append(chromium_edge.edge_logindata(tmp_file_path))

                if 'Bookmarks' in files:
                    tmp_file_path = edge_output_path + file_check[0] + os.sep + file_check[1] + os.sep + 'Bookmarks'
                    edge_bookmarks.append(chromium_edge.edge_bookmarks(tmp_file_path))

            # delete chrome output dir
            shutil.rmtree(edge_output_path)

            info = [par_id, configuration.case_id, configuration.evidence_id]

            # insert data
            for search_terms, profile_match in zip(edge_search_result, os_user_edge_profile):
                for row in search_terms:
                    table_name = 'lv1_app_web_chromium_edge_search_terms'

                    row = info + list(row) + profile_match

                    query = f"Insert into {table_name} values ('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s');" % tuple(
                        row)

                    # print(query)
                    configuration.cursor.execute_query(query)
            # print("[chrome] search terms data insert complete")

            for visit_urls, profile_match in zip(edge_visit_urls_result, os_user_edge_profile):
                for row in visit_urls:
                    table_name = 'lv1_app_web_chromium_edge_visit_urls'
                    row = info + list(row) + profile_match

                    query = f"Insert into {table_name} values ('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s');" % tuple(
                        row)

                    # print(query)
                    configuration.cursor.execute_query(query)

            for visit_history, profile_match in zip(edge_visit_history, os_user_edge_profile):
                for row in visit_history:
                    table_name = 'lv1_app_web_chromium_edge_visit_history'
                    row = info + list(row) + profile_match

                    query = f"Insert into {table_name} values ('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s'," \
                            f"'%s', '%s', '%s', '%s');" % tuple(row)

                    configuration.cursor.execute_query(query)

            for download_files, profile_match in zip(edge_download_result, os_user_edge_profile):
                for row in download_files:
                    table_name = 'lv1_app_web_chromium_edge_download'
                    row = info + list(row) + profile_match

                    query = f"Insert into {table_name} values ('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s'" \
                            f", '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s'" \
                            f", '%s', '%s');" % tuple(row)

                    # print(query)
                    configuration.cursor.execute_query(query)

            for top_sites, profile_match in zip(edge_top_sites, os_user_edge_profile):
                for row in top_sites:
                    table_name = 'lv1_app_web_chromium_edge_top_sites'
                    row = info + list(row) + profile_match

                    query = f"Insert into {table_name} values ('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s');" % tuple(
                        row)

                    # print(query)
                    configuration.cursor.execute_query(query)

            for shortcuts, profile_match in zip(edge_shortcuts, os_user_edge_profile):
                for row in shortcuts:
                    table_name = 'lv1_app_web_chromium_edge_shortcuts'
                    row = info + list(row) + profile_match

                    query = f"Insert into {table_name} values ('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s');" % tuple(
                        row)

                    # print(query)
                    configuration.cursor.execute_query(query)

            for favicons, profile_match in zip(edge_favicons, os_user_edge_profile):
                for row in favicons:
                    table_name = 'lv1_app_web_chromium_edge_favicons'
                    row = info + list(row) + profile_match

                    query = f"Insert into {table_name} values ('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', " % tuple(
                        row[0:8]) + \
                            "(UNHEX(\'" + row[8].hex() + "\'))" \
                                                         ", '%s', '%s', '%s', '%s');" % tuple(row[9:])
                    # print(query)
                    configuration.cursor.execute_query(query)

            for cookies, profile_match in zip(edge_cookies, os_user_edge_profile):
                for row in cookies:
                    table_name = 'lv1_app_web_chromium_edge_cookies'
                    row = info + list(row) + profile_match

                    query = f"Insert into {table_name} values ('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', " % tuple(
                        row[0:14]) + \
                            "(UNHEX(\'" + row[14].hex() + "\'))" \
                                                          ", '%s', '%s', '%s');" % tuple(row[15:])
                    # print(query)
                    configuration.cursor.execute_query(query)

            for autofill, profile_match in zip(edge_autofill, os_user_edge_profile):
                for row in autofill:
                    table_name = 'lv1_app_web_chromium_edge_autofill'
                    row = info + list(row) + profile_match

                    # query = f"Insert into {table_name} values ('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s');" % tuple(row)

                    query = f"Insert into {table_name} values ('%s', '%s', '%s', '%s', " % tuple(row[0:4]) + \
                            "(UNHEX(\'" + row[4].hex() + "\'))" + ", " + "(UNHEX(\'" + row[5].hex() + "\'))" \
                                                                                                      ", '%s', '%s', '%s', '%s', '%s');" % tuple(
                        row[6:])

                    # print(query)
                    configuration.cursor.execute_query(query)

            for logindata, profile_match in zip(edge_logindata, os_user_edge_profile):
                for row in logindata:
                    table_name = 'lv1_app_web_chromium_edge_logindata'
                    row = info + list(row) + profile_match

                    query = f"Insert into {table_name} values ('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', " % tuple(
                        row[0:8]) + \
                            "(UNHEX(\'" + row[8].hex() + "\'))" \
                                                         ", '%s', '%s', " % tuple(row[9:11]) + \
                            "(UNHEX(\'" + row[11].hex() + "\'))" \
                                                          ", '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', " % tuple(
                        row[12:22]) + \
                            "(UNHEX(\'" + row[22].hex() + "\'))" \
                                                          ", '%s', '%s', '%s', '%s', '%s');" % tuple(row[23:])
                    # print(query)
                    configuration.cursor.execute_query(query)

            for bookmark, profile_match in zip(edge_bookmarks, os_user_edge_profile):
                for row in bookmark:
                    table_name = 'lv1_app_web_chromium_edge_bookmarks'
                    row = info + list(row) + profile_match

                    query = f"Insert into {table_name} values ('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s');" % tuple(
                        row)

                    # print(query)
                    configuration.cursor.execute_query(query)

            print("[Web] " + "\033[32m" + "Chromium Edge Analysis Complete" + "\033[0m")

        else:
            print("[Web] " + "\033[31m" + "No Chromium Edge artifact" + "\033[0m" + " in par_id %s." % (par_id))

        ################ Opera ###################
        if len(opera_artifact) != 0:

            full_path = []

            for i in range(len(opera_artifact)):
                full_path.append(opera_artifact[i][1] + os.sep + opera_artifact[i][0])

            # Make Chrome artifact output dir
            opera_output_path = configuration.root_tmp_path + os.sep + configuration.case_id + os.sep + \
                               configuration.evidence_id + os.sep + par_id + os.sep + "web" + os.sep + "opera" + os.sep

            # Match between os user chrome profile
            os_user_opera_profile = []

            for user in user_list:
                os_user_opera_profile.append([user, 'default user'])

            # print(os_user_firefox_profile)

            # Create profile dir in output dir
            if os.path.isdir(opera_output_path) == False:
                for make_dir_tree in os_user_opera_profile:
                    os.makedirs(opera_output_path + make_dir_tree[0] + os.sep + make_dir_tree[1] + os.sep)

            opera_artifact_file_list = ['Bookmarks', 'Cookies', 'Favicons', 'History', 'Login Data', 'Preferences', 'Shortcuts', 'Web Data']

            for make_dir_tree in os_user_opera_profile:

                for file in opera_artifact_file_list:
                    self.ExtractTargetFileToPath(
                        source_path_spec=source_path_spec,
                        configuration=configuration,
                        file_path='/Users/' + make_dir_tree[0] + '/AppData/Roaming/Opera Software/Opera Stable/' + file,
                        output_path=opera_output_path + make_dir_tree[0] + os.sep + make_dir_tree[1] + os.sep)

            print("[Web] Opera artifact files extraction success")

            opera_search_terms = []
            opera_visit_urls = []
            opera_download = []
            opera_visit_history = []
            opera_shortcuts = []
            opera_favicons = []
            opera_cookies = []
            opera_autofill = []
            opera_logindata = []
            opera_bookmarks = []

            for file_check in os_user_opera_profile:

                files = [f for f in os.listdir(opera_output_path + file_check[0] + os.sep + file_check[1] + os.sep) if
                         os.path.isfile(
                             os.path.join(opera_output_path + file_check[0] + os.sep + file_check[1] + os.sep, f))]

                if 'History' in files:
                    tmp_file_path = opera_output_path + file_check[0] + os.sep + file_check[1] + os.sep + 'History'
                    opera_search_terms.append(opera.opera_search_terms(tmp_file_path))
                    opera_visit_urls.append(opera.opera_visit_urls(tmp_file_path))
                    opera_download.append(opera.opera_download(tmp_file_path))
                    opera_visit_history.append(opera.opera_visit_history(tmp_file_path))

                if 'Shortcuts' in files:
                    tmp_file_path = opera_output_path + file_check[0] + os.sep + file_check[1] + os.sep + 'Shortcuts'
                    opera_shortcuts.append(opera.opera_shortcuts(tmp_file_path))

                if 'Favicons' in files:
                    tmp_file_path = opera_output_path + file_check[0] + os.sep + file_check[1] + os.sep + 'Favicons'
                    opera_favicons.append(opera.opera_favicons(tmp_file_path))

                if 'Cookies' in files:
                    tmp_file_path = opera_output_path + file_check[0] + os.sep + file_check[1] + os.sep + 'Cookies'
                    opera_cookies.append(opera.opera_cookies(tmp_file_path))

                if 'Web Data' in files: #autofill
                    tmp_file_path = opera_output_path + file_check[0] + os.sep + file_check[1] + os.sep + 'Web Data'
                    opera_autofill.append(opera.opera_autofill(tmp_file_path))

                if 'Login Data' in files:
                    tmp_file_path = opera_output_path + file_check[0] + os.sep + file_check[1] + os.sep + 'Login Data'
                    opera_logindata.append(opera.opera_logindata(tmp_file_path))

                if 'Bookmarks' in files:
                    tmp_file_path = opera_output_path + file_check[0] + os.sep + file_check[1] + os.sep + 'Bookmarks'
                    opera_bookmarks.append(opera.opera_bookmarks(tmp_file_path))


            # delete chrome output dir
            shutil.rmtree(opera_output_path)

            info = [par_id, configuration.case_id, configuration.evidence_id]

            # insert data
            for search_terms, profile_match in zip(opera_search_terms, os_user_opera_profile):
                for row in search_terms:
                    table_name = 'lv1_app_web_opera_search_terms'

                    row = info + list(row) + profile_match

                    query = f"Insert into {table_name} values ('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s');" % tuple(row)

                    # print(query)
                    configuration.cursor.execute_query(query)

            for visit_urls, profile_match in zip(opera_visit_urls, os_user_opera_profile):
                for row in visit_urls:
                    table_name = 'lv1_app_web_opera_visit_urls'

                    row = info + list(row) + profile_match

                    query = f"Insert into {table_name} values ('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s'" \
                            f", '%s', '%s', '%s', '%s', '%s', '%s', '%s');" % tuple(row)

                    # print(query)
                    configuration.cursor.execute_query(query)

            for visit_history, profile_match in zip(opera_visit_history, os_user_opera_profile):
                for row in visit_history:
                    table_name = 'lv1_app_web_opera_visit_history'
                    row = info + list(row) + profile_match

                    query = f"Insert into {table_name} values ('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s'," \
                            f"'%s', '%s', '%s', '%s');" % tuple(row)

                    configuration.cursor.execute_query(query)

            for downlads, profile_match in zip(opera_download, os_user_opera_profile):
                for row in downlads:
                    table_name = 'lv1_app_web_opera_download'

                    row = info + list(row) + profile_match

                    query = f"Insert into {table_name} values ('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s'" \
                            f", '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s'" \
                            f", '%s', '%s');" % tuple(row)

                    # print(query)
                    configuration.cursor.execute_query(query)

            for shortcuts, profile_match in zip(opera_shortcuts, os_user_opera_profile):
                for row in shortcuts:
                    table_name = 'lv1_app_web_opera_shortcuts'
                    row = info + list(row) + profile_match

                    query = f"Insert into {table_name} values ('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s');" % tuple(
                        row)

                    # print(query)
                    configuration.cursor.execute_query(query)

            for favicons, profile_match in zip(opera_favicons, os_user_opera_profile):
                for row in favicons:
                    table_name = 'lv1_app_web_opera_favicons'
                    row = info + list(row) + profile_match

                    query = f"Insert into {table_name} values ('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', " % tuple(
                        row[0:8]) + \
                            "(UNHEX(\'" + row[8].hex() + "\'))" \
                                                         ", '%s', '%s', '%s', '%s');" % tuple(row[9:])
                    # print(query)
                    configuration.cursor.execute_query(query)

            for cookies, profile_match in zip(opera_cookies, os_user_opera_profile):
                for row in cookies:
                    table_name = 'lv1_app_web_opera_cookies'
                    row = info + list(row) + profile_match

                    query = f"Insert into {table_name} values ('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', " % tuple(
                        row[0:14]) + \
                            "(UNHEX(\'" + row[14].hex() + "\'))" \
                                                          ", '%s', '%s', '%s');" % tuple(row[15:])
                    # print(query)
                    configuration.cursor.execute_query(query)

            for autofill, profile_match in zip(opera_autofill, os_user_opera_profile):
                for row in autofill:
                    table_name = 'lv1_app_web_opera_autofill'
                    row = info + list(row) + profile_match

                    query = f"Insert into {table_name} values ('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s');" % tuple(row)

                    configuration.cursor.execute_query(query)

            for logindata, profile_match in zip(opera_logindata, os_user_opera_profile):
                for row in logindata:
                    table_name = 'lv1_app_web_opera_logindata'
                    row = info + list(row) + profile_match

                    query = f"Insert into {table_name} values ('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', " % tuple(
                        row[0:8]) + \
                            "(UNHEX(\'" + row[8].hex() + "\'))" \
                                                         ", '%s', '%s', " % tuple(row[9:11]) + \
                            "(UNHEX(\'" + row[11].hex() + "\'))" \
                                                          ", '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', " % tuple(
                        row[12:22]) + \
                            "(UNHEX(\'" + row[22].hex() + "\'))" \
                                                          ", '%s', '%s', '%s', '%s', '%s');" % tuple(row[23:])
                    # print(query)
                    configuration.cursor.execute_query(query)

            for bookmark, profile_match in zip(opera_bookmarks, os_user_opera_profile):
                for row in bookmark:
                    table_name = 'lv1_app_web_opera_bookmarks'
                    row = info + list(row) + profile_match

                    query = f"Insert into {table_name} values ('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s');" % tuple(
                        row)

                    # print(query)
                    configuration.cursor.execute_query(query)

            print("[Web] " + "\033[32m" + "Opera Analysis Complete" + "\033[0m")

        else:
            print("[Web] " + "\033[31m" + "No Opera artifact" + "\033[0m" + " in par_id %s." % (par_id))

        ################ Firefox ###################
        if len(firefox_artifact) != 0:

            full_path = []
            for i in range(len(firefox_artifact)):

                if '.default-release' in firefox_artifact[i][0]:
                    full_path.append(firefox_artifact[i][1] + os.sep + firefox_artifact[i][0])

            # Make Chrome artifact output dir
            firefox_output_path = configuration.root_tmp_path + os.sep + configuration.case_id + os.sep + \
                               configuration.evidence_id + os.sep + par_id + os.sep + "web" + os.sep + "firefox" + os.sep

            # Match between os user chrome profile
            os_user_firefox_profile = []

            for f in full_path:
                for user in user_list:
                    if f.find(user) != -1:
                        profile_start_index = f.rfind(os.sep) + 1
                        profile_end_index = f.rfind('default-release') - 1
                        os_user_firefox_profile.append([user, f[profile_start_index:profile_end_index]])

            # Create profile dir in output dir
            if os.path.isdir(firefox_output_path) == False:
                for make_dir_tree in os_user_firefox_profile:
                    os.makedirs(firefox_output_path + make_dir_tree[0] + os.sep + make_dir_tree[1] + os.sep)

            # Extract chrome artifact file
            firefox_artifact_file_list = ['places.sqlite', 'content-prefs.sqlite', 'cookies.sqlite', 'favicons.sqlite', 'formhistory.sqlite', 'permissions.sqlite', 'prefs.js']

            for make_dir_tree in os_user_firefox_profile:

                for file in firefox_artifact_file_list:
                    self.ExtractTargetFileToPath(
                        source_path_spec=source_path_spec,
                        configuration=configuration,
                        file_path='/Users/' + make_dir_tree[0] + '/AppData/Roaming/Mozilla/Firefox/Profiles/' +
                                  make_dir_tree[1] + '.default-release/' + file,
                        output_path=firefox_output_path + make_dir_tree[0] + os.sep + make_dir_tree[1] + os.sep)

            print("[Web] Firefox artifact files extraction success")

            firefox_visit_history = []
            firefox_visit_urls = []
            firefox_domains = []
            firefox_downloads = []
            firefox_cookies = []
            firefox_permissions = []
            firefox_formhistory = []
            firefox_favicons = []
            firefox_content_prefs = []
            firefox_bookmarks = []

            for file_check in os_user_firefox_profile:

                files = [f for f in os.listdir(firefox_output_path + file_check[0] + os.sep + file_check[1] + os.sep) if
                         os.path.isfile(
                             os.path.join(firefox_output_path + file_check[0] + os.sep + file_check[1] + os.sep, f))]

                if 'places.sqlite' in files:
                    tmp_file_path = firefox_output_path + file_check[0] + os.sep + file_check[1] + os.sep + 'places.sqlite'
                    firefox_visit_history.append(firefox.firefox_visit_history(tmp_file_path))
                    firefox_visit_urls.append(firefox.firefox_visit_urls(tmp_file_path))
                    firefox_domains.append(firefox.firefox_domain(tmp_file_path))
                    firefox_downloads.append(firefox.firefox_downloads(tmp_file_path))
                    firefox_bookmarks.append(firefox.firefox_bookmarks(tmp_file_path))

                if 'cookies.sqlite' in files:
                    tmp_file_path = firefox_output_path + file_check[0] + os.sep + file_check[1] + os.sep + 'cookies.sqlite'
                    firefox_cookies.append(firefox.firefox_cookies(tmp_file_path))

                if 'permissions.sqlite' in files:
                    tmp_file_path = firefox_output_path + file_check[0] + os.sep + file_check[1] + os.sep + 'permissions.sqlite'
                    firefox_permissions.append(firefox.firefox_perms(tmp_file_path))

                if 'formhistory.sqlite' in files:
                    tmp_file_path = firefox_output_path + file_check[0] + os.sep + file_check[1] + os.sep + 'formhistory.sqlite'
                    firefox_formhistory.append(firefox.firefox_forms(tmp_file_path))

                if 'favicons.sqlite' in files:
                    tmp_file_path = firefox_output_path + file_check[0] + os.sep + file_check[1] + os.sep + 'favicons.sqlite'
                    firefox_favicons.append(firefox.firefox_favicons(tmp_file_path))

                if 'content-prefs.sqlite' in files:
                    tmp_file_path = firefox_output_path + file_check[0] + os.sep + file_check[1] + os.sep + 'content-prefs.sqlite'
                    firefox_content_prefs.append(firefox.firefox_prefs(tmp_file_path))


            # delete chrome output dir
            shutil.rmtree(firefox_output_path)

            info = [par_id, configuration.case_id, configuration.evidence_id]

            for visit_history, profile_match in zip(firefox_visit_history, os_user_firefox_profile):
                for row in visit_history:

                    table_name = 'lv1_app_web_firefox_visit_history'
                    row = info + list(row) + profile_match
                    query = f"Insert into {table_name} values ('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s');" % tuple(row)

                    # print(query)
                    configuration.cursor.execute_query(query)

            for visit_urls, profile_match in zip(firefox_visit_urls, os_user_firefox_profile):
                for row in visit_urls:

                    table_name = 'lv1_app_web_firefox_visit_urls'
                    row = info + list(row) + profile_match

                    query = f"Insert into {table_name} values ('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s');" % tuple(row)

                    # print(query)
                    configuration.cursor.execute_query(query)

            for domain, profile_match in zip(firefox_domains, os_user_firefox_profile):
                for row in domain:

                    table_name = 'lv1_app_web_firefox_domain'
                    row = info + list(row) + profile_match
                    query = f"Insert into {table_name} values ('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s');" % tuple(row)

                    # print(query)
                    configuration.cursor.execute_query(query)

            for download, profile_match in zip(firefox_downloads, os_user_firefox_profile):
                for row in download:

                    table_name = 'lv1_app_web_firefox_download'
                    row = info + list(row) + profile_match
                    query = f"Insert into {table_name} values ('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s');" % tuple(row)

                    configuration.cursor.execute_query(query)

            for cookies, profile_match in zip(firefox_cookies, os_user_firefox_profile):
                for row in cookies:

                    table_name = 'lv1_app_web_firefox_cookies'
                    row = info + list(row) + profile_match
                    query = f"Insert into {table_name} values ('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s');" % tuple(row)

                    configuration.cursor.execute_query(query)

            for permissions, profile_match in zip(firefox_permissions, os_user_firefox_profile):
                for row in permissions:

                    table_name = 'lv1_app_web_firefox_permissions'
                    row = info + list(row) + profile_match
                    query = f"Insert into {table_name} values ('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s');" % tuple(row)

                    configuration.cursor.execute_query(query)

            for forms, profile_match in zip(firefox_formhistory, os_user_firefox_profile):
                for row in forms:

                    table_name = 'lv1_app_web_firefox_formhistory'
                    row = info + list(row) + profile_match
                    query = f"Insert into {table_name} values ('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s');" % tuple(row)

                    configuration.cursor.execute_query(query)

            for favicons, profile_match in zip(firefox_favicons, os_user_firefox_profile):
                for row in favicons:
                    table_name = 'lv1_app_web_firefox_favicons'
                    row = info + list(row) + profile_match

                    query = f"Insert into {table_name} values ('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', " % tuple(
                        row[0:10]) + \
                            "(UNHEX(\'" + row[10].hex() + "\'))" \
                                                         ", '%s', '%s', '%s');" % tuple(row[11:])

                    configuration.cursor.execute_query(query)

            for prefs, profile_match in zip(firefox_content_prefs, os_user_firefox_profile):
                for row in prefs:

                    table_name = 'lv1_app_web_firefox_content_prefs'
                    row = info + list(row) + profile_match
                    query = f"Insert into {table_name} values ('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s');" % tuple(row)

                    configuration.cursor.execute_query(query)

            for bookmarks, profile_match in zip(firefox_bookmarks, os_user_firefox_profile):
                for row in bookmarks:

                    table_name = 'lv1_app_web_firefox_bookmarks'
                    row = info + list(row) + profile_match
                    query = f"Insert into {table_name} values ('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s');" % tuple(row)

                    configuration.cursor.execute_query(query)

            print("[Web] " + "\033[32m" + "Firefox Analysis Complete" + "\033[0m")

        else:
            print("[Web] " + "\033[31m" + "No Firefox artifact" + "\033[0m" + " in par_id %s." % (par_id))

manager.ModulesManager.RegisterModule(ChromiumConnector)
