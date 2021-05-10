# -*- coding: utf-8 -*-
import os
from modules import manager
from modules import interface
from modules import logger
from modules.windows_thumbnailcache import ThumbnailParser as tc


class ThumbnailCacheConnector(interface.ModuleConnector):
    NAME = 'thumbnailcache_connector'
    DESCRIPTION = 'Module for ThumbnailCache'

    _plugin_classes = {}

    def __init__(self):
        super(ThumbnailCacheConnector, self).__init__()

    def Connect(self, par_id, configuration, source_path_spec, knowledge_base):

        # 모든 yaml 파일 리스트
        this_file_path = os.path.dirname(os.path.abspath(__file__)) + os.sep + 'schema' + os.sep
        yaml_list = [this_file_path + 'lv1_os_win_thumbnail_cache.yaml']
        # 모든 테이블 리스트
        table_list = ['lv1_os_win_thumbnail_cache']

        if not self.check_table_from_yaml(configuration, yaml_list, table_list):
            return False

        query = f"SELECT name, parent_path, extension FROM file_info WHERE par_id='{par_id}' " \
                f"and (name like '%Thumbs%' or name regexp 'thumbcache_[0-9]') and size > 24 and extension = 'db' and ("
        query_separator = self.GetQuerySeparator(source_path_spec, configuration)
        path_separator = self.GetPathSeparator(source_path_spec) 

        user_accounts_list = knowledge_base._user_accounts.values()
        if user_accounts_list:
            for user_accounts in user_accounts_list:
                for hostname in user_accounts.values():
                    if hostname.identifier.find('S-1-5-21') == -1:
                        continue
                    query += f"parent_path like '%{hostname.username}{query_separator}AppData{query_separator}Local" \
                        f"{query_separator}Microsoft{query_separator}Windows{query_separator}Explorer%' or "
            query = query[:-4] + ");"
        else:
            # print("No user accounts")
            return False

        thumbnail_cache_files = configuration.cursor.execute_query_mul(query)

        if thumbnail_cache_files == -1 or len(thumbnail_cache_files) == 0:
            return False

        insert_ThumbnailCache_info = []

        for ThumbnailCache in thumbnail_cache_files:
            thumbnail_cache_path = ThumbnailCache[1][ThumbnailCache[1].find(path_separator):] + path_separator + ThumbnailCache[0]  # document full path
            file_name = ThumbnailCache[0]
            owner = ThumbnailCache[1][ThumbnailCache[1].find(path_separator):].split(path_separator)[2]

            # Windows.old 폴더 체크
            if 'Windows.old' in thumbnail_cache_path:
                file_name = ThumbnailCache[0]
                owner = ThumbnailCache[1][ThumbnailCache[1].find(path_separator):].split(path_separator)[3] + "(Windows.old)"

            output_path = configuration.root_tmp_path + os.sep + configuration.case_id + os.sep + configuration.evidence_id + os.sep + par_id
            img_output_path = output_path + os.sep + "ThumbnailCache_img" + os.sep + owner + os.sep + file_name[:-3]
            self.ExtractTargetFileToPath(
                source_path_spec=source_path_spec,
                configuration=configuration,
                file_path=thumbnail_cache_path,
                output_path=output_path)

            fn = output_path + os.path.sep + file_name
            app_path = os.path.abspath(os.path.dirname(__file__)) + os.path.sep + "windows_thumbnailcache"

            results = tc.main(fn, app_path, img_output_path)

            if not results:
                os.remove(output_path + os.sep + file_name)
                continue

            for i in range(len(results["ThumbsData"])):
                if i == 0:
                    continue
                result = results["ThumbsData"][i]

                filename = result[0]
                filesize = result[1]
                imagetype = result[2]
                data = result[3]
                sha1 = result[4]
                tmp = [par_id, configuration.case_id, configuration.evidence_id, owner, filename, filesize,
                       imagetype, data, sha1]

                insert_ThumbnailCache_info.append(tuple(tmp))

            os.remove(output_path + os.sep + file_name)


        query = "Insert into lv1_os_win_thumbnail_cache values (%s, %s, %s, %s, %s, %s, %s, %s, %s);"
        configuration.cursor.bulk_execute(query, insert_ThumbnailCache_info)


manager.ModulesManager.RegisterModule(ThumbnailCacheConnector)
