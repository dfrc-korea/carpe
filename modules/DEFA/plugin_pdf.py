# -*- coding: utf-8 -*-

from modules import defa_connector
from modules.DEFA import interface
from modules.DEFA.MappingDocuments import MappingDocuments
from modules.DEFA.PDF.carpe_pdf import PDF

class PDFPlugin(interface.DEFAPlugin):
    NAME = "PDF"
    DESCRIPTION = 'pdf plugin'

    def Process(self, **kwargs):
        super(PDFPlugin, self).Process(**kwargs)

        data = MappingDocuments()

        with PDF(kwargs['fp']) as pdf:
            pdf.parse_content()
            pdf.parse_metadata()
            # pdf.extract_multimedia(data.ole_path)

            data.content = pdf.content
            try:
                try:
                    if type(pdf.metadata[0]['Title']) == bytes:
                        try:
                            data.title = pdf.metadata[0]['Title'].decode('UTF-16')
                        except UnicodeDecodeError:
                            try:
                                data.title = pdf.metadata[0]['Title'].decode('UTF-8')
                            except UnicodeDecodeError:
                                data.title = None
                        except Exception:
                            data.title = None
                    else:
                        data.title = pdf.metadata[0]['Title']
                except TypeError:
                    data.title = None
                # print(type(pdf.metadata[0]['Subject']))

                try:
                    if type(pdf.metadata[0]['Subject']) == bytes:
                        try:
                            data.subject = pdf.metadata[0]['Subject'].decode('UTF-16')
                        except UnicodeDecodeError:
                            try:
                                data.subject = pdf.metadata[0]['Subject'].decode('UTF-8')
                            except UnicodeDecodeError:
                                data.subject = None
                        except Exception:
                            data.subject = None
                    else:
                        data.subject = pdf.metadata[0]['Subject']
                except TypeError:
                    data.subject = None
                # print(type(pdf.metadata[0]['Author']))

                try:
                    if type(pdf.metadata[0]['Author']) == bytes:
                        try:
                            data.author = pdf.metadata[0]['Author'].decode('UTF-16')
                        except UnicodeDecodeError:
                            try:
                                data.author = pdf.metadata[0]['Author'].decode('UTF-8')
                            except UnicodeDecodeError:
                                data.author = None
                        except Exception:
                            data.author = None
                    else:
                        data.author = pdf.metadata[0]['Author']
                except TypeError:
                    data.author = None

                try:
                    if type(pdf.metadata[0]['Tags']) == bytes:
                        try:
                            data.tags = pdf.metadata[0]['Tags'].decode('UTF-16')
                        except UnicodeDecodeError:
                            try:
                                data.tags = pdf.metadata[0]['Tags'].decode('UTF-8')
                            except UnicodeDecodeError:
                                data.tags = None
                        except Exception:
                            data.tags = None
                    else:
                        data.tags = pdf.metadata[0]['Tags']
                except TypeError:
                    data.tags = None
                # data.tags = pdf.metadata[0]['Tags']
                data.explanation = None
                data.lastsavedby = None
                data.version = None
                data.date = None
                data.lastprintedtime = None
                try:
                    if isinstance(pdf.metadata[0]['CreatedTime'], bytes):
                        data.createdtime = pdf.metadata[0]['CreatedTime'].decode('UTF-8')
                    elif isinstance(pdf.metadata[0]['CreatedTime'], str):
                        data.createdtime = pdf.metadata[0]['CreatedTime']
                except TypeError:
                    data.createdtime = None

                try:
                    if isinstance(pdf.metadata[0]['LastSavedTime'], bytes):
                        data.lastsavedtime = pdf.metadata[0]['LastSavedTime'].decode('UTF-8')
                    elif isinstance(pdf.metadata[0]['LastSavedTime'], str):
                        data.lastsavedtime = pdf.metadata[0]['LastSavedTime']
                except TypeError:
                    data.lastsavedtime = None
                data.comment = None
                data.revisionnumber = None
                data.category = None
                data.manager = None
                data.company = None
                # print(type(pdf.metadata[0]['Author']))
                try:
                    if type(pdf.metadata[0]['ProgramName']) == bytes:
                        try:
                            data.programname = pdf.metadata[0]['ProgramName'].decode('UTF-16')
                        except UnicodeDecodeError:
                            try:
                                data.programname = pdf.metadata[0]['ProgramName'].decode('UTF-8')
                            except UnicodeDecodeError:
                                data.programname = None
                        except Exception:
                            data.programname = None
                    else:
                        data.programname = pdf.metadata[0]['ProgramName']
                except TypeError:
                    data.programname = None
                # data.programname = pdf.metadata[0]['ProgramName'].decode('UTF-8')
                data.totaltime = None
                # print(type(pdf.metadata[0]['Author']))
                try:
                    if type(pdf.metadata[0]['Creator']) == bytes:
                        try:
                            data.creator = pdf.metadata[0]['Creator'].decode('UTF-16')
                        except UnicodeDecodeError:
                            try:
                                data.creator = pdf.metadata[0]['Creator'].decode('UTF-8')
                            except UnicodeDecodeError:
                                data.creator = None
                        except Exception:
                            data.creator = None
                    else:
                        data.creator = pdf.metadata[0]['Creator']
                except TypeError:
                    data.creator = None
                # data.creator = pdf.metadata[0]['Creator'].decode('UTF-8')
                try:
                    data.trapped = pdf.metadata[0]['Trapped']['name']
                except Exception:
                    data.trapped = None

                # data.creation_time = pdf.metadata[0]['CreationDate'].decode('utf-8')
                # data.last_written_time = pdf.metadata[0]['ModDate'].decode('utf-8')
                data.has_metadata = pdf.has_metadata
                data.has_content = pdf.has_content
                data.is_damaged = pdf.is_damaged
            except Exception:
                data.title = None
                data.subject = None
                data.author = None
                data.tags = None
                data.explanation = None
                data.lastsavedby = None
                data.version = None
                data.date = None
                data.lastprintedtime = None
                data.createdtime = None
                data.lastsavedtime = None
                data.comment = None
                data.revisionnumber = None
                data.category = None
                data.manager = None
                data.company = None
                data.programname = None

                data.totaltime = None
                data.creator = None
                data.trapped = None
                data.has_metadata = pdf.has_metadata
                data.has_content = pdf.has_content
                data.is_damaged = pdf.is_damaged

            return data


defa_connector.DEFAConnector.RegisterPlugin(PDFPlugin)
