# -*- coding: utf-8 -*-
"""This file contains a parser for the Android WI-FI profile xml file.

Android usagestats is stored in /data/system/usagestats named.
"""

import os
import glob
import json
import datetime
import xml.etree.ElementTree
from enum import IntEnum

from modules.android_basic_apps.usagestats_pb.protobuf import usagestatsservice_pb2
from modules.android_basic_apps import logger

def parse_usagestats(target_files, result_path):
    """Parse android usagestats.

    Args:
        target_files (list): target files.
        result_path (str): result path.
    """


    logger.info('Parse usagestats')

    results = []
    for file in target_files:
        if os.path.dirname(str(file)).endswith('usagestats'):
            uid = str(file).split(os.sep)[-1]
            result = _parse_usagestats(str(file), uid, result_path)
            if result:
                results.append(result)

    return results

def _parse_usagestats(directory, uid, result_path):
    """Parse usagestats from /system/usagestats.

    Args:
        directory (str): target direcotry path.
        uid (str): user id.
        result_path (str): result path.
    """
    data = {}
    data['title'] = 'usagestats' + f'_{uid}'
    header = ('usage_type', 'last_time_active', 'time_active_in_msecs', 'time_active_in_secs',
              'last_time_service_used', 'last_time_visible', 'total_time_visible', 'app_launch_count',
              'package', 'types', 'class', 'source', 'all_attributes')
    data['number_of_data_headers'] = len(header)
    data['data_header'] = header
    data_list = []

    for file in glob.iglob(os.path.join(directory, '**'), recursive=True):
        if os.path.isfile(file):
            source = None
            filename = os.path.basename(file)

            if os.path.dirname(file).endswith('daily'):
                source = 'daily'
            elif os.path.dirname(file).endswith('weekly'):
                source = 'weekly'
            elif os.path.dirname(file).endswith('monthly'):
                source = 'monthly'
            elif os.path.dirname(file).endswith('yearly'):
                source = 'yearly'

            try:
                filename_int = int(filename)
            except:
                logger.error('Invalid File Name: {0:s}'.format(filename))

            try:
                tree = xml.etree.ElementTree.parse(file)
                root = tree.getroot()
                logger.info('processing: {0:s}'.format(file))
                for elem in root:
                    if elem.tag == 'packages':
                        usagestat = UsageStats()
                        usagestat.source = source
                        usagestat.usage_type = elem.tag
                        for subelem in elem:
                            usagestat.all_attributes = json.dumps(subelem.attrib)
                            last_time_active = int(subelem.attrib['lastTimeActive'])
                            if last_time_active < 0:
                                usagestat.last_time_active = abs(last_time_active)
                            else:
                                usagestat.last_time_active = filename_int + last_time_active

                            usagestat.last_time_active = datetime.datetime.fromtimestamp(usagestat.last_time_active / 1000,
                                 datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%fZ')

                            usagestat.package = subelem.attrib['package']
                            usagestat.time_active_in_msecs = subelem.attrib['timeActive']
                            usagestat.time_active_in_secs = int(usagestat.time_active_in_msecs) / 1000
                            usagestat.app_launch_count = subelem.attrib.get('appLaunchCount', None)

                            data_list.append(
                                (usagestat.usage_type, usagestat.last_time_active, usagestat.time_active_in_msecs,
                                 usagestat.time_active_in_secs, usagestat.last_time_service_used,
                                 usagestat.last_time_visible,
                                 usagestat.total_time_visible, usagestat.app_launch_count, usagestat.package,
                                 usagestat.types, usagestat.cls, usagestat.source, usagestat.all_attributes))

                    elif elem.tag == 'configurations':
                        usagestat = UsageStats()
                        usagestat.source = source
                        usagestat.usage_type = elem.tag
                        for subelem in elem:
                            usagestat.all_attributes = json.dumps(subelem.attrib)
                            last_time_active = int(subelem.attrib['lastTimeActive'])
                            if last_time_active < 0:
                                usagestat.last_time_active = abs(last_time_active)
                            else:
                                usagestat.last_time_active = filename_int + last_time_active

                            usagestat.last_time_active = datetime.datetime.fromtimestamp(usagestat.last_time_active / 1000,
                                 datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%fZ')

                            usagestat.time_active_in_msecs = subelem.attrib['timeActive']
                            usagestat.time_active_in_secs = int(usagestat.time_active_in_msecs) / 1000

                            data_list.append(
                                (usagestat.usage_type, usagestat.last_time_active, usagestat.time_active_in_msecs,
                                 usagestat.time_active_in_secs, usagestat.last_time_service_used,
                                 usagestat.last_time_visible,
                                 usagestat.total_time_visible, usagestat.app_launch_count, usagestat.package,
                                 usagestat.types, usagestat.cls, usagestat.source, usagestat.all_attributes))

                    elif elem.tag == 'event-log':
                        usagestat = UsageStats()
                        usagestat.source = source
                        usagestat.usage_type = elem.tag
                        for subelem in elem:
                            usagestat.all_attributes = json.dumps(subelem.attrib)
                            time = int(subelem.attrib['time'])
                            if time < 0:
                                usagestat.last_time_active = abs(time)
                            else:
                                usagestat.last_time_active = filename_int + time

                            usagestat.last_time_active = datetime.datetime.fromtimestamp(usagestat.last_time_active / 1000,
                                 datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%fZ')

                            usagestat.package = subelem.attrib['package']
                            usagestat.types = str(EventType(int(subelem.attrib['type'])))
                            usagestat.cls =  subelem.attrib.get('class', None)

                            data_list.append((usagestat.usage_type, usagestat.last_time_active, usagestat.time_active_in_msecs,
                                    usagestat.time_active_in_secs, usagestat.last_time_service_used, usagestat.last_time_visible,
                                    usagestat.total_time_visible, usagestat.app_launch_count, usagestat.package,
                                    usagestat.types, usagestat.cls, usagestat.source, usagestat.all_attributes))


            except xml.etree.ElementTree.ParseError:
                # Perhaps an Android Q protobuf file
                try:
                    stats = _ReadUsageStatsPbFile(file)
                except:
                    logger.error('Parse Error: Non XML file and Non Protobuf file: {0:s}'.format(file))
                    continue

                if stats:
                    for stat in stats.packages:
                        usagestat = UsageStats()
                        usagestat.source = source
                        usagestat.usage_type = 'packages'
                        if stat.HasField('last_time_active_ms'):
                            last_time_active = stat.last_time_active_ms
                            if last_time_active < 0:
                                usagestat.last_time_active = abs(last_time_active)
                            else:
                                usagestat.last_time_active = filename_int + last_time_active

                            usagestat.last_time_active = datetime.datetime.fromtimestamp(usagestat.last_time_active / 1000,
                                datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%fZ')

                        if stat.HasField('total_time_active_ms'):
                            usagestat.time_active_in_msecs = abs(stat.total_time_active_ms)

                        usagestat.package = stats.stringpool.strings[usagestat.package_index - 1]

                        if stat.HasField('app_launch_count'):
                            usagestat.app_launch_count = abs(stat.app_launch_count)

                        data_list.append(
                            (usagestat.usage_type, usagestat.last_time_active, usagestat.time_active_in_msecs,
                             usagestat.time_active_in_secs, usagestat.last_time_service_used,
                             usagestat.last_time_visible,
                             usagestat.total_time_visible, usagestat.app_launch_count, usagestat.package,
                             usagestat.types, usagestat.cls, usagestat.source, usagestat.all_attributes))

                    for stat in stats.configurations:
                        usagestat = UsageStats()
                        usagestat.source = source
                        usagestat.usage_type = 'configurations'
                        if stat.HasField('last_time_active_ms'):
                            last_time_active = stat.last_time_active_ms
                            if last_time_active < 0:
                                usagestat.last_time_active = abs(last_time_active)
                            else:
                                usagestat.last_time_active = filename_int + last_time_active

                                usagestat.last_time_active = datetime.datetime.fromtimestamp(usagestat.last_time_active / 1000,
                                    datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%fZ')

                        if stat.HasField('total_time_active_ms'):
                            usagestat.time_active_in_msecs = abs(stat.total_time_active_ms)

                        usagestat.all_attributes = str(stat.config)

                        data_list.append(
                            (usagestat.usage_type, usagestat.last_time_active, usagestat.time_active_in_msecs,
                             usagestat.time_active_in_secs, usagestat.last_time_service_used,
                             usagestat.last_time_visible,
                             usagestat.total_time_visible, usagestat.app_launch_count, usagestat.package,
                             usagestat.types, usagestat.cls, usagestat.source, usagestat.all_attributes))

                    for stat in stats.event_log:
                        if stat.HasField('time_ms'):
                            last_time_active = stat.time_ms
                            if last_time_active < 0:
                                usagestat.last_time_active = abs(last_time_active)
                            else:
                                usagestat.last_time_active = filename_int + last_time_active

                            usagestat.last_time_active = datetime.datetime.fromtimestamp(usagestat.last_time_active / 1000,
                                datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%fZ')

                        if stat.HasField('package_index'):
                            usagestat.package = stats.stringpool.strings[stat.package_index - 1]
                        if stat.HasField('package_index'):
                            usagestat.cls = stats.stringpool.strings[stat.class_index - 1]
                        if stat.HasField('type'):
                            usagestat.types = str(EventType(stat.type)) if stat.type <= 18 else str(stat.type)

                        data_list.append(
                            (usagestat.usage_type, usagestat.last_time_active, usagestat.time_active_in_msecs,
                             usagestat.time_active_in_secs, usagestat.last_time_service_used,
                             usagestat.last_time_visible,
                             usagestat.total_time_visible, usagestat.app_launch_count, usagestat.package,
                             usagestat.types, usagestat.cls, usagestat.source, usagestat.all_attributes))

                    continue

    data['number_of_data'] = len(data_list)
    data['data'] = data_list

    return data


def _ReadUsageStatsPbFile(input_path):
    stats = usagestatsservice_pb2.IntervalStatsProto()

    with open (input_path, 'rb') as f:
        stats.ParseFromString(f.read())
        return stats

class UsageStats(object):
    def __init__(self):
        self.usage_type = None
        self.last_time_active = None
        self.time_active_in_msecs = None
        self.time_active_in_secs = None
        self.last_time_service_used = None
        self.last_time_visible = None
        self.total_time_visible = None
        self.app_launch_count = None
        self.package = None
        self.types = None
        self.cls = None
        self.source = None
        self.all_attributes = None


class EventType(IntEnum):
    NONE = 0
    MOVE_TO_FOREGROUND = 1
    MOVE_TO_BACKGROUND = 2
    END_OF_DAY = 3
    CONTINUE_PREVIOUS_DAY = 4
    CONFIGURATION_CHANGE = 5
    SYSTEM_INTERACTION = 6
    USER_INTERACTION = 7
    SHORTCUT_INVOCATION = 8
    CHOOSER_ACTION = 9
    NOTIFICATION_SEEN = 10
    STANDBY_BUCKET_CHANGED = 11
    NOTIFICATION_INTERRUPTION = 12
    SLICE_PINNED_PRIV = 13
    SLICE_PINNED = 14
    SCREEN_INTERACTIVE = 15
    SCREEN_NON_INTERACTIVE = 16
    KEYGUARD_SHOWN = 17
    KEYGUARD_HIDDEN = 18

    def __str__(self):
        return self.name # This returns 'KNOWN' instead of 'EventType.KNOWN'