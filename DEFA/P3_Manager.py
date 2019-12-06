#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import csv
import json

from os import listdir
from os.path import isfile, join
from datetime import datetime, timedelta
from elasticsearch import Elasticsearch

from DEFA.PDF.carpe_pdf import PDF
from DEFA.OOXML.Carpe_OOXML import OOXML
from DEFA.MS_Office.carpe_compound import Compound
from DEFA.Hancom.carpe_hwp import HWP



class DEFA:
    def documentFilter(self, data, file):
        es = Elasticsearch(hosts="220.73.134.142", port=9200)
        index_name = 'defa'
        type_name = 'document'
        data
        data.name = file[4] # 파일이름
        data.ext = file[34] # 파일 확장자
        data.parent_full_path = file[33] # parent 경로
        data.path_with_ext = file[33] + file[4] # 파일 전체 경로
        data.path = data.path_with_ext.replace('.'+data.ext, '') # 확장자 제외
        data.creation_time = datetime.fromtimestamp(file[13])
        data.last_written_time = datetime.fromtimestamp(file[11])
        data.last_access_time = datetime.fromtimestamp(file[12])
        data.original_size = file[10]
        
        data.has_exif = 'No'
        data.doc_id = file[0]
        data.doc_type = 'documents'
        data.doc_type_sub = data.ext

        #work_file = file[37]
        data.download_path = file[37]
        data.ole_path = data.work_dir[:-1] + "_extracted/"
        print(data.download_path)
        
        if data.ext.lower() in 'pdf':
            #return False
            with PDF(data.download_path) as pdf:
                pdf.parse_content() 
                pdf.parse_metadata() 
                pdf.extract_multimedia(data.ole_path) 
                try:	
                    data.content = pdf.content
                    data.title = pdf.metadata[0]['Title']
                    data.subject = pdf.metadata[0]['Subject']
                    data.author = pdf.metadata[0]['Author'].decode('utf-16') 
                    data.tags = pdf.metadata[0]['Tags']
                    data.explanation = None
                    data.lastsavedby = None
                    data.version = None
                    data.date = None
                    data.lastprintedtime = None
                    data.createdtime = pdf.metadata[0]['CreatedTime']
                    data.lastsavedtime = pdf.metadata[0]['LastSavedTime']
                    data.comment = None
                    data.revisionnumber = None
                    data.category = None
                    data.manager = None
                    data.company = None
                    data.programname = pdf.metadata[0]['ProgramName']
                    data.totaltime = None
                    data.creator = pdf.metadata[0]['Creator']
                    data.trapped = pdf.metadata[0]['Trapped']

                    #data.creation_time = pdf.metadata[0]['CreationDate'].decode('utf-8')
                    #data.last_written_time = pdf.metadata[0]['ModDate'].decode('utf-8')
                    data.has_metadata = pdf.has_metadata
                    data.has_content = pdf.has_content
                    data.is_damaged = pdf.is_damaged
                    es.index(index=index_name, doc_type=type_name, body=data.__dict__)
                    #print(data.__dict__)
                    return True
                except Exception as ex:
                    print('[Error]%s-%s'%(ex, data.name))
                    return False
        
        elif data.ext.lower() in 'hwp': 
            hwp = HWP(data.download_path)
            hwp.parse()
            try:
                data.content = hwp.content
				
                data.title = hwp.metaList[0]['Title']
                data.subject = hwp.metaList[0]['Subject']
                data.author = hwp.metaList[0]['Author']
                data.tags = hwp.metaList[0]['Tags']
                data.explanation = hwp.metaList[0]['Explanation']
                data.lastsavedby = hwp.metaList[0]['LastSavedBy']
                data.version = hwp.metaList[0]['Version']
                data.date = hwp.metaList[0]['Date']
                data.lastprintedtime = hwp.metaList[0]['LastPrintedTime']
                data.createdtime = hwp.metaList[0]['CreatedTime']
                data.lastsavedtime = hwp.metaList[0]['LastSavedTime']
                data.comment = hwp.metaList[0]['Comment']
                data.revisionnumber = hwp.metaList[0]['RevisionNumber']
                data.category = None
                data.manager = None
                data.company = None
                data.programname = None
                data.totaltime = None
                data.creator = None
                data.trapped = None
			
                #data.creation_time = hwp.metaList[0]['createTime']
                #data.last_written_time = hwp.metaList[0]['lastSavedTime']
                data.has_metadata = hwp.has_metadata
                data.has_content = hwp.has_content
                data.is_damaged = hwp.isDamaged
                es.index(index=index_name, doc_type=type_name, body=data.__dict__)
                #print(data.__dict__)
                return True
            except Exception as ex:
                print('[Error]%s-%s'%(ex, data.name))
                return False
        elif data.ext.lower() in ('doc', 'xls', 'ppt'): 
            compound = Compound(data.download_path) 
            compound.parse(data.ole_path)
            try:
                data.content = compound.content
                data.title = compound.metadata['Title']
                data.subject = compound.metadata['Subject']
                data.author = compound.metadata['Author']
                data.tags = compound.metadata['Tags']
                data.explanation = None
                data.lastsavedby = compound.metadata['LastSavedBy']
                data.version = None
                data.date = None
                data.lastprintedtime = compound.metadata['LastPrintedTime']
                data.createdtime = compound.metadata['CreatedTime']
                data.lastsavedtime = compound.metadata['LastSavedTime']
                data.comment = compound.metadata['Comment']
                data.revisionnumber = compound.metadata['RevisionNumber']
                data.category = None
                data.manager = None
                data.company = None
                data.programname = compound.metadata['ProgramName']
                data.totaltime = None
                data.creator = None
                data.trapped = None
				
                #data.creation_time = compound.metadata['create_time']
                #data.last_written_time = compound.metadata['modified_time']
                data.has_metadata = compound.has_metadata
                data.has_content = compound.has_content
                data.is_damaged = compound.is_damaged
                es.index(index=index_name, doc_type=type_name, body=data.__dict__)
                #print(data.__dict__)
                return True
            except Exception as ex:
                print('[Error]%s-%s'%(ex, data.name))
                return False
        elif data.ext.lower() in ('docx', 'xlsx', 'pptx'): 
            ooxml = OOXML(data.download_path)
            ooxml.parse_ooxml(data.ole_path)
            try:
                data.content = ooxml.content
                data.title = ooxml.metadata['Title']
                data.subject = ooxml.metadata['Subject']
                data.author = ooxml.metadata['Author']
                data.tags = ooxml.metadata['Tags']
                data.explanation = None
                data.lastsavedby = ooxml.metadata['LastSavedBy']
                data.version = ooxml.metadata['Version']
                data.date = None
                data.lastprintedtime = ooxml.metadata['LastPrintedTime']
                data.createdtime = ooxml.metadata['CreatedTime']
                data.lastsavedtime = ooxml.metadata['LastSavedTime']
                data.comment = ooxml.metadata['Comment']
                data.revisionnumber = ooxml.metadata['RevisionNumber']
                data.category = ooxml.metadata['Category']
                data.manager = ooxml.metadata['Manager']
                data.company = ooxml.metadata['Company']
                data.programname = ooxml.metadata['ProgramName']
                data.totaltime = ooxml.metadata['TotalTime']
                data.creator = None
                data.trapped = None
				
		
                #data.creation_time = ooxml.metadata['created']
                #data.last_written_time = ooxml.metadata['modified']
                data.has_metadata = ooxml.has_metadata
                data.has_content = ooxml.has_content
                data.is_damaged = ooxml.is_damaged
                es.index(index=index_name, doc_type=type_name, body=data.__dict__)
                #print(data.__dict__)
                return True
            except Exception as ex:
                print('[Error]%s-%s'%(ex, data.name))
                return False
        else:
            print('this file format not supported!')
		


def run_daemon(data, file_list):
    
    try:
        if len(file_list) == 0: return False
       
        defa = DEFA()
        f = open("out.txt", "w")

        success = 0
        failed = 0
        time1 = datetime.now()
        for file in file_list:
            if defa.documentFilter(data, file):
                success += 1
            else:
                failed += 1
                f.write(file[37])		
                f.write('\n')
        f.close()				
        print('success: %d failed: %d'% (success, failed))
        time2 = datetime.now()
        print((time2-time1).seconds, 'sec')		

    except KeyboardInterrupt:
        print('error')

