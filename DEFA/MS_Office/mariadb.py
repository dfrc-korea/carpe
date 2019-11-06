#           OH MY GIRL License
#   To create a program using this source code,
#   Follow the link below to listen to the OH MY GIRL's song at least once.
#   LINK (1): https://youtu.be/RrvdjyIL0fA
#   LINK (2): https://youtu.be/QIN5_tJRiyY

"""
@author:    Seonho Lee
@license:   OH_MY_GIRL License
@contact:   horensic@gmail.com
"""

import mysql.connector as maria
from mysql.connector import errorcode

LOG_OFF = 0x0


class MariaDB:

    def __init__(self, user, password, database=None, verbose=LOG_OFF):
        # passwd = input("Password > ")
        # passwd = password
        self._v = verbose

        if database is not None:
            self.database = database
            try:
                self.conn = maria.connect(user=user, password=password, database=self.database)
            except maria.Error as err:
                if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                    print("Something is wrong with your user name or password")
                elif err.errno == errorcode.ER_BAD_DB_ERROR:
                    print("Database does not exist")
                else:
                    print(err)
        else:
            try:
                self.conn = maria.connect(user=user, password=password)
            except maria.Error as err:
                if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                    print("Something is wrong with your user name or password")
                else:
                    print(err)

    def __repr__(self):
        return "Maria DB"

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self._end()

    def __del__(self):
        self._end()

    def _end(self):
        if self.conn.is_connected():
            self.conn.close()

    def _verbose(self, msg, level):
        if (self._v & level) == level:
            print(msg)

    def query(self, q, *args):
        cursor = self.conn.cursor()
        if not args:
            try:
                cursor.execute(q)
            except maria.Error as err:
                print("Failed query: {}".format(q))
                print(err)
                return False
        else:
            try:
                cursor.execute(q, tuple(v for v in args))
            except maria.Error as err:
                print("Failed query: {} {}".format(q, tuple(v for v in args)))
                print(err)
                return False

        self.conn.commit()
        return True
