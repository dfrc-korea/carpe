import os
import logging
from modules.andForensics.modules.utils.android_sqlite3 import SQLite3
from modules.andForensics.modules.analyzer.android_data_analyzer_utils import AnalyzerUtils
from multiprocessing import Process, Queue, Lock
import math

logger = logging.getLogger('andForensics')
#ANALYSIS_EXCEPTION_CALL_HISTORY = os.getcwd() + os.sep + 'config' + os.sep + 'ANALYSIS_EXCEPTION_CALL_HISTORY.conf'
ANALYSIS_EXCEPTION_CALL_HISTORY = '/home/byeongchan/modules/andForensics/config/ANALYSIS_EXCEPTION_CALL_HISTORY.conf'

class CallHistory(object):
	def get_logs_from_pp_db(case):
		query = "SELECT DISTINCT pp.cnt_records, di.id_package, di.inode, di.parent_path, di.name, pp.table_name, pp.cnt_timestamp, pp.cnt_time_duration, pp.cnt_phonenumber, pp.cnt_account, pp.cnt_digit_positive, pp.cnt_file, pp.cnt_contents, pp.timestamp, pp.time_duration, pp.phonenumber, pp.account, pp.digit_positive, pp.file, pp.contents, di.extracted_path \
			FROM sqlitedb_info as di, package_info as pi, sqlitedb_table_preprocess as pp\
			WHERE di.inode = pp.inode and pp.cnt_time_duration >= 1 and (pp.cnt_phonenumber >= 1 or pp.cnt_digit_positive >= 1) and pp.cnt_pwd = 0 and pp.cnt_url = 0 and pp.cnt_geodata = 0 and pp.cnt_ip = 0 and pp.cnt_mac = 0 and pp.cnt_bin = 0 and pp.cnt_cipher = 0 and pp.cnt_pkg = 0"
		list_userinfo_record = SQLite3.execute_fetch_query_multi_values(query, case.preprocess_db_path)
		if (list_userinfo_record == False) | (list_userinfo_record == []):
			logger.error('The image has no call history information.')
			return False
		return list_userinfo_record

#---------------------------------------------------------------------------------------------------------------
	def do_analyze(list_userinfo_record, case, result):
		AnalyzerUtils.load_exception_rule(ANALYSIS_EXCEPTION_CALL_HISTORY)
		for userinfo_record in list_userinfo_record:
			dic_userinfo_record = {'id_package':0, 'package_name':"", 'inode':0, 'parent_path':"", 'db_name':"", 'table_name':"", 'cnt_records':0, 'timestamp':"", 'time_duration':"", 'phonenumber':"", 'account':"", 'digit_positive':"", 'contents':"", 'file':"", 'db_path':""}
			dic_userinfo_cnt = {'timestamp':0, 'time_duration':0, 'phonenumber':0, 'account':0, 'digit_positive':0, 'contents':0, 'file':0}

			dic_userinfo_record['db_name'] 		= userinfo_record[4]
			dic_userinfo_record['table_name'] 	= userinfo_record[5]

			if AnalyzerUtils.exception_rule_db_table(dic_userinfo_record['db_name'], dic_userinfo_record['table_name']):
				continue

			dic_userinfo_record['cnt_records']	= userinfo_record[0]
			dic_userinfo_record['id_package']	= userinfo_record[1]
			dic_userinfo_record['inode'] 		= userinfo_record[2]
			dic_userinfo_record['parent_path']	= userinfo_record[3]

			dic_userinfo_cnt['timestamp'] 		= userinfo_record[6]
			dic_userinfo_cnt['time_duration'] 	= userinfo_record[7]
			dic_userinfo_cnt['phonenumber'] 	= userinfo_record[8]
			dic_userinfo_cnt['account']			= userinfo_record[9]
			dic_userinfo_cnt['digit_positive'] 	= userinfo_record[10]
			dic_userinfo_cnt['file'] 			= userinfo_record[11]
			dic_userinfo_cnt['contents'] 		= userinfo_record[12]

			dic_userinfo_record['timestamp'] 		= userinfo_record[13]
			dic_userinfo_record['time_duration']	= userinfo_record[14]
			dic_userinfo_record['phonenumber'] 		= userinfo_record[15]
			dic_userinfo_record['account'] 			= userinfo_record[16]
			dic_userinfo_record['digit_positive'] 	= userinfo_record[17]
			dic_userinfo_record['file'] 			= userinfo_record[18]
			dic_userinfo_record['contents'] 		= userinfo_record[19]
			dic_userinfo_record['db_path'] 			= userinfo_record[20]
			
			dic_userinfo_record['package_name'] = AnalyzerUtils.get_package_name(dic_userinfo_record['id_package'], dic_userinfo_record['parent_path'], case)
			table_name_to_insert = "call_history"
			not_null_userinfo_type = "timestamp"

			list_userinfo_type, list_value_format, list_col_name, list_userinfo_col_value = AnalyzerUtils.get_userinfo_type_format_value_from_sqlitedb(dic_userinfo_record, dic_userinfo_cnt, not_null_userinfo_type)
			AnalyzerUtils.compose_col_value_to_insert(dic_userinfo_record, list_userinfo_type, list_value_format, list_col_name, list_userinfo_col_value, case, table_name_to_insert)
		result.put(len(list_userinfo_record))

#---------------------------------------------------------------------------------------------------------------
	def analyze_with_preprocess_db(case):
		list_userinfo_record = CallHistory.get_logs_from_pp_db(case)
		if (list_userinfo_record == []) | (list_userinfo_record == False):
			logger.error('There are no call history to analyze.')
			return False

		length = len(list_userinfo_record)
		NUMBER_OF_PROCESSES = case.number_of_input_processes
		MAX_NUMBER_OF_PROCESSES_THIS_MODULE = math.ceil(length/2)

		if NUMBER_OF_PROCESSES*2 > length:
			NUMBER_OF_PROCESSES = MAX_NUMBER_OF_PROCESSES_THIS_MODULE

		if length < NUMBER_OF_PROCESSES:
			result = Queue()
			CallHistory.do_analyze(list_userinfo_record, case, result)
		else:
			num_item_per_list = math.ceil(length/NUMBER_OF_PROCESSES)
			start_pos = 0
			divied_list = list()
			for idx in range(start_pos, length, num_item_per_list):
				out = list_userinfo_record[start_pos:start_pos+num_item_per_list]
				if out != []:
					divied_list.append(out)
				start_pos += num_item_per_list

			result = Queue()
			procs = []

			for i in range(len(divied_list)):
				proc = Process(target=CallHistory.do_analyze, args=(divied_list[i], case, result))
				procs.append(proc)
				proc.start()

			for proc in procs:
				proc.join()

			result.put('STOP')
			while True:
				tmp = result.get()
				if tmp == 'STOP':
					break
