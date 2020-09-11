# -*- coding: utf-8 -*-
"""This file contains a parser for the Android FileCache database.

Android file cache is stored in SQLite database files named /com.sec.android.app.myfiles/databases/FileCache.db.
"""
import sqlite3
import datetime

from modules.android_basic_apps import logger

query = \
'''
    SELECT
        storage,
        path,
        size,
        date,
        latest
    from FileCache
    where path is not NULL 
'''
#datetime(date / 1000, "unixepoch"),
#datetime(latest /1000, "unixepoch")

def parse_file_cache(target_files, result_path):
    """Parse file cache databases.

    Args:
        target_files (list): target files.
        result_path (str): result path.
    """

    logger.info('Parse file cache databases.')

    results = []
    for file in target_files:
        if str(file).endswith('FileCache.db'):
            database = sqlite3.connect(str(file))
            database.row_factory = sqlite3.Row

            result = _parse_file_cache(database, result_path)
            if result:
                results.append(result)

    return results

def _parse_file_cache(database, result_path):
    """Parse FileCache.db.

    Args:
        database (SQLite3): target SQLite3 database.
        result_path (str): result path.
    """
    cursor = database.cursor()
    try:
        cursor.execute(query)
    except sqlite3.Error as exception:
        logger.error('File cache not found! {0!s}'.format(exception))

    results = cursor.fetchall()
    num_of_results = len(results)

    data = {}
    header =  ('storage', 'path', 'size', 'timestamp', 'latest')
    data['title'] = 'file_cache'
    data['number_of_data_headers'] = len(header)
    data['number_of_data'] = num_of_results
    data['data_header'] = header
    data_list = []
    if num_of_results >0:
        for row in results:
            data_list.append((row[0], row[1], row[2],
                  datetime.datetime.fromtimestamp(row[3]/1000, datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
                  datetime.datetime.fromtimestamp(row[4]/1000, datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%fZ')))

        data['data'] = data_list
    else:
        logger.warning('NO File cache found!')

    return data