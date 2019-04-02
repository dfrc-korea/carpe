#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
from __future__ import unicode_literals

import os
import sys

from multiprocessing import Process

from dfvfs.lib import errors
from dfvfs.lib import tsk_image
from dfvfs.resolver import resolver


class DiskSpliter:
    def __init__(self, disk_info=None, prefix='p'):
        self.disk_info = disk_info
        self.prefix = prefix

    def SetDiskInfo(self, disk_info):
        self.disk_info = disk_info

    def SplitDisk(self, output_writer):
        if self.disk_info is None:
            return
        procs = []
        for par_name, length, par_type, base_path_spec in self.disk_info:
            file_system = resolver.Resolver.OpenFileSystem(base_path_spec)
            if par_type in ['VSS', 'TSK']:
                tsk_image_object = tsk_image.TSKFileSystemImage(file_system._file_object)
                file_name = par_name
                imageWrite_process = Process(target=self._tskWriteImage, args=(tsk_image_object, length, output_writer, file_name))
                imageWrite_process.start()
                procs.append(imageWrite_process)
            else: # apfs
                raise NotImplementedError

        for proc in procs:
            proc.join()

    def _tskWriteImage(self, image_object, length, output_writer, file_name):
        offset = 0
        try:
            output_writer.Open(file_name)
        except IOError as exception:
            print('Unable to open output writer with error: {0!s}.'.format(exception))
            print('')
            return
        MAX_LENGTH = 1024 * 1024 # 1 MB
        while True: # need to add multiprocessing that extract data in 100 MB  => need not develop
            rlen = MAX_LENGTH if length - offset > MAX_LENGTH else length - offset
            data = image_object.read(offset, rlen)
            offset += rlen
            output_writer.Write(data)
            del data
            if offset >= length:
                break
        output_writer.Close()

class FileOutputWriter:
    def __init__(self, path):
        self._file_object = None
        self._path = path
    
    def Close(self):
        self._file_object.close()

    def Open(self, file_name):
        self._file_object = open(os.path.join(self._path, file_name), 'wb')

    def Write(self, buf):
        self._file_object.write(buf)