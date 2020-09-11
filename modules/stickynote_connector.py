# -*- coding: utf-8 -*-
"""module for Registry."""
import os
from modules import manager
from modules import interface
from modules import logger
from modules.sticky_note import lv1_stickynote as sn
from dfvfs.lib import definitions as dfvfs_definitions


class StickyNoteConnector(interface.ModuleConnector):

    NAME = 'stickynote_connector'
    DESCRIPTION = 'Module for StickyNote'

    _plugin_classes = {}

    def __init__(self):
        super(StickyNoteConnector, self).__init__()

    def Connect(self, configuration, source_path_spec, knowledge_base):

        this_file_path = os.path.dirname(os.path.abspath(__file__)) + os.sep + 'schema' + os.sep
        # 모든 yaml 파일 리스트
        yaml_list = [this_file_path + 'lv1_os_win_stickynote.yaml']
        # 모든 테이블 리스트
        table_list = ['lv1_os_win_sticky_note']
        # 모든 테이블 생성
        for count in range(0, len(yaml_list)):
            if not self.LoadSchemaFromYaml(yaml_list[count]):
                logger.error('cannot load schema from yaml: {0:s}'.format(table_list[count]))
                return False

            # if table is not existed, create table
            if not configuration.cursor.check_table_exist(table_list[count]):
                ret = self.CreateTable(configuration.cursor)
                if not ret:
                    logger.error('cannot create database table name: {0:s}'.format(table_list[count]))
                    return False

        try:
            if source_path_spec.parent.type_indicator != dfvfs_definitions.TYPE_INDICATOR_TSK_PARTITION:
                par_id = configuration.partition_list['p1']
            else:
                par_id = configuration.partition_list[getattr(source_path_spec.parent, 'location', None)[1:]]

            if par_id == None:
                return False

            query = f"SELECT name, parent_path, extension FROM file_info WHERE (par_id='{par_id}') and name = 'plum.sqlite'"
            stickynote_files = configuration.cursor.execute_query_mul(query)

            if len(stickynote_files) == 0:
                return False

            print('[MODULE]: StickyNote Connect')

            for stickynote in stickynote_files:
                stickynote_path = stickynote[1][stickynote[1].find('/'):] + '/' + stickynote[0]  # document full path
                fileExt = stickynote[2]
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
            print('[MODULE]: StickyNote')
            insert_data = []
            for note in sn.STICKYNOTE(fn):
                insert_data.append(
                    tuple([par_id, configuration.case_id, configuration.evidence_id, str(note.note_id),
                         str(note.type), str(note.content),
                         str(note.activated), str(note.createdtime), str(note.modifiedtime)]))
            query = "Insert into lv1_os_win_sticky_note values (%s, %s, %s, %s, %s, %s, %s, %s, %s);"
            configuration.cursor.bulk_execute(query, insert_data)

            print('[MODULE]: StickyNote Complete')
        except:
            print("StickyNote Connector Error")

manager.ModulesManager.RegisterModule(StickyNoteConnector)
