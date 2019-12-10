import pymysql
import carpe_file

class Mariadb(object):
	#To Do
	# Tune the columns
	TABLE_INFO = {

		"carpe_block_info":{"p_id":"varchar", "block_start":"BIGINT", "block_end":"BIGINT"},
		"carpe_case_info":{"case_id":"BIGINT PRIMARY KEY", "case_no":"TEXT", "case_name":"TEXT", "administrator":"TEXT", "create_date":"DATETIME", "description":"TEXT"},
		"investigator":{"id":"TEXT PRIMARY KEY", "name":"TEXT", "password":"TEXT", "acl":"TEXT"},
		"carpe_evidence_info":{"evd_id":"BIGINT PRIMARY KEY", "evd_no":"TEXT", "c_id":"BIGINT", "type1":"TEXT", "type2":"TEXT", "added_date":"DATETIME", "md5":"TEXT", "sha1":"TEXT", "sha256":"TEXT", "path":"TEXT", "time_zone":"TEXT"},
		"carpe_partition_info":{"par_id":"BIGINT PRIMARY KEY", "par_name":"TEXT", "par_path":"TEXT", "e_id":"BIGINT", "type":"INTEGER", "sector_size":"INTEGER", "size":"INTEGER", "sha1":"TEXT", "sha256":"TEXT", "time_zone":"TEXT"},
		"carpe_fs_info":{"p_id":"varchar(20)", "block_size":"BIGINT", "block_count":"BIGINT", "root_inum":"BIGINT", "first_inum":"BIGINT", "last_inum":"BIGINT"},
		"file_info":{"par_id":"BIGINT", "file_id":"BIGINT", "inode":"TEXT", "name":"TEXT", "meta_seq":"BIGINT", "type":"INTEGER", "dir_type":"INTEGER", "meta_type":"INTEGER", "meta_flags":"INTEGER", "size":"BIGINT",
					"si_mtime":"BIGINT", "si_atime":"BIGINT", "si_ctime":"BIGINT", "si_etime":"BIGINT", "si_mtime_nano":"BIGINT", "si_atime_nano":"BIGINT", "si_ctime_nano":"BIGINT", "si_etime_nano":"BIGINT",
					"fn_mtime":"BIGINT", "fn_atime":"BIGINT", "fn_ctime":"BIGINT", "fn_etime":"BIGINT", "fn_mtime_nano":"BIGINT", "fn_atime_nano":"BIGINT", "fn_ctime_nano":"BIGINT", "fn_etime_nano":"BIGINT",
					"mode":"INTEGER", "uid":"INTEGER", "gid":"INTEGER", "md5":"TEXT", "parent_path":"TEXT", "extension":"TEXT", "parent_id":"BIGINT"}
	}
	#To Do
	#Fill all the values
	INSERT_HELPER = {
		"carpe_case_info":"%s, %s, %s, %s, %s, %s",
		"investigator":"%s, %s, %s, %s",
		"carpe_evidence_info":"%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s",
		"carpe_partition_info":"%s, %s, %s, %s, %d, %d, %s, %d, %d, %d",
		"carpe_fs_info":"%s, %s, %s, %s, %s, %s, %s",
		#"carpe_file":"%s, %s, %s, %s, %s, %d, %d, %d, %d, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %d, %d, %d, %s, %s, %s, %s"
		#"carpe_file":"%d, %s, %d, %d, %d, %d, %d, %d, %d, %d, %d, %d, %s, %d, %s, %d, %d, %d, %d, %s, %s, %d, %d, %d, %d, %d, %d, %d, %d, %d, %d, %d"
		"carpe_file":"%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s"
	}

	CREATE_HELPER = {
		"carpe_case_info":"CREATE TABLE carpe_case_info (case_id BIGINT NOT NULL AUTO_INCREMENT, case_no TEXT NOT NULL, case_name TEXT NOT NULL, administrator TEXT NOT NULL, create_date DATETIME NOT NULL, description TEXT NULL, PRIMARY KEY(case_id));",
		"investigator":"CREATE TABLE investigator (id varchar(255) NOT NULL, name varchar(100) NOT NULL, password varchar(100) NOT NULL, acl TEXT NULL, PRIMARY KEY(id));",
		"carpe_evidence_info":"CREATE TABLE carpe_evidence_info (evd_id BIGINT NOT NULL AUTO_INCREMENT, evd_no TEXT NOT NULL, c_id BIGINT NOT NULL, type1 TEXT NOT NULL, type2 TEXT NOT NULL, added_date DATETIME NULL, md5 TEXT NULL, sha1 TEXT NULL, sha256 TEXT NULL, path TEXT NULL, time_zone TEXT NULL, PRIMARY KEY(evd_id), FOREIGN KEY(c_id) REFERENCES carpe_case_info(case_id));",
		"carpe_partition_info":"CREATE TABLE carpe_partition_info (par_id BIGINT NOT NULL AUTO_INCREMENT, par_name TEXT NOT NULL, par_path TEXT NOT NULL, e_id BIGINT NOT NULL, type INTEGER, sector_size INTEGER, size BIGINT, sha1 TEXT, sha256 TEXT, time_zone TEXT, PRIMARY KEY(par_id), FOREIGN KEY(e_id) REFERENCES carpe_evidence_info(evd_id));",
		"carpe_fs_info":"CREATE TABLE carpe_fs_info (fs_id BIGINT NOT NULL AUTO_INCREMENT, p_id BIGINT NOT NULL, block_size BIGINT NOT NULL, block_count BIGINT NOT NULL, root_inum BIGINT NOT NULL, first_inum BIGINT NOT NULL, last_inum BIGINT NOT NULL, PRIMARY KEY(fs_id), FOREIGN KEY(p_id) REFERENCES carpe_partition_info(par_id));",
		"carpe_file":"CREATE TABLE carpe_file (id BIGINT NOT NULL AUTO_INCREMENT, par_id BIGINT NOT NULL, inode TEXT, name TEXT NOT NULL, meta_seq BIGINT, type INTEGER, dir_type INTEGER, meta_type INTEGER, meta_flags INTEGER, size BIGINT, si_mtime BIGINT, si_atime BIGINT, si_ctime BIGINT, si_etime BIGINT, si_mtime_nano BIGINT, si_atime_nano BIGINT, si_ctime_nano BIGINT, si_etime_nano BIGINT, fn_mtime BIGINT, fn_atime BIGINT, fn_ctime BIGINT, fn_etime BIGINT, fn_mtime_nano BIGINT, fn_atime_nano BIGINT, fn_ctime_nano BIGINT, fn_etime_nano BIGINT, mode INTEGER, uid INTEGER, gid INTEGER, hash TEXT, hash_type TEXT, parent_path TEXT, extension TEXT, PRIMARY KEY(id), FOREIGN KEY(par_id) REFERENCES carpe_partition_info(par_id));",
		"datamap":"create table datamap (blk_num bigint not null, block_id bigint(20), blk_type char(10) default null, blk_sig char(10) default null, blk_alloc bool default 0, blk_stat char(20) default null, primary key(blk_num), foreign key  (block_id) references carpe_block_info (id))"
	}

	# To Do 
	# query for select specific file's metadata such as inode by extension 
	PREPARED_QUERY = {		
	}

	def __init__(self):
		self._conn = None

	def open(self):
		try:
			self._conn = pymysql.connect(host='127.0.0.1', port=23306, user='root',
                        passwd='dfrc4738', db='carpe',charset='utf8',autocommit=True)
		except Exception:
			self._conn=None
			print("db connection error")

	def i_open(self,ip,port,user,pw,db):
		try:
			self._conn = pymysql.connect(host=ip, port=port, user=user, passwd=pw, db=db,charset='utf8',autocommit=True)
			return self._conn.cursor()
		except Exception:
			self._conn=None
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
			cursor.executemany(query, values)
			data = cursor.fetchall()
			cursor.close()
			return data			
		except Exception:
			print(query)
			print("db execution error")
			return -1

	def insert_query_builder(self, table_name):
		if table_name in self.TABLE_INFO.keys():
			query = "INSERT INTO {0} (".format(table_name)
			query += "".join([lambda:column +") ", lambda:column+", "][column!=sorted(self.TABLE_INFO[table_name].keys())[-1]]() for column in (sorted(self.TABLE_INFO[table_name].keys())))
			#query += "\nVALUES({})".format(self.INSERT_HELPER[table_name])
		return query	

	def execute_query(self, query):
		cursor = self._conn.cursor()
		try:
			cursor.execute(query)
			data = cursor.fetchall()
			cursor.close()
			return data
		except Exception:
			print(query)
			print("db execution error")
			return -1
