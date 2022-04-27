# -*- coding: utf-8 -*-
"""module for Chromium Web Browser."""
import os
import shutil
from json import decoder

from engine import logger
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

    def Connect(self, par_id, configuration, source_path_spec, knowledge_base):

        chrome_query = f"SELECT name, parent_path, extension FROM file_info WHERE par_id='{par_id}' and ("
        whale_query = f"SELECT name, parent_path, extension FROM file_info WHERE par_id='{par_id}' and ("
        chromium_edge_query = f"SELECT name, parent_path, extension FROM file_info WHERE par_id='{par_id}' and ("
        opera_query = f"SELECT name, parent_path, extension FROM file_info WHERE par_id='{par_id}' and ("
        firefox_query = f"SELECT name, parent_path, extension FROM file_info WHERE par_id='{par_id}' and ("

        user_list = []

        query_sep = self.GetQuerySeparator(source_path_spec, configuration)
        if not knowledge_base._user_accounts:
            return False

        #query_sep = query_sep.replace('\\\\', '\\')

        for user_accounts in knowledge_base._user_accounts.values():
            for hostname in user_accounts.values():
                if hostname.identifier.find('S-1-5-21') == -1:
                    continue

                chrome_query += f"parent_path like \'root{query_sep}Users{query_sep}{hostname.username}{query_sep}AppData{query_sep}Local{query_sep}Google{query_sep}Chrome{query_sep}User Data\' or "
                whale_query += f"parent_path like \'root{query_sep}Users{query_sep}{hostname.username}{query_sep}AppData{query_sep}Local{query_sep}Naver{query_sep}Naver Whale{query_sep}User Data\' or "
                chromium_edge_query += f"parent_path like \'root{query_sep}Users{query_sep}{hostname.username}{query_sep}AppData{query_sep}Local{query_sep}Microsoft{query_sep}Edge{query_sep}User Data\' or "
                opera_query += f"parent_path like \'root{query_sep}Users{query_sep}{hostname.username}{query_sep}AppData{query_sep}Roaming{query_sep}Opera Software{query_sep}Opera Stable\' or "
                firefox_query += f"parent_path like \'root{query_sep}Users{query_sep}{hostname.username}{query_sep}AppData{query_sep}Roaming{query_sep}Mozilla{query_sep}Firefox{query_sep}Profiles\' or "
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
        firefox_file_path = os.path.dirname(os.path.abspath(__file__)) + os.sep + 'schema' + os.sep + 'web' + os.sep \
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

        whale_yaml_list = [whale_file_path + 'lv1_app_web_whale_bookmarks.yaml',
                           whale_file_path + 'lv1_app_web_whale_download.yaml',
                           whale_file_path + 'lv1_app_web_whale_visit_urls.yaml',
                           whale_file_path + 'lv1_app_web_whale_visit_history.yaml',
                           whale_file_path + 'lv1_app_web_whale_search_terms.yaml',
                           whale_file_path + 'lv1_app_web_whale_cookies.yaml',
                           whale_file_path + 'lv1_app_web_whale_top_sites.yaml',
                           whale_file_path + 'lv1_app_web_whale_autofill.yaml',
                           whale_file_path + 'lv1_app_web_whale_logindata.yaml',
                           whale_file_path + 'lv1_app_web_whale_shortcuts.yaml',
                           whale_file_path + 'lv1_app_web_whale_favicons.yaml']

        edge_yaml_list = [edge_file_path + 'lv1_app_web_chromium_edge_search_terms.yaml',
                          edge_file_path + 'lv1_app_web_chromium_edge_visit_urls.yaml',
                          edge_file_path + 'lv1_app_web_chromium_edge_visit_history.yaml',
                          edge_file_path + 'lv1_app_web_chromium_edge_download.yaml',
                          edge_file_path + 'lv1_app_web_chromium_edge_shortcuts.yaml',
                          edge_file_path + 'lv1_app_web_chromium_edge_favicons.yaml',
                          edge_file_path + 'lv1_app_web_chromium_edge_cookies.yaml',
                          edge_file_path + 'lv1_app_web_chromium_edge_autofill.yaml',
                          edge_file_path + 'lv1_app_web_chromium_edge_logindata.yaml',
                          edge_file_path + 'lv1_app_web_chromium_edge_bookmarks.yaml',
                          edge_file_path + 'lv1_app_web_chromium_edge_top_sites.yaml']

        opera_yaml_list = [opera_file_path + 'lv1_app_web_opera_search_terms.yaml',
                           opera_file_path + 'lv1_app_web_opera_visit_urls.yaml',
                           opera_file_path + 'lv1_app_web_opera_visit_history.yaml',
                           opera_file_path + 'lv1_app_web_opera_autofill.yaml',
                           opera_file_path + 'lv1_app_web_opera_bookmarks.yaml',
                           opera_file_path + 'lv1_app_web_opera_cookies.yaml',
                           opera_file_path + 'lv1_app_web_opera_favicons.yaml',
                           opera_file_path + 'lv1_app_web_opera_logindata.yaml',
                           opera_file_path + 'lv1_app_web_opera_shortcuts.yaml',
                           opera_file_path + 'lv1_app_web_opera_download.yaml']

        firefox_yaml_list = [firefox_file_path + 'lv1_app_web_firefox_visit_history.yaml',
                             firefox_file_path + 'lv1_app_web_firefox_visit_urls.yaml',
                             firefox_file_path + 'lv1_app_web_firefox_domain.yaml',
                             firefox_file_path + 'lv1_app_web_firefox_download.yaml',
                             firefox_file_path + 'lv1_app_web_firefox_cookies.yaml',
                             firefox_file_path + 'lv1_app_web_firefox_permissions.yaml',
                             firefox_file_path + 'lv1_app_web_firefox_formhistory.yaml',
                             firefox_file_path + 'lv1_app_web_firefox_favicons.yaml',
                             firefox_file_path + 'lv1_app_web_firefox_content_prefs.yaml',
                             firefox_file_path + 'lv1_app_web_firefox_bookmarks.yaml']

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
                    full_path.append(chrome_artifact[i][1] + query_sep + chrome_artifact[i][0])

                if 'Profile' in chrome_artifact[i][0]:
                    full_path.append(chrome_artifact[i][1] + query_sep + chrome_artifact[i][0])

            if len(full_path) != 0:

                # Make Chrome artifact output dir
                chrome_output_path = configuration.root_tmp_path + os.sep + configuration.case_id + os.sep + \
                                     configuration.evidence_id + os.sep + par_id + os.sep + "web" + os.sep + "chrome" + os.sep

                # Match between os user chrome profile
                os_user_chrome_profile = []

                for f in full_path:
                    for user in user_list:
                        if f.find(user) != -1:
                            f = f.replace(query_sep, os.sep)
                            profile_index = f.rfind(os.sep)
                            os_user_chrome_profile.append([user, f[profile_index + 1:]])

                # Create profile dir in output dir
                if not os.path.isdir(chrome_output_path):
                    for make_dir_tree in os_user_chrome_profile:
                        os.makedirs(chrome_output_path + make_dir_tree[0] + os.sep + make_dir_tree[1] + os.sep)

                # Extract chrome artifact file
                chromium_artifact_file_list = ['Preferences', 'History', 'Login Data', 'Shortcuts', 'Top Sites', 'Web Data',
                                               'Favicons', 'Cookies', 'Bookmarks']

                for make_dir_tree in os_user_chrome_profile:
                    for file in chromium_artifact_file_list:
                        file_path = f'{query_sep}Users{query_sep}{make_dir_tree[0]}{query_sep}AppData{query_sep}Local' \
                                    f'{query_sep}Google{query_sep}Chrome{query_sep}User Data{query_sep}' \
                                    f'{make_dir_tree[1]}{query_sep}{file}'

                        self.ExtractTargetFileToPath(
                            source_path_spec=source_path_spec,
                            configuration=configuration,
                            file_path=file_path,
                            output_path=chrome_output_path + make_dir_tree[0] + os.sep + make_dir_tree[1] + os.sep)

                # print("[Web] Chrome artifact files extraction success")

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
                    try:
                        if 'Preferences' in files:
                            tmp_file_path = chrome_output_path + file_check[0] + os.sep + file_check[1] \
                                            + os.sep + 'Preferences'
                            chrome_domain.append(chrome.chrome_domain_analysis(tmp_file_path))
                            chrome_google_account.append(chrome.chrome_google_account(tmp_file_path))
                            chrome_zoom_level.append(chrome.chrome_zoom_level(tmp_file_path))
                    except decoder.JSONDecodeError:
                        pass
                    except UnicodeDecodeError:
                        pass

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
                # Chrome Search Terms
                result = []
                for search_terms, profile_match in zip(chrome_search_result, os_user_chrome_profile):
                    source = get_source_path(profile_match, 'History', 'Chrome')
                    for row in search_terms:
                        row[2] = configuration.apply_time_zone(row[2], knowledge_base.time_zone)  # searched_time
                        row = info + row + profile_match + [source]
                        result.append(row)
                query = f"Insert into lv1_app_web_chrome_search_terms values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"
                configuration.cursor.bulk_execute(query, result)

                # Chrome Visit Urls
                result = []
                for visit_urls, profile_match in zip(chrome_visit_urls_result, os_user_chrome_profile):
                    source = get_source_path(profile_match, 'History', 'Chrome')
                    for row in visit_urls:
                        row[1] = configuration.apply_time_zone(row[1], knowledge_base.time_zone)  # last_visited_time
                        row = info + row + profile_match + [source]
                        result.append(row)
                query = f"Insert into lv1_app_web_chrome_visit_urls values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"
                configuration.cursor.bulk_execute(query, result)

                # Chrome Visit History
                result = []
                for visit_history, profile_match in zip(chrome_visit_history, os_user_chrome_profile):
                    source = get_source_path(profile_match, 'History', 'Chrome')
                    for row in visit_history:
                        row[4] = configuration.apply_time_zone(row[4], knowledge_base.time_zone)  # visit_time
                        row = info + row + profile_match + [source]
                        result.append(row)
                query = f"Insert into lv1_app_web_chrome_visit_history values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, " \
                        f"%s, %s, %s, %s);"
                configuration.cursor.bulk_execute(query, result)

                # Chrome Download
                result = []
                for download_files, profile_match in zip(chrome_download_result, os_user_chrome_profile):
                    source = get_source_path(profile_match, 'History', 'Chrome')
                    for row in download_files:
                        row[7] = configuration.apply_time_zone(row[7], knowledge_base.time_zone)  # start_time
                        row[8] = configuration.apply_time_zone(row[8], knowledge_base.time_zone)  # end_time
                        row[9] = configuration.apply_time_zone(row[9], knowledge_base.time_zone)  # file_last_access_time
                        row[10] = configuration.apply_time_zone(row[10],
                                                                knowledge_base.time_zone)  # file_last_modified_time
                        row = info + row + profile_match + [source]
                        result.append(row)
                query = f"Insert into lv1_app_web_chrome_download values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, " \
                        f"%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"
                configuration.cursor.bulk_execute(query, result)

                # Chrome Top Sites
                result = []
                for top_sites, profile_match in zip(chrome_top_sites, os_user_chrome_profile):
                    source = get_source_path(profile_match, 'Top Sites', 'Chrome')
                    for row in top_sites:
                        row = info + row + profile_match + [source]
                        result.append(row)
                query = f"Insert into lv1_app_web_chrome_top_sites values (%s, %s, %s, %s, %s, %s, %s, %s, %s);"
                configuration.cursor.bulk_execute(query, result)

                # Chrome Shortcuts
                result = []
                for shortcuts, profile_match in zip(chrome_shortcuts, os_user_chrome_profile):
                    source = get_source_path(profile_match, 'Shortcuts', 'Chrome')
                    for row in shortcuts:
                        row[6] = configuration.apply_time_zone(row[6], knowledge_base.time_zone)  # last_access_time
                        row = info + row + profile_match + [source]
                        result.append(row)
                query = f"Insert into lv1_app_web_chrome_shortcuts values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, " \
                        f"%s, %s, %s, %s);"
                configuration.cursor.bulk_execute(query, result)

                # Chrome Favicons
                for favicons, profile_match in zip(chrome_favicons, os_user_chrome_profile):
                    source = get_source_path(profile_match, 'Favicons', 'Chrome')
                    for row in favicons:
                        row[3] = configuration.apply_time_zone(row[3], knowledge_base.time_zone)  # last_updated
                        row[4] = configuration.apply_time_zone(row[4], knowledge_base.time_zone)  # last_requested
                        row = info + row + profile_match + [source]

                        query = f"Insert into lv1_app_web_chrome_favicons values ('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', " % tuple(
                            row[0:8]) + \
                                "(UNHEX(\'" + row[8].hex() + "\'))" \
                                                             ", '%s', '%s', '%s', '%s', '%s');" % tuple(row[9:])
                        configuration.cursor.execute_query(query)

                # Chrome Cookies
                for cookies, profile_match in zip(chrome_cookies, os_user_chrome_profile):
                    source = get_source_path(profile_match, 'Cookies', 'Chrome')
                    for row in cookies:
                        row[0] = configuration.apply_time_zone(row[0], knowledge_base.time_zone)  # creation_utc
                        row[4] = configuration.apply_time_zone(row[4], knowledge_base.time_zone)  # expires_utc
                        row[7] = configuration.apply_time_zone(row[7], knowledge_base.time_zone)  # last_access_utc
                        row = info + row + profile_match + [source]
                        #print(row[14])
                        try:
                            query = f"Insert into lv1_app_web_chrome_cookies values ('%s', '%s', '%s', '%s', '%s', '%s', " \
                                    f"'%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', " % tuple(row[0:14]) + \
                                    "(UNHEX(\'" + row[14].hex() + "\')), '%s', '%s', '%s', '%s');" % tuple(row[15:])
                        except Exception as e:
                            logger.error(str(e))
                        configuration.cursor.execute_query(query)

                # Chrome Autofill
                result = []
                for autofill, profile_match in zip(chrome_autofill, os_user_chrome_profile):
                    source = get_source_path(profile_match, 'Web Data', 'Chrome')
                    for row in autofill:
                        row[3] = configuration.apply_time_zone(row[3], knowledge_base.time_zone)  # date_created
                        row[4] = configuration.apply_time_zone(row[4], knowledge_base.time_zone)  # date_last_used
                        row = info + row + profile_match + [source]
                        result.append(row)

                query = f"Insert into lv1_app_web_chrome_autofill values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"
                configuration.cursor.bulk_execute(query, result)

                # Chrome Login Data
                for logindata, profile_match in zip(chrome_logindata, os_user_chrome_profile):
                    source = get_source_path(profile_match, 'Login Data', 'Chrome')
                    for row in logindata:
                        row[7] = configuration.apply_time_zone(row[7], knowledge_base.time_zone)  # date_created
                        row[13] = configuration.apply_time_zone(row[13], knowledge_base.time_zone)  # date_synced
                        row[22] = configuration.apply_time_zone(row[22], knowledge_base.time_zone)  # date_last_used
                        row = info + row + profile_match + [source]

                        query = f"Insert into lv1_app_web_chrome_logindata values ('%s', '%s', '%s', '%s', '%s', '%s', " \
                                f"'%s', '%s', " % tuple(row[0:8]) + \
                                "(UNHEX(\'" + row[8].hex() + "\'))" \
                                                             ", '%s', '%s', " % tuple(row[9:11]) + \
                                "(UNHEX(\'" + row[11].hex() + "\'))" \
                                                              ", '%s', '%s', '%s', '%s', '%s', '%s', '%s', " \
                                                              "'%s', '%s', '%s', " % tuple(row[12:22]) + \
                                "(UNHEX(\'" + row[22].hex() + "\'))" \
                                                              ", '%s', '%s', '%s', '%s', '%s', '%s');" % tuple(row[23:])
                        configuration.cursor.execute_query(query)

                # Chrome Bookmarks
                result = []
                for bookmark, profile_match in zip(chrome_bookmarks, os_user_chrome_profile):
                    source = get_source_path(profile_match, 'Bookmarks', 'Chrome')
                    for row in bookmark:
                        row[0] = configuration.apply_time_zone(row[0], knowledge_base.time_zone)  # date_added
                        row = info + row + profile_match + [source]
                        result.append(row)
                query = f"Insert into lv1_app_web_chrome_bookmarks values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, " \
                        f"%s, %s, %s, %s);"
                configuration.cursor.bulk_execute(query, result)

                # Chrome Domain
                result = []
                for domain, profile_match in zip(chrome_domain, os_user_chrome_profile):
                    source = get_source_path(profile_match, 'Preferences', 'Chrome')
                    for row in domain:
                        row[2] = configuration.apply_time_zone(row[2], knowledge_base.time_zone)  # last_modified
                        row[4] = configuration.apply_time_zone(row[4], knowledge_base.time_zone)  # last_engagement_time
                        row[5] = configuration.apply_time_zone(row[5],
                                                               knowledge_base.time_zone)  # last_shortcut_launch_time
                        row = info + row + profile_match + [source]
                        result.append(row)
                query = f"Insert into lv1_app_web_chrome_domain values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, " \
                        f"%s, %s, %s, %s);"
                configuration.cursor.bulk_execute(query, result)

                # Chrome Google Account
                result = []
                for google_account, profile_match in zip(chrome_google_account, os_user_chrome_profile):
                    source = get_source_path(profile_match, 'Preferences', 'Chrome')
                    for row in google_account:
                        row = info + row + profile_match + [source]
                        result.append(row)
                query = f"Insert into lv1_app_web_chrome_google_account values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, " \
                        f"%s, %s, %s, %s, %s, %s);"
                configuration.cursor.bulk_execute(query, result)

                # Chrome Zoom Level
                result = []
                for zoom_level, profile_match in zip(chrome_zoom_level, os_user_chrome_profile):
                    source = get_source_path(profile_match, 'Preferences', 'Chrome')
                    for row in zoom_level:
                        row[2] = configuration.apply_time_zone(row[2], knowledge_base.time_zone)  # last_modified_time
                        row = info + row + profile_match + [source]
                        result.append(row)
                query = f"Insert into lv1_app_web_chrome_zoom_level values (%s, %s, %s, %s, %s, %s, %s, %s, %s);"
                configuration.cursor.bulk_execute(query, result)

                # print("[Web] " + "\033[32m" + "Chrome Analysis Complete" + "\033[0m")
        else:
            pass
            # print("[Web] " + "\033[31m" + "No Chrome artifact" + "\033[0m" + " in par_id %s." % (par_id))

        ################## Whale ###################
        if len(whale_artifact) != 0:

            # Whale profile check
            full_path = []
            for i in range(len(whale_artifact)):

                if 'Default' in whale_artifact[i][0]:
                    full_path.append(whale_artifact[i][1] + query_sep + whale_artifact[i][0])

                if 'Profile' in whale_artifact[i][0]:
                    full_path.append(whale_artifact[i][1] + query_sep + whale_artifact[i][0])

            if len(full_path) == 0:
                # Make Whale artifact output dir
                whale_output_path = configuration.root_tmp_path + os.sep + configuration.case_id + os.sep + \
                                    configuration.evidence_id + os.sep + par_id + os.sep + "web" + os.sep + "whale" + os.sep

                # Match between os user whale profile
                os_user_whale_profile = []

                for f in full_path:
                    for user in user_list:
                        if f.find(user) != -1:
                            f = f.replace(query_sep, os.sep)
                            profile_index = f.rfind(os.sep)
                            os_user_whale_profile.append([user, f[profile_index + 1:]])

                # Create profile dir in output dir
                if not os.path.isdir(whale_output_path):
                    for make_dir_tree in os_user_whale_profile:
                        os.makedirs(whale_output_path + make_dir_tree[0] + os.sep + make_dir_tree[1] + os.sep)

                # Extract whale artifact file
                chromium_artifact_file_list = ['Preferences', 'History', 'Login Data', 'Shortcuts', 'Top Sites', 'Web Data',
                                               'Favicons', 'Cookies', 'Bookmarks']

                for make_dir_tree in os_user_whale_profile:
                    for file in chromium_artifact_file_list:
                        file_path = f'{query_sep}Users{query_sep}{make_dir_tree[0]}{query_sep}AppData{query_sep}Local' \
                                    f'{query_sep}Naver{query_sep}Naver Whale{query_sep}User Data{query_sep}' \
                                    f'{make_dir_tree[1]}{query_sep}{file}'
                        self.ExtractTargetFileToPath(
                            source_path_spec=source_path_spec,
                            configuration=configuration,
                            file_path=file_path,
                            output_path=whale_output_path + make_dir_tree[0] + os.sep + make_dir_tree[1] + os.sep)

                # print("[Web] Whale artifact files extraction success")

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
                # Whale Bookmarks
                result = []
                for bookmark, profile_match in zip(whale_bookmarks, os_user_whale_profile):
                    source = get_source_path(profile_match, 'Bookmarks', 'Whale')
                    for row in bookmark:
                        row[0] = configuration.apply_time_zone(row[0], knowledge_base.time_zone)  # date_added
                        row = info + row + profile_match + [source]
                        result.append(row)
                query = f"Insert into lv1_app_web_whale_bookmarks values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, " \
                        f"%s, %s, %s, %s);"
                configuration.cursor.bulk_execute(query, result)

                # Whale Download
                result = []
                for download_files, profile_match in zip(whale_download_result, os_user_whale_profile):
                    source = get_source_path(profile_match, 'History', 'Whale')
                    for row in download_files:
                        row[7] = configuration.apply_time_zone(row[7], knowledge_base.time_zone)  # start_time
                        row[8] = configuration.apply_time_zone(row[8], knowledge_base.time_zone)  # end_time
                        row[9] = configuration.apply_time_zone(row[9], knowledge_base.time_zone)  # file_last_access_time
                        row[10] = configuration.apply_time_zone(row[10],
                                                                knowledge_base.time_zone)  # file_last_modified_time
                        row = info + row + profile_match + [source]
                        result.append(row)
                query = f"Insert into lv1_app_web_whale_download values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, " \
                        f"%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"
                configuration.cursor.bulk_execute(query, result)

                # Whale Visit Urls
                result = []
                for visit_urls, profile_match in zip(whale_visit_urls_result, os_user_whale_profile):
                    source = get_source_path(profile_match, 'History', 'Whale')
                    for row in visit_urls:
                        row[5] = configuration.apply_time_zone(row[5], knowledge_base.time_zone)  # last_visited_time
                        row = info + row + profile_match + [source]
                        result.append(row)
                query = f"Insert into lv1_app_web_whale_visit_urls values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"
                configuration.cursor.bulk_execute(query, result)

                # Whale Visit History
                result = []
                for visit_history, profile_match in zip(whale_visit_history, os_user_whale_profile):
                    source = get_source_path(profile_match, 'History', 'Whale')
                    for row in visit_history:
                        row[4] = configuration.apply_time_zone(row[4], knowledge_base.time_zone)  # visit_time
                        row = info + row + profile_match + [source]
                        result.append(row)
                query = f"Insert into lv1_app_web_whale_visit_history values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, " \
                        f"%s, %s, %s, %s);"
                configuration.cursor.bulk_execute(query, result)

                # Whale Search Terms
                result = []
                for search_terms, profile_match in zip(whale_search_result, os_user_whale_profile):
                    source = get_source_path(profile_match, 'History', 'Whale')
                    for row in search_terms:
                        row[4] = configuration.apply_time_zone(row[4], knowledge_base.time_zone)  # last_visit_time
                        row = info + row + profile_match + [source]
                        result.append(row)
                query = f"Insert into lv1_app_web_whale_search_terms values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"
                configuration.cursor.bulk_execute(query, result)

                # Whale Cookies
                for cookies, profile_match in zip(whale_cookies, os_user_whale_profile):
                    source = get_source_path(profile_match, 'Cookies', 'Whale')
                    for row in cookies:
                        row[5] = configuration.apply_time_zone(row[5], knowledge_base.time_zone)  # creation_utc
                        row[6] = configuration.apply_time_zone(row[6], knowledge_base.time_zone)  # expires_utc
                        row[7] = configuration.apply_time_zone(row[7], knowledge_base.time_zone)  # last_access_utc
                        row = info + row + profile_match + [source]
                        query = f"Insert into lv1_app_web_whale_cookies values ('%s', '%s', '%s', '%s', '%s', '%s', '%s'," \
                                f" " % tuple(row[0:7]) + \
                                "(UNHEX(\'" + row[7].hex() + "\'))" \
                                                             ", '%s', '%s', '%s', '%s', '%s', '%s');" % tuple(row[8:])
                        configuration.cursor.execute_query(query)

                # Whale Top Sites
                result = []
                for top_sites, profile_match in zip(whale_top_sites, os_user_whale_profile):
                    source = get_source_path(profile_match, 'Top Sites', 'Whale')
                    for row in top_sites:
                        row = info + row + profile_match + [source]
                        result.append(row)
                query = f"Insert into lv1_app_web_whale_top_sites values (%s, %s, %s, %s, %s, %s, %s, %s, %s);"
                configuration.cursor.bulk_execute(query, result)

                # Whale Autofill
                result = []
                for autofill, profile_match in zip(whale_autofill, os_user_whale_profile):
                    source = get_source_path(profile_match, 'Web Data', 'Whale')
                    for row in autofill:
                        row[1] = configuration.apply_time_zone(row[1], knowledge_base.time_zone)  # date_created
                        row[2] = configuration.apply_time_zone(row[2], knowledge_base.time_zone)  # date_last_used
                        row = info + row + profile_match + [source]
                        result.append(row)
                query = f"Insert into lv1_app_web_whale_autofill values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"
                configuration.cursor.bulk_execute(query, result)

                # Whale Login Data
                for logindata, profile_match in zip(whale_logindata, os_user_whale_profile):
                    source = get_source_path(profile_match, 'Login Data', 'Whale')
                    for row in logindata:
                        row[7] = configuration.apply_time_zone(row[7], knowledge_base.time_zone)  # date_created
                        row[13] = configuration.apply_time_zone(row[13], knowledge_base.time_zone)  # date_synced
                        row[22] = configuration.apply_time_zone(row[22], knowledge_base.time_zone)  # date_last_used
                        row = info + row + profile_match + [source]
                        query = f"Insert into lv1_app_web_whale_logindata values ('%s', '%s', '%s', '%s', '%s', '%s', " \
                                f"'%s', '%s', " % tuple(row[0:8]) + \
                                "(UNHEX(\'" + row[8].hex() + "\'))" \
                                                             ", '%s', '%s', " % tuple(row[9:11]) + \
                                "(UNHEX(\'" + row[11].hex() + "\'))" \
                                                              ", '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', " \
                                                              "'%s', " % tuple(row[12:22]) + \
                                "(UNHEX(\'" + row[22].hex() + "\'))" \
                                                              ", '%s', '%s', '%s', '%s', '%s', '%s');" % tuple(row[23:])
                        configuration.cursor.execute_query(query)

                # Whale Shortcuts
                result = []
                for shortcuts, profile_match in zip(whale_shortcuts, os_user_whale_profile):
                    source = get_source_path(profile_match, 'Shortcuts', 'Whale')
                    for row in shortcuts:
                        row[6] = configuration.apply_time_zone(row[6], knowledge_base.time_zone)  # last_access_time
                        row = info + row + profile_match + [source]
                        result.append(row)
                query = f"Insert into lv1_app_web_whale_shortcuts values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, " \
                        f"%s, %s, %s, %s);"
                configuration.cursor.bulk_execute(query, result)

                # Whale Favicons
                for favicons, profile_match in zip(whale_favicons, os_user_whale_profile):
                    source = get_source_path(profile_match, 'Favicons', 'Whale')
                    for row in favicons:
                        row[3] = configuration.apply_time_zone(row[3], knowledge_base.time_zone)  # last_updated
                        row[4] = configuration.apply_time_zone(row[4], knowledge_base.time_zone)  # last_requested
                        row = info + row + profile_match + [source]
                        query = f"Insert into lv1_app_web_whale_favicons values ('%s', '%s', '%s', '%s', '%s', '%s', " \
                                f"'%s', '%s', " % tuple(row[0:8]) + \
                                "(UNHEX(\'" + row[8].hex() + "\')), '%s', '%s', '%s', '%s', '%s');" % tuple(row[9:])
                        configuration.cursor.execute_query(query)

                # print("[Web] " + "\033[32m" + "Whale Analysis Complete" + "\033[0m")
        else:
            pass
            # print("[Web] " + "\033[31m" + "No Whale artifact" + "\033[0m" + " in par_id %s." % (par_id))


        ################ Chromium Edge ###################
        if len(chromium_edge_artifact) != 0:

            # Profile check
            full_path = []
            for i in range(len(chromium_edge_artifact)):

                if 'Default' in chromium_edge_artifact[i][0]:
                    full_path.append(chromium_edge_artifact[i][1] + os.sep + chromium_edge_artifact[i][0])

                if 'Profile' in chromium_edge_artifact[i][0]:
                    full_path.append(chromium_edge_artifact[i][1] + os.sep + chromium_edge_artifact[i][0])

            if len(full_path) != 0:
                # Make Chrome artifact output dir
                edge_output_path = configuration.root_tmp_path + os.sep + configuration.case_id + os.sep + \
                                   configuration.evidence_id + os.sep + par_id + os.sep + "web" + os.sep \
                                   + "chromium_edge" + os.sep

                # Match between os user chrome profile
                os_user_edge_profile = []

                for f in full_path:
                    for user in user_list:
                        if f.find(user) != -1:
                            f = f.replace(query_sep, os.sep)
                            profile_index = f.rfind(os.sep)
                            os_user_edge_profile.append([user, f[profile_index + 1:]])

                # Create profile dir in output dir
                if not os.path.isdir(edge_output_path):
                    for make_dir_tree in os_user_edge_profile:
                        os.makedirs(edge_output_path + make_dir_tree[0] + os.sep + make_dir_tree[1] + os.sep)

                # Extract chrome artifact file
                chromium_artifact_file_list = ['Preferences', 'History', 'Login Data', 'Shortcuts', 'Top Sites', 'Web Data',
                                               'Favicons', 'Cookies', 'Bookmarks']

                for make_dir_tree in os_user_edge_profile:
                    for file in chromium_artifact_file_list:
                        file_path = f'{query_sep}Users{query_sep}{make_dir_tree[0]}{query_sep}AppData{query_sep}Local' \
                                    f'{query_sep}Microsoft{query_sep}Edge{query_sep}User Data{query_sep}' \
                                    f'{make_dir_tree[1]}{query_sep}{file}'
                        self.ExtractTargetFileToPath(
                            source_path_spec=source_path_spec,
                            configuration=configuration,
                            file_path=file_path,
                            output_path=edge_output_path + make_dir_tree[0] + os.sep + make_dir_tree[1] + os.sep)

                # print("[Web] Chromium Edge artifact files extraction success")

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
                        edge_search_result.append(chromium_edge.edge_search_terms(tmp_file_path))  # fp 대신 dict 자료형으로??
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

                # Delete chromium edge output dir
                shutil.rmtree(edge_output_path)

                info = [par_id, configuration.case_id, configuration.evidence_id]

                # Edge Search Terms
                result = []
                for search_terms, profile_match in zip(edge_search_result, os_user_edge_profile):
                    source = get_source_path(profile_match, 'History', 'Edge')
                    for row in search_terms:
                        row[2] = configuration.apply_time_zone(row[2], knowledge_base.time_zone)  # searched_time
                        row = info + row + profile_match + [source]
                        result.append(row)
                query = f"Insert into lv1_app_web_chromium_edge_search_terms values (%s, %s, %s, %s, %s, %s, %s, %s, %s, " \
                        f"%s);"
                configuration.cursor.bulk_execute(query, result)

                # Edge Visit Urls
                result = []
                for visit_urls, profile_match in zip(edge_visit_urls_result, os_user_edge_profile):
                    source = get_source_path(profile_match, 'History', 'Edge')
                    for row in visit_urls:
                        row[1] = configuration.apply_time_zone(row[1], knowledge_base.time_zone)  # last_visited_time
                        row = info + row + profile_match + [source]
                        result.append(row)
                query = f"Insert into lv1_app_web_chromium_edge_visit_urls values (%s, %s, %s, %s, %s, %s, %s, %s, %s, " \
                        f"%s, %s);"
                configuration.cursor.bulk_execute(query, result)

                # Edge Visit History
                result = []
                for visit_history, profile_match in zip(edge_visit_history, os_user_edge_profile):
                    source = get_source_path(profile_match, 'History', 'Edge')
                    for row in visit_history:
                        row[4] = configuration.apply_time_zone(row[4], knowledge_base.time_zone)  # visit_time
                        row = info + row + profile_match + [source]
                        result.append(row)
                query = f"Insert into lv1_app_web_chromium_edge_visit_history values (%s, %s, %s, %s, %s, %s, %s, %s, " \
                        f"%s, %s, %s, %s, %s, %s);"
                configuration.cursor.bulk_execute(query, result)

                # Edge Download
                result = []
                for download_files, profile_match in zip(edge_download_result, os_user_edge_profile):
                    source = get_source_path(profile_match, 'History', 'Edge')
                    for row in download_files:
                        row[7] = configuration.apply_time_zone(row[7], knowledge_base.time_zone)  # start_time
                        row[8] = configuration.apply_time_zone(row[8], knowledge_base.time_zone)  # end_time
                        row[9] = configuration.apply_time_zone(row[9], knowledge_base.time_zone)  # file_last_access_time
                        row[10] = configuration.apply_time_zone(row[10],
                                                                knowledge_base.time_zone)  # file_last_modified_time
                        row = info + row + profile_match + [source]
                        result.append(row)
                query = f"Insert into lv1_app_web_chromium_edge_download values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, " \
                        f"%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"
                configuration.cursor.bulk_execute(query, result)

                # Edge Top Sites
                result = []
                for top_sites, profile_match in zip(edge_top_sites, os_user_edge_profile):
                    source = get_source_path(profile_match, 'Top Sites', 'Edge')
                    for row in top_sites:
                        row = info + row + profile_match + [source]
                        result.append(row)
                query = f"Insert into lv1_app_web_chromium_edge_top_sites values (%s, %s, %s, %s, %s, %s, %s, %s, %s);"
                configuration.cursor.bulk_execute(query, result)

                # Edge Shortcuts
                for shortcuts, profile_match in zip(edge_shortcuts, os_user_edge_profile):
                    source = get_source_path(profile_match, 'Shortcuts', 'Edge')
                    for row in shortcuts:
                        row[6] = configuration.apply_time_zone(row[6], knowledge_base.time_zone)  # last_access_time
                        row = info + row + profile_match + [source]
                        query = f"Insert into lv1_app_web_chromium_edge_shortcuts values ('%s', '%s', '%s', '%s', '%s', " \
                                f"'%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s');" % tuple(row)
                        configuration.cursor.execute_query(query)

                # Edge Favicons
                for favicons, profile_match in zip(edge_favicons, os_user_edge_profile):
                    source = get_source_path(profile_match, 'Favicons', 'Edge')
                    for row in favicons:
                        row[3] = configuration.apply_time_zone(row[3], knowledge_base.time_zone)  # last_updated
                        row[4] = configuration.apply_time_zone(row[4], knowledge_base.time_zone)  # last_requested
                        row = info + row + profile_match + [source]
                        query = f"Insert into lv1_app_web_chromium_edge_favicons values ('%s', '%s', '%s', '%s', '%s', " \
                                f"'%s', '%s', '%s', " % tuple(row[0:8]) \
                                + "(UNHEX(\'" + row[8].hex() + "\')), '%s', '%s', '%s', '%s', '%s');" % tuple(row[9:])
                        configuration.cursor.execute_query(query)

                # Edge Cookies
                for cookies, profile_match in zip(edge_cookies, os_user_edge_profile):
                    source = get_source_path(profile_match, 'Cookies', 'Edge')
                    for row in cookies:
                        row[0] = configuration.apply_time_zone(row[0], knowledge_base.time_zone)  # creation_utc
                        row[4] = configuration.apply_time_zone(row[4], knowledge_base.time_zone)  # expires_utc
                        row[7] = configuration.apply_time_zone(row[7], knowledge_base.time_zone)  # last_access_utc
                        row = info + row + profile_match + [source]
                        query = f"Insert into lv1_app_web_chromium_edge_cookies values ('%s', '%s', '%s', '%s', '%s', " \
                                f"'%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', " % tuple(row[0:14]) + \
                                "(UNHEX(\'" + row[14].hex() + "\'))" \
                                                              ", '%s', '%s', '%s', '%s');" % tuple(row[15:])
                        configuration.cursor.execute_query(query)

                # for autofill, profile_match in zip(edge_autofill, os_user_edge_profile):
                #     for row in autofill:
                #         table_name = 'lv1_app_web_chromium_edge_autofill'
                #         row = info + list(row) + profile_match

                #         # query = f"Insert into {table_name} values ('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s');" % tuple(row)

                #         query = f"Insert into {table_name} values ('%s', '%s', '%s', '%s', " % tuple(row[0:4]) + \
                #                 "(UNHEX(\'" + row[4].hex() + "\'))" + ", " + "(UNHEX(\'" + row[5].hex() + "\'))" \
                #                                                                                           ", '%s', '%s', '%s', '%s', '%s');" % tuple(
                #             row[6:])

                #         # print(query)
                #         configuration.cursor.execute_query(query)

                # Edge Login Data
                for logindata, profile_match in zip(edge_logindata, os_user_edge_profile):
                    source = get_source_path(profile_match, 'Login Data', 'Edge')
                    for row in logindata:
                        row[7] = configuration.apply_time_zone(row[7], knowledge_base.time_zone)  # date_created
                        row[13] = configuration.apply_time_zone(row[13], knowledge_base.time_zone)  # date_synced
                        row[22] = configuration.apply_time_zone(row[22], knowledge_base.time_zone)  # date_last_used
                        row = info + row + profile_match + [source]

                        query = f"Insert into lv1_app_web_chromium_edge_logindata values ('%s', '%s', '%s', '%s', '%s', " \
                                f"'%s', '%s', '%s', " % tuple(row[0:8]) + \
                                "(UNHEX(\'" + row[8].hex() + "\'))" \
                                                             ", '%s', '%s', " % tuple(row[9:11]) + \
                                "(UNHEX(\'" + row[11].hex() + "\'))" \
                                                              ", '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', " \
                                                              "'%s', " % tuple(row[12:22]) + \
                                "(UNHEX(\'" + row[22].hex() + "\'))" \
                                                              ", '%s', '%s', '%s', '%s', '%s', '%s');" % tuple(row[23:])

                        configuration.cursor.execute_query(query)

                # Edge Bookmark
                result = []
                for bookmark, profile_match in zip(edge_bookmarks, os_user_edge_profile):
                    source = get_source_path(profile_match, 'Bookmarks', 'Edge')
                    for row in bookmark:
                        row[0] = configuration.apply_time_zone(row[0], knowledge_base.time_zone)  # date_added
                        row = info + row + profile_match + [source]
                        result.append(row)
                query = f"Insert into lv1_app_web_chromium_edge_bookmarks values (%s, %s, %s, %s, %s, %s, %s, %s, %s, " \
                        f"%s, %s, %s, %s, %s);"
                configuration.cursor.bulk_execute(query, result)

                # print("[Web] " + "\033[32m" + "Chromium Edge Analysis Complete" + "\033[0m")
        else:
            pass
            # print("[Web] " + "\033[31m" + "No Chromium Edge artifact" + "\033[0m" + " in par_id %s." % (par_id))

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

            # Create profile dir in output dir
            if not os.path.isdir(opera_output_path):
                for make_dir_tree in os_user_opera_profile:
                    os.makedirs(opera_output_path + make_dir_tree[0] + os.sep + make_dir_tree[1] + os.sep)

            opera_artifact_file_list = ['Bookmarks', 'Cookies', 'Favicons', 'History', 'Login Data', 'Preferences',
                                        'Shortcuts', 'Web Data']

            for make_dir_tree in os_user_opera_profile:
                for file in opera_artifact_file_list:
                    file_path = f'{query_sep}Users{query_sep}{make_dir_tree[0]}{query_sep}AppData{query_sep}Roaming' \
                                f'{query_sep}Opera Software{query_sep}Opera Stable{query_sep}{make_dir_tree[1]}' \
                                f'{query_sep}{file}'
                    self.ExtractTargetFileToPath(
                        source_path_spec=source_path_spec,
                        configuration=configuration,
                        file_path=file_path,
                        output_path=opera_output_path + make_dir_tree[0] + os.sep + make_dir_tree[1] + os.sep)

            # print("[Web] Opera artifact files extraction success")

            opera_search_result = []
            opera_visit_urls_result = []
            opera_download_result = []
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
                    opera_search_result.append(opera.opera_search_terms(tmp_file_path))
                    opera_visit_urls_result.append(opera.opera_visit_urls(tmp_file_path))
                    opera_download_result.append(opera.opera_download(tmp_file_path))
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

                if 'Web Data' in files:  # autofill
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
            # Opera Search Terms
            result = []
            for search_terms, profile_match in zip(opera_search_result, os_user_opera_profile):
                source = get_source_path(profile_match, 'History', 'Opera')
                for row in search_terms:
                    row[2] = configuration.apply_time_zone(row[2], knowledge_base.time_zone)  # searched_time
                    row = info + row + profile_match + [source]
                    result.append(row)
            query = f"Insert into lv1_app_web_opera_search_terms values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"
            configuration.cursor.bulk_execute(query, result)

            # Opera Visit Urls
            result = []
            for visit_urls, profile_match in zip(opera_visit_urls_result, os_user_opera_profile):
                source = get_source_path(profile_match, 'History', 'Opera')
                for row in visit_urls:
                    row[10] = configuration.apply_time_zone(row[10], knowledge_base.time_zone)  # last_visited_time
                    row = info + row + profile_match + [source]
                    result.append(row)
            query = f"Insert into lv1_app_web_opera_visit_urls values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, " \
                    f"%s, %s, %s, %s, %s, %s, %s);"
            configuration.cursor.bulk_execute(query, result)

            # Opera Visit History
            result = []
            for visit_history, profile_match in zip(opera_visit_history, os_user_opera_profile):
                source = get_source_path(profile_match, 'History', 'Opera')
                for row in visit_history:
                    row[4] = configuration.apply_time_zone(row[4], knowledge_base.time_zone)  # visit_time
                    row = info + row + profile_match + [source]
                    result.append(row)
            query = f"Insert into lv1_app_web_opera_visit_history values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, " \
                    f"%s, %s, %s, %s);"
            configuration.cursor.bulk_execute(query, result)

            # Opera Download
            result = []
            for download_files, profile_match in zip(opera_download_result, os_user_opera_profile):
                source = get_source_path(profile_match, 'History', 'Opera')
                for row in download_files:
                    row[7] = configuration.apply_time_zone(row[7], knowledge_base.time_zone)  # start_time
                    row[8] = configuration.apply_time_zone(row[8], knowledge_base.time_zone)  # end_time
                    row[9] = configuration.apply_time_zone(row[9], knowledge_base.time_zone)  # file_last_access_time
                    row[10] = configuration.apply_time_zone(row[10],
                                                            knowledge_base.time_zone)  # file_last_modified_time
                    row = info + row + profile_match + [source]
                    result.append(row)
            query = f"Insert into lv1_app_web_opera_download values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, " \
                    f"%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"
            configuration.cursor.bulk_execute(query, result)

            # Opera Shortcuts
            result = []
            for shortcuts, profile_match in zip(opera_shortcuts, os_user_opera_profile):
                source = get_source_path(profile_match, 'Shortcuts', 'Opera')
                for row in shortcuts:
                    row[6] = configuration.apply_time_zone(row[6], knowledge_base.time_zone)  # last_access_time
                    row = info + row + profile_match + [source]
                    result.append(row)
            query = f"Insert into lv1_app_web_opera_shortcuts values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, " \
                    f"%s, %s, %s);"
            configuration.cursor.bulk_execute(query, result)

            # Opera Favicons
            for favicons, profile_match in zip(opera_favicons, os_user_opera_profile):
                source = get_source_path(profile_match, 'Favicons', 'Opera')
                for row in favicons:
                    row[3] = configuration.apply_time_zone(row[3], knowledge_base.time_zone)  # last_updated
                    row[4] = configuration.apply_time_zone(row[4], knowledge_base.time_zone)  # last_requested
                    row = info + row + profile_match + [source]
                    query = f"Insert into lv1_app_web_opera_favicons values ('%s', '%s', '%s', '%s', '%s', '%s', " \
                            f"'%s', '%s', " % tuple(row[0:8]) + \
                            "(UNHEX(\'" + row[8].hex() + "\'))" \
                                                         ", '%s', '%s', '%s', '%s', '%s');" % tuple(row[9:])
                    configuration.cursor.execute_query(query)

            # Opera Cookies
            for cookies, profile_match in zip(opera_cookies, os_user_opera_profile):
                source = get_source_path(profile_match, 'Cookies', 'Opera')
                for row in cookies:
                    row[0] = configuration.apply_time_zone(row[0], knowledge_base.time_zone)  # creation_utc
                    row[4] = configuration.apply_time_zone(row[4], knowledge_base.time_zone)  # expires_utc
                    row[7] = configuration.apply_time_zone(row[7], knowledge_base.time_zone)  # last_access_utc
                    row = info + row + profile_match + [source]
                    query = f"Insert into lv1_app_web_opera_cookies values ('%s', '%s', '%s', '%s', '%s', '%s', " \
                            f"'%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', " % tuple(row[0:14]) + \
                            "(UNHEX(\'" + row[14].hex() + "\'))" \
                                                          ", '%s', '%s', '%s', '%s');" % tuple(row[15:])
                    configuration.cursor.execute_query(query)

            # Opera Autofill
            result = []
            for autofill, profile_match in zip(opera_autofill, os_user_opera_profile):
                source = get_source_path(profile_match, 'Web Data', 'Opera')
                for row in autofill:
                    row[3] = configuration.apply_time_zone(row[3], knowledge_base.time_zone)  # date_created
                    row[4] = configuration.apply_time_zone(row[4], knowledge_base.time_zone)  # date_last_used
                    row = info + row + profile_match + [source]
                    result.append(row)
            query = f"Insert into lv1_app_web_opera_autofill values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"
            configuration.cursor.bulk_execute(query, result)

            # Opera Login Data
            for logindata, profile_match in zip(opera_logindata, os_user_opera_profile):
                source = get_source_path(profile_match, 'Login Data', 'Opera')
                for row in logindata:
                    row[7] = configuration.apply_time_zone(row[7], knowledge_base.time_zone)  # date_created
                    row[13] = configuration.apply_time_zone(row[13], knowledge_base.time_zone)  # date_synced
                    row[22] = configuration.apply_time_zone(row[22], knowledge_base.time_zone)  # date_last_used
                    row = info + row + profile_match + [source]
                    query = f"Insert into lv1_app_web_opera_logindata values ('%s', '%s', '%s', '%s', '%s', '%s', " \
                            f"'%s', '%s', " % tuple(row[0:8]) + \
                            "(UNHEX(\'" + row[8].hex() + "\'))" \
                                                         ", '%s', '%s', " % tuple(row[9:11]) + \
                            "(UNHEX(\'" + row[11].hex() + "\'))" \
                                                          ", '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', " \
                                                          "'%s', '%s', " % tuple(row[12:22]) + \
                            "(UNHEX(\'" + row[22].hex() + "\'))" \
                                                          ", '%s', '%s', '%s', '%s', '%s', '%s');" % tuple(row[23:])
                    configuration.cursor.execute_query(query)

            # Opera Bookmark
            result = []
            for bookmark, profile_match in zip(opera_bookmarks, os_user_opera_profile):
                source = get_source_path(profile_match, 'Bookmarks', 'Opera')
                for row in bookmark:
                    row[0] = configuration.apply_time_zone(row[0], knowledge_base.time_zone)  # date_added
                    row = info + row + profile_match + [source]
                    result.append(row)
            query = f"Insert into lv1_app_web_opera_bookmarks values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, " \
                    f"%s, %s);"
            configuration.cursor.bulk_execute(query, result)

            # print("[Web] " + "\033[32m" + "Opera Analysis Complete" + "\033[0m")

        else:
            pass
            # print("[Web] " + "\033[31m" + "No Opera artifact" + "\033[0m" + " in par_id %s." % par_id)


        ################ Firefox ###################
        if len(firefox_artifact) != 0:

            full_path = []
            for i in range(len(firefox_artifact)):

                if '.default-release' in firefox_artifact[i][0]:
                    full_path.append(firefox_artifact[i][1] + os.sep + firefox_artifact[i][0])

            if len(full_path) != 0 :
                # Make Chrome artifact output dir
                firefox_output_path = configuration.root_tmp_path + os.sep + configuration.case_id + os.sep + \
                                      configuration.evidence_id + os.sep + par_id + os.sep + "web" + os.sep + \
                                      "firefox" + os.sep

                # Match between os user chrome profile
                os_user_firefox_profile = []

                for f in full_path:
                    for user in user_list:
                        if f.find(user) != -1:
                            f = f.replace(query_sep, os.sep)
                            profile_start_index = f.rfind(os.sep) + 1
                            profile_end_index = f.rfind('default-release') - 1
                            os_user_firefox_profile.append([user, f[profile_start_index:profile_end_index]])

                # Create profile dir in output dir
                if not os.path.isdir(firefox_output_path):
                    for make_dir_tree in os_user_firefox_profile:
                        os.makedirs(firefox_output_path + make_dir_tree[0] + os.sep + make_dir_tree[1] + os.sep)

                # Extract chrome artifact file
                firefox_artifact_file_list = ['places.sqlite', 'content-prefs.sqlite', 'cookies.sqlite', 'favicons.sqlite',
                                              'formhistory.sqlite', 'permissions.sqlite', 'prefs.js']

                for make_dir_tree in os_user_firefox_profile:
                    for file in firefox_artifact_file_list:
                        file_path = f'{query_sep}Users{query_sep}{make_dir_tree[0]}{query_sep}AppData{query_sep}Roaming' \
                                    f'{query_sep}Mozilla{query_sep}Firefox{query_sep}Profiles{query_sep}' \
                                    f'{make_dir_tree[1]}{query_sep}{file}'
                        self.ExtractTargetFileToPath(
                            source_path_spec=source_path_spec,
                            configuration=configuration,
                            file_path=file_path,
                            output_path=firefox_output_path + make_dir_tree[0] + os.sep + make_dir_tree[1] + os.sep)

                # print("[Web] Firefox artifact files extraction success")

                firefox_visit_history = []
                firefox_visit_urls_result = []
                firefox_domains = []
                firefox_download_result = []
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
                        tmp_file_path = firefox_output_path + file_check[0] + os.sep + file_check[
                            1] + os.sep + 'places.sqlite'
                        firefox_visit_history.append(firefox.firefox_visit_history(tmp_file_path))
                        firefox_visit_urls_result.append(firefox.firefox_visit_urls(tmp_file_path))
                        firefox_domains.append(firefox.firefox_domain(tmp_file_path))
                        firefox_download_result.append(firefox.firefox_downloads(tmp_file_path))
                        firefox_bookmarks.append(firefox.firefox_bookmarks(tmp_file_path))

                    if 'cookies.sqlite' in files:
                        tmp_file_path = firefox_output_path + file_check[0] + os.sep + file_check[
                            1] + os.sep + 'cookies.sqlite'
                        firefox_cookies.append(firefox.firefox_cookies(tmp_file_path))

                    if 'permissions.sqlite' in files:
                        tmp_file_path = firefox_output_path + file_check[0] + os.sep + file_check[
                            1] + os.sep + 'permissions.sqlite'
                        firefox_permissions.append(firefox.firefox_perms(tmp_file_path))

                    if 'formhistory.sqlite' in files:
                        tmp_file_path = firefox_output_path + file_check[0] + os.sep + file_check[
                            1] + os.sep + 'formhistory.sqlite'
                        firefox_formhistory.append(firefox.firefox_forms(tmp_file_path))

                    if 'favicons.sqlite' in files:
                        tmp_file_path = firefox_output_path + file_check[0] + os.sep + file_check[
                            1] + os.sep + 'favicons.sqlite'
                        firefox_favicons.append(firefox.firefox_favicons(tmp_file_path))

                    if 'content-prefs.sqlite' in files:
                        tmp_file_path = firefox_output_path + file_check[0] + os.sep + file_check[
                            1] + os.sep + 'content-prefs.sqlite'
                        firefox_content_prefs.append(firefox.firefox_prefs(tmp_file_path))

                # delete chrome output dir
                shutil.rmtree(firefox_output_path)

                info = [par_id, configuration.case_id, configuration.evidence_id]

                # Firefox Visit History
                result = []
                for visit_history, profile_match in zip(firefox_visit_history, os_user_firefox_profile):
                    source = get_source_path(profile_match, 'places.sqlite', 'Firefox')
                    for row in visit_history:
                        row[4] = configuration.apply_time_zone(row[4], knowledge_base.time_zone)  # visit_date
                        row = info + row + profile_match + [source]
                        result.append(row)
                query = f"Insert into lv1_app_web_firefox_visit_history values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, " \
                        f"%s, %s);"
                configuration.cursor.bulk_execute(query, result)

                # Firefox Visit Urls
                result = []
                for visit_urls, profile_match in zip(firefox_visit_urls_result, os_user_firefox_profile):
                    source = get_source_path(profile_match, 'places.sqlite', 'Firefox')
                    for row in visit_urls:
                        row[7] = configuration.apply_time_zone(row[7], knowledge_base.time_zone)  # last_visited_date
                        row = info + row + profile_match + [source]
                        result.append(row)
                query = f"Insert into lv1_app_web_firefox_visit_urls values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, " \
                        f"%s, %s, %s, %s, %s, %s, %s);"
                configuration.cursor.bulk_execute(query, result)

                # Firefox Domains
                result = []
                for domain, profile_match in zip(firefox_domains, os_user_firefox_profile):
                    source = get_source_path(profile_match, 'places.sqlite', 'Firefox')
                    for row in domain:
                        row = info + row + profile_match + [source]
                        result.append(row)
                query = f"Insert into lv1_app_web_firefox_domain values (%s, %s, %s, %s, %s, %s, %s, %s, %s);"
                configuration.cursor.bulk_execute(query, result)

                # Firefox Downloads
                result = []
                for download_files, profile_match in zip(firefox_download_result, os_user_firefox_profile):
                    source = get_source_path(profile_match, 'places.sqlite', 'Firefox')
                    for row in download_files:
                        row[4] = configuration.apply_time_zone(row[4], knowledge_base.time_zone)  # start_time
                        row[5] = configuration.apply_time_zone(row[5], knowledge_base.time_zone)  # end_time
                        row = info + row + profile_match + [source]
                        result.append(row)
                query = f"Insert into lv1_app_web_firefox_download values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, " \
                        f"%s, %s, %s);"
                configuration.cursor.bulk_execute(query, result)

                # Firefox Cookies
                result = []
                for cookies, profile_match in zip(firefox_cookies, os_user_firefox_profile):
                    source = get_source_path(profile_match, 'cookies.sqlite', 'Firefox')
                    for row in cookies:
                        row[4] = configuration.apply_time_zone(row[4], knowledge_base.time_zone)  # expire_time
                        row[5] = configuration.apply_time_zone(row[5], knowledge_base.time_zone)  # last_accessed_time
                        row[6] = configuration.apply_time_zone(row[6], knowledge_base.time_zone)  # created_time
                        row = info + row + profile_match + [source]
                        result.append(row)
                query = f"Insert into lv1_app_web_firefox_cookies values (%s, %s, %s, %s, %s, %s, %s, %s, %s, " \
                        f"%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"
                configuration.cursor.bulk_execute(query, result)

                # Firefox Permission
                result = []
                for permissions, profile_match in zip(firefox_permissions, os_user_firefox_profile):
                    source = get_source_path(profile_match, 'permissions.sqlite', 'Firefox')
                    for row in permissions:
                        row[4] = configuration.apply_time_zone(row[4], knowledge_base.time_zone)  # expire_time
                        row[5] = configuration.apply_time_zone(row[5], knowledge_base.time_zone)  # modified_time
                        row = info + row + profile_match + [source]
                        result.append(row)
                query = f"Insert into lv1_app_web_firefox_permissions values (%s, %s, %s, %s, %s, %s, %s, %s, %s, " \
                        f"%s, %s, %s);"
                configuration.cursor.bulk_execute(query, result)

                # Firefox Form History
                result = []
                for forms, profile_match in zip(firefox_formhistory, os_user_firefox_profile):
                    source = get_source_path(profile_match, 'formhistory.sqlite', 'Firefox')
                    for row in forms:
                        row[3] = configuration.apply_time_zone(row[3], knowledge_base.time_zone)  # first_used_time
                        row[4] = configuration.apply_time_zone(row[4], knowledge_base.time_zone)  # last_used_time
                        row = info + row + profile_match + [source]
                        result.append(row)
                query = f"Insert into lv1_app_web_firefox_formhistory values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, " \
                        f"%s, %s);"
                configuration.cursor.bulk_execute(query, result)

                # Firefox Favicons
                for favicons, profile_match in zip(firefox_favicons, os_user_firefox_profile):
                    source = get_source_path(profile_match, 'favicons.sqlite', 'Firefox')
                    for row in favicons:
                        row[6] = configuration.apply_time_zone(row[6], knowledge_base.time_zone)  # expired_time
                        row = info + row + profile_match + [source]
                        query = f"Insert into lv1_app_web_firefox_favicons values ('%s', '%s', '%s', '%s', '%s', '%s', " \
                                f"'%s', '%s', '%s', '%s', " % tuple(row[0:10]) + \
                                "(UNHEX(\'" + row[10].hex() + "\'))" \
                                                              ", '%s', '%s', '%s', '%s');" % tuple(row[11:])
                        configuration.cursor.execute_query(query)

                # Firefox Content Prefs
                result = []
                for prefs, profile_match in zip(firefox_content_prefs, os_user_firefox_profile):
                    source = get_source_path(profile_match, 'content-prefs.sqlite', 'Firefox')
                    for row in prefs:
                        row[3] = configuration.apply_time_zone(row[3], knowledge_base.time_zone)    # time
                        row = info + row + profile_match + [source]
                        result.append(row)
                query = f"Insert into lv1_app_web_firefox_content_prefs values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"
                configuration.cursor.bulk_execute(query, result)

                # Firefox Bookmarks
                result = []
                for bookmarks, profile_match in zip(firefox_bookmarks, os_user_firefox_profile):
                    source = get_source_path(profile_match, 'places.sqlite', 'Firefox')
                    for row in bookmarks:
                        row[4] = configuration.apply_time_zone(row[4], knowledge_base.time_zone)  # added_time
                        row[5] = configuration.apply_time_zone(row[5], knowledge_base.time_zone)  # last_modified_time
                        row = info + row + profile_match + [source]
                        result.append(row)
                query = f"Insert into lv1_app_web_firefox_bookmarks values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, " \
                        f"%s, %s, %s);"
                configuration.cursor.bulk_execute(query, result)

                # print("[Web] " + "\033[32m" + "Firefox Analysis Complete" + "\033[0m")
        else:
            pass
            # print("[Web] " + "\033[31m" + "No Firefox artifact" + "\033[0m" + " in par_id %s." % par_id)


def get_source_path(profile, file_name, browser):
    path = f'/Users/{profile[0]}/AppData'
    if browser == 'Chrome':
        path += f'/Local/Google/Chrome/User Data'
    elif browser == 'Whale':
        path += f'/Local/Naver/Naver Whale/User Data'
    elif browser == 'Edge':
        path += f'/Local/Microsoft/Edge/User Data'
    elif browser == 'Opera':
        path += f'/Roaming/Opera Software/Opera Stable'
    elif browser == 'Firefox':
        path += f'/Roaming/Mozilla/Firefox/Profiles'
    path += f'/{profile[1]}/{file_name}'
    return path


manager.ModulesManager.RegisterModule(ChromiumConnector)
