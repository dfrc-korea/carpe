# -*- coding: utf-8 -*-
"""module for extract file or directory."""

from modules import manager
from modules import interface


class Extract(interface.ModuleConnector):
    NAME = 'extract_connector'
    DESCRIPTION = 'Module for file carving'

    def __init__(self):
        super(Extract, self).__init__()

    def Connect(self, configuration, knowledge_base, source_path_spec=None, par_id=None):
        pass


manager.ModulesManager.RegisterModule(Extract)
