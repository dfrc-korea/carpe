#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The carpe carving command line tool."""

from __future__ import print_function
from __future__ import unicode_literals

import logging
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))

import dependencies

from tools import carpe_tool
from utility import errors


def main():
    """The main function."""
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

    # TODO: dependencies_check 되게 해야함!!
    if tool.dependencies_check and not dependencies.CheckDependencies(
            verbose_output=False):
        return False
    try:
        tool.ExtractDataFromSources(mode='Carve')

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
    if not main():
        sys.exit(1)
    else:
        sys.exit(0)
