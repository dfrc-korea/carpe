# -*- coding: utf-8 -*-
"""module for DEFA."""
import os
import configparser
from datetime import datetime

from dfvfs.lib import definitions as dfvfs_definitions
from elasticsearch import Elasticsearch, helpers

from modules import manager
from modules import interface

class DEFAConnector(interface.ModuleConnector):

    NAME = 'defa_connector'
    DESCRIPTION = 'Module for DEFA'

    _plugin_classes = {}

    def __init__(self):
        super(DEFAConnector, self).__init__()

    def Connect(self, configuration, source_path_spec, knowledge_base):
        print('[MODULE]: DEFA Connect')

        if source_path_spec.parent.type_indicator != dfvfs_definitions.TYPE_INDICATOR_TSK_PARTITION:
            par_id = configuration.partition_list['p1']
        else:
            par_id = configuration.partition_list[getattr(source_path_spec.parent, 'location', None)[1:]]

        if par_id == None:
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

        # sig_type -> extension 임시 변경,
        query = f"SELECT name, parent_path, sig_type, extension FROM file_info WHERE par_id='{par_id}'" \
                f"and parent_path not like '%/Hnc/Office%' and parent_path not like '%_damaged%' and parent_path not like '%_encrypted%' and ("  # and parent_path not like '%_damaged/%' 임시

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

            if i == len(self._plugins) - 1:
                query += ");"
            else:
                query += "or "

        document_files = configuration.cursor.execute_query_mul(query)

        if len(document_files) == 0:
            return False

        config = configparser.ConfigParser()
        conf_file = os.path.dirname(
            os.path.dirname(os.path.abspath(__file__))) + os.sep + 'config' + os.sep + 'carpe.conf'
        if not os.path.exists(conf_file):
            raise Exception('%s file does not exist.\n' % conf_file)
        config.read(conf_file)
        _host = config.get('elasticsearch', 'host')
        _port = config.getint('elasticsearch', 'port')
        _index_name = config.get('document', 'index')
        _type_name = config.get('document', 'type')
        es = Elasticsearch(hosts=_host, port=_port)

        for document in document_files:
            document_path = document[1][document[1].find('/'):] + '/' + document[0]  # document full path
            #document_path = "/Users/Woosung/AppData/Local/Mendeley Ltd/Mendeley Desktop/Downloaded/Choi, Lee, Sohn - 2017 - Analyzing research trends in personal information privacy using topic modeling(2).pdf"
            print("\ndocument_path : " + document_path)

            """ # 이 주석은 메모리로 사용
            #################### load가 느려서 임시로 추가 ######################
            sig_type = document[2].lower()
            extension = document[3].lower()
            result = None
            # 에러가 많아서 임시처리로 sig_type, extension이 같아야 동작하게 처리
            if sig_type != extension:
                continue
            #################### load가 느려서 임시로 추가 ######################

            print("loading time : " + str(datetime.now()))
            file_object = self.LoadTargetFileToMemory(
                source_path_spec=source_path_spec,
                configuration=configuration,
                file_path=document_path)
            print("load time : " + str(datetime.now()))

            if not file_object:
                continue
            
            sig_type = document[2].lower()
            extension = document[3].lower()
            result = None
            # 에러가 많아서 임시처리로 sig_type, extension이 같아야 동작하게 처리
            if sig_type == 'hwp' and extension == 'hwp':
                result = hwp_plugin.Process(fp=file_object)
            elif sig_type == 'doc' and extension == 'doc':
                result = doc_plugin.Process(fp=file_object)
            elif sig_type == 'ppt' and extension == 'ppt':
                result = ppt_plugin.Process(fp=file_object)
            elif sig_type == 'xls' and extension == 'xls':
                result = xls_plugin.Process(fp=file_object)
            elif sig_type == 'docx' and extension == 'docx':
                result = docx_plugin.Process(fp=file_object)
            elif sig_type == 'pptx' and extension == 'pptx':
                result = pptx_plugin.Process(fp=file_object)
            elif sig_type == 'xlsx' and extension == 'xlsx':
                result = xlsx_plugin.Process(fp=file_object)
            elif sig_type == 'pdf' and extension == 'pdf':
                try:
                    result = pdf_plugin.Process(fp=file_object)
                except Exception:
                    file_object.close()
                    continue
            else:
                print("unknown sig_type")
                file_object.close()
                continue

            if result == None:
                file_object.close()
                continue


            result.case_id = configuration.case_id
            result.evdnc_id = configuration.evidence_id
            result.name = document[0]
            result.path_with_ext = document_path
            result.original_size = file_object._size

            file_object.close()
            """
            output_path = configuration.root_tmp_path + os.sep + configuration.case_id + os.sep + \
                            configuration.evidence_id + os.sep + par_id + os.sep + document_path.replace(os.sep, '~#')
            ole_path = output_path + os.sep + "ole"

            if not os.path.exists(output_path):
                os.makedirs(output_path)
                os.makedirs(ole_path)

            self.ExtractTargetFileToPath(
                source_path_spec=source_path_spec,
                configuration=configuration,
                file_path=document_path,
                output_path=output_path)

            file_path = output_path + os.sep + document[0]
            extension = document[3].lower()

            if extension == 'hwp':
                result = hwp_plugin.Process(fp=file_path, ole_path=ole_path)
            elif extension == 'doc':
                result = doc_plugin.Process(fp=file_path, ole_path=ole_path)
            elif extension == 'ppt':
                result = ppt_plugin.Process(fp=file_path, ole_path=ole_path)
            elif extension == 'xls':
                result = xls_plugin.Process(fp=file_path, ole_path=ole_path)
            elif extension == 'docx':
                result = docx_plugin.Process(fp=file_path, ole_path=ole_path)
            elif extension == 'pptx':
                result = pptx_plugin.Process(fp=file_path, ole_path=ole_path)
            elif extension == 'xlsx':
                result = xlsx_plugin.Process(fp=file_path, ole_path=ole_path)
            elif extension == 'pdf':
                try:
                    result = pdf_plugin.Process(fp=file_path, ole_path=ole_path)
                except Exception:
                    continue

            result.case_id = configuration.case_id
            result.evdnc_id = configuration.evidence_id
            result.download_path = file_path
            result.full_path = document_path  # 이미지 내 full_path
            result.path_with_ext = document_path  # 이미지 내 full_path
            result.parent_full_path = document_path[:document_path.rfind('/')]
            result.name = document[0]
            result.original_size = os.path.getsize(file_path)
            result.ole_path = ole_path
            print(result.__dict__)

            try:
                es.index(index=_index_name, doc_type=_type_name, body=result.__dict__)
            except Exception as e:
                print(f"Error : {str(e)}")
                continue

            """
            jsonobject = {
                '_index': index_name,
                '_type': type_name,
                '_source': result.__dict__
            }
            actions = [jsonobject]
            try:
                helpers.bulk(es, actions, chunk_size=1000, request_timeout=200)
            except Exception as e:
                print(f"Error : {str(e)}")
                continue
            """

manager.ModulesManager.RegisterModule(DEFAConnector)