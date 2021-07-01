# -*- coding: utf-8 -*-
"""module for android basic apps."""

import os

from modules import logger
from modules import manager
from modules import interface
from utility import errors

from modules.Android_app import lv1_os_and_app_email_android as ea

#지훈

class AndroidEmailConnector(interface.ModuleConnector):
    NAME = 'android_email_connector'
    DESCRIPTION = 'Module for Android Email'

    def __init__(self):
        super(AndroidEmailConnector, self).__init__()

    def Connect(self, par_id, configuration, source_path_spec, knowledge_base):
        """Connector to connect to Android Basic Apps modules.

        Args:
            par_id: partition id.
            configuration: configuration values.
            source_path_spec (dfvfs.PathSpec): path specification of the source file.
            knowledge_base (KnowledgeBase): knowledge base.

        """

        # Check Filesystem
        query = f"SELECT filesystem FROM partition_info WHERE par_id like '{par_id}'"
        filesystem = configuration.cursor.execute_query(query)

        if filesystem is None or filesystem[0] != "TSK_FS_TYPE_EXT4":
            #print("No EXT filesystem.")
            return False

        this_file_path = os.path.dirname(
            os.path.abspath(__file__)) + os.sep + 'schema' + os.sep + 'android' + os.sep

        yaml_list = [this_file_path + 'lv1_os_and_app_email_android.yaml']
        table_list = ['lv1_os_and_app_email_android']

        if not self.check_table_from_yaml(configuration, yaml_list, table_list):
            return False

        query_sep = self.GetQuerySeparator(source_path_spec, configuration)
        config_path = f"root{query_sep}data{query_sep}com.samsung.android.email.provider{query_sep}databases"

        query = f"SELECT name, parent_path, extension FROM file_info WHERE (par_id='{par_id}') and name = 'EmailProvider.db' and parent_path like '{config_path}'"
        email_android_file = configuration.cursor.execute_query_mul(query)

        if len(email_android_file) == 0:
            # print("There are no email_android files")
            return False

        output_path = configuration.root_tmp_path + os.path.sep + configuration.case_id + \
                      os.path.sep + configuration.evidence_id + os.path.sep + par_id

        email_android_path = email_android_file[0][1][email_android_file[0][1].find('/'):]+os.path.sep+email_android_file[0][0]

        if not os.path.exists(output_path):
            os.mkdir(output_path)

        self.ExtractTargetFileToPath(
            source_path_spec=source_path_spec,
            configuration=configuration,
            file_path=email_android_path,
            output_path=output_path)

        file_object = open(output_path + os.path.sep + email_android_file[0][0], 'rb')
        if file_object is None:
            return

        print(f'[{self.print_now_time()}] [MODULE] Android - Email-Android')
        insert_data = []

        for email in ea.Email_android(file_object.name):
            insert_data.append(
                tuple([par_id, configuration.case_id, configuration.evidence_id, str(email.subject),
                       str(email.fromlist), str(email.tolist), str(email.cc), str(email.bcc),
                       str(email.message)]))
        query = "Insert into lv1_os_and_app_email_android values (%s, %s, %s, %s, %s, %s, %s, %s, %s);"
        if len(insert_data) > 0:
            configuration.cursor.bulk_execute(query, insert_data)

manager.ModulesManager.RegisterModule(AndroidEmailConnector)
