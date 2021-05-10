# -*- coding: utf-8 -*-
"""module for Registry."""
import os
from modules import manager
from modules import interface
from modules import logger
from modules.sticky_note import lv1_stickynote as sn


class StickyNoteConnector(interface.ModuleConnector):
    NAME = 'stickynote_connector'
    DESCRIPTION = 'Module for StickyNote'

    _plugin_classes = {}

    def __init__(self):
        super(StickyNoteConnector, self).__init__()

    def Connect(self, par_id, configuration, source_path_spec, knowledge_base):

        this_file_path = os.path.dirname(os.path.abspath(__file__)) + os.sep + 'schema' + os.sep

        # 모든 yaml 파일 리스트
        yaml_list = [this_file_path + 'lv1_os_win_stickynote.yaml']
        # 모든 테이블 리스트
        table_list = ['lv1_os_win_sticky_note']

        if not self.check_table_from_yaml(configuration, yaml_list, table_list):
            return False

    # try:
        query = f"SELECT name, parent_path, extension FROM file_info WHERE (par_id='{par_id}') and name = 'plum.sqlite'"
        stickynote_files = configuration.cursor.execute_query_mul(query)

        if len(stickynote_files) == 0:
            # print("There are no sticky note files")
            return False

        query_separator = self.GetQuerySeparator(source_path_spec, configuration)
        path_separator = self.GetPathSeparator(source_path_spec) 
        for stickynote in stickynote_files:
            stickynote_path = stickynote[1][stickynote[1].find(path_separator):] + path_separator + stickynote[0]  # document full path
            fileName = stickynote[0]
            output_path = configuration.root_tmp_path + os.sep + configuration.case_id + os.sep + configuration.evidence_id + os.sep + par_id
            self.ExtractTargetFileToPath(
                source_path_spec=source_path_spec,
                configuration=configuration,
                file_path=stickynote_path,
                output_path=output_path)

            self.ExtractTargetFileToPath(
                source_path_spec=source_path_spec,
                configuration=configuration,
                file_path=stickynote_path + '-wal',
                output_path=output_path)

            self.ExtractTargetFileToPath(
                source_path_spec=source_path_spec,
                configuration=configuration,
                file_path=stickynote_path + '-journal',
                output_path=output_path)

            fn = output_path + os.path.sep + fileName

        # STICKY NOTE
        insert_data = []
        for note in sn.STICKYNOTE(fn):
            created_time = configuration.apply_time_zone(str(note.createdtime), knowledge_base.time_zone)
            modified_time = configuration.apply_time_zone(str(note.modifiedtime), knowledge_base.time_zone)
            insert_data.append(
                tuple([par_id, configuration.case_id, configuration.evidence_id, str(note.note_id),
                        str(note.type), str(note.content), str(note.activated), created_time, modified_time]))
        query = "Insert into lv1_os_win_sticky_note values (%s, %s, %s, %s, %s, %s, %s, %s, %s);"
        configuration.cursor.bulk_execute(query, insert_data)


manager.ModulesManager.RegisterModule(StickyNoteConnector)
