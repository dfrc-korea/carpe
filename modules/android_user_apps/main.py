# -*- coding: utf-8 -*-
"""android user apps parser."""

import os
import datetime
import argparse

from modules.android_user_apps import loggers
from modules.android_user_apps import logger
from modules.android_user_apps.process import *


def main(input=None, debug_mode=False, quiet_mode=False):
    # TODO: print program infromation.

    if not input:
        argument_parser = argparse.ArgumentParser(description='Android User Apps Parser.')
        argument_parser.add_argument('-i', '--input_path', required=True, action='store',
                                     help='Path to input file/directory')
        argument_parser.add_argument('-o', '--output_path', required=True, action='store', help='Output path')
        argument_parser.add_argument('-d', '--debug', default=False, action='store', help='set debug mode')
        argument_parser.add_argument('-q', '--quiet', default=False, action='store', help='set quiet mode')

        args = argument_parser.parse_args()

        input_path = args.input_path
        output_path = os.path.abspath(args.output_path)
        _debug_mode = args.debug
        _quiet_mode = args.quiet
    else:
        input_path = input
        output_path = input
        _debug_mode = debug_mode
        _quiet_mode = quiet_mode

    if len(input_path) == 0:
        print('invalid input file or directory.')
        return

    if len(output_path) == 0:
        print('invalid output file or directory.')
        return

    # set output directory and logfile
    local_date_time = datetime.datetime.now()
    _result_path = '{0:s}AU2A_Results-{1:04d}{2:02d}{3:02d}T{4:02d}{5:02d}{6:02d}'.format(
        output_path + os.sep, local_date_time.year, local_date_time.month,
        local_date_time.day, local_date_time.hour, local_date_time.minute,
        local_date_time.second)

    _log_file = '{0:s}{1:s}-{2:04d}{3:02d}{4:02d}T{5:02d}{6:02d}{7:02d}.log.gz'.format(
        _result_path, os.sep + 'AU2A', local_date_time.year, local_date_time.month,
        local_date_time.day, local_date_time.hour, local_date_time.minute,
        local_date_time.second)

    loggers.ConfigureLogging(debug_output=_debug_mode, filename=_log_file,
                             quiet_mode=_quiet_mode)

    results = []
    for key, val in SUPPORTED_USER_APPS.items():
        search_results = search(input_path, val[0])
        if not search_results:
            if not os.path.exists(_result_path):
                os.mkdir(_result_path)
            logger.info(f'No results: {key}:{val[0]}')
        else:
            result = process(search_results, val[1], _result_path)
            if result:
                for ret in result:
                    results.append(ret)

    return results


if __name__ == '__main__':
    #    parser = argparse.ArgumentParser(de)
    main()
