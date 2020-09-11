# -*- coding: utf-8 -*-
"""android user apps process."""

import os
from pathlib import Path

from modules.android_user_apps import logger
from modules.android_user_apps.android_yogiyo import parse_yogiyo
from modules.android_user_apps.android_okcashbag import parse_okcashbag
from modules.android_user_apps.android_google_photo import parse_google_photo
from modules.android_user_apps.android_media import parse_media

SUPPORTED_USER_APPS = {
    'yogiyo': ('**/com.fineapp.yogiyo/databases/ygy-database*', 'parse_yogiyo'),
    'okcashbag': ('**/com.skmc.okcashbag.home_google/databases/c3po.wifi*', 'parse_okcashbag'),
    'google_photo': ('**/com.google.android.apps.photos/databases/gphotos*', 'parse_google_photo'),
    'media': ('**/com.android.providers.media/databases/*', 'parse_media')
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
    """Android user apps parsing process

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