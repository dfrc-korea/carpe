import pymysql
import carpe_file

class Mariadb(object):
	#To Do
	# Tune the columns
	TABLE_INFO = {
		"carpe_case_info":{"case_id":"TEXT", "case_manager":"TEXT"},
		"carpe_evidence_info":{"evidence_id":"TEXT", "c_id":"TEXT", "time_zone":"TEXT"},
		"carpe_image_info":{"image_id":"TEXT PRIMARY KEY", "e_id":"TEXT", "type":"INTEGER", "sector_size":"INTEGER", "time_zone":"TEXT", "size":"BIGINT", "hash":"TEXT", "hash_type":"TEXT"},
		"carpe_fs_info":{"partition_id":"TEXT PRIMARY KEY", "i_id":"TEXT", "fs_type":"INTEGER", "block_size":"BIGINT", "block_count":"BIGINT", "root_inum":"BIGINT", "first_inum":"BIGINT", "last_inum":"BIGINT"},
		"carpe_file":{"p_id":"TEXT", "inode":"TEXT", "name":"TEXT", "meta_seq":"BIGINT", "type":"INTEGER", "dir_type":"INTEGER", "meta_type":"INTEGER", "meta_flags":"INTEGER", "size":"BIGINT",
					"si_mtime":"BIGINT", "si_atime":"BIGINT", "si_ctime":"BIGINT", "si_etime":"BIGINT", "si_mtime_nano":"BIGINT", "si_atime_nano":"BIGINT", "si_ctime_nano":"BIGINT", "si_etime_nano":"BIGINT",
					"fn_mtime":"BIGINT", "fn_atime":"BIGINT", "fn_ctime":"BIGINT", "fn_etime":"BIGINT", "fn_mtime_nano":"BIGINT", "fn_atime_nano":"BIGINT", "fn_ctime_nano":"BIGINT", "fn_etime_nano":"BIGINT",
					"mode":"INTEGER", "uid":"INTEGER", "gid":"INTEGER", "hash":"TEXT", "parent_path":"TEXT", "extension":"TEXT"}
	}
	#To Do
	#Fill all the values
	INSERT_HELPER = {
		"carpe_evidence_info":"%s, %d, %s",
		"carpe_image_info":"",
		"carpe_fs_info":"",
		"carpe_file":"%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s"
	}

	CREATE_HELPER = {
		"carpe_case_info":"CREATE TABLE carpe_case_info (index BIGSERIAL PRIMARY KEY, case_id TEXT NOT NULL, case_manager TEXT);",
		"carpe_evidence_info":"CREATE TABLE carpe_evidence_info (index BIGSERIAL PRIMARY KEY, evidence_id TEXT NOT NULL, c_id TEXT NOT NULL time_zone TEXT NOT NULL, FOREIGN KEY(c_id) REFERENCES carpe_case_info(case_id));",
		"carpe_image_info":"CREATE TABLE carpe_image_info (index BIGSERIAL PRIMARY KEY, image_id TEXT NOT NULL, e_id TEXT NOT NULL, type INTEGER, sector_size INTEGER, time_zone TEXT, size BIGINT, hash TEXT, hash_type TEXT, FOREIGN KEY(e_id) REFERENCES carpe_evidence_info(evidence_id));",
		"carpe_fs_info":"CREATE TABLE carpe_fs_info (index BIGSERIAL PRIMARY KEY, partition_id BIGINT NOT NULL, i_id TEXT NOT NULL, block_size BIGINT NOT NULL, block_count BIGINT NOT NULL, root_inum BIGINT NOT NULL, first_inum BIGINT NOT NULL, last_inum BIGINT NOT NULL, FOREIGN KEY(i_id) REFERENCES carpe_image_info(image_id));",
		"carpe_file":"CREATE TABLE carpe_file (index BIGSERIAL PRIMARY KEY, p_id TEXT NOT NULL, inode TEXT, name TEXT NOT NULL, meta_seq BIGINT, type INTEGER, dir_type INTEGER, meta_type INTEGER, meta_flags INTEGER, size BIGINT, " +
		       							"si_mtime BIGINT, si_atime BIGINT, si_ctime BIGINT, si_etime_nano BIGINT,si_mtime_nano BIGINT, si_atime_nano BIGINT, si_ctime_nano BIGINT, si_etime_nano BIGINT, fn_mtime BIGINT, fn_atime BIGINT, fn_ctime BIGINT, fn_etime BIGINT, fn_mtime_nano BIGINT, fn_atime_nano BIGINT, fn_ctime_nano BIGINT, fn_etime_nano BIGINT, " + 
		       							"mode INTEGER, uid INTEGER, gid INTEGER, hash TEXT, hash_type TEXT, parent_path TEXT, extension TEXT, "+
		        						"FOREIGN KEY(p_id) REFERENCES carpe_fs_info(partition_id));"
	}

	# To Do 
	# query for select specific file's metadata such as inode by extension 
	PREPARED_QUERY = {		
	}

	def __init__(self):
		self._conn = None

	def open(self):
		try:
			self._conn = pymysql.connect(host='192.168.1.232', port=3306, user='test', passwd='dfrc4738', db='carpe',charset='utf8',autocommit=True)
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
			ret = self.execute_query(query)
			self.close()
			if ret[0] == 1:				
				return True
			else:
				return False
		else:
			self.open()
			return self.check_table_exist(tables)

	def initialize(self):
		self.open()
		for table_name in self.TABLE_INFO.keys():
			if not (self.check_table_exist(table_name)):
				self.execute_query(self.CREATE_HELPER[table_name])
		self.commit()
		self.close()		

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

	def insert_query_builder(self, table_name):
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
