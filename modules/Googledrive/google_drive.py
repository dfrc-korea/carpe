# Coding by YES


# path : C:\Users\[user_name]\AppData\Local\Google\Drive
# TODO : 경로작업 , DB 추가적인 부분 / Author NAME 찾기 / UTC 시간작업

import os
import sqlite3
from datetime import datetime
from pprint import pprint

def g_account(path):
    with sqlite3.connect(path + 'account_db_sqlite.db') as con:
        c = con.cursor()
        c.execute("SELECT account_token FROM account_info")
        user_tokens = c.fetchall()

        return user_tokens


def gdrive_parse(path):
    with sqlite3.connect(path + 'metadata_sqlite_db') as con:
        c = con.cursor()
        c.execute("SELECT modified_date, viewed_by_me_date, file_size, local_title, is_folder, trashed FROM items")
        data = c.fetchall()
        result = []
        #table.field_names = ["modified date", "Viewed by me date", "File size", "Filename", "extension", "is_deleted"]
        for time in data:

            if 1 == time[4]:
                ext = "Directory"
                fname = time[3]
            else:
                fname, ext = os.path.splitext(time[3])

            if 1 == time[5]:
                is_deleted = "delete"
            else:
                is_deleted = "-"

            result.append([TimeTrans(time[0]), TimeTrans(time[1]), time[2], fname, ext, is_deleted])
        return result

def TimeTrans(timestamp):

    if type(timestamp) == int:
        date = datetime.fromtimestamp(timestamp/1000).strftime('%Y-%m-%dT%H:%M:%S.%f') + 'Z'
        return date

    elif type(timestamp) == float:
        date = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%dT%H:%M:%S.%f') + 'Z'
        return date




