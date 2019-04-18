#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
from __future__ import unicode_literals

import os
import sys

from multiprocessing import Process

from dfvfs.lib import errors
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
        for base_path_spec, type_indicator, length, bytes_per_sector, start_sector, vol_name, identifier in self.disk_info:
            file_object = resolver.Resolver.OpenFileObject(base_path_spec)
            imageWrite_process = Process(target=self._tskWriteImage, args=(file_object, length, output_writer, vol_name))
            procs.append(imageWrite_process)
            imageWrite_process.start()
            
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
            #image_object.seek(offset)
            data = image_object.read(rlen)
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