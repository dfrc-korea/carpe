# -*- coding: utf-8 -*-
"""module for Registry."""
import os
import json
from modules import manager
from modules import interface
from modules import logger
from modules.Evernote import evernote_parser
from typing import List


class EvernoteConnector(interface.ModuleConnector):

    NAME = "evernote_connector"
    DESCRIPTION = "Module for Evernote"

    _plugin_classes = {}

    def __init__(self):
        super(EvernoteConnector, self).__init__()

    def Connect(self, par_id, configuration, source_path_spec, knowledge_base):
        this_file_path = (
            os.path.dirname(os.path.abspath(__file__))
            + os.sep
            + "schema"
            + os.sep
            + "evernote"
        )
        # 모든 yaml 파일 리스트
        yamls = [
            this_file_path + os.sep + "lv1_app_evernote_accounts.yaml",
            this_file_path + os.sep + "lv1_app_evernote_notes.yaml",
            this_file_path + os.sep + "lv1_app_evernote_workchats.yaml",
        ]
        # 모든 테이블 리스트
        tables = [
            "lv1_app_evernote_accounts",
            "lv1_app_evernote_notes",
            "lv1_app_evernote_workchats",
        ]
        # 모든 테이블 생성
        if not self.check_table_from_yaml(configuration, yamls, tables):
            return False

        # extension -> sig_type 변경해야 함
        query = f"""
            SELECT name, parent_path, extension 
            FROM file_info 
            WHERE par_id = '{par_id}' 
            AND extension = 'exb'
            AND parent_path like '%Evernote%' > 0; 
        """
        evernote_db_query_results: List = configuration.cursor.execute_query_mul(query)

        if evernote_db_query_results == -1 or len(evernote_db_query_results) == 0:
            logger.error('db execution failed.')
            # print("There are no evernote files")
            return False

        query_separator = self.GetQuerySeparator(source_path_spec, configuration)
        path_separator = self.GetPathSeparator(source_path_spec)

        for file_name, parent_path, _ in evernote_db_query_results:
            file_path = (
                parent_path[parent_path.find(path_separator):] + path_separator + file_name
            )

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
            self.ExtractTargetFileToPath(
                source_path_spec=source_path_spec,
                configuration=configuration,
                file_path=file_path,
                output_path=output_path,
            )

            parse_result = evernote_parser.main(output_path + os.sep + file_name)
            account = parse_result["user"]
            query = "INSERT INTO lv1_app_evernote_accounts values (%s, %s, %s, %s, %s, %s, %s)"

            account_tuple = tuple(
                [
                    par_id,
                    configuration.case_id,
                    configuration.evidence_id,
                ]
                + list(account.values())
            )
            configuration.cursor.execute_query(query, account_tuple)
            notes = parse_result["notes"]
            query = "INSERT INTO lv1_app_evernote_notes values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"

            for note in notes:
                note_tuple = tuple(
                    [
                        par_id,
                        configuration.case_id,
                        configuration.evidence_id,
                    ]
                    + list(note.values())
                )

                configuration.cursor.execute_query(query, note_tuple)

            workchats = parse_result["workchats"]
            query = "INSERT INTO lv1_app_evernote_workchats values (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
            for workchat in workchats:
                workchat_tuple = tuple(
                    [
                        par_id,
                        configuration.case_id,
                        configuration.evidence_id,
                    ]
                    # json.dumps for stringify array
                    + [
                        json.dumps(column) if index > 3 else column
                        for index, column in enumerate(workchat.values())
                    ]
                )

                configuration.cursor.execute_query(query, workchat_tuple)

            os.remove(output_path + os.sep + file_name)


manager.ModulesManager.RegisterModule(EvernoteConnector)