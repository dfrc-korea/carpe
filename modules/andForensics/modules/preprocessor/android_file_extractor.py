#-*- coding: utf-8 -*-
import os
import logging
import math
from modules.andForensics.modules.utils.android_sqlite3 import SQLite3
from modules.andForensics. modules.utils.android_TSK import TSK
from multiprocessing import Process, Queue
import sys

logger = logging.getLogger('andForensics')

class FileExtractor(object):
	def insert_extracted_files_info_to_resultdb(format_name, file_info, preprocess_db_path, extracted_file_path):
		inode = file_info[0]
		id_package = file_info[1]
		parent_path = file_info[2]
		name = file_info[3]
		size = file_info[4]
		ctime = file_info[5]
		crtime = file_info[6]
		atime = file_info[7]
		mtime = file_info[8]

		if format_name.upper() == "SQLITEDB":
			query = 'INSERT INTO sqlitedb_info(inode, id_package, parent_path, name, size, ctime, crtime, atime, mtime, extracted_path) VALUES(%d, %d, "%s", "%s", %d, %d, %d, %d, %d, "%s")' % (int(inode), int(id_package), parent_path, name, int(size), int(ctime), int(crtime), int(atime), int(mtime), extracted_file_path)
		elif format_name.upper() == "APK":
			query = 'INSERT INTO apk_file_info(inode, id_package, parent_path, name, size, ctime, crtime, atime, mtime, extracted_path) VALUES(%d, %d, "%s", "%s", %d, %d, %d, %d, %d, "%s")' % (int(inode), int(id_package), parent_path, name, int(size), int(ctime), int(crtime), int(atime), int(mtime), extracted_file_path)

		SQLite3.execute_commit_query(query, preprocess_db_path)

#---------------------------------------------------------------------------------------------------------------
	def do_extract(list_file_info, case, format_name, result):
		for file_info in list_file_info:
			inode = file_info[0]
			id_package = file_info[1]
			parent_path = file_info[2]
			name = file_info[3]
			extracted_parent_path = str(file_info[2]).replace("/", os.sep)

			if format_name.upper() == "SQLITEDB":
				extracted_file_dir = case.extracted_files_dir_path_sqlitedb + extracted_parent_path
			elif format_name.upper() == "APK":
				extracted_file_dir = case.extracted_files_dir_path_apk + extracted_parent_path

			if os.path.exists(extracted_file_dir) == False:
				try:
					os.makedirs(extracted_file_dir)
				except OSError as e:
					logger.error("Directory is already exist. filepath: %s" % extracted_file_dir + name)
					pass

			extracted_file_path = extracted_file_dir + name
			if os.path.exists(extracted_file_path) == False:
				if TSK.icat_for_extract_file(case.image_file_path, inode, extracted_file_path):
					FileExtractor.insert_extracted_files_info_to_resultdb(format_name, file_info, case.preprocess_db_path, extracted_file_path)
		result.put(len(list_file_info))

#---------------------------------------------------------------------------------------------------------------
	def extract_files_with_format(case, format_name):
		logger.info('    - Extracting the %s files...' % format_name)
		query = 'SELECT flag FROM file_format WHERE format = "%s"' % format_name.upper()
		file_format_info = SQLite3.execute_fetch_query(query, case.load_db_path)
		if file_format_info == False:
			return False

		format_flag = file_format_info[0]
		query = 'SELECT meta_addr, id_package, parent_path, name, size, ctime, crtime, atime, mtime FROM tsk_files WHERE format = %d' % format_flag
		list_file_info = SQLite3.execute_fetch_query_multi_values(query, case.load_db_path)
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
			FileExtractor.do_extract(list_file_info, case, format_name, result)
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
				proc = Process(target=FileExtractor.do_extract, args=(divied_list[i], case, format_name, result))
				procs.append(proc)
				proc.start()

			for proc in procs:
				proc.join()

			result.put('STOP')
			while True:
				tmp = result.get()
				if tmp == 'STOP':
					break


