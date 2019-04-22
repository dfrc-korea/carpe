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

# Test
from dfvfs.lib import definitions


class DiskSpliter:
    def __init__(self, disk_info=None, prefix='p'):
        self.disk_info = disk_info
        self.prefix = prefix

    def SetDiskInfo(self, disk_info):
        self.disk_info = disk_info

    def SplitDisk(self, output_writer):
        if self.disk_info is None:
            return
        #procs = []
        for par_info in self.disk_info:
            file_object = resolver.Resolver.OpenFileObject(par_info["base_path_spec"])
            tsk_image_object = tsk_image.TSKFileSystemImage(file_object)
            if par_info["type_indicator"] == definitions.TYPE_INDICATOR_TSK_PARTITION:
                continue
            print("type: " + str(par_info["type_indicator"]))
            print("length: " + str(par_info["length"]))
            print("bytes_per_sector: " + str(par_info["bytes_per_sector"]))
            print("start_sector: " + str(par_info["start_sector"]))
            print("name: " + par_info["vol_name"])
            ###############################################
            offset = 0
            length = par_info["length"]
            vol_name = par_info["vol_name"]
            try:
                output_writer.Open(vol_name)
            except IOError as exception:
                print('Unable to open output writer with error: {0!s}'.format(exception))
                print('')
                return
            MAX_LENGTH = 1024 * 1024
            #MAX_LENGTH = 512
            while True:
                rlen = MAX_LENGTH if length - offset > MAX_LENGTH else length - offset
                #file_object.seek(offset)
                #data = file_object.read(rlen)
                data = tsk_image_object.read(offset, rlen)
                offset += rlen
                output_writer.Write(data)
                print(offset)
                del data
                if offset >= length:
                    break
            output_writer.Close()
            ###############################################
            #imageWrite_process = Process(target=self._tskWriteImage, args=(file_object, par_info["length"], output_writer, par_info["vol_name"]))
            #procs.append(imageWrite_process)
            #imageWrite_process.start()
            
        #for proc in procs:
            #proc.join()

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
