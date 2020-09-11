# -*- coding: utf-8 -*-
"""This file contains a parser for the Android accounts_ce database.

Android accounts are stored in SQLite database files named accounts_ce.db.
"""
import os
import sqlite3

from modules.android_basic_apps import logger

query = \
'''
    SELECT
        name,
        type,
        password
    FROM
    accounts
'''

def parse_accounts_ce(target_files, result_path):
    """Parse accounts_ce databases.

    Args:
        target_files (list): target files.
        result_path (str): result path.
    """

    logger.info('Parse accounts_ce databases.')

    results = []
    for file in target_files:
        if str(file).endswith('accounts_ce.db'):
            uid = str(file).split(os.sep)[-2]
            database = sqlite3.connect(str(file))
            database.row_factory = sqlite3.Row

            result = _parse_accounts_ce(database, uid, result_path)
            if result:
                results.append(result)

    return results

def _parse_accounts_ce(database, uid, result_path):
    """Parse accounts_ce.db.

    Args:
        database (SQLite3): target SQLite3 database.
        uid (str): user id.
        result_path (str): result path.
    """
    cursor = database.cursor()
    try:
        cursor.execute(query)
    except sqlite3.Error as exception:
        logger.error('Accounts not found! {0!s}'.format(exception))

    results = cursor.fetchall()
    num_of_results = len(results)

    data = {}
    header = ('name', 'type', 'password')
    data['title'] = 'accounts_ce'+f'_{uid}'
    data['number_of_data_headers'] = len(header)
    data['number_of_data'] = num_of_results
    data['data_header'] = header
    data_list = []
    if num_of_results >0:
        for row in results:
            data_list.append((row[0], row[1], row[2]))

        data['data'] = data_list
    else:
        logger.warning('NO Accounts found!')

    return data