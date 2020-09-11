#-*- coding: utf-8 -*-
import os
import logging
import math
from modules.andForensics.modules.utils.android_sqlite3 import SQLite3
from modules.andForensics.modules.utils.android_TSK import TSK
from binascii import b2a_hex
from multiprocessing import Process, Queue

logger = logging.getLogger('andForensics')
#FILE_FORMAT_CONF_PATH = os.getcwd() + os.sep + 'config' + os.sep + 'FILE_FORMAT.conf'
FILE_FORMAT_CONF_PATH = '/home/byeongchan/modules/andForensics/config/FILE_FORMAT.conf'

class Classifier(object):
	def set_loaddb(load_db_path):
		# create a id_package column in loaddb's tsk_files table
		query = "SELECT sql FROM sqlite_master WHERE name='tsk_files' AND sql LIKE '%id_package%'"
		if(SQLite3.execute_fetch_query(query, load_db_path)) == None:
			query = "ALTER TABLE tsk_files ADD id_package INTEGER DEFAULT 0 NOT NULL"
			SQLite3.execute_commit_query(query, load_db_path)

		# create a format column in loaddb's tsk_files table
		query = "SELECT sql FROM sqlite_master WHERE name='tsk_files' AND sql LIKE '%format%'"
		if(SQLite3.execute_fetch_query(query, load_db_path)) == None:
			query = "ALTER TABLE tsk_files ADD format INTEGER DEFAULT 0 NOT NULL"
			SQLite3.execute_commit_query(query, load_db_path)

		# create a file_format table in loaddb
		query = 'SELECT count(*) FROM sqlite_master WHERE name = "file_format"'
		if SQLite3.execute_fetch_query(query, load_db_path)[0] == 0:
			query = "CREATE TABLE file_format (format TEXT, flag INTEGER)"
			SQLite3.execute_commit_query(query, load_db_path)

#---------------------------------------------------------------------------------------------------------------
	def classify_with_package_name(case):
		query = 'SELECT DISTINCT uid_suid, code_path, log_path, package_name FROM package_info ORDER BY uid_suid'
		list_package_uidsuid_codepath_logpath_packagename = SQLite3.execute_fetch_query_multi_values(query, case.preprocess_db_path)
		for package_uidsuid_codepath_logpath_packagename in list_package_uidsuid_codepath_logpath_packagename:
			uid_suid = package_uidsuid_codepath_logpath_packagename[0]
			code_path = package_uidsuid_codepath_logpath_packagename[1]
			log_path = package_uidsuid_codepath_logpath_packagename[2]
			package_name = package_uidsuid_codepath_logpath_packagename[3]
			if package_name != "android":
				query = 'UPDATE tsk_files set id_package = %d WHERE parent_path LIKE "%s" and id_package = 0' % (int(uid_suid), "/data/"+package_name+"%")
				SQLite3.execute_commit_query(query, case.load_db_path)
				query = 'UPDATE tsk_files set id_package = %d WHERE parent_path LIKE "%s" and id_package = 0' % (int(uid_suid), "%/"+package_name+"%")
				SQLite3.execute_commit_query(query, case.load_db_path)
				query = 'UPDATE tsk_files set id_package = %d WHERE name LIKE "%s" and id_package = 0' % (int(uid_suid), package_name+"%")
				SQLite3.execute_commit_query(query, case.load_db_path)
				if code_path[:10] == "/data/app/":
					code_path = code_path[5:]
					query = 'UPDATE tsk_files set id_package = %d WHERE parent_path LIKE "%s" and id_package = 0' % (int(uid_suid), code_path+"%")
					SQLite3.execute_commit_query(query, case.load_db_path)

#---------------------------------------------------------------------------------------------------------------
	def classify_with_app_name(case):
		query = 'SELECT DISTINCT uid_suid, app_name FROM package_info'
		list_package_uidsuid_app_name = SQLite3.execute_fetch_query_multi_values(query, case.preprocess_db_path)
		for package_uidsuid_app_name in list_package_uidsuid_app_name:
			uid_suid = package_uidsuid_app_name[0]
			app_name = package_uidsuid_app_name[1]

			if app_name != "":
				query = 'UPDATE tsk_files set id_package = %d WHERE parent_path LIKE "%s" and id_package = 0' % (int(uid_suid), "/media/%"+app_name+"%")
				SQLite3.execute_commit_query(query, case.load_db_path)

		# samsung camera app -> /media/0/DCIM...
		query = 'SELECT uid_suid FROM package_info WHERE package_name = "com.sec.android.app.camera"'
		ret = SQLite3.execute_fetch_query(query, case.preprocess_db_path)
		if ret != None:
			uid_suid = SQLite3.execute_fetch_query(query, case.preprocess_db_path)[0]
			query = 'UPDATE tsk_files set id_package = %d WHERE parent_path LIKE "%s" and id_package = 0' % (int(uid_suid), "/media/%"+"DCIM/"+"%")
			SQLite3.execute_commit_query(query, case.load_db_path)

#---------------------------------------------------------------------------------------------------------------
	def get_list_dic_file_format_signature():
		if os.path.exists(FILE_FORMAT_CONF_PATH) == False:
			logger.error('Not exist the config (\"%s\").' % FILE_FORMAT_CONF_PATH)
			return False
		try:
			f = open(FILE_FORMAT_CONF_PATH, 'r')
		except Exception as e:
			logger.error("Fail to open file [%s]" % FILE_FORMAT_CONF_PATH)
			return False
			
		line = f.readline()
		if line.strip() == "## Size of Header Buffer":
			size_buf = f.readline().strip()
		if (size_buf.strip().isdigit() == False) | (size_buf == ""):
			return False
		list_dic_file_format_signature = list()       
		while True:
			line = f.readline()
			if not line: break
			line = line.strip()

			if (line.startswith("#") == True) | (line == ""):    continue
			line = line.replace(" ", "")
			line = line.replace("\t", "")

			dic_file_format_signature = {'size_header':0, 'format':"", 'offset_sig_start':0, 'cnt_sig':0, 'signature':""}
			dic_file_format_signature['format'] = str(line.split(",")[0]).upper()
			dic_file_format_signature['size_header'] = int(line.split(",")[1])
			dic_file_format_signature['offset_sig_start'] = int(line.split(",")[2])
			dic_file_format_signature['cnt_sig'] = int(line.split(",")[3])
			dic_file_format_signature['signature'] = line.split(",", 4)[4]
			list_dic_file_format_signature.append(dic_file_format_signature)
		f.close()
		list_dic_file_format_signature = [y for (x,y) in sorted([(i['size_header'],i) for i in list_dic_file_format_signature], reverse=True)]
		return (int(size_buf), list_dic_file_format_signature)

#---------------------------------------------------------------------------------------------------------------
	def compare_signature(header_hex, list_dic_file_format_signature):
		for i in range(len(list_dic_file_format_signature)):
			list_signature = list_dic_file_format_signature[i]['signature'].split(",")
			header_hex_tmp = header_hex

			if list_dic_file_format_signature[i]['offset_sig_start'] != 0:
				header_hex_tmp = header_hex[list_dic_file_format_signature[i]['offset_sig_start']:]

			for j in range(list_dic_file_format_signature[i]['cnt_sig']):
				if header_hex_tmp.decode().startswith(list_signature[j]):
					return list_dic_file_format_signature[i]['format']
		return False

#---------------------------------------------------------------------------------------------------------------
	def set_file_format_table_to_loaddb(list_dic_file_format_signature, load_db_path):
		for i in range(len(list_dic_file_format_signature)):
			format_name = list_dic_file_format_signature[i]['format']
			format_flag = i+1
			query = 'SELECT count(*) FROM "file_format" WHERE format = "%s"' % format_name
			if(SQLite3.execute_fetch_query(query, load_db_path)[0]) == 0:
				query = 'INSERT INTO file_format(format, flag) VALUES("%s", %d)' % (format_name, format_flag)
				SQLite3.execute_commit_query(query, load_db_path)

#---------------------------------------------------------------------------------------------------------------
	def do_compare(list_file_inode, image_file_path, size_buf, list_dic_file_format_signature, load_db_path, result):
		for i in range(0, len(list_file_inode)):
			inode = '%d' % list_file_inode.pop()
			header = TSK.get_file_buffer(image_file_path, int(inode), size_buf)
			header_hex = b2a_hex(header)

			# insert_file_signature_to_loaddb
			format_name = Classifier.compare_signature(header_hex, list_dic_file_format_signature)
			if format_name != False:
				query = 'SELECT flag FROM file_format WHERE format = "%s"' % format_name
				flag_signature = SQLite3.execute_fetch_query(query, load_db_path)
				if flag_signature != None:
					query = 'UPDATE tsk_files set format = %d WHERE meta_addr = %d and dir_flags != 2 and type = 0' % (int(flag_signature[0]), int(inode))
					# print("query: ", query)
					SQLite3.execute_commit_query(query, load_db_path)
		result.put(len(list_file_inode))

#---------------------------------------------------------------------------------------------------------------
	def classify_with_file_format(size_buf, list_dic_file_format_signature, case):
		# get_list_all_file_inode
		query = "SELECT meta_addr FROM tsk_files WHERE size != 0 and dir_flags != 2 and dir_type = 5 and type = 0"
		list_all_file_inode = SQLite3.execute_fetch_query_multi_values(query, case.load_db_path)
		length = len(list_all_file_inode)

		NUMBER_OF_PROCESSES = case.number_of_input_processes
		MAX_NUMBER_OF_PROCESSES_THIS_MODULE = math.ceil(length/2)
		if NUMBER_OF_PROCESSES*2 > length:
			NUMBER_OF_PROCESSES = MAX_NUMBER_OF_PROCESSES_THIS_MODULE

		if length < NUMBER_OF_PROCESSES:
			result = Queue()
			Classifier.do_compare(list_all_file_inode, case.image_file_path, size_buf, list_dic_file_format_signature, case.load_db_path, result)
		else:
			num_item_per_list = math.ceil(length/NUMBER_OF_PROCESSES)
			start_pos = 0
			divied_list = list()
			for idx in range(start_pos, length, num_item_per_list):
				out = list_all_file_inode[start_pos:start_pos+num_item_per_list]
				if out != []:
					divied_list.append(out)
				start_pos += num_item_per_list

			result = Queue()
			procs = []

			for i in range(len(divied_list)):
				proc = Process(target=Classifier.do_compare, args=(divied_list[i], case.image_file_path, size_buf, list_dic_file_format_signature, case.load_db_path, result))
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
	def set_file_format_table(file_name, load_db_path):
		query = 'SELECT flag FROM file_format ORDER BY flag DESC LIMIT 1'
		flag_last = SQLite3.execute_fetch_query(query, load_db_path)[0]
		query = 'SELECT count(*) FROM "%s" WHERE format = "%s"' % ("file_format", file_name)
		flag = '%d' % SQLite3.execute_fetch_query(query, load_db_path)
		if flag == '0':
			query = 'INSERT INTO file_format(format, flag) VALUES("%s", %d)' % (file_name, flag_last+1)
			SQLite3.execute_commit_query(query, load_db_path)

#---------------------------------------------------------------------------------------------------------------
	def classify_with_file_name(file_name, load_db_path):
		query = 'SELECT flag FROM file_format WHERE format = "%s"' % file_name
		flag_signature = SQLite3.execute_fetch_query(query, load_db_path)[0]

		if file_name == "SQLITEDB_JOURNAL":
			query = 'UPDATE tsk_files set format = %d WHERE name LIKE ' % flag_signature
			query2 = '"%-journal" and dir_type !=3 and dir_flags != 2 and type = 0 and size != 0'
			# print(query + query2)
			SQLite3.execute_commit_query(query + query2, load_db_path)
		elif file_name == "APK":
			query = 'UPDATE tsk_files set format = %d WHERE name LIKE ' % flag_signature
			query2 = '"%.apk" and dir_type !=3 and dir_flags != 2 and type = 0 and size != 0'
			SQLite3.execute_commit_query(query + query2, load_db_path)
		else:
			return 0

#---------------------------------------------------------------------------------------------------------------
	def data_grouping_appdata_with_package_filesystem_path(case):
		Classifier.set_loaddb(case.load_db_path)
		logger.info('    - Data grouping with package name information...')
		Classifier.classify_with_package_name(case)
		logger.info('    - Data grouping with app name information...')
		Classifier.classify_with_app_name(case)

#---------------------------------------------------------------------------------------------------------------
	def data_classify_all_files_with_signature(case):
		logger.info('    - Data classifying with file signature...')
		ret = Classifier.get_list_dic_file_format_signature()
		size_buf = ret[0]
		list_dic_file_format_signature = ret[1]

		size_buf = Classifier.set_file_format_table_to_loaddb(list_dic_file_format_signature, case.load_db_path)
		Classifier.classify_with_file_format(size_buf, list_dic_file_format_signature, case)

#---------------------------------------------------------------------------------------------------------------
	def data_classify_all_files_with_file_name(case):
		logger.info('    - Data classifying with file name (SQLite-journal)...')
		Classifier.set_file_format_table("SQLITEDB_JOURNAL", case.load_db_path)
		Classifier.classify_with_file_name("SQLITEDB_JOURNAL", case.load_db_path)
		logger.info('    - Data classifying with file name (APK)...')
		Classifier.set_file_format_table("APK", case.load_db_path)
		Classifier.classify_with_file_name("APK", case.load_db_path)

