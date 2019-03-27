#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
from __future__ import unicode_literals

import os
import sys
import argparse
import logging

from dfvfs.helpers import volume_scanner
from dfvfs.lib import errors
from dfvfs.lib import tsk_image
from dfvfs.resolver import resolver

import pdb

class DiskSpliter(volume_scanner.VolumeScanner):
    base_path_specs = None

    def __init__(self, mediator=None):
        super(DiskSpliter, self).__init__(mediator=mediator)
        self.base_path_specs = None

    def AnalyzePartitionInfo(self, source):
        self.base_path_specs = self.GetBasePathSpecs(source)

    def SplitDisk(self, base_path_spec, output_writer):
        file_system = resolver.Resolver.OpenFileSystem(base_path_spec)

        if file_system.type_indicator == 'TSK':
            tsk_image_object = tsk_image.TSKFileSystemImage(file_system._file_object)

            offset = 0
            length = file_system._file_object._range_size

            try:
                output_writer.Open(base_path_spec.parent.location[1:])
            except IOError as exception:
                print('Unable to open output writer with error: {0!s}.'.format(exception))
                print('')
                return
            
            MAX_LENGTH = 1024 * 1024

            while True:
                rlen = MAX_LENGTH if length - offset > MAX_LENGTH else length - offset
                data = tsk_image_object.read(offset, rlen)
                offset += rlen
                output_writer.Write(data)
                del data

                if offset >= length:
                    break
            
            output_writer.Close()

class DiskSpliterMediator(volume_scanner.VolumeScannerMediator):
    def __init__(self):
        super(DiskSpliterMediator, self).__init__() 

    def GetAPFSVolumeIdentifiers(self, volume_system, volume_identifiers):
        return volume_identifiers

    def GetPartitionIdentifiers(self, volume_system, volume_identifiers):
        return volume_identifiers

    def GetVSSStoreIdentifiers(self, volume_system, volume_identifiers):
        return volume_identifiers

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