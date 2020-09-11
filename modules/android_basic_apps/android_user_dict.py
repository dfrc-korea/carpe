# -*- coding: utf-8 -*-
"""This file contains a parser for the Android user_dict database.

Android User Dictionary is stored in SQLite database files named user_dict.db.
"""
import sqlite3

from modules.android_basic_apps import logger

query = \
'''
    select 
    word,
    frequency,
    locale,
    appid,
    shortcut
    from words
'''

def parse_user_dict(target_files, result_path):
    """Parse user_dict databases.

    Args:
        target_files (list): target files.
        result_path (str): result path.
    """

    logger.info('Parse User Dictionary databases.')

    results = []
    for file in target_files:
        if str(file).endswith('user_dict.db'):
            database = sqlite3.connect(str(file))
            database.row_factory = sqlite3.Row

            result = _parse_user_dict(database, result_path)
            if result:
                results.append(result)

    return results

def _parse_user_dict(database, result_path):
    """Parse User Dictionary.

    Args:
        database (SQLite3): target SQLite3 database.
        result_path (str): result path.
    """
    cursor = database.cursor()
    try:
        cursor.execute(query)
    except sqlite3.Error as exception:
        logger.error('User Dictionary not found! {0!s}'.format(exception))

    results = cursor.fetchall()
    num_of_results = len(results)

    data = {}
    data['title'] = 'user_dict'
    header = ('word', 'frequency', 'locale', 'app_id', 'shortcut')
    data['number_of_data_headers'] = len(header)
    data['number_of_data'] = num_of_results
    data['data_header'] = header
    data_list = []
    if num_of_results > 0:
        for row in results:
            data_list.append((row[0], row[1], row[2], row[3], row[4]))

        data['data'] = data_list
    else:
        logger.warning('NO User Dictionary found!')

    return data