import sqlite3
from sqlite3 import Error
from modules.windows_jumplist.lib.yjSysUtils import debug_mode


class TSQLite3:
    def __init__(self, db_file):
        self.conn = None
        self.cursor = None
        try:
            self.conn = sqlite3.connect(db_file)
            self.cursor = self.conn.cursor()
        except Error as e:
            print(e)

    def execmanySQL(self, *sql):
        try:
            self.cursor.executemany(*sql)
            return True
        except Error as e:
            print(e)
            return False

    def execSQL(self, *sql):
        try:
            self.cursor.execute(*sql)
            return True
        except Error as e:
            print(e)
            return False

    def getInsertSQL(self, tableName, fieldNames):
        if debug_mode:
            assert type(fieldNames) in [list, tuple]
        return 'insert into %s(%s) Values (%s)' % (
        tableName, ','.join(fieldNames), ','.join(['?' for i in range(0, len(fieldNames)) if True]))

    def commit(self):
        self.conn.commit()
