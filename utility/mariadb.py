import pymysql

class Mariadb(object):
	def open(self):
		try:
			conn=pymysql.connect(host='192.168.1.232', port=3306, user='root', passwd='dfrc4738', db='carpe',charset='utf8',autocommit=True)
			return conn
		except Exception:
			conn=None
			print("db connection error")
			return conn
	def close(self, conn):
		try:
			conn.close()
			ret=1
		except Exception:
			print("db connection close error")
			ret=0
		return ret
	def execute_query(self, conn, query):
		cursor =  conn.cursor()
		try:
			cursor.execute(query)
			data = cursor.fetchone()
			cursor.close()
			return data
		except Exception:
			print("db execution error")
			return "error"
	def query_builder(self, evidence_id, data, table):
		if(table == "file"):
			data=data.split("|")
			query = "insert into files(evidence_id, type, allocated, path, name, mtime, atime, ctime, file_extension) values ("
			query+= evidence_id+","
			#query+= ",".join(data) + ");"
			query+= "\"" + data[0] + "\","
			query+= "\"" + data[1] + "\","
			query+= "\"" + data[2] + "\","
			query+= "\"" + data[3] + "\","
			query+= "\"" + data[4] + "\","
			query+= "\"" + data[5] + "\","
			query+= "\"" + data[6] + "\","
			query+= "\"" + data[7] + "\");"
			
			return query
		else:
			print("not surported table")

