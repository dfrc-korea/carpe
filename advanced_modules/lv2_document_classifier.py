# -*- coding: utf-8 -*-
"""module for LV2."""
import os
import pandas as pd
import numpy as np
from advanced_modules import manager
from advanced_modules import interface
from advanced_modules import logger
# from dfvfs.lib import definitions as dfvfs_definitions

from advanced_modules.last_saved_program_classifier import module, Classifier

class LV2DOCUMENTCLASSIFIERAnalyzer(interface.AdvancedModuleAnalyzer):
    NAME = 'lv2_document_classifier'
    DESCRIPTION = 'Module for LV2 Document Classifier'

    _plugin_classes = {}

    def __init__(self):
        super(LV2DOCUMENTCLASSIFIERAnalyzer, self).__init__()

    def Analyze(self, par_id, configuration, source_path_spec, knowledge_base):
        
        this_file_path = os.path.dirname(os.path.abspath(__file__)) + os.sep + 'schema' + os.sep
        # 모든 yaml 파일 리스트
        yaml_list = [this_file_path + 'lv2_document_classifier.yaml']

        # 모든 테이블 리스트
        table_list = ['lv2_document_classifier']

        # 모든 테이블 생성
        for count in range(0, len(yaml_list)):
            if not self.LoadSchemaFromYaml(yaml_list[count]):
                logger.error('cannot load schema from yaml: {0:s}'.format(table_list[count]))
                return False

            # if table is not existed, create table
            if not configuration.cursor.check_table_exist(table_list[count]):
                ret = self.CreateTable(configuration.cursor)
                if not ret:
                    logger.error('cannot create database table name: {0:s}'.format(table_list[count]))
                    return False
        
        query_separator = self.GetQuerySeparator(source_path_spec, configuration)
        # extension -> sig_type 변경해야 함
        query = f"SELECT name, parent_path, extension, ctime, ctime_nano, inode FROM file_info " \
                f"WHERE par_id='{par_id}' and (extension = lower('pptx') or extension = lower('docx') or extension = lower('xlsx'));"

        document_files = configuration.cursor.execute_query_mul(query)

        if len(document_files) == 0:
            return False
        
        doc_docx = pd.DataFrame(columns=["filename", "contents"])
        doc_pptx = pd.DataFrame(columns=["filename", "contents"])
        doc_xlsx = pd.DataFrame(columns=["filename", "contents"])
        
        doc_list = []
        
        # output_path에 저장된 것들을 토대로 분석 진행
        output_dir = "parsedSource"        
        output_path = configuration.root_tmp_path + os.sep + configuration.case_id + os.sep + configuration.evidence_id + os.sep + par_id + os.sep + output_dir
        # 없으면 경로 생성
        if not os.path.exists(output_path):
            os.makedirs(output_path) 
            
        for document in document_files:
            # 문서 네이밍을 위한 이름 및 확장자 추가 ([name][extension])
            doc_list.append([document[0], document[2]])
            
            if configuration.source_type == 'directory' or configuration.source_type == 'file':
                document_path = document[1][document[1].find(source_path_spec.location) + len(source_path_spec.location):] + query_separator + document[0]
            else:
                document_path = document[1][document[1].find(query_separator):] + query_separator + document[0]
           
            self.ExtractTargetFileToPath(
                        source_path_spec=source_path_spec,
                        configuration=configuration,
                        file_path=document_path,
                        output_path=output_path)

        
        # 대상 문서 파싱된 목록들 로드
        target = module.extractContents(output_path)
        
        # 문서 형태에 따라 리스트로 분류하는 부분
        for index, row in target.iterrows():
            if 'docx' in row["filename"]:
                doc_docx = doc_docx.append(row, ignore_index=True)
            elif 'xlsx' in row["filename"]:
                doc_xlsx = doc_xlsx.append(row, ignore_index=True)
            elif 'pptx' in row["filename"]:
                doc_pptx = doc_pptx.append(row, ignore_index=True)
            else:
                print("Error: no documents -> filename: " + row["filename"])
        
        # 형식에 따른 분석기 생성
        docx_anl = Classifier.DocxAnalyzer()
        pptx_anl = Classifier.PptxAnalyzer()
        xlsx_anl = Classifier.XlsxAnalyzer()
        
        # docx
        print("==========Classification [DOCX FILE]==========")
        docx_anl.train_docx_model()
        docx_pred = docx_anl.predict_document(doc_docx)
        docx_labels = module.decode_onehot(docx_pred, docx_anl.uniqueLabel)

        # pptx
        print("==========Classification [PPTX FILE]==========")
        pptx_anl.train_pptx_model()
        pptx_pred = pptx_anl.predict_document(doc_pptx)
        pptx_labels = module.decode_onehot(pptx_pred, pptx_anl.uniqueLabel)
        
        # xlsx
        print("==========Classification [XLSX FILE]==========")
        xlsx_anl.train_xlsx_model()
        xlsx_pred = xlsx_anl.predict_document(doc_xlsx)
        xlsx_labels = module.decode_onehot(xlsx_pred, xlsx_anl.uniqueLabel)

        # 결과 schema 정리
        """
        - par_id
        - case_id
        - evd_id
        - file name
        - extension
        - source
        """
        based = [par_id, configuration.case_id, configuration.evidence_id]
        docx_df = pd.DataFrame(columns=["par_id", "case_id", "evd_id", "filename", "extension", "source"])
        docx_df = module.concat_df(based, doc_docx, docx_df, docx_labels, "docx")
        pptx_df = pd.DataFrame(columns=["par_id", "case_id", "evd_id", "filename", "extension", "source"])
        pptx_df = module.concat_df(based, doc_pptx, pptx_df, pptx_labels, "pptx")
        xlsx_df = pd.DataFrame(columns=["par_id", "case_id", "evd_id", "filename", "extension", "source"])
        xlsx_df = module.concat_df(based, doc_xlsx, xlsx_df, xlsx_labels, "xlsx")
        
        total_df = pd.concat([docx_df, pptx_df, xlsx_df], ignore_index=True)   # 전체 데이터프레임 통합
        insert_data = []

        # 이제 DB에 업로드
        query = "INSERT INTO lv2_document_classifier values (%s, %s, %s, %s, %s, %s);"
        for _, e in total_df.iterrows():  
            insert_data.append(tuple([par_id, configuration.case_id, configuration.evidence_id] + list((e['filename'], e['extension'], e['source'])))) 
        configuration.cursor.bulk_execute(query, insert_data)
        
        
manager.AdvancedModulesManager.RegisterModule(LV2DOCUMENTCLASSIFIERAnalyzer)