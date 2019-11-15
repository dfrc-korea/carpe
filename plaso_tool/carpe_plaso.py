# -*- coding: utf-8 -*-
from __future__ import print_function
from __future__ import unicode_literals

import logging
import multiprocessing
import os
import sys

from plaso import dependencies
from plaso.cli import log2timeline_tool
from plaso.cli import tools as cli_tools
from plaso.cli import psort_tool
from plaso.lib import errors

import pdb

def Main():
  
  pdb.set_trace()
  l2t_tool = log2timeline_tool.Log2TimelineTool()
  
  # Run Log2timeline Tool
  if not l2t_tool.ParseArguments(sys.argv[1:]):
    return False

  try:
    l2t_tool.ExtractEventsFromSources()

  except (KeyboardInterrupt, errors.UserAbort):
    logging.warning('Aborted by user.')
    return False

  except (errors.BadConfigOption, errors.SourceScannerError) as exception:
    logging.warning(exception)
    return False
  
  # Run PSort Tool
  input_reader = cli_tools.StdinInputReader()
  p_tool = psort_tool.PsortTool(input_reader=input_reader)

  if not p_tool.ParseArguments(sys.argv[1:]):
    return False

  try:
    p_tool.ProcessStorage()

  except (KeyboardInterrupt, errors.UserAbort):
    logging.warning('Aborted by user.')
    return False

  except errors.BadConfigOption as exception:
    logging.warning(exception)
    return False

  return True


if __name__ == '__main__':
  multiprocessing.freeze_support()

  if not Main():
    sys.exit(1)
  else:
    sys.exit(0)
