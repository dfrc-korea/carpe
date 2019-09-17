#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@author:    Seonho Lee
@contact:   horensic@gmail.com
"""

import mysql.connector as maria
from mysql.connector import errorcode
from error import *


class MariaDB:

    def __init__(self, user, password, database=None, verbose=LOG_OFF):
        self._v = verbose
        self._verbose("Called __init__", level=LOG_DEBUG)

        if database is not None:
            self.database = database
            try:
                self.conn = maria.connect(user=user, password=password, database=self.database)
            except maria.Error as err:
                if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                    print("Something is wrong with your user name or password")
                    exit(-1)
                elif err.errno == errorcode.ER_BAD_DB_ERROR:
                    print("Database does not exist")
                    exit(-1)
                else:
                    print(err)
        else:
            try:
                self.conn = maria.connect(user=user, password=password)
            except maria.Error as err:
                if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                    print("Something is wrong with your user name or password")
                    exit(-1)
                else:
                    print(err)
                    exit(-1)

    def __repr__(self):
        return "CARPE Maria DB"

    def __enter__(self):
        self._verbose("Called __enter__", level=LOG_DEBUG)
        return self

    def __exit__(self, type, value, traceback):
        self._verbose("Called __exit__", level=LOG_DEBUG)
        self._end()

    def __del__(self):
        self._verbose("Called __del__", level=LOG_DEBUG)
        self._end()

    def _end(self):
        if self.conn.is_connected():
            self.conn.close()

    def _verbose(self, msg, level):
        if (self._v & level) == level:
            print("{lv} {m}".format(lv=LOG_MSG[level], m=msg))

    def query(self, q, *args):
        cursor = self.conn.cursor()

        try:
            if not args:
                cursor.execute(q)
            else:
                cursor.execute(q, tuple(v for v in args))
            self.conn.commit()

        except maria.Error:
            print("Failed query: {}".format(q))
            self.conn.rollback()
            return False

        finally:
            cursor.close()

        return True
