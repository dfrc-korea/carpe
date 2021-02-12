# -*- coding: utf-8 -*-

from modules import defa_connector
from modules.DEFA import interface
from modules.DEFA.MS_Office.carpe_compound import Compound
from modules.DEFA.MappingDocuments import MappingDocuments

class DOCPlugin(interface.DEFAPlugin):
    NAME = "DOC"
    DESCRIPTION = 'doc plugin'

    def Process(self, **kwargs):
        super(DOCPlugin, self).Process(**kwargs)

        data = MappingDocuments()
        data.ole_path = kwargs['ole_path']
        compound = Compound(kwargs['fp'])
        compound.fileType = "doc"
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

            # data.creation_time = compound.metadata['create_time']
            # data.last_written_time = compound.metadata['modified_time']
            data.has_metadata = compound.has_metadata
            data.has_content = compound.has_content
            data.is_damaged = compound.is_damaged

            #print(f"{data.__dict__['name']}")

            #es.index(index=index_name, doc_type=type_name, body=data.__dict__)
            # print(data.__dict__)
            return data
        except Exception as ex:
            print('[Error]%s-%s' % (ex, data.name))
            return None

defa_connector.DEFAConnector.RegisterPlugin(DOCPlugin)
