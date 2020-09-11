# -*- coding: utf-8 -*-
"""module for Registry."""
import os
from modules import manager
from modules import interface
from modules import logger
from modules.windows_timeline import lv1_windows_timeline as wt
from dfvfs.lib import definitions as dfvfs_definitions


class WindowsTimelineConnector(interface.ModuleConnector):

    NAME = 'windows_timeline_connector'
    DESCRIPTION = 'Module for windwos_timeline'

    _plugin_classes = {}

    def __init__(self):
        super(WindowsTimelineConnector, self).__init__()

    def Connect(self, configuration, source_path_spec, knowledge_base):
        print('[MODULE]: WindowsTimelineConnector Connect')
        try:
            this_file_path = os.path.dirname(os.path.abspath(__file__)) + os.sep + 'schema' + os.sep
            # 모든 yaml 파일 리스트
            yaml_list = [this_file_path + 'lv1_os_win_windows_timeline.yaml']
            # 모든 테이블 리스트
            table_list = ['lv1_os_win_windows_timeline']

            if not self.check_table_from_yaml(configuration, yaml_list, table_list):
                return False

            if source_path_spec.parent.type_indicator != dfvfs_definitions.TYPE_INDICATOR_TSK_PARTITION:
                par_id = configuration.partition_list['p1']
            else:
                par_id = configuration.partition_list[getattr(source_path_spec.parent, 'location', None)[1:]]

            if par_id == None:
                return False

            query = f"SELECT name, parent_path, extension FROM file_info WHERE (par_id='{par_id}' and name like '%ActivitiesCache.db') and ("
            for user_accounts in knowledge_base._user_accounts.values():
                for hostname in user_accounts.values():
                    if hostname.identifier.find('S-1-5-21') == -1:
                        continue
                    query += f"parent_path like '%L.{hostname.username}%' or "
            query = query[:-4] + ");"

            windows_timeline_files = configuration.cursor.execute_query_mul(query)

            if len(windows_timeline_files) == 0:
                return False

            for timeline in windows_timeline_files:
                timeline_path = timeline[1][timeline[1].find('/'):] + '/' + timeline[0]  # document full path
                fileExt = timeline[2]
                fileName = timeline[0]
                output_path = configuration.root_tmp_path + os.sep + configuration.case_id + os.sep + configuration.evidence_id + os.sep + par_id
                self.ExtractTargetFileToPath(
                    source_path_spec=source_path_spec,
                    configuration=configuration,
                    file_path=timeline_path,
                    output_path=output_path)

                self.ExtractTargetFileToPath(
                    source_path_spec=source_path_spec,
                    configuration=configuration,
                    file_path=timeline_path + '-wal',
                    output_path=output_path)

                self.ExtractTargetFileToPath(
                    source_path_spec=source_path_spec,
                    configuration=configuration,
                    file_path=timeline_path + '-journal',
                    output_path=output_path)

                fn = output_path + os.path.sep + fileName



            # WindowsTimeline
            print('[MODULE]: WindowsTimeline')
            insert_data = []
            for timeline in wt.WINDOWSTIMELINE(fn):
                insert_data.append(
                    tuple([par_id, configuration.case_id, configuration.evidence_id, str(timeline.program_name).replace('\\', '/'),
                           str(timeline.display_name), str(timeline.content),
                           str(timeline.activity_type), str(timeline.focus_seconds), str(timeline.start_time),
                           str(timeline.end_time), str(timeline.activity_id), str(timeline.platform),
                           str(timeline.created_time), str(timeline.created_in_cloud_time), str(timeline.last_modified_time),
                           str(timeline.last_modified_on_client_time), str(timeline.original_last_modified_on_client_time), str(timeline.local_only_flag), str(timeline.group), str(timeline.clipboardpayload), str(timeline.timezone)]))
            query = "Insert into lv1_os_win_windows_timeline values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"
            configuration.cursor.bulk_execute(query, insert_data)

            print('[MODULE]: WindowsTimeline Complete')
        except Exception as e:
            print("WindowsTimeline Connector Error" + str(e))

manager.ModulesManager.RegisterModule(WindowsTimelineConnector)
