# -*- coding: utf-8 -*-
"""This file contains a parser for the Android contacts2 database.

Android accounts are stored in SQLite database files named contacts2.db.
"""
import os
import datetime
import sqlite3

from modules.android_basic_apps import logger

query = \
    '''
    SELECT 
        c.display_name as name, p.normalized_number as phone_number
    FROM 
        raw_contacts c, phone_lookup p 
    WHERE 
        p.raw_contact_id=c._id
    '''


def parse_contacts(target_files, result_path):
    """Parse contacts databases.

    Args:
        target_files (list): target files.
        result_path (str): result path.
    """

    logger.info('Parse contacts2 databases.')

    results = []
    for file in target_files:
        if str(file).endswith('contacts2.db'):
            database = sqlite3.connect(str(file))
            database.row_factory = sqlite3.Row

            result = _parse_contacts(database, result_path)
            if result:
                results.append(result)

    return results


def _parse_contacts(database, result_path):
    """Parse contacts2.db

    Args:
        database (SQLite3): target SQLite3 database.
        result_path (str): result path.
    """
    cursor = database.cursor()
    try:
        cursor.execute(query)
    except sqlite3.Error as exception:
        logger.error('Contacts not found! {0!s}'.format(exception))

    results = cursor.fetchall()
    num_of_results = len(results)

    data = {}
    data['title'] = 'contact'
    header = ('name', 'number')
    data['number_of_data_headers'] = len(header)
    data['number_of_data'] = num_of_results
    data['data_header'] = header
    data_list = []
    if num_of_results > 0:
        for row in results:
            data_list.append((row[0], row[1]))

        data['data'] = data_list
    else:
        logger.warning('NO Contacts found!')

    return data
