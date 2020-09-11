# -*- coding: utf-8 -*-
import os
import sys
import logging
from modules.andForensics.modules.utils.android_sqlite3 import SQLite3
import multiprocessing
import binascii

logger = logging.getLogger('andForensics')

class Case(object):
	def __init__(self, args):
		self.number_of_system_processes = 0
		self.number_of_input_processes = args.number_process
		self.log_file_name = ""
		self.log_file_path = ""
		self.input_dir_path = args.input_dir
		self.output_dir_path = args.output_dir
		self.list_image_file_path = list()
		self.image_file_name = ""
		self.image_file_path = ""		
		self.load_db_path = ""				# result of TSK's loaddb module
		self.preprocess_db_path = ""		# result of pre-processing phase
		self.analysis_db_path = ""			# result of analysis phase
		self.extracted_files_dir_path = ""
		self.extracted_files_dir_path_slog = ""
		self.extracted_files_dir_path_apk = ""
		self.extracted_files_dir_path_apk_decompiled = ""
		self.extracted_files_dir_path_sqlitedb = ""

#---------------------------------------------------------------------------------------------------------------
	def check_number_process(self):
		self.number_of_system_processes = multiprocessing.cpu_count()
		if self.number_of_input_processes == None:
			self.number_of_input_processes = 1
		else:
			self.number_of_input_processes = int(self.number_of_input_processes)
			if self.number_of_input_processes > self.number_of_system_processes:
				return False

#---------------------------------------------------------------------------------------------------------------
	def find_list_image_file_path(self):
		if os.path.isdir(self.input_dir_path):			
			for root, dirs, files in os.walk(self.input_dir_path):
				if files == []:
					logger.error('Input directory must contain a image file.')
					return False
				else:					
					for fname in files:
						with open(os.path.join(root, fname), "rb") as f:
							f.seek(0x438)
							signature = binascii.b2a_hex(f.read(2))
							if str(signature) == "b'53ef'":
								self.image_file_path = os.path.join(root, fname)
								self.list_image_file_path.append(self.image_file_path)
			if self.list_image_file_path == []:
				logger.error("Insert the EXT4 filesystem image file.")
		else: return False
		return self.list_image_file_path

#---------------------------------------------------------------------------------------------------------------
	def set_file_path(self, args, image_file_path):
		self.image_file_path = image_file_path
		self.output_dir_path = args.output_dir
		if self.input_dir_path[-1] == os.sep:
			self.input_dir_path = self.input_dir_path[:-1]
		if self.output_dir_path[-1] == os.sep:
			self.output_dir_path = self.output_dir_path[:-1]
		self.image_file_name = os.path.basename(self.image_file_path)
		self.output_dir_path = self.output_dir_path + os.sep + self.image_file_name
		self.log_file_name = 'log_' + self.image_file_name + '.txt'
		self.log_file_path = self.output_dir_path + os.sep + 'log_' + self.image_file_name + '.txt'
		self.load_db_path = self.output_dir_path + os.sep + 'loaddb_' + self.image_file_name + '.db'
		self.preprocess_db_path = self.output_dir_path + os.sep + 'preprocess_' + self.image_file_name + '.db'
		self.analysis_db_path = self.output_dir_path + os.sep + 'analysis_' + self.image_file_name + '.db'
		self.extracted_files_dir_path = self.output_dir_path + os.sep + 'extracted_files'
		self.extracted_files_dir_path_slog = self.extracted_files_dir_path + os.sep + 'slog'
		self.extracted_files_dir_path_apk = self.extracted_files_dir_path + os.sep + 'apk'
		self.extracted_files_dir_path_apk_decompiled = self.extracted_files_dir_path + os.sep + 'apk_decompiled'
		self.extracted_files_dir_path_sqlitedb = self.extracted_files_dir_path + os.sep + 'format_sqlitedb'

		if os.path.exists(self.output_dir_path) == False:
			os.makedirs(self.output_dir_path)
		return self.log_file_path

#---------------------------------------------------------------------------------------------------------------
	def create_preprocess_db(self):
		if os.path.exists(self.preprocess_db_path):
			return self.preprocess_db_path
			
		list_query = list()
		query_create_image_file_info_table = "CREATE TABLE image_file_info (image_file_path TEXT, size_image INTEGER, size_alloc_area INTEGER, size_unalloc_area INTEGER, size_metadata_area INTEGER, size_apks INTEGER, size_applogs INTEGER, size_sdcard_area INTEGER)"
		query_create_permission_info_table = "CREATE TABLE permission_info (permission_name TEXT, package_name TEXT, protection INTEGER)"
		query_create_package_info_table = "CREATE TABLE package_info (flag_del INTEGER, package_name TEXT, app_name TEXT, uid_suid INTEGER, is_suid INTEGER, code_path TEXT, log_path TEXT, version INTEGER, flag_private INTEGER, dt INTEGER, ft INTEGER, it INTEGER, ut INTEGER, cnt_perms INTEGER, perms TEXT, has_updated INTEGER, category TEXT, cnt_aid INTEGER, aids TEXT)"
		query_create_updated_package_info_table = "CREATE TABLE updated_package_info (flag_del INTEGER, package_name TEXT, uid_suid INTEGER, is_suid INTEGER, code_path TEXT, version INTEGER, dt INTEGER, ft INTEGER, it INTEGER, ut INTEGER, cnt_perms INTEGER, perms TEXT)"
		query_create_aid_info_table = "CREATE TABLE aid_info (aid_name TEXT, aid INTEGER)"
		query_create_sqlitedb_info_table = "CREATE TABLE sqlitedb_info (inode INTEGER, id_package INTEGER DEFAULT 0 NOT NULL, parent_path TEXT, name TEXT, size INTEGER, ctime INTEGER, crtime INTEGER, atime INTEGER, mtime INTEGER, extracted_path TEXT)"
		query_create_apk_file_info_table = "CREATE TABLE apk_file_info (inode INTEGER, id_package INTEGER DEFAULT 0 NOT NULL, parent_path TEXT, name TEXT, size INTEGER, ctime INTEGER, crtime INTEGER, atime INTEGER, mtime INTEGER, app_name TEXT, cnt_perms INTEGER, perms TEXT, sha1 TEXT, extracted_path TEXT)"
		query_create_sqlitedb_table_preprocess_table = "CREATE TABLE sqlitedb_table_preprocess (inode INTEGER, table_name TEXT, cnt_records INTEGER, cnt_timestamp INTEGER, cnt_time_duration INTEGER, cnt_phonenumber INTEGER, cnt_account INTEGER, cnt_pwd INTEGER, cnt_url INTEGER, cnt_geodata INTEGER, cnt_ip INTEGER, cnt_mac INTEGER, cnt_digit_positive INTEGER, cnt_contents INTEGER, cnt_bin INTEGER, cnt_file INTEGER, cnt_cipher INTEGER, cnt_pkg INTEGER, timestamp TEXT, time_duration TEXT, phonenumber TEXT, account TEXT, pwd TEXT, url TEXT, geodata TEXT, ip TEXT, mac TEXT, digit_positive TEXT, contents TEXT, bin TEXT, file TEXT, cipher TEXT, pkg TEXT, last_col INTEGER)"

		list_query.append(query_create_image_file_info_table)
		list_query.append(query_create_permission_info_table)
		list_query.append(query_create_package_info_table)
		list_query.append(query_create_updated_package_info_table)
		list_query.append(query_create_aid_info_table)
		list_query.append(query_create_sqlitedb_info_table)
		list_query.append(query_create_apk_file_info_table)
		list_query.append(query_create_sqlitedb_table_preprocess_table)

		SQLite3.execute_commit_query(list_query, self.preprocess_db_path)

#---------------------------------------------------------------------------------------------------------------
	def create_analysis_db(self):
		if os.path.exists(self.analysis_db_path):
			return self.analysis_db_path

		list_query = list()
		query_create_application_list_table = "CREATE TABLE application_list (is_deleted INTEGER, category TEXT, package_name TEXT, app_name TEXT, version TEXT, installed_time INTEGER, apk_changed_time INTEGER, updated_time INTEGER, deleted_time INTEGER, fs_ctime INTEGER, fs_crtime INTEGER, fs_atime INTEGER, fs_mtime INTEGER, is_updated INTEGER, source TEXT)"
		query_create_id_password_hash_table = "CREATE TABLE id_password_hash (package_name TEXT, url TEXT, account TEXT, pwd TEXT, contents TEXT, timestamp TEXT, source TEXT)"
		query_create_call_history_table = "CREATE TABLE call_history (package_name TEXT, timestamp TEXT, time_duration TEXT, phonenumber TEXT, account TEXT, digit_positive TEXT, file TEXT, contents TEXT, source TEXT)"
		query_create_geodata_table = "CREATE TABLE geodata (package_name TEXT, timestamp TEXT, geodata TEXT, file TEXT, contents TEXT, source TEXT)"
		query_create_web_brwoser_history_table = "CREATE TABLE web_browser_history (package_name TEXT, timestamp TEXT, url TEXT, account TEXT, digit_positive TEXT, file TEXT, contents TEXT, source TEXT)"
		query_create_file_history_table = "CREATE TABLE file_history (package_name TEXT, timestamp TEXT, file TEXT, phonenumber TEXT, account TEXT, contents TEXT, source TEXT)"
		query_create_embedded_filetable = "CREATE TABLE embedded_file (is_compressed INTEGER, parent_path TEXT, name TEXT, extension TEXT, mod_time TEXT, size INTEGER, compressed_size INTEGER, CRC INTEGER, create_system TEXT, source_path TEXT, source TEXT)"

		list_query.append(query_create_application_list_table)
		list_query.append(query_create_id_password_hash_table)
		list_query.append(query_create_call_history_table)
		list_query.append(query_create_geodata_table)
		list_query.append(query_create_web_brwoser_history_table)
		list_query.append(query_create_file_history_table)
		list_query.append(query_create_embedded_filetable)

		SQLite3.execute_commit_query(list_query, self.analysis_db_path)


