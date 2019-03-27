from disk_util import split_disk
from dfvfs.lib import errors

import sys
import os
import argparse
import logging

def Main():
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
        
    output_writer = split_disk.FileOutputWriter(output_dir)
 
    return_value = True
    mediator = split_disk.DiskSpliterMediator()
    disk_spliter = split_disk.DiskSpliter(mediator=mediator)

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