# -*- coding: utf-8 -*-
"""module for Timeline."""
import os
from modules import manager
from modules import interface
from modules import logger
from modules.windows_telemetry import lv1_windows_telemetry as wt


class WindowsTelemetryConnector(interface.ModuleConnector):

    NAME = 'windows_telemetry_connector'
    DESCRIPTION = 'Module for Windows 10 telemetry (.rbs file)'
    # Reference = https://arxiv.org/abs/2002.12506

    _plugin_classes = {}

    def __init__(self):
        super(WindowsTelemetryConnector, self).__init__()

    def Connect(self, par_id, configuration, source_path_spec, knowledge_base):

        this_file_path = os.path.dirname(os.path.abspath(__file__)) + os.sep + 'schema' + os.sep

        yaml_list  = [this_file_path + 'lv1_os_win_windows_telemetry.yaml']
        table_list = ['lv1_os_win_windows_telemetry']

        if not self.check_table_from_yaml(configuration, yaml_list, table_list):
            return False

        # try:
        query = f"SELECT name, parent_path, extension FROM file_info WHERE (par_id='{par_id}') and extension = 'rbs'"
        rbs_files = configuration.cursor.execute_query_mul(query)

        if len(rbs_files) == 0:
            print("There are no rbs files (Win10 Telemetry)")
            return False

        # Identify the target
        query_separator = self.GetQuerySeparator(source_path_spec, configuration)
        path_separator = self.GetPathSeparator(source_path_spec)

        # File extraction
        for col in rbs_files:
            rbs_path = col[1] + os.sep + col[0]
            output_path = configuration.root_tmp_path + os.sep + configuration.case_id + os.sep + configuration.evidence_id + os.sep + par_id

            self.ExtractTargetFileToPath(
                source_path_spec=source_path_spec,
                configuration=configuration,
                file_path=rbs_path,
                output_path=output_path)

            extracted = output_path + os.sep + col[0]

            if os.path.exists(extracted) == False:
                logger.debug("There is no file:%s" % extracted)
                continue
            else:
                # Parsing
                self.print_run_info('Parse a rbs file (Win10 Telemetry)', start=True)
                wt.aaaa()
                #parsed_data = self.process_mft(par_id, configuration, table_list, knowledge_base)
                self.print_run_info('Parse a rbs file (Win10 Telemetry)', start=False)

        # 수정할 것.
        # fn = output_path + path_separator + file_name
        # time_zone = knowledge_base.time_zone
        # result = wt.WINDOWSTIMELINE(fn)

        insert_data = []
        #insert_data.append("1", "2", "3", "2.1", "Microsoft.Windows.Kernel.Power.OSStateChange", "2018-05-11T18:48:58.3499732Z", "137346", 2, 257, "Windows", "10.0.10586.0.amd64fre.th2_release.151029-1700", "W:0000da39a3ee5e6b4b0d3255bfef95601890afd80709!00006000000000000000000000000000000000000000!", "1970/01/01:00:00:00!0!", "a", "b")
        #query = "insert into lv1_os_win_windows_telemetry values(
        #query = "Insert into lv1_os_win_windows_telemetry values (%s, %s, %s, %s, %s, %s, %s, %d, %d, %s, %s, %s, %s, %s, %s);"
        #configuration.cursor.bulk_execute(query, insert_data)

manager.ModulesManager.RegisterModule(WindowsTelemetryConnector)
