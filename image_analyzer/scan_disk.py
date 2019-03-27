#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
from __future__ import unicode_literals

import os
import sys

from dfvfs.helpers import volume_scanner
from dfvfs.lib import errors
from dfvfs.lib import tsk_image
from dfvfs.resolver import resolver

class DiskScanner(volume_scanner.VolumeScanner):
    def __init__(self, mediator=None):
        super(DiskScanner, self).__init__(mediator=mediator)
        self.base_path_specs = None

    def ScanDisk(self, base_path_specs):
        self.base_path_specs = base_path_specs
        for base_path_spec in self.base_path_specs:
            file_system = resolver.Resolver.OpenFileSystem(base_path_spec)
            if file_system.type_indicator == 'TSK':
                tsk_image_object = tsk_image.TSKFileSystemImage(file_system._file_object)
                print('Disk scan')
            else:
                raise NotImplementedError

        return 0

class DiskScannerMediator(volume_scanner.VolumeScannerMediator):
    def __init__(self):
        super(DiskScannerMediator, self).__init__()

    def GetAPFSVolumeIdentifiers(self, volume_system, volume_identifiers):
        return volume_identifiers
    
    def GetPartitionIdentifiers(self, volume_system, volume_identifiers):
        return volume_identifiers

    def GetVSSStoreIdentifiers(self, volume_system, volume_identifiers):
        return volume_identifiers

