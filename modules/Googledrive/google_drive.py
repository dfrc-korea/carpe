# Coding by YES
# path : C:\Users\[user_name]\AppData\Local\Google\Drive
# TODO : 경로작업 , DB 추가적인 부분 / Author NAME 찾기 / UTC 시간작업

# Updated to v57.0.5.0 by Jeongyoon

import sqlite3
from datetime import datetime

def gdrive_parse(path):
    db_path = path + 'metadata_sqlite_db'
    with sqlite3.connect(db_path) as con:
        c = con.cursor()
        c.execute(
            "SELECT local_title, file_size, is_folder, mime_type, \
            trashed, modified_date, viewed_by_me_date FROM items;"
        )
        data = c.fetchall()

        res = []
        for d in data:
            if 1 == d[2]:
                ext = "Directory"
            else:
                ext = "File"
            if 1 == d[4]:
                is_deleted = "Deleted"
            else:
                is_deleted = "-"
            res.append([d[0], d[1], ext, d[3], is_deleted, TimeTrans(d[5]), TimeTrans(d[6])])
        return res


def TimeTrans(timestamp):

    if type(timestamp) == int:
        date = datetime.fromtimestamp(timestamp/1000).strftime('%Y-%m-%dT%H:%M:%S.%f') + 'Z'
        return date

    elif type(timestamp) == float:
        date = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%dT%H:%M:%S.%f') + 'Z'
        return date