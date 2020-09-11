import sqlite3
import os
import re
import datetime
import binascii

from utility.res.sqlite_dict import TABLE_INFO, INSERT_HELPER, CREATE_HELPER


def mysql_to_sqlite(query):
    # (%s, %s, %s) -> (?, ?, ?)
    if 'insert' in query.lower():
        return query.replace('%s', '?')
    else:
        return query


def regexp(expr, item):
    reg = re.compile(expr)
    return reg.search(item) is not None


class Database:
    def __init__(self, case_id, evd_id, source_path, output_path):
        self._conn = None
        self.case_id = case_id
        self.evd_id = evd_id
        self.source_path = source_path
        self.output_path = output_path

    def open(self):
        try:
            path = f'{self.output_path}'+os.sep+f'{self.case_id}.db'
            self._conn = sqlite3.connect(path)
            self._conn.create_function('UNHEX', 1, lambda value: binascii.unhexlify(value))
            self._conn.create_function('regexp', 2, regexp)
            cursor = self._conn.cursor()
            cursor.execute("""PRAGMA synchronous = OFF""")
            cursor.execute("""PRAGMA journal_mode = WAL""")
        except sqlite3.Error:
            self._conn = None
            print("db connection error")

    def commit(self):
        try:
            self._conn.commit()
        except sqlite3.Error:
            print("db commit error")

    def close(self):
        try:
            self._conn.close()
        except sqlite3.Error:
            print("db connection close error")

    def check_table_exist(self, table_name):
        if self._conn is not None:
            query = "SELECT COUNT(*) FROM sqlite_master WHERE name = '" + table_name + "';"
            ret = self.execute_query(query)
            if ret[0] == 1:
                return True
            else:
                return False
        else:
            self.open()
            return self.check_table_exist(table_name)

    def make_base_dir(self):
        path = f'{self.output_path}'
        if not os.path.isdir(path):
            os.mkdir(path)

    def initialize(self):
        self.make_base_dir()
        self.open()
        now_time = datetime.datetime.now()
        for table_name in TABLE_INFO.keys():
            if not self.check_table_exist(table_name):
                self.execute_query(CREATE_HELPER[table_name])
                if table_name == 'case_info':
                    # column: case_id, case_name, administrator, create_date, description
                    query = "insert into case_info values (?, ?, ?, ?, ?)"
                    values = (self.case_id, self.case_id, 'DFRC', now_time, 'CARPE Demo Case')
                    self.execute_query(query, values)

                elif table_name == 'evidence_info':
                    # TODO: Calculate hash value
                    # Columns
                    # evd_id, evd_name, evd_path, tmp_path, case_id, main_type, sub_type, timezone,
                    # acquired_date, md5, sha1, sha3, process_state
                    query = "insert into evidence_info values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
                    evd_path = self.source_path
                    tmp_path = self.output_path
                    values = (self.evd_id, self.evd_id, evd_path, tmp_path, self.case_id, 'image', 'EWF',
                              'UTC+9', now_time, '', '', '', 0)
                    self.execute_query(query, values)
        self.commit()
        self.close()

    def bulk_execute(self, query, values):
        try:
            cursor = self._conn.cursor()
        except sqlite3.Error:
            print("db cursor error")
            return -1
        query = mysql_to_sqlite(query)
        try:
            cursor.executemany(query, values)
            cursor.close()
        except Exception as e:
            print("db execution error : " + str(e))
            return -1
        self.commit()

    def insert_query_builder(self, table_name):
        query = ""
        if table_name in TABLE_INFO.keys():
            query = "INSERT INTO {0} (".format(table_name)
            query += "".join([lambda: column + ") ", lambda: column + ", "][column != sorted(
                TABLE_INFO[table_name].keys())[-1]]() for column in (sorted(TABLE_INFO[table_name].keys())))
        return query

    def execute_query(self, query, values=None):
        cursor = self._conn.cursor()
        query = mysql_to_sqlite(query)
        try:
            if values:
                cursor.execute(query, values)
            else:
                cursor.execute(query)

            data = cursor.fetchone()
            cursor.close()
            self.commit()
            return data
        except Exception as e:
            print(query)
            print("db execution failed: %s" % e)
            return -1

    def execute_query_mul(self, query):
        cursor = self._conn.cursor()
        query = mysql_to_sqlite(query)
        try:
            cursor.execute(query)
            data = cursor.fetchall()
            cursor.close()
            self.commit()
        except Exception as e:
            print(query)
            print("db execution failed: %s" % e)
            return -1
        return data

    def delete_table(self, table_name):
        query = f"drop table if exists {table_name}"
        self.execute_query(query)
