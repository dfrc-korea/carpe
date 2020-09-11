#-*- coding: utf-8 -*-
import os
import logging
import math
import subprocess
from modules.andForensics.modules.utils.android_sqlite3 import SQLite3
from modules.andForensics.modules.utils.android_jadx import JADX
from multiprocessing import Process, Queue, Lock
import math

logger = logging.getLogger('andForensics')

class APKDecompiler(object):
	def do_decompile(list_file_info, case, result):
		for file_info in list_file_info:
			file_name = file_info[0]
			extracted_file_path = file_info[1]

			extracted_file_dir = os.path.dirname(extracted_file_path)
			decompiled_files_dir_path = case.extracted_files_dir_path_apk + "_decompiled" + extracted_file_dir.split(case.extracted_files_dir_path_apk)[1] + os.sep
			decompiled_files_path = decompiled_files_dir_path + file_name

			apk_path = extracted_file_path
			decompiled_path = decompiled_files_path
			JADX.decompile(apk_path, decompiled_path)
		result.put(len(list_file_info))

#---------------------------------------------------------------------------------------------------------------
	def decompile_with_jadx(case):
		logger.info('    - Decompiling the APK files...')
		query = "SELECT name, extracted_path FROM apk_file_info"
		list_file_info = SQLite3.execute_fetch_query_multi_values(query, case.preprocess_db_path)

		if list_file_info == []:
			logger.error('There are no files to extract.')
			return False

		length = len(list_file_info)
		NUMBER_OF_PROCESSES = case.number_of_input_processes
		MAX_NUMBER_OF_PROCESSES_THIS_MODULE = math.ceil(length/2)
		
		if NUMBER_OF_PROCESSES*2 > length:
			NUMBER_OF_PROCESSES = MAX_NUMBER_OF_PROCESSES_THIS_MODULE
		if length < NUMBER_OF_PROCESSES:
			result = Queue()
			APKDecompiler.do_decompile(list_file_info, case, result)
		else:
			num_item_per_list = math.ceil(length/NUMBER_OF_PROCESSES)
			start_pos = 0
			divied_list = list()
			for idx in range(start_pos, length, num_item_per_list):
				out = list_file_info[start_pos:start_pos+num_item_per_list]
				if out != []:
					divied_list.append(out)
				start_pos += num_item_per_list

			result = Queue()
			procs = []

			for i in range(len(divied_list)):
				proc = Process(target=APKDecompiler.do_decompile, args=(divied_list[i], case, result))
				procs.append(proc)
				proc.start()

			for proc in procs:
				proc.join()

			result.put('STOP')
			while True:
				tmp = result.get()
				if tmp == 'STOP':
					break
