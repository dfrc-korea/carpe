# -*- coding: utf-8 -*-
"""The parsers CLI arguments helper."""

from __future__ import unicode_literals

from tools import carpe_tool
from tools.helpers import interface
from tools.helpers import manager
from utility import errors


class AdvancedModulesArgumentsHelper(interface.ArgumentsHelper):
  """Modules CLI arguments helper."""

  NAME = 'advanced_modules'
  DESCRIPTION = 'Advanced Modules command line arguments.'

  @classmethod
  def AddArguments(cls, argument_group):
    """Adds command line arguments to an argument group.
    This function takes an argument parser or an argument group object and adds
    to it all the command line arguments this helper supports.
    Args:
      argument_group (argparse._ArgumentGroup|argparse.ArgumentParser):
          argparse group.
    """
    # TODO: 문구 수정해야함
    argument_group.add_argument(
        '--advanced_modules', dest='advanced_modules', type=str, action='store',
        default='', metavar='ADVANCED_MODULE_FILTER_EXPRESSION', help=(
            'Define which presets, modules to use, or show '
            'possible values. The expression is a comma separated string '
            'where each element is a module name. Each '
            'element can be prepended with an exclamation mark to exclude the '
            'item. Matching is case insensitive. Examples: "linux,'
            '!bash_history" enables the linux preset, without the '
            'bash_history parser. "sqlite,!sqlite/chrome_history" enables '
            'all sqlite plugins except for chrome_history". "win7,syslog" '
            'enables the win7 preset, as well as the syslog parser. Use '
            '"--modules list" or "--info" to list available modules.'))

  @classmethod
  def ParseOptions(cls, options, configuration_object):
    """Parses and validates options.
    Args:
      options (argparse.Namespace): parser options.
      configuration_object (CLITool): object to be configured by the argument
          helper.
    Raises:
      BadConfigObject: when the configuration object is of the wrong type.
    """
    if not isinstance(configuration_object, carpe_tool.CarpeTool):
      raise errors.BadConfigObject(
          'Configuration object is not an instance of CLITool')

    modules = cls._ParseStringOption(options, 'advanced_modules', default_value='')
    modules = modules.replace('\\', '/')

    # TODO: validate parser names.

    setattr(configuration_object, '_advanced_module_filter_expression', modules)


manager.ArgumentHelperManager.RegisterHelper(AdvancedModulesArgumentsHelper)