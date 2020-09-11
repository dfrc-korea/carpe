# -*- coding: utf-8 -*-
import os
import sqlite3
import pathlib

from modules.android_user_apps import logger


location_query = \
'''
    SELECT capture_timestamp as timestamp,
        latitude as latitude,
        longitude as longitude,
        filepath as contents
    FROM local_media
'''

def parse_google_photo(target_files, result_path):
    """Parse Google photo databases.

    Args:
        target_files (list): target files.
        result_path (str): result path.
    """
    logger.info('Parse Google photo databases.')
    results = []
    for file in target_files:
        if str(file).find('com.google.android.apps.photos'+os.path.sep+'databases'+os.path.sep+'gphotos'):
            database = sqlite3.connect(str(file))
            database.row_factory = sqlite3.Row

            location_data = _parse_google_photo_location(database, result_path)
            if location_data:
                results.append(location_data)

    return results

def _parse_google_photo_location(database, result_path):
    """Parse Google photo location.

    Args:
        database (SQLite3): target SQLite3 database.
        result_path (str): result path.
    """
    try:
        cursor = database.cursor()
        cursor.execute("PRAGMA database_list")  # for database file name
        rows = cursor.fetchall()
        db_name = rows[0][2][rows[0][2].rfind(os.path.sep) + 1:]

        cursor.execute(location_query)
        results = cursor.fetchall()
        num_of_results = len(results)
    except Exception as e:
        #print(str(e))
        return False

    data = {}
    header = ('package_name', 'timestamp', 'longitude', 'latitude', 'contents', 'source', 'is_visited')
    data['number_of_data_headers'] = len(header)
    data['number_of_data'] = num_of_results
    data['data_header'] = header
    data['title'] = "geodata"
    data_list = []
    if num_of_results >0:
        for row in results:
            data_list.append(("com.google.android.apps.photos", row['timestamp'], row['longitude'], row['latitude'], row['contents'],  "DB:"+db_name+"|Table:local_media", "Yes"))
        data['data'] = data_list
    else:
        logger.info('Not found location data!')

    return data