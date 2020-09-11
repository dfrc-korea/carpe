import os
import logging
from modules.andForensics.modules.utils.android_sqlite3 import SQLite3
import re

logger = logging.getLogger('andForensics')

RE_PACKAGENAME = '^[a-zA-Z0-9]*\.[a-zA-Z0-9]*.?[a-zA-Z0-9]*.?[a-zA-Z0-9]*.?[a-zA-Z0-9]*.?[a-zA-Z0-9]*.?[a-zA-Z0-9]*.?[a-zA-Z0-9]*$'

class ApplicationList(object):
	def analyze_applist(case):
		# from system logs
		query = "SELECT pi.category, pi.package_name, pi.app_name, pi.version, pi.it, pi.ft, pi.ut, pi.dt, pi.has_updated FROM package_info as pi"
		list_package = SQLite3.execute_fetch_query_multi_values(query, case.preprocess_db_path)
		if (list_package == False) | (list_package == []):
			logger.error('The image has no package information.')
			return False
		
		query_inode = "SELECT meta_addr FROM tsk_files WHERE parent_path = '/system/' and name = 'packages.xml'"
		inode_packages_xml = SQLite3.execute_fetch_query(query_inode, case.load_db_path)[0]
		query_inode = "SELECT meta_addr FROM tsk_files WHERE parent_path = '/system/' and name = 'packages.list'"
		inode_packages_list = SQLite3.execute_fetch_query(query_inode, case.load_db_path)[0]
		source = str(inode_packages_xml) + "," + str(inode_packages_list)

		for package_info in list_package:
			is_deleted = 0
			category = package_info[0]
			package_name = package_info[1]
			app_name = package_info[2]
			version = package_info[3]
			it = package_info[4]
			ft = package_info[5]
			up = package_info[6]
			dt = package_info[7]
			is_updated = package_info[8]
			query = 'INSERT INTO application_list(is_deleted, category, package_name, app_name, version, installed_time, apk_changed_time, updated_time, deleted_time, fs_ctime, fs_crtime, fs_atime, fs_mtime, is_updated, source) VALUES (%d, "%s", "%s", "%s", "%s", %d, %d, %d, %d, %d, %d, %d, %d, %d, "%s")' % (is_deleted, category, package_name, app_name, version, it, ft, up, dt, 0, 0, 0, 0, is_updated, source)
			SQLite3.execute_commit_query(query, case.analysis_db_path)

		# from system logs2
		query = "SELECT upi.package_name, upi.version, upi.it, upi.ft, upi.ut, upi.dt FROM updated_package_info as upi"
		list_updated_package = SQLite3.execute_fetch_query_multi_values(query, case.preprocess_db_path)
		if (list_updated_package != False) & (list_updated_package != []):
			for updated_package_info in list_updated_package:
				# print(updated_package_info)
				is_deleted = 0
				up_package_name = updated_package_info[0]
				up_version = updated_package_info[1]
				up_it = updated_package_info[2]
				up_ft = updated_package_info[3]
				up_ut = updated_package_info[4]
				up_dt = updated_package_info[5]

				for package_info in list_package:
					if up_package_name == package_info[1]:
						up_category = package_info[0]
						up_app_name = package_info[2]
						up_is_updated = 0
						query = 'INSERT INTO application_list(is_deleted, category, package_name, app_name, version, installed_time, apk_changed_time, updated_time, deleted_time, fs_ctime, fs_crtime, fs_atime, fs_mtime, is_updated, source) VALUES (%d, "%s", "%s", "%s", "%s", %d, %d, %d, %d, %d, %d, %d, %d, %d, "%s")' % (1, up_category, up_package_name, up_app_name, up_version, up_it, up_ft, up_ut, up_dt, 0, 0, 0, 0, up_is_updated, source)
						SQLite3.execute_commit_query(query, case.analysis_db_path)

		# from filesystem /data/[package_name]
		query = "SELECT name, ctime, crtime, atime, mtime, meta_addr FROM tsk_files WHERE type = 0 and dir_flags != 2 and dir_type = 3 and parent_path = '/data/' and size = 4096 and (name != '.' and name != '..' and name != 'media' and name != '.drm')"
		list_fs_package = SQLite3.execute_fetch_query_multi_values(query, case.load_db_path)
		if (list_fs_package != False) & (list_fs_package != []):
			for fs_package_info in list_fs_package:
				fs_package_name = fs_package_info[0]
				fs_ctime = fs_package_info[1]
				fs_crtime = fs_package_info[2]
				fs_atime = fs_package_info[3]
				fs_mtime = fs_package_info[4]
				inode = fs_package_info[5]

				query = 'SELECT count(*) FROM application_list WHERE package_name = "%s" and (is_updated = 1 or is_updated = 0)' % fs_package_name
				cnt_records = SQLite3.execute_fetch_query(query, case.analysis_db_path)[0]
				if cnt_records == 0:
					query = 'INSERT INTO application_list(is_deleted, category, package_name, app_name, version, installed_time, apk_changed_time, updated_time, deleted_time, fs_ctime, fs_crtime, fs_atime, fs_mtime, is_updated, source) VALUES (%d, "%s", "%s", "%s", "%s", %d, %d, %d, %d, %d, %d, %d, %d, %d, "%s")' % (1, "", fs_package_name, "", "", 0, 0, 0, 0, fs_ctime, fs_crtime, fs_atime, fs_mtime, 0, inode)
					SQLite3.execute_commit_query(query, case.analysis_db_path)
				else:
					if cnt_records == 1:
						query = 'UPDATE application_list set fs_ctime = %d, fs_crtime = %d, fs_atime = %d, fs_mtime = %d WHERE package_name = "%s"' % (fs_ctime, fs_crtime, fs_atime, fs_mtime, fs_package_name)
					else:
						query = 'UPDATE application_list set fs_ctime = %d, fs_crtime = %d, fs_atime = %d, fs_mtime = %d WHERE package_name = "%s" and is_updated = 1' % (fs_ctime, fs_crtime, fs_atime, fs_mtime, fs_package_name)
					SQLite3.execute_commit_query(query, case.analysis_db_path)

		# from filesystem sdcard e.g., /media/0/Android/[package_name]
		query = "SELECT name, ctime, crtime, atime, mtime, meta_addr FROM tsk_files WHERE type = 0 and dir_flags != 2 and dir_type = 3 and parent_path LIKE '%/Android/data/' and size = 4096 and (name != '.' and name != '..' and name != 'media' and name != '.drm')"
		list_fs_package = SQLite3.execute_fetch_query_multi_values(query, case.load_db_path)
		if (list_fs_package != False) & (list_fs_package != []):
			for fs_package_info in list_fs_package:
				fs_package_name = fs_package_info[0]
				fs_package_name = "%s" % fs_package_name
				if (fs_package_name.count('.') >= 1) & (fs_package_name.count('.') <= 7) & (len(fs_package_name) <= 60) & (fs_package_name.count(' ') == 0):
					if re.match(RE_PACKAGENAME, fs_package_name):
						fs_ctime = fs_package_info[1]
						fs_crtime = fs_package_info[2]
						fs_atime = fs_package_info[3]
						fs_mtime = fs_package_info[4]
						inode = fs_package_info[5]

						query = 'SELECT count(*) FROM application_list WHERE package_name = "%s" and (is_updated = 1 or is_updated = 0)' % fs_package_name
						cnt_records = SQLite3.execute_fetch_query(query, case.analysis_db_path)[0]
						if cnt_records == 0:							
							query = 'INSERT INTO application_list(is_deleted, category, package_name, app_name, version, installed_time, apk_changed_time, updated_time, deleted_time, fs_ctime, fs_crtime, fs_atime, fs_mtime, is_updated, source) VALUES (%d, "%s", "%s", "%s", "%s", %d, %d, %d, %d, %d, %d, %d, %d, %d, "%s")' % (1, "", fs_package_name, "", "", 0, 0, 0, 0, fs_ctime, fs_crtime, fs_atime, fs_mtime, 0, inode)
							SQLite3.execute_commit_query(query, case.analysis_db_path)
				else:
					continue

