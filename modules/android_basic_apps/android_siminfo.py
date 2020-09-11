# -*- coding: utf-8 -*-
"""This file contains a parser for the Android SIM information database.

Android SIM information is stored in SQLite database files named telephony.db.
"""
import sqlite3
import datetime

from modules.android_basic_apps import logger

query = \
'''
    SELECT
        icc_id,
        sim_id,
        display_name,
        carrier_name
    FROM
        siminfo
'''

def parse_sim_info(target_files, result_path):
    """Parse SIM information databases.

    Args:
        target_files (list): target files.
        result_path (str): result path.
    """

    logger.info('Parse SIM information databases.')

    results = []
    for file in target_files:
        if str(file).endswith('telephony.db'):
            database = sqlite3.connect(str(file))
            database.row_factory = sqlite3.Row

            result = _parse_sim_info(database, result_path)
            if result:
                results.append(result)
        elif str(file).endswith('SimCard.dat'):
            result = _parse_simcard_dat(str(file), result_path)
            if result:
                results.append(result)

    return results

def _parse_sim_info(database, result_path):
    """Parse SIM Information.

    Args:
        database (SQLite3): target SQLite3 database.
        result_path (str): result path.
    """
    cursor = database.cursor()
    try:
        cursor.execute(query)
    except sqlite3.Error as exception:
        logger.error('SIM Information not found! {0!s}'.format(exception))

    results = cursor.fetchall()
    num_of_results = len(results)

    data = {}
    data['title'] = 'sim_info'
    header = ('icc_id', 'sim_id','display_name', 'carrier_name')
    data['number_of_data_headers'] = len(header)
    data['number_of_data'] = num_of_results
    data['data_header'] = header
    data_list = []
    if num_of_results >0:
        for row in results:
            data_list.append((row['icc_id'], row['sim_id'], row['display_name'], row['carrier_name']))

        data['data'] = data_list
    else:
        logger.warning('NO SIM Information found!')

    return data

def _parse_simcard_dat(file, result_path):
    """Parse SIM Information from /system/SimCard.dat.

    Args:
        file (str): target file path.
        result_path (str): result path.
    """
    result = {}
    header = list()
    data = list()
    data_list = []
    with open(file, 'r') as f:
        for line in f.readlines():
            key, value = line[:len(line)-1].split('=')
            header.append(key)
            if key == 'SimChangeTime':
                data.append(datetime.datetime.fromtimestamp(float(value)/1000, datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%fZ'))
            else:
                data.append(value)

    data_list.append(tuple(data))

    result['title'] = 'sim_info_dat'
    result['number_of_data_headers'] = len(header)
    result['number_of_data'] = len(data)
    result['data_header'] = tuple(header)
    result['data'] = data_list

    return result
