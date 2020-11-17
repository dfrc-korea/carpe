#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import csv
import json
import configparser

from os import listdir
from os.path import isfile, join
from datetime import datetime, timedelta
from elasticsearch import Elasticsearch

# pdf 주석
#from DEFA.PDF.carpe_pdf import PDF
from modules.DEFA.OOXML.Carpe_OOXML import OOXML
from modules.DEFA.MS_Office.carpe_compound import Compound
from modules.DEFA.Hancom.carpe_hwp import HWP

import pdb

class DEFA:
    def documentFilter(self, data, file):

        config = configparser.ConfigParser()
        conf_file = os.path.dirname(
            os.path.dirname(os.path.abspath(__file__))) + os.sep + 'config' + os.sep + 'carpe.conf'
        if not os.path.exists(conf_file):
            raise Exception('%s file does not exist.\n' % conf_file)
        config.read(conf_file)
        _host = config.get('elasticsearch', 'host')
        _port = config.getint('elasticsearch', 'port')
        _es_id = config.get('elasticsearch', 'id')
        _es_passwd = config.get('elasticsearch', 'passwd')
        es = Elasticsearch(hosts=_host, port=_port, http_auth=(_es_id, _es_passwd))

        index_name = 'documents'
        type_name = 'document'

        data.name = file[4] # 파일이름
        data.ext = file[34] # 파일 확장자
        data.parent_full_path = file[33] # parent 경로
        data.path_with_ext = file[33] + file[4] # 파일 전체 경로
        data.full_path = data.path_with_ext.replace('.'+data.ext, '') # 확장자 제외
        #data.full_path = data.case_id + '/' + data.evdnc_id + '/documents/' + data.name

        #data.full_path = 'test'
        file_export_path = data.work_dir+file[4]
        data.creation_time = datetime.fromtimestamp(file[13])
        data.last_written_time = datetime.fromtimestamp(file[11])
        data.last_access_time = datetime.fromtimestamp(file[12])
        data.original_size = file[10]
        
        data.has_exif = 'No'
        data.doc_id = file[0]
        data.doc_type = 'documents'
        data.doc_type_sub = data.ext

        #work_file = file[37]
        #data.download_path = file[38]
        data.download_path = data.case_id + '/' + data.evdnc_id + '/documents/' + data.name
        data.ole_path = file[38] + "_extracted"
        #print(data.download_path)
            
        if data.ext.lower() in 'pdf':
            #return False
            # pdf 주석
            """
            with PDF(file_export_path) as pdf:
                pdf.parse_content() 
                pdf.parse_metadata() 
                pdf.extract_multimedia(data.ole_path) 
                #try:	
                data.content = pdf.content
                #print(type(pdf.metadata[0]['Title']))
                if type(pdf.metadata[0]['Title']) == bytes:
                    try:
                        data.title = pdf.metadata[0]['Title'].decode('UTF-16')
                    except UnicodeDecodeError:
                        data.title = pdf.metadata[0]['Title'].decode('UTF-8')
                else:
                    data.title = pdf.metadata[0]['Title']
                #print(type(pdf.metadata[0]['Subject']))
                if type(pdf.metadata[0]['Subject']) == bytes:
                    try:
                        data.subject = pdf.metadata[0]['Subject'].decode('UTF-16')
                    except UnicodeDecodeError:
                        data.subject = pdf.metadata[0]['Subject'].decode('UTF-8')
                else:
                    data.subject = pdf.metadata[0]['Subject']
                #print(type(pdf.metadata[0]['Author']))
                if type(pdf.metadata[0]['Author']) == bytes:
                    try:
                        data.author = pdf.metadata[0]['Author'].decode('UTF-16')
                    except UnicodeDecodeError:
                        data.author = pdf.metadata[0]['Author'].decode('UTF-8')
                else:
                    data.author = pdf.metadata[0]['Author']
						
                if type(pdf.metadata[0]['Tags']) == bytes:
                    try:
                        data.tags = pdf.metadata[0]['Tags'].decode('UTF-16')
                    except UnicodeDecodeError:
                        data.tags = pdf.metadata[0]['Tags'].decode('UTF-8')
                else:
                    data.tags = pdf.metadata[0]['Tags']
                #data.tags = pdf.metadata[0]['Tags']
                data.explanation = None
                data.lastsavedby = None
                data.version = None
                data.date = None
                data.lastprintedtime = None
                data.createdtime = pdf.metadata[0]['CreatedTime'].decode('UTF-8')
                data.lastsavedtime = pdf.metadata[0]['LastSavedTime'].decode('UTF-8')
                data.comment = None
                data.revisionnumber = None
                data.category = None
                data.manager = None
                data.company = None
				#print(type(pdf.metadata[0]['Author']))
                if type(pdf.metadata[0]['ProgramName']) == bytes:
                    try:
                        data.programname = pdf.metadata[0]['ProgramName'].decode('UTF-16')
                    except UnicodeDecodeError:
                        data.programname = pdf.metadata[0]['ProgramName'].decode('UTF-8')
                else:
                    data.programname = pdf.metadata[0]['ProgramName']
                #data.programname = pdf.metadata[0]['ProgramName'].decode('UTF-8')
                data.totaltime = None
				#print(type(pdf.metadata[0]['Author']))
                if type(pdf.metadata[0]['Creator']) == bytes:
                    try:
                        data.creator = pdf.metadata[0]['Creator'].decode('UTF-16')
                    except UnicodeDecodeError:
                        data.creator = pdf.metadata[0]['Creator'].decode('UTF-8')
                else:
                    data.creator = pdf.metadata[0]['Creator']
                #data.creator = pdf.metadata[0]['Creator'].decode('UTF-8')
                data.trapped = pdf.metadata[0]['Trapped']

				#data.creation_time = pdf.metadata[0]['CreationDate'].decode('utf-8')
				#data.last_written_time = pdf.metadata[0]['ModDate'].decode('utf-8')
                data.has_metadata = pdf.has_metadata
                data.has_content = pdf.has_content
                data.is_damaged = pdf.is_damaged
				
                #print(f"{data.__dict__['name']}")				
				
                es.index(index=index_name, doc_type=type_name, body=data.__dict__)
                #print(data.__dict__)
                return True
                #except Exception as ex:
                #    print('[Error]%s-%s'%(ex, data.name))
                #    return False
        """
        elif data.ext.lower() in 'hwp': 
            hwp = HWP(file_export_path)
            hwp.parse(data.ole_path)
            try:
                
                data.content = hwp.content
                data.title = hwp.metaList['Title']
                data.subject = hwp.metaList['Subject']
                data.author = hwp.metaList['Author']
                data.tags = hwp.metaList['Tags']
                data.explanation = hwp.metaList['Explanation']
                data.lastsavedby = hwp.metaList['LastSavedBy']
                data.version = hwp.metaList['Version']
                data.date = hwp.metaList['Date']
                data.lastprintedtime = hwp.metaList['LastPrintedTime']
                data.createdtime = hwp.metaList['CreatedTime']
                data.lastsavedtime = hwp.metaList['LastSavedTime']
                data.comment = hwp.metaList['Comment']
                data.revisionnumber = hwp.metaList['RevisionNumber']
                data.category = hwp.metaList['Category']
                data.manager = hwp.metaList['Manager']
                data.company = hwp.metaList['Company']
                data.programname = hwp.metaList['ProgramName']
                data.totaltime = hwp.metaList['TotalTime']
                data.creator = hwp.metaList['Creator']
                data.trapped = hwp.metaList['Trapped']
			
                #data.creation_time = hwp.metaList[0]['createTime']
                #data.last_written_time = hwp.metaList[0]['lastSavedTime']
                data.has_metadata = hwp.has_metadata
                data.has_content = hwp.has_content
                data.is_damaged = hwp.isDamaged
				
                print(f"{data.__dict__['name']}")				
				
                es.index(index=index_name, doc_type=type_name, body=data.__dict__)
                #print(data.__dict__)

                return True
            except Exception as ex:
                #print(hwp.metaList)
                print('[Error]%s-%s'%(ex, data.name))
                return False
        elif data.ext.lower() in ('doc', 'xls', 'ppt'): 
            compound = Compound(file_export_path) 
            compound.parse(data.ole_path)
            try:
                data.content = compound.content
                data.title = compound.metadata['Title']
                data.subject = compound.metadata['Subject']
                data.author = compound.metadata['Author']
                data.tags = compound.metadata['Tags']
                data.explanation = compound.metadata['Explanation']
                data.lastsavedby = compound.metadata['LastSavedBy']
                data.version = compound.metadata['Version']
                data.date = compound.metadata['Date']
                data.lastprintedtime = compound.metadata['LastPrintedTime']
                data.createdtime = compound.metadata['CreatedTime']
                data.lastsavedtime = compound.metadata['LastSavedTime']
                data.comment = compound.metadata['Comment']
                data.revisionnumber = compound.metadata['RevisionNumber']
                data.category = compound.metadata['Category']
                data.manager = compound.metadata['Manager']
                data.company = compound.metadata['Company']
                data.programname = compound.metadata['ProgramName']
                data.totaltime = compound.metadata['TotalTime']
                data.creator = compound.metadata['Creator']
                data.trapped = compound.metadata['Trapped']
				
                #data.creation_time = compound.metadata['create_time']
                #data.last_written_time = compound.metadata['modified_time']
                data.has_metadata = compound.has_metadata
                data.has_content = compound.has_content
                data.is_damaged = compound.is_damaged
				
                print(f"{data.__dict__['name']}")				
				
                es.index(index=index_name, doc_type=type_name, body=data.__dict__)
                #print(data.__dict__)
                return True
            except Exception as ex:
                print('[Error]%s-%s'%(ex, data.name))
                return False
        elif data.ext.lower() in ('docx', 'xlsx', 'pptx'): 
            ooxml = OOXML(file_export_path)
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
				
                print(f"{data.__dict__['name']}")				
				
                es.index(index=index_name, doc_type=type_name, body=data.__dict__)
                #print(data.__dict__)
                return True
            except Exception as ex:
                print('[Error]%s-%s'%(ex, data.name))
                return False
        else:
            pass
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
                f.write(file[38])		
                f.write('\n')
        f.close()				
        print('success: %d failed: %d'% (success, failed))
        time2 = datetime.now()
        print((time2-time1).seconds, 'sec')		

    except KeyboardInterrupt:
        print('error')

