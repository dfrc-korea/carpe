# -*- coding: utf-8 -*-
"""This file contains a parser for the Android Call logs database.

Android call logs are stored in SQLite database files named calllog.db.
"""
import sqlite3
import datetime

from modules.android_basic_apps import logger

query = \
'''
    SELECT
    CASE
        WHEN phone_account_address is NULL THEN ' '
        ELSE phone_account_address
        end as phone_account_address,
    number,
    date, 
    CASE
        WHEN type = 1 THEN  'Incoming'
        WHEN type = 2 THEN  'Outgoing'
        WHEN type = 3 THEN  'Missed'
        WHEN type = 4 THEN  'Voicemail'
        WHEN type = 5 THEN  'Rejected'
        WHEN type = 6 THEN  'Blocked'
        WHEN type = 7 THEN  'Answered Externally'
        ELSE 'Unknown'
        end as types,
    duration,
    CASE
        WHEN geocoded_location is NULL THEN ' '
        ELSE geocoded_location
        end as geocoded_location,
    countryiso,
    CASE
        WHEN _data is NULL THEN ' '
        ELSE _data
        END as _data,
    CASE
        WHEN mime_type is NULL THEN ' '
        ELSE mime_type
        END as mime_type,
    CASE
        WHEN transcription is NULL THEN ' '
        ELSE transcription
        END as transcription,
    deleted
    FROM
    calls
'''
#datetime(date /1000, 'unixepoch') as date,

def parse_call_logs(target_files, result_path):
    """Parse calllogs databases.

    Args:
        target_files (list): target files.
        result_path (str): result path.
    """

    logger.info('Parse Call Logs databases.')

    results = []
    for file in target_files:
        if str(file).endswith('calllog.db'):
            database = sqlite3.connect(str(file))
            database.row_factory = sqlite3.Row

            result = _parse_call_logs(database, result_path)
            if result:
                results.append(result)

    return results

def _parse_call_logs(database, result_path):
    """Parse Call Logs.

    Args:
        database (SQLite3): target SQLite3 database.
        result_path (str): result path.
    """
    cursor = database.cursor()
    try:
        cursor.execute(query)
    except sqlite3.Error as exception:
        logger.error('Call Logs not found! {0!s}'.format(exception))

    results = cursor.fetchall()
    num_of_results = len(results)

    data = {}
    data['title'] = 'call_logs'
    header = ('phone_account_address', 'partner', 'call_date', 'type', 'duration_in_secs', 'partner_location',
              'country_iso', 'data', 'mime_type', 'transcription', 'deleted')
    data['number_of_data_headers'] = len(header)
    data['number_of_data'] = num_of_results
    data['data_header'] = header
    data_list = []
    if num_of_results >0:
        for row in results:
            data_list.append((row[0], row[1],
                  datetime.datetime.fromtimestamp(row[2]/1000, datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
                  row[3], str(row[4]), row[5], row[6], row[7], row[8], row[9],
                  str(row[10])))

        data['data'] = data_list
    else:
        logger.warning('NO Call Logs found!')

    return data