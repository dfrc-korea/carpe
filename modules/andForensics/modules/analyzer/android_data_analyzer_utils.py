import os
import logging
from modules.andForensics.modules.utils.android_sqlite3 import SQLite3
import collections

logger = logging.getLogger('andForensics')
LIST_EXCEPTION_DB = list()
LIST_EXCEPTION_TABLE = list()
LIST_EXCEPTION_DB_TABLE = list()

class AnalyzerUtils(object):
	def load_exception_rule(config_file):
		if os.path.exists(config_file) == False:
			logger.error('Not exist the config file (\"%s\").' % config_file)
			return False
		try:
			f = open(config_file, 'r')
		except Exception as e:
			logger.error("Fail to open file [%s]" % config_file)
			return False

		while True:
			line = f.readline()
			if not line: break
			line = line.strip()
			if line.startswith("# ONLY DATABASE"):
				while  True:
					line = f.readline()
					if line.startswith("#"): break
					line = line.replace(" ", "")
					line = line.rstrip()
					if line != "":
						LIST_EXCEPTION_DB.append(line)						
			if line.startswith("# ONLY TABLE"):
				while  True:
					line = f.readline()
					if line.startswith("#"): break
					line = line.replace(" ", "")
					line = line.rstrip()
					if line != "":
						LIST_EXCEPTION_TABLE.append(line)
			if line.startswith("# DATABASE AND TABLE"):
				while  True:
					if not line: break
					line = f.readline()
					line = line.replace(" ", "")
					line = line.rstrip()
					if line != "":
						LIST_EXCEPTION_DB_TABLE.append(line)
		f.close()

#---------------------------------------------------------------------------------------------------------------
	def exception_rule_db_table(db_name, table_name):
		for EXCEPTION_DB in LIST_EXCEPTION_DB:
			if db_name == EXCEPTION_DB:
				return True
		for EXCEPTION_TABLE in LIST_EXCEPTION_TABLE:
			if table_name == EXCEPTION_TABLE:
				return True
		for EXCEPTION_DB_TABLE in LIST_EXCEPTION_DB_TABLE:
			db = EXCEPTION_DB_TABLE.split(",")[0]
			table = EXCEPTION_DB_TABLE.split(",")[1]
			if (db_name == db) & (table_name == table):
				return True

#---------------------------------------------------------------------------------------------------------------
	def get_package_name(id_package, parent_path, case):
		if id_package == 0:
			if parent_path.startswith("/system/"):
				return "SYSTEM_LOG"
			else:
				return "UNKNOWN_APP"

		query = 'SELECT count(*) FROM package_info as pi WHERE pi.uid_suid = %d' % id_package
		cnt_records = SQLite3.execute_fetch_query(query, case.preprocess_db_path)[0]
		if cnt_records == 1:
			query = 'SELECT pi.package_name FROM package_info as pi WHERE pi.uid_suid = %d' % id_package
			return SQLite3.execute_fetch_query(query, case.preprocess_db_path)[0]
		else:
			if (parent_path.startswith("/data/") & parent_path.endswith("/databases/")):			
				tmp = parent_path.split("/")[2]
				query = 'SELECT DISTINCT package_name FROM package_info WHERE package_name = "%s" and uid_suid = %d' % (tmp, id_package)
				list_ret = SQLite3.execute_fetch_query_multi_values(query, case.preprocess_db_path)
				if len(list_ret) == 1:
					return tmp
				else:
					query = 'SELECT DISTINCT package_name FROM package_info WHERE package_name = "%s"' % tmp
					list_ret = SQLite3.execute_fetch_query_multi_values(query, case.preprocess_db_path)
					if len(list_ret) == 1:
						return tmp
					else:
						return "UNKNOWN_APP"
			elif parent_path.startswith("/data/"):
				tmp = parent_path.split("/")[2]
				query = 'SELECT DISTINCT package_name FROM package_info WHERE package_name = "%s" and uid_suid = %d' % (tmp, id_package)
				list_ret = SQLite3.execute_fetch_query_multi_values(query, case.preprocess_db_path)
				if len(list_ret) == 1:
					return tmp
				else:
					query = 'SELECT DISTINCT package_name FROM package_info WHERE package_name = "%s"' % tmp
					list_ret = SQLite3.execute_fetch_query_multi_values(query, case.preprocess_db_path)
					if len(list_ret) == 1:
						return tmp
					else:
						return "UNKNOWN_APP"
			elif parent_path.endswith("/databases/"):
				tmp = parent_path.split("/")[-3]
				query = 'SELECT DISTINCT package_name FROM package_info WHERE package_name = "%s" and uid_suid = %d' % (tmp, id_package)
				list_ret = SQLite3.execute_fetch_query_multi_values(query, case.preprocess_db_path)
				if len(list_ret) == 1:
					return tmp
				else:
					query = 'SELECT DISTINCT package_name FROM package_info WHERE package_name = "%s"' % tmp
					list_ret = SQLite3.execute_fetch_query_multi_values(query, case.preprocess_db_path)
					if len(list_ret) == 1:
						return tmp
					else:
						return "UNKNOWN_APP"
			else:
				return "UNKNOWN_APP"

#---------------------------------------------------------------------------------------------------------------
	def get_userinfo_type_format_value_from_sqlitedb(dic_userinfo_record, dic_userinfo_cnt, not_null_userinfo_type):
		list_userinfo_type = list()
		list_col_name = list()
		list_value_format = list()
		list_idx_col = list()
		list_not_null_col = list()

		for userinfo_type, cnt_userinfo in dic_userinfo_cnt.items():
			for i in range(cnt_userinfo):
				list_userinfo_type.append(userinfo_type)
				userinfo_record = dic_userinfo_record[userinfo_type].split(",")[i]				
				list_col_name.append(userinfo_record.split("(")[0])

				col_name = userinfo_record.split("(")[0]
				if userinfo_type == not_null_userinfo_type:
					list_not_null_col.append(col_name)

				list_value_format.append(userinfo_record.split("(")[1].replace(")",""))
				list_idx_col.append(userinfo_record.split("(")[2].replace(")",""))

		query_select_contents = ""
		if len(list_col_name) == 1:
			query_select_contents += list_col_name[0]
		else:
			for col_name in list_col_name:
				query_select_contents += "\"" + col_name + "\", "
			query_select_contents = query_select_contents[:-2]

		query_where_not_null = ""
		for not_null_col in list_not_null_col:
			query_where_not_null += not_null_col + " !=\"\" or "
		query_where_not_null = query_where_not_null[:-3]


		query = 'SELECT DISTINCT %s FROM \"%s\" WHERE %s' % (query_select_contents, dic_userinfo_record['table_name'], query_where_not_null)
		list_userinfo_col_value = SQLite3.execute_fetch_query_multi_values(query, dic_userinfo_record['db_path'])
		return list_userinfo_type, list_value_format, list_col_name, list_userinfo_col_value

#---------------------------------------------------------------------------------------------------------------
	def compose_col_value_to_insert(dic_userinfo_record, list_userinfo_type, list_value_format, list_col_name, list_userinfo_col_value, case, table_name_to_insert):		
		counter = collections.Counter(list_userinfo_type)

		if list_userinfo_col_value == False:
			logger.error("False!!! dic_userinfo_record: ", dic_userinfo_record) 
			return False

		for idx_col in range(len(list_userinfo_col_value)):
			dic_userinfo_type_value = dict.fromkeys(counter)

			for idx_userinfo in range(len(list_userinfo_type)):
				col_userinfo_type = list_userinfo_type[idx_userinfo]
				col_name = list_col_name[idx_userinfo]
				col_format = list_value_format[idx_userinfo]
				col_value = str(list_userinfo_col_value[idx_col][idx_userinfo])
				col_value = col_value.replace("\n", "")
				col_value = col_value.replace("\t", " ")
				col_value = col_value.replace("\"", "\"\"")
				col_value = col_value.replace("\'", "\'\'")
				col_value = col_value.replace("\x00", "")

				if col_value == "None":
					col_value = ""
				if (col_value != "None") | (col_value != ""):
					col_value += "(" + col_name + ":" + col_format + ")"

				before_value = dic_userinfo_type_value.get(list_userinfo_type[idx_userinfo])
				if before_value == None:
					dic_userinfo_type_value[list_userinfo_type[idx_userinfo]] = col_value
				else:
					dic_userinfo_type_value[list_userinfo_type[idx_userinfo]] = before_value + "|" + col_value

			query_col_name = ""
			query_col_value = ""
			list_query_col_name = list(dic_userinfo_type_value.keys())
			for i in range(len(list_query_col_name)):
				query_col_name += "\"" + list_query_col_name[i] + "\", "
				query_col_value += "\"" + dic_userinfo_type_value[list_query_col_name[i]] + "\", "
			query_col_name = query_col_name[:-2]
			query_col_value = query_col_value[:-2]
			package_name = dic_userinfo_record['package_name']
			source = str(dic_userinfo_record['inode']) + "(" + str(dic_userinfo_record['table_name']) + ")"

			query = 'INSERT INTO %s(%s, package_name, source) VALUES(%s, "%s", "%s")' % (table_name_to_insert, query_col_name, query_col_value, package_name, source)
			SQLite3.execute_commit_query(query, case.analysis_db_path)


