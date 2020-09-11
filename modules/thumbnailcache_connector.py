# -*- coding: utf-8 -*-
import os
from modules import manager
from modules import interface
from modules import logger
from modules.windows_thumbnailcache import ThumbnailParser as tc


class ThumbnailCacheConnector(interface.ModuleConnector):
    NAME = 'thumbnailcache_connector'
    DESCRIPTION = 'Module for ThumbnailCache_connector'

    _plugin_classes = {}

    def __init__(self):
        super(ThumbnailCacheConnector, self).__init__()

    def Connect(self, configuration, source_path_spec, knowledge_base):
        print('[MODULE]: ThumbnailCacheConnector Connect')

        # 모든 yaml 파일 리스트
        this_file_path = os.path.dirname(os.path.abspath(__file__)) + os.sep + 'schema' + os.sep
        yaml_list = [this_file_path + 'lv1_os_win_thumbnail_cache.yaml']
        # 모든 테이블 리스트
        table_list = ['lv1_os_win_thumbnail_cache']

        if not self.check_table_from_yaml(configuration, yaml_list, table_list):
            return False

        par_id = configuration.partition_list[getattr(source_path_spec.parent, 'location', None)[1:]]
        if par_id is None:
            return False
        owner = ''
        query = f"SELECT name, parent_path, extension FROM file_info WHERE par_id='{par_id}' and (name like '%Thumbs%' or name regexp 'thumbcache_[0-9]') and size > 24 and extension = 'db' and ("
        for user_accounts in knowledge_base._user_accounts.values():
            for hostname in user_accounts.values():
                if hostname.identifier.find('S-1-5-21') == -1:
                    continue
                query += f"parent_path like '%{hostname.username}/AppData/Local/Microsoft/Windows/Explorer%' or "
        query = query[:-4] + ");"
        # print(query)
        # print(par_id)
        ThumbnailCache_files = configuration.cursor.execute_query_mul(query)
        # print(len(ThumbnailCache_files))
        if len(ThumbnailCache_files) == 0:
            return False

        insert_ThumbnailCache_info = []

        for ThumbnailCache in ThumbnailCache_files:
            ThumbnailCache_path = ThumbnailCache[1][ThumbnailCache[1].find('/'):] + '/' + ThumbnailCache[
                0]  # document full path
            fileExt = ThumbnailCache[2]
            fileName = ThumbnailCache[0]
            owner = ThumbnailCache[1][ThumbnailCache[1].find('/'):].split('/')[2]
            # Windows.old 폴더 체크
            if 'Windows.old' in ThumbnailCache_path:
                # print(ThumbnailCache_path)
                fileExt = ThumbnailCache[2]
                fileName = ThumbnailCache[0]
                owner = ThumbnailCache[1][ThumbnailCache[1].find('/'):].split('/')[3] + "(Windows.old)"

            output_path = configuration.root_tmp_path + os.sep + configuration.case_id + os.sep + configuration.evidence_id + os.sep + par_id
            img_output_path = output_path + os.sep + "ThumbnailCache_img" + os.sep + owner + os.sep + fileName[:-3]
            self.ExtractTargetFileToPath(
                source_path_spec=source_path_spec,
                configuration=configuration,
                file_path=ThumbnailCache_path,
                output_path=output_path)

            fn = output_path + os.path.sep + fileName
            app_path = os.path.abspath(os.path.dirname(__file__)) + os.path.sep + "windows_thumbnailcache"

            results = tc.main(fn, app_path, img_output_path)
            # print(owner)
            # print(fileName)
            # print(results)

            if not results:
                os.remove(output_path + os.sep + fileName)
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

            os.remove(output_path + os.sep + fileName)
            # ThumbnailCache

        print('[MODULE]: ThumbnailCache')
        query = "Insert into lv1_os_win_thumbnail_cache values (%s,%s,%s,%s,%s,%s,%s,%s,%s);"
        configuration.cursor.bulk_execute(query, insert_ThumbnailCache_info)

        print('[MODULE]: ThumbnailCache Complete')

        #except Exception as e:
        #    print("ThumbnailCache Connector Error", e)


manager.ModulesManager.RegisterModule(ThumbnailCacheConnector)
