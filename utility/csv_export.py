# Coding by YES

import os
import sqlite3
from pandas import pandas as pd

def export_table_list(path):
    with sqlite3.connect(path) as conn:
        cur = conn.cursor()
        cur.execute('SELECT name FROM sqlite_master WHERE type IN ("table", "view") AND name NOT LIKE "sqlite_%"'
                    ' UNION ALL SELECT name FROM sqlite_temp_master WHERE type IN ("table", "view")')

        table_list = cur.fetchall()
        tables = list()

        for table in table_list:
            tables.append(table[0])

        return tables

def export_csv(path, db_name, tablelist):
    with sqlite3.connect(path + os.sep + db_name) as conn:
        cur = conn.cursor()
        for table in tablelist:
            cur.execute('PRAGMA table_info("{0}")'.format(table))
            c_list = cur.fetchall()

            column_list = list()
            for c in c_list:
                column_list.append(c[1])

            cur.execute('SELECT * FROM {0}'.format(table))
            data = cur.fetchall()

            df = pd.DataFrame(data, columns=column_list)
            try:
                df.to_csv(path + os.sep + 'output_csv' + os.sep + table + '.csv', encoding='utf-8-sig')
            except FileNotFoundError:
                os.mkdir(path + os.sep + 'output_csv')
                df.to_csv(path + os.sep + 'output_csv' + os.sep + table + '.csv', mode='a', encoding='utf-8-sig')
