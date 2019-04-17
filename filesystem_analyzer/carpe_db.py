import pymysql
import carpe_file


class Mariadb(object):
	TABLE_INFO = {
		"carpe_evidence_info":{"evidence_id":"TEXT PRIMARY KEY","device_id":"INTEGER", "time_zone":"TEXT"},
		"carpe_image_info":{"image_id":"TEXT PRIMARY KEY", "e_id":"TEXT", "type":"INTEGER", "sector_size":"INTEGER", "time_zone":"TEXT", "size":"INTEGER"},
		"carpe_fs_info":{"partition_id":"TEXT PRIMARY KEY", "i_id":"TEXT", "fs_type":"INTEGER", "block_size":"INTEGER", "block_count":"INTEGER", "root_inum":"INTEGER", "first_inum":"INTEGER"},
		"carpe_file":{"file_id":"INTEGER", "p_id":"TEXT", "inode":"INTEGER", "name":"TEXT", "meta_seq":"INTEGER", "type":"INTEGER", "dir_type":"INTEGER", "meta_type":"INTEGER", "meta_flags":"INTEGER", "size":"INTEGER",
					"si_mtime":"INTEGER", "si_atime":"INTEGER", "si_ctime":"INTEGER", "si_etime":"INTEGER", "si_mtime_nano":"INTEGER", "si_atime_nano":"INTEGER", "si_ctime_nano":"INTEGER", "si_etime_nano":"INTEGER",
					"fn_mtime":"INTEGER", "fn_atime":"INTEGER", "fn_ctime":"INTEGER", "fn_etime":"INTEGER", "fn_mtime_nano":"INTEGER", "fn_atime_nano":"INTEGER", "fn_ctime_nano":"INTEGER", "fn_etime_nano":"INTEGER",
					"uid":"INTEGER", "gid":"INTEGER", "hash":"TEXT", "parent_path":"TEXT", "extension":"TEXT"}
	}
	#To Do
	#Fill all the values
	INSERT_HELPER = {
		"carpe_evidence_info":"%s, %d, %s",
		"carpe_image_info":"",
		"carpe_fs_info":"",
		"carpe_file":""
	}

	# To Do 
	# query for select specific file's metadata such as inode by extension 
	PREPARED_QUERY = {		
	}


	def __init__(self):
		self._conn = None

	##To Do
	##DB Initialize (Create Table etc...)



	def open(self):
		try:
			self._conn = pymysql.connect(host='localhost', port=3306, user='test', passwd='dfrc4738', db='carpe',charset='utf8',autocommit=True)
		except Exception:
			self._conn=null
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

	def check_table_exist(self, table_name):
		if (self._conn is not None):
			query = "SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME ="+ table_name
			ret = self.execute_query(self, query)
			if ret[0] == 1:				
				return True
			else:
				return False
		else:
			self.open(self)
			return self.check_table_exist(self, tables)

	def initialize(self):
		ret = False
		for table_name in self.TABLE_INFO.keys():
			if not (self.check_table_exist(table_name)):
				#CREATE QUERY
				#CREATE TABLE tsk_image_info (obj_id BIGSERIAL PRIMARY KEY, type INTEGER, ssize INTEGER, tzone TEXT, size BIGINT, md5 TEXT, display_name TEXT, FOREIGN KEY(obj_id) REFERENCES tsk_objects(obj_id));",
				query = "CREATE TABLE {} ( e_id  TEXT PRIMARY KEY, "   

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
		if table_name in self.TABLE_INFO.keys():
			query = "INSERT INTO {0} (".format(table_name)
			query += "".join([lambda:column +") ", lambda:column+", "][column!=self.TABLE_INFO[table_name].keys()[-1]]() for column in (self.TABLE_INFO[table_name].keys()))
			query += "VALUES ({})".format(self.INSERT_HELPER[table_name])
			print (query)
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
			return -1
