# -*- coding: utf-8 -*-
"""module for google takeout."""
import os

from modules import logger
from modules import manager
from modules import interface
from modules.Google_Takeout import gtForensics
import pdb


class GoogleTakeoutConnector(interface.ModuleConnector):
    NAME = 'google_takeout_connector'
    DESCRIPTION = 'Google Takeout Connector'
    TABLE_NAME = 'lv1_google_takeout'

    _plugin_classes = {}

    def __init__(self):
        super(GoogleTakeoutConnector, self).__init__()

    def Connect(self, par_id, configuration, source_path_spec, knowledge_base):
        this_file_path = os.path.dirname(
            os.path.abspath(__file__)) + os.sep + 'schema' + os.sep + 'google_takeout' + os.sep

        yaml_list = [this_file_path + 'lv1_google_takeout_contacts.yaml',
                     this_file_path + 'lv1_google_takeout_drive.yaml',
                     this_file_path + 'lv1_google_takeout_my_activity_android.yaml',
                     this_file_path + 'lv1_google_takeout_my_activity_assistant.yaml',
                     this_file_path + 'lv1_google_takeout_my_activity_chrome.yaml',
                     this_file_path + 'lv1_google_takeout_my_activity_gmail.yaml',
                     this_file_path + 'lv1_google_takeout_my_activity_google_analytics.yaml',
                     this_file_path + 'lv1_google_takeout_my_activity_map.yaml',
                     this_file_path + 'lv1_google_takeout_my_activity_video_search.yaml',
                     this_file_path + 'lv1_google_takeout_my_activity_voice_audio.yaml',
                     this_file_path + 'lv1_google_takeout_my_activity_youtube.yaml']

        table_list = ['lv1_google_takeout_contacts',
                      'lv1_google_takeout_drive',
                      'lv1_google_takeout_my_activity_android',
                      'lv1_google_takeout_my_activity_assistant',
                      'lv1_google_takeout_my_activity_chrome',
                      'lv1_google_takeout_my_activity_gmail',
                      'lv1_google_takeout_my_activity_google_analytics',
                      'lv1_google_takeout_my_activity_map',
                      'lv1_google_takeout_my_activity_video_search',
                      'lv1_google_takeout_my_activity_voice_audio',
                      'lv1_google_takeout_my_activity_youtube']

        if not self.check_table_from_yaml(configuration, yaml_list, table_list):
            return False

        query = f"SELECT name, parent_path FROM file_info WHERE par_id like '{par_id}' and dir_type = 3 and " \
                f"name like 'takeout-%T%Z-00%';"

        google_takeout_dirs = configuration.cursor.execute_query_mul(query)

        if len(google_takeout_dirs) == 0:
            # print("There are no google-takeout directories")
            return False

        output_path = (
                configuration.root_tmp_path
                + os.sep
                + configuration.case_id
                + os.sep
                + configuration.evidence_id
                + os.sep
                + par_id
        )
        if not os.path.exists(output_path):
            os.mkdir(output_path)

        for google_takeout_dir in google_takeout_dirs:
            self.ExtractTargetDirToPath(source_path_spec=source_path_spec,
                                        configuration=configuration,
                                        dir_path=google_takeout_dir[0],
                                        output_path=output_path)
            src_path = os.path.join(google_takeout_dir[1], google_takeout_dir[0])
            parse_return = gtForensics.parse_google_takeout(os.path.join(output_path, google_takeout_dir[0]))

            # Contacts
            contacts = parse_return['Contacts']
            if contacts:
                query = f"INSERT INTO lv1_google_takeout_contacts values ('{par_id}', '{configuration.case_id}', " \
                        f"'{configuration.evidence_id}', '{src_path}', %s, %s, %s, %s, %s, %s)"
                configuration.cursor.bulk_execute(query, contacts)

            # Drive
            drive = parse_return['Drive']
            if drive:
                query = f"INSERT INTO lv1_google_takeout_drive values ('{par_id}', '{configuration.case_id}', " \
                        f"'{configuration.evidence_id}', '{src_path}', %s, %s, %s, %s, %s, %s)"
                configuration.cursor.bulk_execute(query, drive)

            # My Activity Android
            my_android = parse_return['myAndroid']
            if my_android:
                query = f"INSERT INTO lv1_google_takeout_my_activity_android values ('{par_id}', " \
                        f"'{configuration.case_id}', '{configuration.evidence_id}', '{src_path}', %s, %s, %s, " \
                        f"%s, %s, %s, %s)"
                configuration.cursor.bulk_execute(query, my_android)

            # My Activity Assistant
            my_assistant = parse_return['myAssistant']
            if my_assistant:
                query = f"INSERT INTO lv1_google_takeout_my_activity_assistant values ('{par_id}', " \
                        f"'{configuration.case_id}', '{configuration.evidence_id}', '{src_path}', %s, %s, %s, %s, " \
                        f"%s, %s," \
                        f"%s, %s, %s, %s, %s, %s, %s, %s)"
                configuration.cursor.bulk_execute(query, my_assistant)

            # My Activity Gmail
            my_gmail = parse_return['myGmail']
            if my_gmail:
                query = f"INSERT INTO lv1_google_takeout_my_activity_gmail values ('{par_id}', " \
                        f"'{configuration.case_id}', '{configuration.evidence_id}', '{src_path}', %s, %s, %s, %s, " \
                        f"%s)"
                configuration.cursor.bulk_execute(query, my_gmail)

            # My Activity Chrome
            my_chrome = parse_return['myChrome']
            if my_chrome:
                query = f"INSERT INTO lv1_google_takeout_my_activity_chrome values ('{par_id}', " \
                        f"'{configuration.case_id}', '{configuration.evidence_id}', '{src_path}', %s, %s, %s, %s, " \
                        f"%s, %s)"
                configuration.cursor.bulk_execute(query, my_chrome)

            # My Activity Google Analytics
            my_google_analytics = parse_return['myGoogleAnalytics']
            if my_google_analytics:
                query = f"INSERT INTO lv1_google_takeout_my_activity_google_analytics values ('{par_id}', " \
                        f"'{configuration.case_id}', '{configuration.evidence_id}', '{src_path}', %s, %s, %s, %s, " \
                        f"%s, %s)"
                configuration.cursor.bulk_execute(query, my_google_analytics)

            # My Activity Maps
            my_map = parse_return['myMap']
            if my_map:
                query = f"INSERT INTO lv1_google_takeout_my_activity_map values ('{par_id}', " \
                        f"'{configuration.case_id}', '{configuration.evidence_id}', '{src_path}', %s, %s, %s, %s, " \
                        f"%s, %s, %s, %s, %s, %s, %s)"
                configuration.cursor.bulk_execute(query, my_map)

            # My Activity Video Search
            my_video_search = parse_return['myVideoSearch']
            if my_video_search:
                query = f"INSERT INTO lv1_google_takeout_my_activity_video_search values ('{par_id}', " \
                        f"'{configuration.case_id}', '{configuration.evidence_id}', '{src_path}', %s, %s, %s, %s, " \
                        f"%s, %s)"
                configuration.cursor.bulk_execute(query, my_video_search)

            # My Activity Voice and Audio
            my_voice_audio = parse_return['myVoiceAudio']
            if my_voice_audio:
                query = f"INSERT INTO lv1_google_takeout_my_activity_voice_audio values ('{par_id}', " \
                        f"'{configuration.case_id}', '{configuration.evidence_id}', '{src_path}', %s, %s, %s, " \
                        f"%s, %s, %s, %s)"
                configuration.cursor.bulk_execute(query, my_voice_audio)

            # My Activity YouTube
            my_youtube = parse_return['myYouTube']
            if my_youtube:
                query = f"INSERT INTO lv1_google_takeout_my_activity_youtube values ('{par_id}', " \
                        f"'{configuration.case_id}', '{configuration.evidence_id}', '{src_path}', %s, %s, %s, " \
                        f"%s, %s, %s, %s)"
                configuration.cursor.bulk_execute(query, my_youtube)


manager.ModulesManager.RegisterModule(GoogleTakeoutConnector)
