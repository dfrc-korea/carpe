# -*- coding: utf-8 -*-
import os
from modules import defa_connector
from modules.DEFA import interface
from modules.DEFA.Hancom.carpe_hwp import HWP
from modules.DEFA.MappingDocuments import MappingDocuments

class HWPPlugin(interface.DEFAPlugin):
    NAME = "HWP"
    DESCRIPTION = 'hwp plugin'

    def Process(self, **kwargs):
        super(HWPPlugin, self).Process(**kwargs)

        data = MappingDocuments()

        #data.name = file[4]  # 파일이름
        #data.ext = file[34]  # 파일 확장자
        #data.parent_full_path = file[33]  # parent 경로
        #data.path_with_ext = file[33] + file[4]  # 파일 전체 경로
        #data.full_path = data.path_with_ext.replace('.' + data.ext, '')  # 확장자 제외
        # data.full_path = data.case_id + '/' + data.evdnc_id + '/documents/' + data.name

        # data.full_path = 'test'
        #file_export_path = data.work_dir + file[4]
        #data.creation_time = datetime.fromtimestamp(file[13])
        #data.last_written_time = datetime.fromtimestamp(file[11])
        #data.last_access_time = datetime.fromtimestamp(file[12])
        #data.original_size = file[10]

        #data.has_exif = 'No'
        #data.doc_id = file[0]
        #data.doc_type = 'documents'
        #data.doc_type_sub = data.ext

        # work_file = file[37]
        # data.download_path = file[38]
        #data.download_path = data.case_id + '/' + data.evdnc_id + '/documents/' + data.name
        #data.ole_path = file[38] + "_extracted"
        # print(data.download_path)
        data.ole_path = kwargs['ole_path']
        hwp = HWP(kwargs['fp'])  # 파일 포인터 전달
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

            # data.creation_time = hwp.metaList[0]['createTime']
            # data.last_written_time = hwp.metaList[0]['lastSavedTime']
            data.has_metadata = hwp.has_metadata
            data.has_content = hwp.has_content
            data.is_damaged = hwp.isDamaged

            #print(f"{data.__dict__['name']}")

            #es.index(index=index_name, doc_type=type_name, body=data.__dict__)
            # print(data.__dict__)

            return data
        except Exception as ex:
            print('[Error]%s-%s' % (ex, data.name))
            return None



defa_connector.DEFAConnector.RegisterPlugin(HWPPlugin)
