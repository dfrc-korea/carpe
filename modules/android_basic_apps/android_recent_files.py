# -*- coding: utf-8 -*-
"""This file contains a parser for the Android myfiles database.

Android recent files are stored in SQLite database files named /com.sec.android.app.myfiles/databases/myfiles.db.
"""
import sqlite3
import datetime

from modules.android_basic_apps import logger

query = \
'''
    select
        name,
        size,
        date,
        _data,
        ext,
        _source,
        _description,
        recent_date
    from recent_files 
'''
#datetime(date / 1000, "unixepoch"),
#datetime(recent_date / 1000, "unixepoch")

def parse_recent_files(target_files, result_path):
    """Parse Recent files databases.

    Args:
        target_files (list): target files.
        result_path (str): result path.
    """

    logger.info('Parse Recent files databases.')

    results = []
    for file in target_files:
        if str(file).endswith('myfiles.db'):
            database = sqlite3.connect(str(file))
            database.row_factory = sqlite3.Row

            result = _parse_recent_files(database, result_path)
            if result:
                results.append(result)

    return results

def _parse_recent_files(database, result_path):
    """Parse myfiles.db.

    Args:
        database (SQLite3): target SQLite3 database.
        result_path (str): result path.
    """
    cursor = database.cursor()
    try:
        cursor.execute(query)
    except sqlite3.Error as exception:
        logger.error('Recent Files not found! {0!s}'.format(exception))

    results = cursor.fetchall()
    num_of_results = len(results)

    data = {}
    header = ('name', 'size', 'timestamp', 'data', 'ext', 'source', 'description', 'recent_timestamp')
    data['title'] = 'recent_files'
    data['number_of_data_headers'] = len(header)
    data['number_of_data'] = num_of_results
    data['data_header'] = header
    data_list = []
    if num_of_results >0:
        for row in results:
            data_list.append((row[0], row[1],
                datetime.datetime.fromtimestamp(row[2]/1000, datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
                row[3], row[4], row[5], row[6],
                datetime.datetime.fromtimestamp(row[7]/1000, datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%fZ')))

        data['data'] = data_list
    else:
        logger.warning('NO Recent Files found!')

    return data