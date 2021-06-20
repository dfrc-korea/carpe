import sqlite3
import os
import re
import datetime
import binascii

from contextlib import closing
from utility.res.sqlite_dict import TABLE_INFO, CREATE_HELPER


def mysql_to_sqlite(query):
    # (%s, %s, %s) -> (?, ?, ?)
    return query.replace('%s', '?') if 'insert' in query.lower() else query


def regexp(expr, item):
    reg = re.compile(expr)
    return reg.search(item) is not None


def from_unixtime(time, fmt):
    if time == 0:
        return ''
    fmt = fmt.replace("%i", "%M").replace("%s", "%S")
    time = datetime.datetime.fromtimestamp(time/1000)
    return time.strftime(fmt)


class Database:
    def __init__(self, case_id, evd_id, source_path, output_path):
        self._conn = None
        self.case_id = case_id
        self.evd_id = evd_id
        self.source_path = source_path
        self.output_path = output_path

    def open(self):
        try:
            path = f'{self.output_path}' + os.sep + f'{self.case_id}.db'
            self._conn = sqlite3.connect(path)
            self._conn.create_function('UNHEX', 1, lambda value: binascii.unhexlify(value))
            self._conn.create_function('regexp', 2, regexp)
            self._conn.create_function('from_unixtime', 2, from_unixtime)
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
                    query = self.insert_query_builder("case_info")
                    values = ('DFRC', self.case_id, self.case_id, str(now_time), 'CARPE Demo Case')
                    query = (query + "\n values " + "%s" % (values,))
                    self.execute_query(query)

            if table_name == 'evidence_info':
                query = f'Select evd_id FROM {table_name}'
                result = self.execute_query_mul(query)
                if not result or self.evd_id not in [item for t in result for item in t]:
                    # TODO: Calculate hash value
                    query = self.insert_query_builder("evidence_info")
                    evd_path = self.source_path
                    tmp_path = self.output_path
                    values = (str(now_time), self.case_id, self.evd_id, self.evd_id, evd_path, 'image', '', 2, '',
                              '', 'EWF', 'UTC+9', tmp_path)
                    query = (query + "\n values " + "%s" % (values,))
                    self.execute_query(query)
        self.commit()
        self.close()

    def bulk_execute(self, query, values):
        with self._conn as conn:
            with closing(conn.cursor()) as cursor:
                query = mysql_to_sqlite(query)
                try:
                    cursor.executemany(query, values)
                except sqlite3.Error as e:
                    #print(query)
                    #print("db execution error : " + str(e))
                    raise e

    def insert_query_builder(self, table_name):
        query = ""
        if table_name in TABLE_INFO.keys():
            query = "INSERT INTO {0} (".format(table_name)
            query += "".join([lambda: column + ") ", lambda: column + ", "][column != sorted(
                TABLE_INFO[table_name].keys())[-1]]() for column in (sorted(TABLE_INFO[table_name].keys())))
        return query

    def execute_query(self, query):
        with self._conn as conn:
            with closing(conn.cursor()) as cursor:
                query = mysql_to_sqlite(query)
                cursor.execute(query)
                data = cursor.fetchone()
        return data

    def execute_query_mul(self, query):
        cursor = self._conn.cursor()
        query = mysql_to_sqlite(query)
        try:
            cursor.execute(query)
            data = cursor.fetchall()
            cursor.close()
            self.commit()
        except Exception as e:
            #print("[DB Execution Failed] %s" % e)
            return -1
        return data

    def delete_table(self, table_name):
        query = f"drop table if exists {table_name}"
        self.execute_query(query)
