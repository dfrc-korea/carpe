# -*- coding: utf-8 -*-
"""This file contains a parser for the Android contacts2 database.

Android accounts are stored in SQLite database files named contacts2.db.
"""
import os
import datetime
import xml.etree.ElementTree as ET

from modules.android_basic_apps import logger


def parse_system_info(target_files, result_path):
    """Parse system info databases.

    Args:
        target_files (list): target files.
        result_path (str): result path.
    """

    logger.info('Parse system information databases.')

    results = []
    for file in target_files:
        if str(file).endswith('settings_secure.xml'):
            result = _parse_system_info(str(file), result_path)
            if result:
                results.append(result)

    return results


def _parse_system_info(file, result_path):
    """Parse System info from /system/users/*/settings_secure.xml.

    Args:
        database (SQLite3): target SQLite3 database.
        result_path (str): result path.
    """
    result = {}
    header = ('device id', 'bluetooth address', 'bluetooth name')

    data_list = []

    tree = ET.parse(file)
    root = tree.getroot()
    si = SystemInfo()
    for node in root.iter('setting'):
        attr = node.attrib
        if attr['name'] == 'android_id':
            si.android_id = attr['value']
        elif attr['name'] == 'bluetooth_address':
            si.bluetooth_addr = attr['value']
        elif attr['name'] == 'bluetooth_name':
            si.bluetooth_name = attr['value']

    data_list.append((si.android_id, si.bluetooth_addr, si.bluetooth_name))

    result['title'] = 'system_info'
    result['number_of_data_headers'] = len(header)
    result['number_of_data'] = len(data_list)
    result['data_header'] = tuple(header)
    result['data'] = data_list

    return result


class SystemInfo:
    def __init__(self):
        self.android_id = None
        self.bluetooth_addr = None
        self.bluetooth_name = None
