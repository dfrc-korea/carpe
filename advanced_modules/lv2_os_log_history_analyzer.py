# -*- coding: utf-8 -*-
"""module for LV2."""
from advanced_modules import manager
from advanced_modules import interface
from advanced_modules.NTFS.combine import collect_mft, collect_usnjrnl, combine_usnjrnl, UsnJrnl, preprocess_mft
import os


class Lv2OSLogHistoryAnalyzer(interface.AdvancedModuleAnalyzer):
    NAME = 'lv2_os_log_history_analyzer'
    DESCRIPTION = 'Module for LV2 OS Log History'

    _plugin_classes = {}

    def __init__(self):
        super(Lv2OSLogHistoryAnalyzer, self).__init__()

    def Analyze(self, par_id, configuration, source_path_spec, knowledge_base):
        this_file_path = os.path.dirname(os.path.abspath(__file__)) + os.sep + 'schema' + os.sep

        # 모든 yaml 파일 리스트
        yaml_list = [this_file_path + 'lv2_os_log_history.yaml']

        # 모든 테이블 리스트
        table_list = ['lv2_os_log_history']

        # 모든 테이블 생성
        if not self.check_table_from_yaml(configuration, yaml_list, table_list):
            return False

        # Load $MFT
        query = f"SELECT mft_ref_num, path, SI_ctime, file_size FROM lv1_fs_ntfs_mft WHERE par_id='{par_id}' AND source='File record';"
        mft_results = configuration.cursor.execute_query_mul(query)
        if not mft_results:
            print("MFT is not exist")
            return False
        elif mft_results == -1:
            print("No Table")
            return False
        mft_results = preprocess_mft(mft_results)

        # Load $Usnjrnl
        query = f"SELECT usn_value, reason, mft_ref_num, timestamp, file_name, file_path_from_mft FROM lv1_fs_ntfs_usnjrnl WHERE par_id='{par_id}';"
        usnjrnl_results = configuration.cursor.execute_query_mul(query)
        if not usnjrnl_results:
            print("$UsnJrnl is not exist")
            return False
        elif usnjrnl_results == -1:
            print("No Table")
            return False
        usnjrnl = UsnJrnl(usnjrnl_results)
        usnjrnl.parse()
        usnjrnl_grouped = usnjrnl.grouped_by_entry

        # Combine $MFT + $UsnJrnl
        # print("Combining $MFT and $UsnJrnl")
        mft_usnjrnl_list = []
        file_ref_num_list = []
        for file_ref_num, seq_val_dict in sorted(usnjrnl_grouped.items()):
            combined_data = combine_usnjrnl(mft_results, file_ref_num, seq_val_dict)
            if combined_data != file_ref_num:
                mft_usnjrnl_list.append(combined_data)
                file_ref_num_list.append(file_ref_num)

        # Process $MFT and $UsnJrnl
        for file_ref_num in file_ref_num_list:
            del mft_results[file_ref_num]
            del usnjrnl_grouped[file_ref_num]

        # Collect Data
        output_data = []
        info = tuple([par_id, configuration.case_id, configuration.evidence_id])

        # Collect $MFT
        for key in mft_results.keys():
            output_data.append(collect_mft(info, mft_results[key]))

        # Collect $UsnJrnl
        for key in usnjrnl_grouped.keys():
            output_data.extend(collect_usnjrnl(info, usnjrnl_grouped[key].values()))

        # Collect $MFT + $UsnJrnl
        for mft_entry_hist_object in mft_usnjrnl_list:
            output_data.extend(mft_entry_hist_object.collect_data(info))

        query = f"Insert into {table_list[0]} values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"
        configuration.cursor.bulk_execute(query, output_data)


manager.AdvancedModulesManager.RegisterModule(Lv2OSLogHistoryAnalyzer)