# -*- coding: utf-8 -*-
import os
import datetime

from modules import defa_connector
from modules.DEFA import interface
from modules.DEFA.MappingDocuments import MappingDocuments
from modules import logger

class TextPlugin(interface.DEFAPlugin):
    NAME = "TEXT"
    DESCRIPTION = "text(txt/log) plugin"

    def Process(self, **kwargs): # fp: file_path, meta: document_info
        super(TextPlugin, self).Process(**kwargs)

        file_path = kwargs['fp']
        meta = kwargs['meta']

        data = MappingDocuments()
        data.date = None
        data.version = None
        data.category = None
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data.content = f.read()
                f.close()
        except UnicodeDecodeError:
            with open(file_path, 'r', encoding='utf-16-le') as f:
                data.content = f.read()
                f.close()
        else:
            log_msg = 'UnicodeDecodeError error occurred when read {}'.format(file_path)
            logger.error(log_msg)
            #raise Exception(log_msg)

        return data




defa_connector.DEFAConnector.RegisterPlugin(TextPlugin)