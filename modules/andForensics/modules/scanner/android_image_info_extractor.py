#-*- coding: utf-8 -*-
import logging
from modules.andForensics.modules.utils.android_sqlite3 import SQLite3
from modules.andForensics.modules.utils.android_TSK import TSK

logger = logging.getLogger('andForensics')

class ImageInfo(object):
    def extract_fs_information(case):
        logger.info('    - File system information with TSK (loaddb)...')
        if not TSK.loaddb(case.image_file_path, case.load_db_path):
            logger.error('\"tsk_loaddb %s\" failed.' % case.image_file_path)
            exit(0)

#---------------------------------------------------------------------------------------------------------------
    def extract_fs_status(case):
        logger.info('    - File system status...')

        # 1. total size
        query = "SELECT SUM(size) FROM tsk_files"
        size_image = '%d' % SQLite3.execute_fetch_query(query, case.load_db_path)

        # 2. unalloc area size
        query = "SELECT SUM(size) FROM tsk_files WHERE type = 4"
        size_unalloc_area = '%d' % SQLite3.execute_fetch_query(query, case.load_db_path)

        # 3. alloc area size
        size_alloc_area = '%d' % (int(size_image) - int(size_unalloc_area))

        # 4. metadata size
        query = "SELECT SUM(size) FROM tsk_files WHERE dir_type = 3"
        size_metadata_area = '%d' % SQLite3.execute_fetch_query(query, case.load_db_path)

        # 5. app installation data size
        query = "SELECT SUM(size) FROM tsk_files WHERE parent_path LIKE '/app/%' and dir_type != 3"
        size_apks = '%d' % SQLite3.execute_fetch_query(query, case.load_db_path)

        # 6. app userdata size
        query = "SELECT SUM(size) FROM tsk_files WHERE parent_path LIKE '/data/%' and dir_type != 3"
        size_applogs = '%d' % SQLite3.execute_fetch_query(query, case.load_db_path)

        # 7. sdcard area size
        query = "SELECT SUM(size) FROM tsk_files WHERE parent_path LIKE '/media/%' and dir_type != 3"
        size_sdcard_area = '%d' % SQLite3.execute_fetch_query(query, case.load_db_path)

        query = 'INSERT INTO image_file_info(image_file_path, size_image, size_alloc_area, size_unalloc_area, size_metadata_area, size_apks, size_applogs, size_sdcard_area) VALUES("%s", %d, %d, %d, %d, %d, %d, %d)' % (case.image_file_path, int(size_image), int(size_alloc_area), int(size_unalloc_area), int(size_metadata_area), int(size_apks), int(size_applogs), int(size_sdcard_area))
        SQLite3.execute_commit_query(query, case.preprocess_db_path)
