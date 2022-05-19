# Coding by YES

import os
import sqlite3
from datetime import datetime

def TimeTrans(timestamp):

    if type(timestamp) == int:
        date = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%dT%H:%M:%S.%f')+'Z'
        return date

    elif type(timestamp) == float:
        date = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%dT%H:%M:%S.%f') + 'Z'
        return date

def account_info(path):
    with sqlite3.connect(path + 'global.db') as con:
        c = con.cursor()
        c.execute("SELECT preference_value FROM global_preferences")
        users = c.fetchall()
        user_account = 'null'

        for user in users:
            for u in user:
                if '@' in u:
                    user_account = u

        return user_account

def snapshot_local(path):
    with sqlite3.connect(path + 'snapshot.db') as con:
        c = con.cursor()
        c.execute("SELECT filename, modified, is_folder FROM local_entry")
        data = c.fetchall()
        l_data = list()

        for d in data:
            if type(d[1]) == int:
                t = TimeTrans(d[1])
                l_data.append([d[0], t, d[2]])
            else:
                l_data.append([d[0], d[1], d[2]])

        return l_data

def snapshot_volume(path):
    with sqlite3.connect(path + 'snapshot.db') as con:
        c = con.cursor()
        c.execute("SELECT full_path, label, size, filesystem FROM volume_info")
        volume = c.fetchall()
        volume_data = list()

        for v in volume:
            volume_data.append([v[0], v[1], v[2], v[3]])

        return volume_data

def fschange_parse(path, db):
    with sqlite3.connect(path + db) as con:
        c = con.cursor()
        c.execute("SELECT action, full_path, name, is_folder, modified, size FROM fschanges")
        data = c.fetchall()
        fs_data = list()

        for d in data:
            if type(d[4]) == int:
                t = TimeTrans(d[4])
                fs_data.append([d[0], d[1][4:], d[2], d[3], t, d[5]])
            else:
                fs_data.append([d[0], d[1][4:], d[2], d[3], d[4], d[5]])

        return fs_data

if __name__ == '__main__':
    path = "C:/Users/YES/AppData/Local/Google/Drive/user_default/"

    print(snapshot_volume(path))