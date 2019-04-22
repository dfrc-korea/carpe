#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
from __future__ import unicode_literals

import os
import sys

from dfvfs.helpers import source_scanner
from dfvfs.resolver import resolver
from dfvfs.lib import errors
from dfvfs.lib import definitions
from dfvfs.lib import tsk_partition
from dfvfs.lib import vshadow

class DiskScanner(object):
    def __init__(self):
        super(DiskScanner, self).__init__()
        self._source_scanner = source_scanner.SourceScanner()
        self.base_path_specs = None
        self.prefix = 'p'

    def Analyze(self, source_path):
        """Analyze Disk.

        Args:
          source_path (str): the source path.

        Raises:
          RuntimeError: if the source path does not exists, or if the
              is not a file or directory, or if the format of or within
              file is not supported.
          NotImplementedError: Must be implemented
        """
        if not os.path.exists(source_path):
            raise RuntimeError('No such source: {0:s}.'.format(source_path))

        scan_context = source_scanner.SourceScannerContext()
        scan_path_spec = None
        scan_step = 0

        scan_context.OpenSourcePath(source_path)

        while True:
            self._source_scanner.Scan(
                scan_context, auto_recurse=True,
                scan_path_spec=scan_path_spec
            )

            if not scan_context.updated:
                break
            
            scan_step += 1

            # The source is a directory or file.
            if scan_context.source_type in [
                definitions.SOURCE_TYPE_DIRECTORY, definitions.SOURCE_TYPE_FILE]:
                break
            
            # The source scanner found a locked volume, e.g. an encrypted voluem,
            # and we need a credential to unlock the volume.
            # TODO: Implement related function
            for locked_scan_node in scan_context.locked_scan_nodes:
                raise NotImplementedError

        return self.ScanDisk(scan_context)

    def ScanDisk(self, scan_context):
        """Scan Disk

        Args:
          scan_context (SourceScannerContext): the source scanner context.
          scan_step (Optional[int]): the scan step, where NOne represents no step.            
        """
        scan_node = scan_context.GetRootScanNode()
        while len(scan_node.sub_nodes) == 1:
            scan_node = scan_node.sub_nodes[0]
        disk_info = []
        self._ScanDisk(scan_context, scan_node, disk_info)
        return disk_info
        
    def _ScanDisk(self, scan_context, scan_node, disk_info):
        """Scan Disk internal

        Args:
          scan_context (SourceScannerContext): the source scanner context.
          scan_node (SourceScanNode): the scan node.
        """
        if not scan_node:
            return

        if scan_node.path_spec.IsVolumeSystem() and not scan_node.path_spec.IsVolumeSystemRoot():
            file_system = resolver.Resolver.OpenFileSystem(scan_node.path_spec)

            if scan_node.type_indicator == definitions.TYPE_INDICATOR_TSK_PARTITION:
                tsk_volumes = file_system.GetTSKVolume()
                vol_part, _ = tsk_partition.GetTSKVsPartByPathSpec(tsk_volumes, scan_node.path_spec)
                if tsk_partition.TSKVsPartIsAllocated(vol_part):
                    bytes_per_sector = tsk_partition.TSKVolumeGetBytesPerSector(vol_part)
                    length = tsk_partition.TSKVsPartGetNumberOfSectors(vol_part)
                    start_sector = tsk_partition.TSKVsPartGetStartSector(vol_part)
                    vol_name = getattr(scan_node.path_spec, 'location', None)[1:]
                    #vol_name = self.prefix + str(scan_node.path_spec.part_index)
                    base_path_spec = scan_node.path_spec
                    disk_info.append({"base_path_spec" : base_path_spec, "type_indicator" : scan_node.type_indicator, \
                        "length" : length * bytes_per_sector, "bytes_per_sector" : bytes_per_sector, "start_sector" : start_sector, \
                            "vol_name" : vol_name, "identifier" : None})
            elif scan_node.type_indicator == definitions.TYPE_INDICATOR_VSHADOW:
                vss_volumes = file_system.GetVShadowVolume()
                store_index = vshadow.VShadowPathSpecGetStoreIndex(scan_node.path_spec)
                vss_part = list(vss_volumes.stores)[store_index]
                length = vss_part.volume_size
                identifier = getattr(vss_part, 'identifier', None)
                vol_name = getattr(scan_node.path_spec, 'location', None)[1:]
                base_path_spec = scan_node.path_spec
                disk_info.append({"base_path_spec" : base_path_spec, "type_indicator" : scan_node.type_indicator, \
                    "length" : length, "bytes_per_sector" : None, "start_sector" : None, "vol_name" : vol_name, \
                        "identifier" : identifier})
            
            
            

        for sub_scan_node in scan_node.sub_nodes:
            self._ScanDisk(scan_context, sub_scan_node, disk_info)


        """disk_info = []
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

        return disk_info"""

    def SetPrefix(self, prefix):
        self.prefix = prefix

    def GetPrefix(self):
        return self.prefix