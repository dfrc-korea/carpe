#-*- coding: utf-8 -*-
import os
import logging
import xml.etree.ElementTree as ET
from modules.andForensics.modules.utils.android_sqlite3 import SQLite3
from modules.andForensics.modules.utils.android_TSK import TSK

logger = logging.getLogger('andForensics')
#APP_PACKAGE_CONF_PATH = os.getcwd() + os.sep + 'config' + os.sep + 'APP_PACKAGE.conf'
APP_PACKAGE_CONF_PATH = '/home/byeongchan/modules/andForensics/config/APP_PACKAGE.conf'
#AID_CONF_PATH = os.getcwd() + os.sep + 'config' + os.sep + 'AID_DEFINE.conf'
AID_CONF_PATH = '/home/byeongchan/modules/andForensics/config/AID_DEFINE.conf'
AID_DEFINE_START = "#define AID_"

SYSTEM_PACKAGES_XML_PARENT_PATH = "/system/"
SYSTEM_PACKAGES_XML_NAME = "packages.xml"
SYSTEM_PACKAGES_LIST_PARENT_PATH = "/system/"
SYSTEM_PACKAGES_LIST_NAME = "packages.list"

class SystemLog(object):
	def parsing_aid_information(preprocess_db_path):
		if not os.path.exists(AID_CONF_PATH):
			logger.error('Not exist the config (\"%s\").' % AID_CONF_PATH)
			return False
			
		try:
			f = open(AID_CONF_PATH, 'r')
		except Exception as e:
			logger.error("Fail to open file [%s]" % AID_CONF_PATH)
			return False

		lines = f.readlines()
		for line in lines:
			if line.startswith(AID_DEFINE_START):
				args = line.split(' ')
				aid_name = args[1]
				aid = args[2]

				query = 'INSERT INTO aid_info(aid_name, aid) VALUES("%s", %d)' % (aid_name, int(aid))
				SQLite3.execute_commit_query(query, preprocess_db_path)
		f.close()

#---------------------------------------------------------------------------------------------------------------
	def	parsing_packages_list(packages_list, preprocess_db_path):
		try:
			f = open(packages_list, 'r')
		except Exception as e:
			logger.error("Fail to open file [%s]" % packages_list)
			return False
		
		lines = f.readlines()
		for line in lines:
			args = line.split(' ')
			cnt_args = len(args)
			if cnt_args >= 4:
				package_name = args[0]
				uid_suid = args[1]
				unknown = args[2]
				log_path = args[3]

				category = ""
				cnt_aid = 0
				aids = ""
				if cnt_args >= 5:
					category = args[4]
					if category.find(":") != False:
						category = category.split(":")[0]
					if cnt_args >= 6:
						aids = args[5]
						if aids != 'none\n':
							cnt_aid = len(aids.split(','))
						else:
							aids = ""

				query = 'UPDATE package_info set log_path = "%s", category = "%s", cnt_aid = %d, aids = "%s" WHERE uid_suid = %d and package_name = "%s"' % (log_path, category, int(cnt_aid), aids, int(uid_suid), package_name)
				SQLite3.execute_commit_query(query, preprocess_db_path)
		f.close()

#---------------------------------------------------------------------------------------------------------------
	def	parsing_updated_package(updated_package, preprocess_db_path):
		has_updated 	= 1
		package_name	= updated_package.get('name')
		code_path		= updated_package.get('codePath')
		if updated_package.get('dt'):
			dt = int(updated_package.get('dt'), 16)/1000
		else:
			dt = 0

		ft = int(updated_package.get('ft'), 16)/1000
		it = int(updated_package.get('it'), 16)/1000
		ut = int(updated_package.get('ut'), 16)/1000
		version	= int(updated_package.get('version'))
		if updated_package.get('userId'):
			uid_suid = int(updated_package.get('userId'))
			is_suid = 0
		elif updated_package.get('sharedUserId'):
			uid_suid = int(updated_package.get('sharedUserId'))
			is_suid = 1
		
		ret_perms = SystemLog.get_package_permission(updated_package, preprocess_db_path)
		cnt_perms	= ret_perms[0]
		perms_value = str(ret_perms[1])
		flag_del = 0

		query = 'UPDATE package_info set has_updated = %d WHERE uid_suid = %d' % (int(has_updated), int(uid_suid))
		SQLite3.execute_commit_query(query, preprocess_db_path)

		query = 'INSERT INTO updated_package_info(flag_del, package_name, code_path, dt, ft, it, ut, version, uid_suid, is_suid, cnt_perms, perms) VALUES(%d, "%s", "%s", %d, %d, %d, %d, %d, %d, %d, %d, "%s")' % (int(flag_del), package_name, code_path, int(dt), int(ft), int(it), int(ut), int(version), int(uid_suid), int(is_suid), int(cnt_perms), perms_value)
		SQLite3.execute_commit_query(query, preprocess_db_path)

#---------------------------------------------------------------------------------------------------------------
	def get_permission_id(name, preprocess_db_path):
		query = 'SELECT rowid FROM permission_info WHERE permission_name = "%s"' % name
		ret = SQLite3.execute_fetch_query(query, preprocess_db_path)
		if ret:
			return ret[0]
		else:
			return False

#---------------------------------------------------------------------------------------------------------------
	def get_package_permission(package, preprocess_db_path):
		cnt_perms = 0
		perms_value = ""

		for perms in package.iter('perms'):
			for item in perms.iter('item'):
				name = item.get('name')
				perms_id = SystemLog.get_permission_id(name, preprocess_db_path)

				if perms_id != 0:
					if perms_value == "":
						perms_value = str(perms_id)
					else:
						perms_value += ","
						perms_value += str(perms_id)
				else:
					query = 'INSERT INTO permission_info(permission_name) VALUES("%s")' % (name)
					SQLite3.execute_commit_query(query, preprocess_db_path)

					perms_id = SystemLog.get_permission_id(name, preprocess_db_path)
					if perms_value == "":
						perms_value = str(perms_id)
					else:
						perms_value = perms_value + "," + str(perms_id)
				cnt_perms += 1
		return cnt_perms, perms_value

#---------------------------------------------------------------------------------------------------------------
	def get_custom_app_name(preprocess_db_path):
		if not os.path.exists(APP_PACKAGE_CONF_PATH):
			logger.error('Not exist the config (\"%s\").' % APP_PACKAGE_CONF_PATH)
			return False
		try:
			f = open(APP_PACKAGE_CONF_PATH, 'r')
		except Exception as e:
			logger.error("Fail to open file [%s]" % APP_PACKAGE_CONF_PATH)
			return False

		lines = f.readlines()
		for line in lines:
			if not line: break
			line = line.strip()
			line = line.replace(" ", "")
			line = line.replace("\t", "")

			package_name = line.split(",")[0]
			app_name = line.split(",")[1]
			query = 'SELECT app_name FROM package_info WHERE package_name = "%s"' % package_name

			ret = SQLite3.execute_fetch_query(query, preprocess_db_path)			
			if ret != None:
				if ret[0] == "":
					query = 'UPDATE package_info set app_name = "%s" WHERE package_name = "%s"' % (app_name, package_name)
					SQLite3.execute_commit_query(query, preprocess_db_path)
		f.close()

#---------------------------------------------------------------------------------------------------------------
	def parsing_package(package, preprocess_db_path):
		package_name = package.get('name')
		code_path = package.get('codePath')
		app_name = ""
		if code_path.startswith('/system/'):
			app_name = code_path.split('/')[-1]
		flag_private = 0

		if package.get('privateFlags'):
			flag_private = int(package.get('privateFlags'))
		if package.get('dt'):
			dt = int(package.get('dt'), 16)/1000
		else:
			dt = 0
		
		ft = int(package.get('ft'), 16)/1000
		it = int(package.get('it'), 16)/1000
		ut = int(package.get('ut'), 16)/1000
		version = int(package.get('version'))

		if package.get('userId'):
			uid_suid = int(package.get('userId'))
			is_suid = 0
		elif package.get('sharedUserId'):
			uid_suid = int(package.get('sharedUserId'))
			is_suid = 1

		ret_perms = SystemLog.get_package_permission(package, preprocess_db_path)
		cnt_perms = ret_perms[0]
		perms_value = str(ret_perms[1])
		has_updated = 0
		flag_del = 0

		query = 'INSERT INTO package_info(flag_del, package_name, app_name, code_path, flag_private, dt, ft, it, ut, version, uid_suid, is_suid, cnt_perms, perms, has_updated) VALUES(%d, "%s", "%s", "%s", %d, %d, %d, %d, %d, %d, %d, %d, %d, "%s", %d)' % (flag_del, package_name, app_name, code_path, int(flag_private), int(dt), int(ft), int(it), int(ut), int(version), int(uid_suid), int(is_suid), int(cnt_perms), perms_value, int(has_updated))
		SQLite3.execute_commit_query(query, preprocess_db_path)

#---------------------------------------------------------------------------------------------------------------
	def parsing_permissions(permissions, preprocess_db_path):
		for item in permissions.iter('item'):
			permission_name = item.get('name')
			package_name = item.get('package')			

			if item.get('protection'):
				protection = int(item.get('protection'))
			else:
				protection = 0

			query = 'INSERT INTO permission_info(permission_name, package_name, protection) VALUES("%s", "%s", %d)' % (permission_name, package_name, int(protection))
			SQLite3.execute_commit_query(query, preprocess_db_path)

#---------------------------------------------------------------------------------------------------------------
	def parsing_packages_xml(file_path, preprocess_db_path):
		tree = ET.parse(file_path)
		root = tree.getroot()

		# permission
		for permissions in root.iter('permissions'):
			SystemLog.parsing_permissions(permissions, preprocess_db_path)
		# package
		for package in root.iter('package'):
			SystemLog.parsing_package(package, preprocess_db_path)
		SystemLog.get_custom_app_name(preprocess_db_path)
		# updated-package
		for updated_package in root.iter('updated-package'):
			SystemLog.parsing_updated_package(updated_package, preprocess_db_path)

#---------------------------------------------------------------------------------------------------------------
	def get_list_system_log():
		list_dic_system_log = list()
		dic_system_log = {'parent_path':SYSTEM_PACKAGES_XML_PARENT_PATH, 'name':SYSTEM_PACKAGES_XML_NAME}
		list_dic_system_log.append(dic_system_log)
		dic_system_log = {'parent_path':SYSTEM_PACKAGES_LIST_PARENT_PATH, 'name':SYSTEM_PACKAGES_LIST_NAME}
		list_dic_system_log.append(dic_system_log)
		return list_dic_system_log

#---------------------------------------------------------------------------------------------------------------
	def extract_system_log_information(case):
		list_dic_system_log = SystemLog.get_list_system_log()

		for dic_system_log in list_dic_system_log:
			query = 'SELECT meta_addr FROM tsk_files WHERE parent_path = "%s" and name = "%s"' % (dic_system_log['parent_path'], dic_system_log['name'])
			ret = SQLite3.execute_fetch_query(query, case.load_db_path)

			if ret == False:
				logger.error('Not exist the system log file(\"%s\").' % dic_system_log['parent_path'] + dic_system_log['name'])
			else:
				extracted_files_dir_path_slog = case.extracted_files_dir_path_slog + dic_system_log['parent_path'].replace("/", os.sep)
				if os.path.exists(extracted_files_dir_path_slog) == False:
					os.makedirs(extracted_files_dir_path_slog)

				extracted_files_path_slog = extracted_files_dir_path_slog + dic_system_log['name']
				inode = ret[0]

				if TSK.icat_for_extract_file(case.image_file_path, inode, extracted_files_path_slog):
					if os.path.basename(extracted_files_path_slog) == "packages.xml":
						logger.info('    - Extracting the system log information (/data/system/packages.xml)...')
						SystemLog.parsing_packages_xml(extracted_files_path_slog, case.preprocess_db_path)
					elif os.path.basename(extracted_files_path_slog) == "packages.list":
						SystemLog.parsing_packages_list(extracted_files_path_slog, case.preprocess_db_path)
						logger.info('    - Extracting the system log information (/data/system/packages.list)...')
				else:
					logger.error('System log extraction failed(%s).' % (dic_system_log['parent_path'] + dic_system_log['name']))

		logger.info('    - Extracting the AID information...')
		SystemLog.parsing_aid_information(case.preprocess_db_path)
		