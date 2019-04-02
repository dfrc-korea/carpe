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
        self.prefix = 'p'

    def ScanDisk(self, base_path_specs):
        disk_info = []
        self.base_path_specs = base_path_specs
        for i, base_path_spec in enumerate(self.base_path_specs):
            file_system = resolver.Resolver.OpenFileSystem(base_path_spec)
            par_name = self.prefix + str(i)
            if file_system.type_indicator == 'TSK':
                tsk_image_object = tsk_image.TSKFileSystemImage(file_system._file_object)
                length = tsk_image_object.get_size()
                par_type = 'TSK' if base_path_spec.parent.type_indicator != 'VSHADOW' else 'VSS'
                par_info = [par_name, length, par_type, base_path_spec]
                disk_info.append(par_info)
            else:
                raise NotImplementedError

        return disk_info

class DiskScannerMediator(volume_scanner.VolumeScannerMediator):
    def __init__(self):
        super(DiskScannerMediator, self).__init__()

    def GetAPFSVolumeIdentifiers(self, volume_system, volume_identifiers):
        return volume_identifiers
    
    def GetPartitionIdentifiers(self, volume_system, volume_identifiers):
        return volume_identifiers

    def GetVSSStoreIdentifiers(self, volume_system, volume_identifiers):
        return volume_identifiers

