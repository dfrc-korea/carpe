# -*- coding: utf-8 -*-
import os
from modules import manager
from modules import interface
from modules import logger
from modules.windows_iconcache import IconCacheParser as ic


class IconCacheConnector(interface.ModuleConnector):
    NAME = 'iconcache_connector'
    DESCRIPTION = 'Module for Iconcache'

    _plugin_classes = {}

    def __init__(self):
        super(IconCacheConnector, self).__init__()

    def Connect(self, par_id, configuration, source_path_spec, knowledge_base):

        this_file_path = os.path.dirname(os.path.abspath(__file__)) + os.sep + 'schema' + os.sep

        # 모든 yaml 파일 리스트
        yaml_list = [this_file_path + 'lv1_os_win_icon_cache.yaml']
        # 모든 테이블 리스트
        table_list = ['lv1_os_win_icon_cache']

        # 모든 테이블 생성
        if not self.check_table_from_yaml(configuration, yaml_list, table_list):
            return False
        
        try:
            query = f"SELECT name, parent_path, extension FROM file_info WHERE par_id='{par_id}' " \
                    f"and extension = 'db' and size > 24 and name regexp 'iconcache_[0-9]' and ("

            user_list = knowledge_base._user_accounts.values()
            if user_list:
                for user_accounts in user_list:
                    for hostname in user_accounts.values():
                        if hostname.identifier.find('S-1-5-21') == -1:
                            continue
                        query += f"parent_path like '%{hostname.username}%' or "
                query = query[:-4] + ");"
            else:
                # print("No user list")
                return False

            iconcache_files = configuration.cursor.execute_query_mul(query)
            if len(iconcache_files) == 0:
                #print("There are no iconcache files")
                return False

            insert_iconcache_info = []
            query_separator = self.GetQuerySeparator(source_path_spec, configuration)
            path_separator = self.GetPathSeparator(source_path_spec)
            for iconcache in iconcache_files:
                iconcache_path = iconcache[1][iconcache[1].find(path_separator):] + path_separator + iconcache[0]  # document full path
                fileName = iconcache[0]
                owner = iconcache[1][iconcache[1].find(path_separator):].split(path_separator)[2]
                # Windows.old 폴더 체크
                if 'Windows.old' in iconcache_path:
                    fileName = iconcache[0]
                    owner = iconcache[1][iconcache[1].find(path_separator):].split(path_separator)[3] + "(Windows.old)"

                output_path = configuration.root_tmp_path + os.sep + configuration.case_id + os.sep + configuration.evidence_id + os.sep + par_id
                img_output_path = output_path + os.sep + "iconcache_img" + os.sep + owner + os.sep + fileName[:-3]
                self.ExtractTargetFileToPath(
                    source_path_spec=source_path_spec,
                    configuration=configuration,
                    file_path=iconcache_path,
                    output_path=output_path)

                fn = output_path + os.path.sep + fileName
                app_path = os.path.abspath(os.path.dirname(__file__)) + os.path.sep + "windows_iconcache"

                if os.path.exists(fn):
                    results = ic.main(fn, app_path, img_output_path)

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
                    tmp = []

                    tmp.append(par_id)
                    tmp.append(configuration.case_id)
                    tmp.append(configuration.evidence_id)
                    tmp.append(owner)
                    tmp.append(filename)
                    tmp.append(filesize)
                    tmp.append(imagetype)
                    tmp.append(data)
                    tmp.append(sha1)

                    insert_iconcache_info.append(tuple(tmp))

                os.remove(output_path + os.sep + fileName)

            query = "Insert into lv1_os_win_icon_cache values (%s, %s, %s, %s, %s, %s, %s, %s, %s);"
            configuration.cursor.bulk_execute(query, insert_iconcache_info)

        except Exception as e:
            logger.error("IconCache Connector Error: {0!s}".format(e))


manager.ModulesManager.RegisterModule(IconCacheConnector)
