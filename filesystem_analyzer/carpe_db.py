import pymysql
import carpe_file


class Mariadb(object):
	TABLE_INFO = [
		"carpe_image_info":["i_id", "type", "sector_size", "tzone", "size"],
		"carpe_fs_info":["p_id", "fs_type", "block_size", "block_count", "root_inum", "first_inum"],
		"carpe_file":["p_id", "inode", "name", "meta_seq", "type", "dir_type", "meta_type", "meta_flags", "size",
					"si_mtime", "si_atime", "si_ctime", "si_etime", "si_mtime_nano", "si_atime_nano", "si_ctime_nano", "si_etime_nano",
					"fn_mtime", "fn_atime", "fn_ctime", "fn_etime", "fn_mtime_nano", "fn_atime_nano", "fn_ctime_nano", "fn_etime_nano",
					"uid", "gid", "hash", "parent_path", "extension"]
	]

	def __init__(self):
		self._conn = None

	def open(self):
		try:
			self._conn = pymysql.connect(host='localhost', port=3306, user='test', passwd='dfrc4738', db='carpe',charset='utf8',autocommit=True)
		except Exception:
			conn=null
			print("db connection error")

	def commit(self):
		try:
			self._conn.commit()
		except Exception:
			print("db commit error")

	def close(self):
		try:
			self._conn.close()
		except Exception:
			print("db connection close error")
			
	def files_object(self, files):
		print(files)

	def bulk_execute(self, query, values):
		try:
			cursor = self._conn.cursor()
		except Exception:
			print("db cursor error")
			return -1
		try:
			cursor.executemany(query, values)
			#cursor.executemany
			data = cursor.fetchone()
			cursor.close()
			return data			
		except Exception:
			print("db execution error")
			return -1


	##To Do
	##Place_holder method implementation	
	def insert_query_builder(self, table_name, columns):
		if table_name in TABLE_INFO.keys():
			query = "INSERT INTO {0} ({1}) VALUES ({2})".format(table_name, TABLE_INFO[table_name], place_holders)

		return query

	def execute_query(self, query):
		cursor = self._conn.cursor()
		try:
			cursor.execute(query)
			#cursor.executemany
			data = cursor.fetchone()
			cursor.close()
			return data
		except Exception:
			print("db execution error")
			return "error"
