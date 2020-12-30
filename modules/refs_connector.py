# -*- coding: utf-8 -*-
"""module for ReFS."""
import os
from datetime import datetime

from modules import manager
from modules import interface
from modules.refs.refs import refs
from modules.refs.refs.volume import VolumeHandle

from dfvfs.lib import tsk_partition as dfvfs_partition
from dfvfs.resolver import resolver as dfvfs_resolver

class ReFSConnector(interface.ModuleConnector):
    NAME = 'refs_connector'
    DESCRIPTION = 'Module for ReFS'

    _plugin_classes = {}

    def __init__(self):
        super(ReFSConnector, self).__init__()

    def Connect(self, par_id, configuration, source_path_spec, knowledge_base):
        query_separator = self.GetQuerySeparator(source_path_spec, configuration)
        path_separator = self.GetPathSeparator(source_path_spec)

        # for volume size
        file_system = dfvfs_resolver.Resolver.OpenFileSystem(source_path_spec)
        tsk_volumes = file_system.GetTSKVolume()
        vol_part, _ = dfvfs_partition.GetTSKVsPartByPathSpec(tsk_volumes, source_path_spec)

        if dfvfs_partition.TSKVsPartIsAllocated(vol_part):
            bytes_per_sector = dfvfs_partition.TSKVolumeGetBytesPerSector(vol_part)
            length = dfvfs_partition.TSKVsPartGetNumberOfSectors(vol_part)
            start_sector = dfvfs_partition.TSKVsPartGetStartSector(vol_part)

        # extract volume
        rf = open(configuration.source_path, 'rb')
        rf.seek(start_sector * bytes_per_sector)

        output_path = configuration.tmp_path + os.sep + 'temp_volume'
        wf = open(output_path, 'wb')
        wf.write(rf.read(length * bytes_per_sector))
        rf.close()
        wf.close()

        vol = VolumeHandle()
        vol.load_image(output_path)
        try:
            _refs = refs.ReFS(vol)
        except refs.UnknownReFSVersionError:
            print('No ReFS')
            os.remove(output_path)
            return
        _refs.read_volume()
        _refs.file_system_metadata()
        _refs.logfile_info()
        if _refs.root_dir():
            _cwd = _refs.root
            if _refs.root.children_table:
                for v in _refs.root.children_table.values():
                    v.ls()

            if _refs.root.table:
                for name, metadata in _refs.root.table.items():
                    print(f"[{metadata['file_type']}] {name:<30} {metadata['ModifiedTime']}")


        os.remove(output_path)
        return vol





manager.ModulesManager.RegisterModule(ReFSConnector)
