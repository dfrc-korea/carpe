# -*- coding: utf-8 -*-
from __future__ import print_function
from __future__ import unicode_literals

import logging
import multiprocessing
import os
import sys

from plaso import dependencies
from plaso.cli import carpe_l2t_tool
from plaso.lib import errors

import pdb

def Main():
  tool = carpe_l2t_tool.CARPEL2TTool()
  if not tool.ParseArguments(sys.argv[1:]):
    return False

  try:
    tool.ExtractEventsFromSources()

  except (KeyboardInterrupt, errors.UserAbort):
    logging.warning('Aborted by user.')
    return False

  except (errors.BadConfigOption, errors.SourceScannerError) as exception:
    logging.warning(exception)
    return False

  return True


if __name__ == '__main__':
  multiprocessing.freeze_support()

  if not Main():
    sys.exit(1)
  else:
    sys.exit(0)
