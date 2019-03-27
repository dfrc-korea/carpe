#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
from __future__ import unicode_literals

import os
import sys
import argparse
import logging

from multiprocessing import Process

from dfvfs.helpers import volume_scanner
from dfvfs.lib import errors
from dfvfs.lib import tsk_image
from dfvfs.resolver import resolver


class DiskSpliter(volume_scanner.VolumeScanner):
    def __init__(self, mediator=None):
        super(DiskSpliter, self).__init__(mediator=mediator)

    def SplitDisk(self, base_path_specs, output_writer):
        print("Split Disk")
        base_name = 0x43 # C:\
        procs = []
        for base_path_spec in base_path_specs:
            #file_object = resolver.Resolver.OpenFileObject(base_path_spec.parent.parent)
            file_system = resolver.Resolver.OpenFileSystem(base_path_spec)
            if file_system.type_indicator == 'TSK':
                tsk_image_object = tsk_image.TSKFileSystemImage(file_system._file_object)
                file_name = str(chr(base_name)) if base_path_spec.parent.type_indicator != 'VSHADOW' \
                    else str(chr(base_name)) + '_' + base_path_spec.parent.location[1:]
                base_name += 1
                imageWrite_process = Process(target=self._tskWriteImage, args=(tsk_image_object, output_writer, file_name))
                imageWrite_process.start()
                procs.append(imageWrite_process)
                #imageWrite_process.join()
            else:
                raise NotImplementedError

        for proc in procs:
            proc.join()

    def _tskWriteImage(self, image_object, output_writer, file_name):
        offset = 0
        length = image_object.get_size()
        try:
            output_writer.Open(file_name)
        except IOError as exception:
            print('Unable to open output writer with error: {0!s}.'.format(exception))
            print('')
            return
        MAX_LENGTH = 1024 * 1024 # 1 MB
        while True: # need to add multiprocessing that extract data in 100 MB 
            rlen = MAX_LENGTH if length - offset > MAX_LENGTH else length - offset
            data = image_object.read(offset, rlen)
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

def Main():
    print("Main program")

    argument_parser = argparse.ArgumentParser(description=(
        'Split disk into several volume images.'
    ))

    argument_parser.add_argument(
        '--output_directory', '--output-directory', dest='output_dir', action='store',
        metavar='source.hashed', default=None, help=(
            'path of the output directory.'
        )
    )

    argument_parser.add_argument(
        'source', nargs='?', action='store', metavar='image.raw',
        default=None, help='path of the directory or storage media image.'
    )

    options = argument_parser.parse_args()

    if not options.source:
        print('Source value is missing.')
        print('')
        argument_parser.print_help()
        print('')
        return False

    logging.basicConfig(
        level=logging.INFO, format='[%(levelname)s] %(message)s'
    )

    if options.output_dir:
        output_dir = options.output_dir
    else:
        output_dir = os.getcwd()
        
    output_writer = FileOutputWriter(output_dir)
 
    return_value = True
    mediator = DiskSpliterMediator()
    disk_spliter = DiskSpliter(mediator=mediator)

    try:
        base_path_specs = disk_spliter.GetBasePathSpecs(options.source)
        if not base_path_specs:
            print('NO supported file system found in source.')
            print('')
            return False
        
        disk_spliter.SplitDisk(base_path_specs, output_writer)

        print('')
        print('Completed.')

    except errors.ScannerError as exception:
        return_value = False

        print('')
        print('[ERROR] {0!s}'.format(exception))

    except KeyboardInterrupt:
        return_value = False

        print('')
        print('Aborted by user.')

    return return_value


if __name__ == "__main__":
    if not Main():
        sys.exit(1)
    else:
        sys.exit(0)
