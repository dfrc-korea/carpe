# -*- coding: utf-8 -*-
"""This file contains a parser for the Android WI-FI profile xml file.

Android Wi-Fi Profiles is stored in WifiConfigStore.xml file named .
"""
import datetime
import xml.etree.ElementTree


from modules.android_basic_apps import logger

def parse_wifi(target_files, result_path):
    """Parse Wi-Fi profile xml file.

    Args:
        target_files (list): target files.
        result_path (str): result path.
    """

    logger.info('Parse Wi-Fi profile XML file.')

    results = []
    for file in target_files:
        if str(file).endswith('WifiConfigStore.xml'):
            result = _parse_wifi(str(file), result_path)
            if result:
                results.append(result)

    return results


def _parse_wifi(file, result_path):
    """Parse Wi-Fi Profiles from /misc/wifi/WifiConfigStore.xml.

    Args:
        file (str): target file path.
        result_path (str): result path.
    """

    result = {}
    header = ('security_mode', 'ssid', 'pre_shared_key', 'wep_keys', 'password', 'identity',
               'default_gw_mac_address', 'sem_creation_time', 'sem_update_time', 'last_connected_time',
               'captive_portal', 'login_url', 'ip_assignment')

    data_list = []

    tree = xml.etree.ElementTree.parse(file)
    for node in tree.iter('Network'):
        wp = WifiProfile()
        for elem in node.iter():
            if not elem.tag == 'Network':
                attribute = elem.attrib
                for key, value in attribute.items():
                    #print(key +':'+ value)
                    if value == 'ConfigKey':
                        wp.security_mode = elem.text.split('"')[2]
                    if value == 'SSID':
                        wp.ssid = elem.text.strip('"')
                    if value == 'PreSharedKey':
                        wp.pre_shared_key = elem.text
                    if value == 'WEPKeys':
                        wp.wep_keys = elem.text
                    if value == 'DefaultGwMacAddress':
                        wp.default_gw_mac_address = elem.text
                    if value == 'semCreationTime':
                        wp.sem_creation_time = elem.attrib['value']
                    if value == 'semUpdateTime':
                        wp.sem_update_time = elem.attrib['value']
                    if value == 'LastConnectedTime':
                        wp.last_connected_time = elem.attrib['value']
                    if value == 'CaptivePortal':
                        wp.captive_portal = elem.attrib['value']
                    if value == 'LoginUrl':
                        wp.login_url = elem.text
                    if value == 'IpAssignment':
                        wp.ip_assignment = elem.text
                    if value == 'Identity':
                        wp.identity = elem.text
                    if value == 'Password':
                        wp.password = elem.text

        if int(wp.sem_creation_time) != 0:
            wp.sem_creation_time = datetime.datetime.fromtimestamp(float(wp.sem_creation_time) / 1000, datetime.timezone.utc).\
                strftime('%Y-%m-%dT%H:%M:%S.%fZ')

        if int(wp.sem_update_time) != 0:
            wp.sem_update_time = datetime.datetime.fromtimestamp(float(wp.sem_update_time) / 1000, datetime.timezone.utc).\
                strftime('%Y-%m-%dT%H:%M:%S.%fZ')

        if int(wp.last_connected_time) != 0:
            wp.last_connected_time = datetime.datetime.fromtimestamp(float(wp.last_connected_time) / 1000, datetime.timezone.utc).\
                strftime('%Y-%m-%dT%H:%M:%S.%fZ')

        data_list.append((wp.security_mode, wp.ssid, wp.pre_shared_key, wp.wep_keys, wp.password,\
                          wp.identity, wp.default_gw_mac_address, wp.sem_creation_time, wp.sem_update_time,\
                          wp.last_connected_time, wp.captive_portal, wp.login_url, wp.ip_assignment))

    result['title'] = 'wifi_info'
    result['number_of_data_headers'] = len(header)
    result['number_of_data'] = len(data_list)
    result['data_header'] = tuple(header)
    result['data'] = data_list

    return result


class WifiProfile(object):
    def __init__(self):
        self.security_mode = None
        self.ssid = None
        self.pre_shared_key = None
        self.wep_keys = None
        self.password = None
        self.identity = None
        self.default_gw_mac_address = None
        self.sem_creation_time = None
        self.sem_update_time = None
        self.last_connected_time = None
        self.captive_portal = None
        self.login_url = None
        self.ip_assignment = None
