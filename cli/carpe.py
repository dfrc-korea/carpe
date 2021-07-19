#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The carpe command line tool."""

from __future__ import print_function
from __future__ import unicode_literals

import logging
import os
import sys
from pyfiglet import Figlet

sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))

import dependencies

from tools import carpe_tool
from utility import errors


def Main():
    """The main function."""
    f = Figlet(font='standard')
    print(f.renderText('Carpe'))
    print(f.renderText('Forensics'))
    print('---------------------------------------------------------------------')
    print('\nComprehensive Analysis and Research Platform for digital Evidence')
    print('Korea University - Digital Forensic Reseach Center')
    print('URL -> https://github.com/dfrc-korea/carpe\n')
    #print("Copyright 2021. Korea University - DFRC. All rights reserved ")
    print('---------------------------------------------------------------------')
    print()
    sys.stdout.flush()

    tool = carpe_tool.CarpeTool()

    if not tool.ParseArguments(sys.argv[1:]):
        return False

    if tool.show_troubleshooting:
        print('Using Python version {0!s}'.format(sys.version))
        print()
        print('Path: {0:s}'.format(os.path.abspath(__file__)))
        print()
        print(tool.GetVersionInformation())
        print()
        dependencies.CheckDependencies(verbose_output=True)

        print('Also see: http://forensic.korea.ac.kr')
        return True

    if tool.show_info:
        tool.ShowInfo()
        return True

    have_list_option = False

    if tool.list_modules:
        tool.ListModules()
        have_list_option = True

    if tool.list_timezones:
        tool.ListTimeZones()
        have_list_option = True

    if have_list_option:
        return True

    # TODO: dependencies_check 되게 해야함!!
    if tool.dependencies_check and not dependencies.CheckDependencies(
            verbose_output=False):
        return False

    try:
        sys.stdout.flush()
        tool.ExtractDataFromSources(mode='Analyze')

    except (KeyboardInterrupt, errors.UserAbort):
        logging.warning('Aborted by user.')
        return False

    except (errors.BadConfigOption, errors.SourceScannerError, errors.BadConfigObject) as exception:
        # Display message on stdout as well as the log file.
        print(exception)
        logging.error(exception)
        return False

    return True


if __name__ == '__main__':

    if not Main():
        sys.exit(1)
    else:
        sys.exit(0)
