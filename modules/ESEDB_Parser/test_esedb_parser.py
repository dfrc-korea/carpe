# -*- coding: utf-8 -*-
"""ESE database parser."""

import pyesedb

from . import logger
from . import esedb_parser
from . import esedb_errors as errors

def PrintUsage():
    pass

#TODO: Argument Parser

if __name__ == '__main__':
    filepath = './samples/WebCacheV01.dat'
    esedb_file = pyesedb.file()

    try:
        esedb_file.open(filepath)
    except IOError as exception:
        logger.debug('unable to open file with error: {0!s}'.format(exception))

    try:
        esedb_parsers = esedb_parser.ESEDBParser.GetESEDBParserObjects()
        table_names = frozenset(esedb_parser.ESEDBParser.GetTableNames(esedb_file))

        for parser in esedb_parsers.values():

            if not parser.required_tables.issubset(table_names):
                continue

            try:
                parser.Process(database=esedb_file)

            except errors.UnableToParseFile as exception:
                logger.debug('[{0:s}] unable to parse file with error: {1!s}'.format(
                    parser.NAME, exception))

    finally:
        esedb_file.close()

