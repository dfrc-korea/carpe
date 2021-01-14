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

        # analyze ReFS
        vol = VolumeHandle()
        vol.load_image(output_path)
        try:
            self.refs = refs.ReFS(vol)
        except refs.UnknownReFSVersionError:
            print('No ReFS')
            os.remove(output_path)
            return
        self.refs.read_volume()
        self.refs.file_system_metadata()
        self.refs.logfile_info()
        self._pwd = []
        self.parent_dir = []
        self._all_items = list()
        if self.refs.root_dir():
            self._cwd = self.refs.root
            self._pwd.append('root')
            if self.refs.root.children_table:
                for v in self.refs.root.children_table.values():
                    v.ls()

            if self.refs.root.table:
                for name, metadata in self.refs.root.table.items():
                    if metadata['file_type'] == 'DIR':
                        self.parent_dir.append(self._cwd)
                        self._pwd.append(self._pwd[-1] + '\\' + name)
                        dir_obj = self.refs.object_table.table[metadata['object_id']]
                        tmp = self._cwd
                        self._explore_directory(dir_obj)
                        self._cwd = tmp
                        self._all_items.append({'name' : name, 'metadata':metadata, 'path':self._pwd.pop()})
                    else:
                        self._all_items.append({'name': name, 'metadata': metadata, 'path':self._pwd[-1] + '\\' + name})
                    print(f"[{metadata['file_type']}] {name:<30} {metadata['ModifiedTime']}")


        os.remove(output_path)
        return vol

    def _explore_directory(self, dir_obj):
        self._cwd = self.refs.change_directory(dir_obj)
        for name, metadata in self._cwd.table.items():
            if metadata['file_type'] == 'DIR':
                self.parent_dir.append(self._cwd)
                self._pwd.append(self._pwd[-1] + '\\' + name)
                dir_obj = self.refs.object_table.table[metadata['object_id']]
                self._explore_directory(dir_obj)
                self._all_items.append({'name': name, 'metadata': metadata, 'path': self._pwd.pop()})
            else:
                self._all_items.append({'name': name, 'metadata': metadata, 'path': self._pwd[-1] + '\\' + name})






manager.ModulesManager.RegisterModule(ReFSConnector)
