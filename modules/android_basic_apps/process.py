# -*- coding: utf-8 -*-
"""android basic apps process."""

import os
from pathlib import Path

from modules.android_basic_apps import logger
from modules.android_basic_apps.android_accounts_ce import parse_accounts_ce
from modules.android_basic_apps.android_accounts_de import parse_accounts_de
from modules.android_basic_apps.android_call_logs import parse_call_logs
from modules.android_basic_apps.android_contacts import parse_contacts
from modules.android_basic_apps.android_file_cache import parse_file_cache
from modules.android_basic_apps.android_recent_files import parse_recent_files
from modules.android_basic_apps.android_siminfo import parse_sim_info
from modules.android_basic_apps.android_smsmms import parse_smsmms
from modules.android_basic_apps.android_system_info import parse_system_info
from modules.android_basic_apps.android_usagestats import parse_usagestats
from modules.android_basic_apps.android_user_dict import parse_user_dict
from modules.android_basic_apps.android_wifi import parse_wifi


SUPPORTED_BASIC_APPS = {
    'accounts_ce': ('**/system_ce/*/accounts_ce.db', 'parse_accounts_ce'),
    'accounts_de': ('**/system_de/*/accounts_de.db', 'parse_accounts_de'),
    'calllog': ('**/com.android.providers.contacts/databases/calllog.db', 'parse_call_logs'),
    'contacts': ('**/com.android.providers.contacts/databases/contacts2.db', 'parse_contacts'),
    'file_cache': ('**/com.sec.android.app.myfiles/databases/FileCache.db', 'parse_file_cache'),
    'recent_files': ('**/com.sec.android.app.myfiles/databases/myfiles.db', 'parse_recent_files'),
    'smsmms': ('**/com.android.providers.telephony/databases/mmssms.db', 'parse_smsmms'),
    'sim_information': ('**/com.android.providers.telephony/databases/telephony.db', 'parse_sim_info'),
    'sim_information_dat': ('**/SimCard.dat', 'parse_sim_info'),
    'system_info': ('**/settings_secure.xml', 'parse_system_info'),
    'userdict': ('**/com.android.providers.userdictionary/databases/user_dict.db', 'parse_user_dict'),
    'usagestats': ('**/usagestats/*', 'parse_usagestats'),
    'wifi': ('**/WifiConfigStore.xml', 'parse_wifi')
}


def search(target_directory, pattern):
    """Directory search using pattern.

    Args:
        target_directory (str): target directory.
        pattern (str): pattern.
    """
    pathlist = []
    for file in Path(target_directory).rglob(pattern):
        pathlist.append(file)
    return pathlist


def process(target_files, func, result_path):
    """Android basic apps parsing process

    Args:
        target_files (list): target files.
        func (str): function name.
        result_path (str): result path.
    """
    try:
        if not os.path.exists(result_path):
            os.mkdir(result_path)

    except Exception as exception:
        logger.error('cannot create result directory at path {0:s}:{1!s}'.format(result_path, exception))

    method = globals()[func]
    results = method(target_files, result_path)

    return results