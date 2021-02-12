# -*- coding: utf-8 -*-

from modules import defa_connector
from modules.DEFA import interface
from modules.DEFA.OOXML.Carpe_OOXML import OOXML
from modules.DEFA.MappingDocuments import MappingDocuments

class DOCXPlugin(interface.DEFAPlugin):
    NAME = "DOCX"
    DESCRIPTION = 'docx plugin'

    def Process(self, **kwargs):
        super(DOCXPlugin, self).Process(**kwargs)

        data = MappingDocuments()

        ooxml = OOXML(kwargs['fp'])
        ooxml.parse_ooxml(data.ole_path, 'docx')
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

            # data.creation_time = ooxml.metadata['created']
            # data.last_written_time = ooxml.metadata['modified']
            data.has_metadata = ooxml.has_metadata
            data.has_content = ooxml.has_content
            data.is_damaged = ooxml.is_damaged

            #print(f"{data.__dict__['name']}")

            #es.index(index=index_name, doc_type=type_name, body=data.__dict__)
            # print(data.__dict__)
            return data
        except Exception as ex:
            print('[Error]%s-%s' % (ex, data.name))
            return None

defa_connector.DEFAConnector.RegisterPlugin(DOCXPlugin)
