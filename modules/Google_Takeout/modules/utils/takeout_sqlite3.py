import sqlite3
import logging
import sys

logger = logging.getLogger('gtForensics')

class SQLite3(object):
    def is_exist_table(table_name, db):
        print('db: ', db)
        try:
            con = sqlite3.connect(db)
            print("111")
        except sqlite3.Error as e:
            print("222")
            logger.error("SQLite open error. it is an invalid file: %s" % db)
            con.close()
        return False

        cursor = con.cursor()
        query = "SELECT count(*) FROM sqlite_master WHERE type='table' AND name='%s'" % table_name
        print('query: ', query)

        try:
            cursor.execute(query)
        except sqlite3.Error as e:
            logger.error("SQLite query execution error. query: %s" % query)
            return False

        try:
            ret = cursor.fetchone()
        except sqlite3.Error as e:
            logger.error("SQLite query execution error. query: %s" % query)
            return False

        con.close()
        return ret

#---------------------------------------------------------------------------------------------------------------
	# def execute_fetch_query_multi_values_order(query, query2, db):
	# 	try:
	# 		con = sqlite3.connect(db)
	# 	except sqlite3.Error as e:
	# 		logger.error("SQLite open error. it is an invalid file: %s" % db)
	# 		return False
	# 	# con.text_factory = str
	# 	# con.text_factory = lambda x: x.decode("utf-8") + "foo"
	# 	cursor = con.cursor()
	# 	try:
	# 		cursor.execute(query)
	# 	except sqlite3.Error as e:
	# 		try:
	# 			cursor.execute(query2)
	# 		except sqlite3.Error as e:
	# 			logger.error("SQLite query execution error. query: %s, db: %s" % (query2, db))
	# 			return False
	# 	try:
	# 		ret = cursor.fetchall()
	# 	except sqlite3.Error as e:
	# 		logger.error("SQLite query execution error. query: %s, db: %s" % (query, db))
	# 		return False
	# 	con.close()
	# 	return ret

#---------------------------------------------------------------------------------------------------------------
# 	def execute_fetch_query_multi_values(query, db):
# 		try:
# 			con = sqlite3.connect(db)
# 		except sqlite3.Error as e:
# 			logger.error("SQLite open error. it is an invalid file: %s" % db)
# 			return False

# 		cursor = con.cursor()
# 		try:
# 			cursor.execute(query)
# 		except sqlite3.Error as e:
# 			logger.error("SQLite query execution error. query: %s, db: %s" % (query, db))
# 			return False
# 		try:
# 			ret = cursor.fetchall()
# 		except sqlite3.Error as e:
# 			logger.error("SQLite query execution error. query: %s, db: %s" % (query, db))
# 			return False
# 		con.close()
# 		return ret

# #---------------------------------------------------------------------------------------------------------------
# 	def execute_fetch_query(query, db):
# 		try:
# 			con = sqlite3.connect(db)
# 		except sqlite3.Error as e:
# 			logger.error("SQLite open error. it is an invalid file: %s" % db)
# 			return False
# 		cursor = con.cursor()
# 		try:
# 			cursor.execute(query)
# 		except sqlite3.Error as e:
# 			logger.error("SQLite query execution error. query: %s" % query)
# 			return False
# 		try:
# 			ret = cursor.fetchone()
# 		except sqlite3.Error as e:
# 			logger.error("SQLite query execution error. query: %s" % query)
# 			return False
# 		con.close()
# 		return ret

#---------------------------------------------------------------------------------------------------------------
    def execute_commit_query(queries, db):
        # con = sqlite3.connect(db.decode('cp949'))
        # con = sqlite3.connect(io.StringIO(db.decode('cp949')))
        try:
            con = sqlite3.connect(db)
        except sqlite3.Error as e:
            logger.error("SQLite open error. it is an invalid file: %s" % db)
            return False
        cursor = con.cursor()

        query_type = type(queries)

        if query_type == list:
            for query in queries:
                # print('query: %s' % query)
                try:
                    cursor.execute(query)
                except sqlite3.Error as e:
                    logger.error("SQLite query execution error. query: %s" % query)
                    return False
        elif query_type == str:
            try:
                cursor.execute(queries)
            except sqlite3.Error as e:
                logger.error("SQLite query execution error. query: %s" % queries)
                return False
        else:
            print(query_type)

        con.commit()
        con.close()
        return

#---------------------------------------------------------------------------------------------------------------
    # def execute_commit_query(queries, db):
    # # con = sqlite3.connect(db.decode('cp949'))
    # # con = sqlite3.connect(io.StringIO(db.decode('cp949')))
    #     try:
    #         con = sqlite3.connect(db)
    #     except sqlite3.Error as e:
    #         logger.error("SQLite open error. it is an invalid file: %s" % db)
    #         return False

    #     cursor = con.cursor()
    #     query_type = type(queries)
    #     if query_type == list:
    #         for query in queries:
    #         # print('query: %s' % query)
    #             try:
    #                 cursor.execute(query)
    #             except sqlite3.Error as e:
    #                 logger.error("SQLite query execution error. query: %s" % query)
    #                 return False
    #     elif query_type == str:
    #         try:
    #             cursor.execute(queries)
    #             print(queries)
    #             print(db)
    #         except sqlite3.Error as e:
    #             logger.error("SQLite query execution error. query: %s" % queries)
    #             return False
    #     else:
    #         # print(query_type)
    #         con.commit()
    #     con.close()
    #     return
