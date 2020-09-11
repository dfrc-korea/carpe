import os
import logging
from modules.andForensics.modules.utils.android_sqlite3 import SQLite3
from modules.andForensics.modules.analyzer.android_data_analyzer_utils import AnalyzerUtils
from multiprocessing import Process, Queue, Lock
import math
import zipfile
import datetime

logger = logging.getLogger('andForensics')

class EmbeddedFile(object):
	def insert_to_analysis_db(dic_embedded_fileinfo, case):
		query = 'INSERT INTO embedded_file(is_compressed, parent_path, name, extension, mod_time, size, compressed_size, CRC, create_system, source_path, source) VALUES(%d, "%s", "%s", "%s", %d, %d, %d, %d, "%s", "%s", "%s")' % (dic_embedded_fileinfo['is_compressed'], dic_embedded_fileinfo['parent_path'], dic_embedded_fileinfo['name'], dic_embedded_fileinfo['extension'], dic_embedded_fileinfo['mod_time'], dic_embedded_fileinfo['size'], dic_embedded_fileinfo['compressed_size'], dic_embedded_fileinfo['CRC'], dic_embedded_fileinfo['create_system'], dic_embedded_fileinfo['source_path'], dic_embedded_fileinfo['source'])
		SQLite3.execute_commit_query(query, case.analysis_db_path)

#---------------------------------------------------------------------------------------------------------------
	def do_analyze_pkzip_compressed_file(list_file_info, case, result):
		for file_info in list_file_info:
			inode = file_info[0]
			extracted_file_path = file_info[1]

			try:
				with zipfile.ZipFile(extracted_file_path, 'r') as zip:
					for info in zip.infolist():
						dic_embedded_fileinfo = {'is_compressed':0, 'parent_path':"", 'name':"", 'extension':"", 'mod_time':0, 'size':0, 'compressed_size':0, 'CRC':0, 'sha1':"", 'create_system':"", 'source_path':"", 'source':""}

						if info.compress_type == 0:
							dic_embedded_fileinfo['is_compressed'] = 1
						dic_embedded_fileinfo['full_filepath'] = info.filename
						if info.filename.find("/") >= 1:
							dic_embedded_fileinfo['parent_path'] = "/" + info.filename.rsplit("/", 1)[0] + "/"
							dic_embedded_fileinfo['name'] = info.filename.rsplit("/", 1)[-1]
						else:
							dic_embedded_fileinfo['name'] = info.filename
						dic_embedded_fileinfo['extension'] = info.filename.rsplit(".", 1)[-1]

						if info.date_time[1] != 0: # month == 0
							unixtime_mod = int(datetime.datetime(*info.date_time).timestamp())
							if len(str(unixtime_mod)) == 10:
								dic_embedded_fileinfo['mod_time'] = unixtime_mod
							
						dic_embedded_fileinfo['size'] = info.file_size
						dic_embedded_fileinfo['compressed_size'] = info.compress_size
						dic_embedded_fileinfo['CRC'] = info.CRC
						if info.create_system == 0:
							dic_embedded_fileinfo['create_system'] = "windows"
						elif info.create_system == 3:
							dic_embedded_fileinfo['create_system'] = "unix"
						dic_embedded_fileinfo['source_path'] = extracted_file_path.split(case.extracted_files_dir_path_apk)[1].replace(os.sep, "/")
						dic_embedded_fileinfo['source'] = inode
						EmbeddedFile.insert_to_analysis_db(dic_embedded_fileinfo, case)
			except zipfile.BadZipfile as e:
				logger.error("%s is not APK file." % extracted_file_path)
				continue

		result.put(len(list_file_info))


#---------------------------------------------------------------------------------------------------------------
	# def analyze_pkzip_file(case):
	# 	print("pkzip")

#---------------------------------------------------------------------------------------------------------------
	def analyze_apk_file(case):
		logger.info('    - Analyze the APK files...')
		query = "SELECT inode, extracted_path FROM apk_file_info"
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
			EmbeddedFile.do_analyze_pkzip_compressed_file(list_file_info, case, result)
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
				proc = Process(target=EmbeddedFile.do_analyze_pkzip_compressed_file, args=(divied_list[i], case, result))
				procs.append(proc)
				proc.start()

			for proc in procs:
				proc.join()

			result.put('STOP')
			while True:
				tmp = result.get()
				if tmp == 'STOP':
					break

#---------------------------------------------------------------------------------------------------------------
	def analyze_compressed_file(case):
		EmbeddedFile.analyze_apk_file(case)
		# EmbeddedFile.analyze_pkzip_file(case)

#---------------------------------------------------------------------------------------------------------------
	def analyze_embedded_file(case):
		EmbeddedFile.analyze_compressed_file(case)

