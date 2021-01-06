# -*- coding: utf-8 -*-
"""module for f2fs."""
import os
import subprocess

from modules import manager
from modules import interface

from modules.f2fs import f2fs_parse


class F2fsConnector(interface.ModuleConnector):
    NAME = 'f2fs_connector'
    DESCRIPTION = 'Module for f2fs'

    def __init__(self):
        super(F2fsConnector, self).__init__()

    def Connect(self, par_id, configuration, source_path_spec, knowledge_base):

        query_separator = self.GetQuerySeparator(source_path_spec, configuration)
        path_separator = self.GetPathSeparator(source_path_spec)

        this_file_path = os.path.dirname(os.path.abspath(__file__)) + os.sep \
                         + 'f2fs' + os.sep + 'carpe_tsk_windows' + os.sep

        output_path = configuration.root_tmp_path + os.sep + configuration.case_id + os.sep + \
                      configuration.evidence_id + os.sep + par_id

        subprocess.run([this_file_path + 'carpe_tsk.exe',
                        '-F', 'loaddb',
                        '-d', output_path + os.sep + 'f2fs.db',
                        'E:\\03. image\\IITP\\f2fs-003.img'])

        file_info = f2fs_parse.main(par_id, output_path + os.sep + 'f2fs.db')
        print(file_info)


manager.ModulesManager.RegisterModule(F2fsConnector)
