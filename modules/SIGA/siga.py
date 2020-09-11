# -*- coding: utf-8 -*-

import os
import textwrap

from modules.SIGA.classes import support

class SIGA():
    """SIGA File Format Analyzer


    """

    NAME = 'SIGA'
    DESCRIPTION = textwrap.dedent('n'.join([
        '',
        ('SIGA is a command line tool to analyze file from individual files'),
        '',
        'More information can be gathered from here',
        '    http://forensic.korea.ac.kr',
        '']))

    def __init__(self, mode):

        self.input = None
        self.mode = mode
        self.input_files = []
        self.ext = None
        self.cls = None

    def Identify(self, file_object, DirOrFile=None):

        if self.mode == 'file':
            if DirOrFile is None: return
            self.input = DirOrFile

            if os.path.isdir(self.input):
                for path, dirs, files in os.walk(self.input):
                    for file in files:
                        self.input_files.append(os.path.join(path, file))
            elif os.path.isfile(self.input):
                self.input_files.append(self.input)
            self._IdentifyFormatFromFile()

        elif self.mode == 'memory':
            self._IdentifyFormatFromMemory(file_object)

        else:
            print("error is occurred!")

    def _IdentifyFormatFromFile(self):
        pass

    def _IdentifyFormatFromMemory(self, file_object):
        if len(file_object) == 0 :
            return

        for module_name, class_name in support.SUPPORT_MODULE:
            mod = __import__('%s' % (module_name), fromlist=[module_name])
            cls = getattr(mod, class_name)()
            self.ext = cls.identifyFormatFromMemory(file_object)

            if self.ext != False:
                self.cls = cls
                break