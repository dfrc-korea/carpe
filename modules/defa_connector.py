# -*- coding: utf-8 -*-
"""module for DEFA."""
import os
import shutil
import hashlib
import configparser
import zipfile
from zipfile import ZipFile
from zipfile import BadZipFile
import xml.etree.ElementTree as ET
from datetime import datetime
from dfvfs.resolver import resolver as dfvfs_resolver


from elasticsearch import Elasticsearch, helpers

from modules import logger
from modules import manager
from modules import interface


class DEFAConnector(interface.ModuleConnector):
    NAME = 'defa_connector'
    DESCRIPTION = 'Module for DEFA'

    _plugin_classes = {}

    def __init__(self):
        super(DEFAConnector, self).__init__()

    def Connect(self, par_id, configuration, source_path_spec, knowledge_base):

        if configuration.standalone_check:
            this_file_path = os.path.dirname(os.path.abspath(__file__)) + os.sep + 'schema' + os.sep
            # 모든 yaml 파일 리스트
            yaml_list = [this_file_path + 'lv1_file_document.yaml']

            # 모든 테이블 리스트
            table_list = ['lv1_file_document']

            if not self.check_table_from_yaml(configuration, yaml_list, table_list):
                return False

        # 선택한 플러그인 파일만 읽어오기
        hwp_plugin = None
        doc_plugin = None
        docx_plugin = None
        ppt_plugin = None
        pptx_plugin = None
        xls_plugin = None
        xlsx_plugin = None
        pdf_plugin = None
        text_plugin = None

        query_separator = self.GetQuerySeparator(source_path_spec, configuration)
        path_separator = self.GetPathSeparator(source_path_spec)
        # sig_type -> extension 임시 변경,
        query = f"SELECT name, parent_path, sig_type, extension, mtime, atime, ctime, etime, mtime_nano, atime_nano, " \
                f"ctime_nano, etime_nano, additional_mtime, additional_atime, additional_ctime, additional_etime, " \
                f"additional_mtime_nano, additional_atime_nano, additional_ctime_nano, additional_etime_nano, inode " \
                f"FROM file_info WHERE par_id='{par_id}'" \
                f"and parent_path not like '%{query_separator}Hnc{query_separator}Office%' " \
                f"and parent_path not like '%$Recycle.Bin{query_separator}S-1-5-21%' and name not like '$I%' and ("  # and parent_path not like '%_damaged/%' 임시

        for i in range(0, len(self._plugins)):
            if self._plugins[i].plugin_name == 'HWP':
                query += " LOWER(extension) = 'hwp' "
                hwp_plugin = self._plugins[i]
            elif self._plugins[i].plugin_name == 'DOC':
                query += " LOWER(extension) = 'doc' "
                doc_plugin = self._plugins[i]
            elif self._plugins[i].plugin_name == 'PPT':
                query += " LOWER(extension) = 'ppt' "
                ppt_plugin = self._plugins[i]
            elif self._plugins[i].plugin_name == 'XLS':
                query += " LOWER(extension) = 'xls' "
                xls_plugin = self._plugins[i]
            elif self._plugins[i].plugin_name == 'DOCX':
                query += " LOWER(extension) = 'docx' "
                docx_plugin = self._plugins[i]
            elif self._plugins[i].plugin_name == 'PPTX':
                query += " LOWER(extension) = 'pptx' "
                pptx_plugin = self._plugins[i]
            elif self._plugins[i].plugin_name == 'XLSX':
                query += " LOWER(extension) = 'xlsx' "
                xlsx_plugin = self._plugins[i]
            elif self._plugins[i].plugin_name == 'PDF':
                query += " LOWER(extension) = 'pdf' "
                pdf_plugin = self._plugins[i]
            # geunyeong start
            elif self._plugins[i].plugin_name == 'TEXT':
                query += " LOWER(extension) = 'txt' or LOWER(extension) = 'log' "
                text_plugin = self._plugins[i]
            # geunyeong end

            if i == len(self._plugins) - 1:
                query += ");"
            else:
                query += "or "

        document_files = configuration.cursor.execute_query_mul(query)

        if document_files == -1 or len(document_files) == 0:
            #print("There are no document files")
            return False

        ### Download Check ###
        query = f"SELECT name, parent_path FROM file_info WHERE par_id='{par_id}'" \
                f"and name like '%Zone.Identifier';"

        zone_identifier_files = configuration.cursor.execute_query_mul(query)
        tmp_list = list()
        for zone in zone_identifier_files:
            tmp_list.append(zone[1][4:] + path_separator + zone[0][:-16])
        zone_list = set(tmp_list)

        if configuration.standalone_check:
            insert_document = list()
        else:
            config = configparser.ConfigParser()
            conf_file = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) \
                        + os.sep + 'config' + os.sep + 'carpe.conf'
            if not os.path.exists(conf_file):
                raise Exception('%s file does not exist.\n' % conf_file)
            config.read(conf_file)
            _host = config.get('elasticsearch', 'host')
            _port = config.getint('elasticsearch', 'port')
            _elastic_id = config.get('elasticsearch', 'id')
            _elastic_passwd = config.get('elasticsearch', 'passwd')
            _index_name = config.get('document', 'index')
            _type_name = config.get('document', 'type')
            es = Elasticsearch(hosts=_host, port=_port, http_auth=(_elastic_id, _elastic_passwd))

        try:
            tsk_file_system = self.get_tsk_file_system(source_path_spec, configuration)
        except Exception as exception:
            tsk_file_system = None
            logger.debug(exception)
        error_count = 0
        for document in document_files:
            document_path = document[1][document[1].find(path_separator):] + path_separator + document[0]
            output_path = configuration.root_tmp_path + os.sep + configuration.case_id + os.sep + \
                          configuration.evidence_id + os.sep + par_id + os.sep \
                          + hashlib.sha1(document_path.encode('utf-8')).hexdigest()
            ole_path = output_path + os.sep + "ole"

            if not os.path.exists(output_path):
                os.makedirs(output_path)
                os.makedirs(ole_path)

            if tsk_file_system == None:
                if source_path_spec.TYPE_INDICATOR == 'OS':
                    if os.path.isdir(source_path_spec.location):
                        for root, dirs, files in os.walk(source_path_spec.location):
                            if document[0] in files:
                                shutil.copy(document[1]+ path_separator + document[0], output_path + path_separator + document[0])
                    elif os.path.isfile(source_path_spec.location):
                        shutil.copy(source_path_spec.location, output_path + path_separator + document[0])
            else:
                self.extract_file_to_path(tsk_file_system=tsk_file_system,
                                          inode=int(document[20]),
                                          file_name=document[0],
                                          output_path=output_path)

            # self.ExtractTargetFileToPath(
            #     source_path_spec=source_path_spec,
            #     configuration=configuration,
            #     file_path=document_path,
            #     output_path=output_path)

            file_path = output_path + os.sep + document[0]
            extension = document[3].lower()
            sigFile = document[2].lower()
            ext_sig_map = {'hwp': 'olecf', 'doc': 'olecf', 'pdf': 'pdf', 'xls': 'olecf', 'ppt': 'olecf',
                           'docx': 'ooxml', 'xlsx': 'ooxml', 'pptx': 'ooxml', 'log': 'text', 'txt': 'text'}

            try:
                #if ext_sig_map[extension] != sigFile:
                if extension == "log" or extension == "txt":
                    pass
                elif ext_sig_map.get(extension, None) != sigFile:
                    if sigFile != '' and sigFile != extension:
                        self._UpdateFileInfoRecords(configuration, document)
                        logger.error(document[0] + ' unmatched signature and extension')
                        #raise Exception()

                if extension == 'hwp':
                    self.print_run_info(f"Parse HWP File : \"{document[0]}\"", start=True)
                    result = hwp_plugin.Process(fp=file_path, ole_path=ole_path)
                    self.print_run_info(f"Parse HWP File : \"{document[0]}\"", start=False)
                elif extension == 'doc':
                    self.print_run_info(f"Parse DOC File : \"{document[0]}\"", start=True)
                    result = doc_plugin.Process(fp=file_path, ole_path=ole_path)
                    self.print_run_info(f"Parse DOC File : \"{document[0]}\"", start=False)
                elif extension == 'ppt':
                    self.print_run_info(f"Parse PPT File : \"{document[0]}\"", start=True)
                    result = ppt_plugin.Process(fp=file_path, ole_path=ole_path)
                    self.print_run_info(f"Parse PPT File : \"{document[0]}\"", start=False)
                elif extension == 'xls':
                    self.print_run_info(f"Parse XLS File : \"{document[0]}\"", start=True)
                    result = xls_plugin.Process(fp=file_path, ole_path=ole_path)
                    self.print_run_info(f"Parse XLS File : \"{document[0]}\"", start=False)
                elif extension == 'docx':
                    self.print_run_info(f"Parse DOCX File : \"{document[0]}\"", start=True)
                    result = docx_plugin.Process(fp=file_path, ole_path=ole_path)
                    self.print_run_info(f"Parse DOCX File : \"{document[0]}\"", start=False)
                elif extension == 'pptx':
                    self.print_run_info(f"Parse PPTX File : \"{document[0]}\"", start=True)
                    result = pptx_plugin.Process(fp=file_path, ole_path=ole_path)
                    self.print_run_info(f"Parse PPTX File : \"{document[0]}\"", start=False)
                elif extension == 'xlsx':
                    self.print_run_info(f"Parse XLSX File : \"{document[0]}\"", start=True)
                    result = xlsx_plugin.Process(fp=file_path, ole_path=ole_path)
                    self.print_run_info(f"Parse XLSX File : \"{document[0]}\"", start=False)
                elif extension == 'pdf':
                    self.print_run_info(f"Parse PDF File : \"{document[0]}\"", start=True)
                    result = pdf_plugin.Process(fp=file_path, ole_path=ole_path)
                    self.print_run_info(f"Parse PDF File : \"{document[0]}\"", start=False)
                elif extension == 'txt' or extension == 'log':
                    self.print_run_info(f"Parse Text File : \"{document[0]}\"", start=True)
                    result = text_plugin.Process(fp=file_path, meta=document)
                    self.print_run_info(f"Parse Text File : \"{document[0]}\"", start=False)
            except Exception as e:
                # print("Error : " + str(e))
                error_count += 1
                continue

            result.content = result.content.replace('\x00','') # \x00 때문에 text가 아닌 BLOB으로 들어감
            result.case_id = configuration.case_id
            result.evdnc_id = configuration.evidence_id
            result.download_path = file_path
            result.full_path = document_path  # 이미지 내 full_path
            result.path_with_ext = document_path  # 이미지 내 full_path
            result.parent_full_path = document_path[:document_path.rfind('\\')]
            result.name = document[0]
            result.original_size = os.path.getsize(file_path)
            result.ole_path = ole_path
            result.content_size = len(result.content)

            # for else
            if source_path_spec.TYPE_INDICATOR == 'TSK' or source_path_spec.TYPE_INDICATOR == 'APFS':
                try:
                    result.mft_st_created_time = datetime.utcfromtimestamp(
                        int(str(document[6]).zfill(10) + str(document[10]).zfill(9)[0:3]) / 1000).strftime(
                        '%Y-%m-%d %H:%M:%S.%f').replace(' ', 'T') + 'Z'
                    result.mft_st_last_modified_time = datetime.utcfromtimestamp(
                        int(str(document[4]).zfill(10) + str(document[8]).zfill(9)[0:3]) / 1000).strftime(
                        '%Y-%m-%d %H:%M:%S.%f').replace(' ', 'T') + 'Z'
                    result.mft_st_last_accessed_time = datetime.utcfromtimestamp(
                        int(str(document[5]).zfill(10) + str(document[9]).zfill(9)[0:3]) / 1000).strftime(
                        '%Y-%m-%d %H:%M:%S.%f').replace(' ', 'T') + 'Z'
                    result.mft_st_entry_modified_time = datetime.utcfromtimestamp(
                        int(str(document[7]).zfill(10) + str(document[11]).zfill(9)[0:3]) / 1000).strftime(
                        '%Y-%m-%d %H:%M:%S.%f').replace(' ', 'T') + 'Z'

                    result.mft_st_created_time = str(
                        configuration.apply_time_zone(result.mft_st_created_time, knowledge_base.time_zone))
                    result.mft_st_last_modified_time = str(
                        configuration.apply_time_zone(result.mft_st_last_modified_time, knowledge_base.time_zone))
                    result.mft_st_last_accessed_time = str(
                        configuration.apply_time_zone(result.mft_st_last_accessed_time, knowledge_base.time_zone))
                    result.mft_st_entry_modified_time = str(
                        configuration.apply_time_zone(result.mft_st_entry_modified_time, knowledge_base.time_zone))
                except Exception as e:
                    logger.debug(str(e))
            elif source_path_spec.TYPE_INDICATOR == 'NTFS':  # for Windows
                try:
                    result.mft_st_created_time = str(datetime.utcfromtimestamp(
                        int(str(document[6]).zfill(11) + str(document[10]).zfill(7)) / 10000000 - 11644473600)).replace(' ',
                                                                                                                        'T') + 'Z'
                    result.mft_st_last_modified_time = str(datetime.utcfromtimestamp(
                        int(str(document[4]).zfill(11) + str(document[8]).zfill(7)) / 10000000 - 11644473600)).replace(' ',
                                                                                                                       'T') + 'Z'
                    result.mft_st_last_accessed_time = str(datetime.utcfromtimestamp(
                        int(str(document[5]).zfill(11) + str(document[9]).zfill(7)) / 10000000 - 11644473600)).replace(' ',
                                                                                                                       'T') + 'Z'
                    result.mft_st_entry_modified_time = str(datetime.utcfromtimestamp(
                        int(str(document[7]).zfill(11) + str(document[11]).zfill(7)) / 10000000 - 11644473600)).replace(' ',
                                                                                                                        'T') + 'Z'
                    result.mft_st_created_time = str(
                        configuration.apply_time_zone(result.mft_st_created_time, knowledge_base.time_zone))
                    result.mft_st_last_modified_time = str(
                        configuration.apply_time_zone(result.mft_st_last_modified_time, knowledge_base.time_zone))
                    result.mft_st_last_accessed_time = str(
                        configuration.apply_time_zone(result.mft_st_last_accessed_time, knowledge_base.time_zone))
                    result.mft_st_entry_modified_time = str(
                        configuration.apply_time_zone(result.mft_st_entry_modified_time, knowledge_base.time_zone))

                    result.mft_fn_created_time = str(datetime.utcfromtimestamp(
                        int(str(document[14]).zfill(11) + str(document[18]).zfill(7)) / 10000000 - 11644473600)).replace(' ',
                                                                                                                         'T') + 'Z'
                    result.mft_fn_last_modified_time = str(datetime.utcfromtimestamp(
                        int(str(document[12]).zfill(11) + str(document[16]).zfill(7)) / 10000000 - 11644473600)).replace(' ',
                                                                                                                         'T') + 'Z'
                    result.mft_fn_last_accessed_time = str(datetime.utcfromtimestamp(
                        int(str(document[13]).zfill(11) + str(document[17]).zfill(7)) / 10000000 - 11644473600)).replace(' ',
                                                                                                                         'T') + 'Z'
                    result.mft_fn_entry_modified_time = str(datetime.utcfromtimestamp(
                        int(str(document[15]).zfill(11) + str(document[19]).zfill(7)) / 10000000 - 11644473600)).replace(' ',
                                                                                                                         'T') + 'Z'
                    result.mft_fn_created_time = str(
                        configuration.apply_time_zone(result.mft_fn_created_time, knowledge_base.time_zone))
                    result.mft_fn_last_modified_time = str(
                        configuration.apply_time_zone(result.mft_fn_last_modified_time, knowledge_base.time_zone))
                    result.mft_fn_last_accessed_time = str(
                        configuration.apply_time_zone(result.mft_fn_last_accessed_time, knowledge_base.time_zone))
                    result.mft_fn_entry_modified_time = str(
                        configuration.apply_time_zone(result.mft_fn_entry_modified_time, knowledge_base.time_zone))

                    result.is_downloaded = 1 if document_path in zone_list else 0  # check Zone.Identifier, 1 = True, 0 = False
                    result.is_copied = 1 if int(str(document[4]).zfill(11) + str(document[8]).zfill(7)) < int(
                        str(document[6]).zfill(11) + str(document[10]).zfill(
                            7)) else 0  # check Mtime > Ctime, 1 = True, 0 = False
                except Exception as e:
                    logger.debug(str(e))
            elif source_path_spec.TYPE_INDICATOR == 'OS':  # for 파일 및 폴더 입력
                try:
                    result.mft_st_created_time = str(datetime.utcfromtimestamp(
                        int(str(document[6]).zfill(12)) / 100)).replace(' ','T') + 'Z'
                    result.mft_st_last_modified_time = str(datetime.utcfromtimestamp(
                        int(str(document[4]).zfill(12)) / 100)).replace(' ','T') + 'Z'
                    result.mft_st_last_accessed_time = str(datetime.utcfromtimestamp(
                        int(str(document[5]).zfill(12)) / 100)).replace(' ','T') + 'Z'
                    result.mft_st_entry_modified_time = str(datetime.utcfromtimestamp(
                        int(str(document[7]).zfill(12)) / 100)).replace(' ','T') + 'Z'
                    result.mft_st_created_time = str(
                        configuration.apply_time_zone(result.mft_st_created_time, knowledge_base.time_zone))
                    result.mft_st_last_modified_time = str(
                        configuration.apply_time_zone(result.mft_st_last_modified_time, knowledge_base.time_zone))
                    result.mft_st_last_accessed_time = str(
                        configuration.apply_time_zone(result.mft_st_last_accessed_time, knowledge_base.time_zone))
                    result.mft_st_entry_modified_time = str(
                        configuration.apply_time_zone(result.mft_st_entry_modified_time, knowledge_base.time_zone))

                    result.mft_fn_created_time = str(datetime.utcfromtimestamp(
                        int(str(document[14]).zfill(12)) / 100)).replace(' ','T') + 'Z'
                    result.mft_fn_last_modified_time = str(datetime.utcfromtimestamp(
                        int(str(document[12]).zfill(12)) / 100)).replace(' ','T') + 'Z'
                    result.mft_fn_last_accessed_time = str(datetime.utcfromtimestamp(
                        int(str(document[13]).zfill(12)) / 100)).replace(' ','T') + 'Z'
                    result.mft_fn_entry_modified_time = str(datetime.utcfromtimestamp(
                        int(str(document[15]).zfill(12)) / 100)).replace(' ','T') + 'Z'
                    result.mft_fn_created_time = str(
                        configuration.apply_time_zone(result.mft_fn_created_time, knowledge_base.time_zone))
                    result.mft_fn_last_modified_time = str(
                        configuration.apply_time_zone(result.mft_fn_last_modified_time, knowledge_base.time_zone))
                    result.mft_fn_last_accessed_time = str(
                        configuration.apply_time_zone(result.mft_fn_last_accessed_time, knowledge_base.time_zone))
                    result.mft_fn_entry_modified_time = str(
                        configuration.apply_time_zone(result.mft_fn_entry_modified_time, knowledge_base.time_zone))

                    result.is_downloaded = 1 if document_path in zone_list else 0  # check Zone.Identifier, 1 = True, 0 = False
                    result.is_copied = 1 if int(str(document[4]).zfill(12)) < int(
                        str(document[6]).zfill(12)
                    ) else 0  # check Mtime > Ctime, 1 = True, 0 = False
                except Exception as e:
                    logger.debug(str(e))
            # is_created
            result.is_created = 0
            try:
                if result.createdtime != 'None' and result.createdtime != '' and result.createdtime is not None:
                    if datetime.fromisoformat(result.createdtime.replace('Z', '')) > datetime.fromisoformat(
                            result.mft_st_created_time.split('+')[0]) == True:
                        result.is_created = 1
            except Exception as e:
                logger.debug(str(e))

            rsid_list = []

            # RSID
            result.rsid = ""
            ext = os.path.splitext(file_path)[-1]
            if ext == '.docx':
                try:
                    zfile = zipfile.ZipFile(file_path)

                    for a in zfile.filelist:
                        if 'word/settings.xml' in a.filename:
                            form = zfile.read(a)
                            xmlroot = ET.fromstring(form)
                            for i in xmlroot:
                                if 'rsid' in i.tag:
                                    for rsid in i:
                                        rsid_list.append(rsid.attrib.get(
                                            "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val"))
                except BadZipFile as e:
                    logger.debug(str(e))

            if configuration.standalone_check:
                if result.has_content:
                    result.has_content = 1
                else:
                    result.has_content = 0

                if result.has_metadata:
                    result.has_metadata = 1
                else:
                    result.has_metadata = 0

                if result.is_damaged:
                    result.is_damaged = 1
                else:
                    result.is_damaged = 0
                insert_document.append(tuple(
                    [par_id, configuration.case_id, configuration.evidence_id, result.author, result.case_name,
                     result.category, result.comment, result.company, result.content, result.content_size,
                     result.createdtime, result.creation_time, result.creator, result.date, result.doc_id,
                     result.doc_type, result.doc_type_sub, result.download_path, result.evdnc_name,
                     result.exclude_user_id, result.explanation, result.ext, result.fail_code, result.full_path,
                     result.has_content, result.has_exif, result.has_metadata, result.id, result.is_damaged,
                     result.is_fail, result.last_access_time, result.last_written_time, result.lastprintedtime,
                     result.lastsavedby, result.lastsavedtime, result.manager, result.name, result.ole_path,
                     result.original_size, result.parent_full_path, result.path_with_ext, result.programname,
                     result.revisionnumber, result.sha1_hash, result.subject, result.tags, result.title,
                     result.totaltime, result.trapped, result.version, result.work_dir, result.mft_st_created_time,
                     result.mft_st_last_modified_time, result.mft_st_last_accessed_time,
                     result.mft_st_entry_modified_time, result.mft_fn_created_time, result.mft_fn_last_modified_time,
                     result.mft_fn_last_accessed_time, result.mft_fn_entry_modified_time, result.is_downloaded,
                     result.is_copied, result.is_created, ''.join(rsid_list)]))

            else:
                try:
                    es.index(index=_index_name, doc_type=_type_name, body=result.__dict__)
                except Exception as e:
                    # print(f"Error : {str(e)}")
                    continue
        if configuration.standalone_check:
            query = "Insert into lv1_file_document values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, " \
                    "%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, " \
                    "%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"
            configuration.cursor.bulk_execute(query, insert_document)
            # print(f"Total Count : {total_count}, Error Count : {error_count}")

    def _UpdateFileInfoRecords(self, configuration, document):
        query = f'UPDATE file_info SET sig_type = "unmatched to extension" WHERE inode = "{document[20]}" and name ="{document[0]}"'
        configuration.cursor.execute_query(query)

manager.ModulesManager.RegisterModule(DEFAConnector)
