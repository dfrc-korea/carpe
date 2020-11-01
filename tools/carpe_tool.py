# -*- coding: utf-8 -*-

import os
import sys
import argparse
import textwrap
import platform

from datetime import datetime
from tools.helpers import manager as helpers_manager
from tools import extraction_tool, case_manager
from engine import process_engine
from modules import manager as modules_manager

from utility import database
from utility import database_sqlite     # for standalone version
from utility import errors
from utility import loggers


class CarpeTool(extraction_tool.ExtractionTool,
                case_manager.CaseManager):
    """Carpe CLI tool.

    Attributes:
        dependencies_check (bool): 나중에 넣자

    """
    NAME = 'CARPE Forensics'
    VERSION = '20200903'
    DESCRIPTION = textwrap.dedent('\n'.join([
        '',
        'CARPE Forensics',
        'files, recursing a directory (e.g. mount point) or storage media ',
        'image or device.',
        '',
        'More information can be gathered from here:',
        '    https://carpeforensic.com'
        '']))
    EPILOG = textwrap.dedent('\n'.join([
        '',
        'Example usage:',
        '',
        'Run the tool against a storage media image (full kitchen sink)',
        '--modules shellbag_connector --cid c1c16a681937b345f1990d10a9d0fdfcc8 --eid e666666666666666666666666666666668',
        '']))

    def __init__(self):
        """Initializes a CarpeTool.

        Args:
            input:

        """
        super(CarpeTool, self).__init__()

        self._cursor = None
        self.dependencies_check = True
        self.rds_check = None
        self.list_modules = False
        self.list_advanced_modules = False
        self.show_info = False

        self.sector_size = None
        self.cluster_size = None

    def ParseArguments(self, arguments):
        """Parses the command line arguments.

        Args:
            arguments (list[str]): command line arguments.

        """
        # TODO: logger 설정
        loggers.ConfigureLogging()

        argument_parser = argparse.ArgumentParser(
            description=self.DESCRIPTION, epilog=self.EPILOG, add_help=False,
            formatter_class=argparse.RawDescriptionHelpFormatter)

        self.AddBasicOptions(argument_parser)

        # Info argument group
        info_group = argument_parser.add_argument_group('informational arguments')

        self.AddInformationalOptions(info_group)

        # Module argument group
        module_group = argument_parser.add_argument_group('module arguments')

        argument_helper_names = ['artifact_definitions', 'modules', 'advanced_modules']
        helpers_manager.ArgumentHelperManager.AddCommandLineArguments(
            module_group, names=argument_helper_names)

        self.AddTimeZoneOption(module_group)
        self.AddStorageMediaImageOptions(module_group)
        self.AddVSSProcessingOptions(module_group)
        self.AddCredentialOptions(module_group)

        # source path
        argument_parser.add_argument(
            'source', action='store', metavar='SOURCE', nargs='?',
            default=None, type=str, help=(
                'Path to a source device, file or directory. If the source is '
                'a supported storage media device or image file, archive file '
                'or a directory, the files within are processed recursively.'))

        # output path
        argument_parser.add_argument(
            'output_file', metavar='OUTPUT', nargs='?', type=str,
            default=None, help='Path to a output file.')

        argument_parser.add_argument(
            '--cid', '--case_id',  action='store', dest='case_id', type=str,
            default='case01',  help='Enter your case id')

        argument_parser.add_argument(
            '--eid', '--evdnc_id', '--evidence_id', action='store', dest='evidence_id', type=str,
            default='evd01', help='Enter your evidence id')

        # sector size
        argument_parser.add_argument(
            '--sector', '--sector_size', action='store', dest='sector_size', type=str,
            default='512', help='Enter your sector size')

        # cluster size
        argument_parser.add_argument(
            '--cluster', '--cluster_size', action='store', dest='cluster_size', type=str,
            default='4096', help='Enter your cluster size')

        # check standalone mode
        argument_parser.add_argument(
            '--sqlite', '--standalone', action='store_true', dest='standalone_check', default=False, help=(
                'Define process mode to be processed.'
            )
        )

        argument_parser.add_argument(
            '--sig-check', '--signature-check', action='store_true', dest='signature_check',
            default=False, help=(
                'Define Signature Check to be processed.'
            )
        )

        argument_parser.add_argument(
            '--rds-check', action='store_true', dest='rds_check',
            default=False, help=(
                'Define RDS Check to be processed.'
            )
        )

        try:
            options = argument_parser.parse_args(arguments)
        except UnicodeEncodeError:
            # If we get here we are attempting to print help in a non-Unicode terminal.
            self._output_writer.Write('\n')
            self._output_writer.Write(argument_parser.format_help())
            return False

        try:
            self.ParseOptions(options)
        except errors.BadConfigOption as exception:
            self._output_writer.Write('ERROR: {0!s}\n'.format(exception))
            self._output_writer.Write('\n')
            self._output_writer.Write(argument_parser.format_usage())
            return False

        loggers.ConfigureLogging(
            debug_output=self._debug_mode, filename=self._log_file,
            quiet_mode=self._quiet_mode)

        return True

    def ParseOptions(self, options):
        """Parses the options.

        Args:
            options (argparse.Namespace): command line arguments.

        Raises:
            BadConfigOption: if the options are invalid.
        """
        # Check the list options first otherwise required options will raise.
        argument_helper_names = ['artifact_definitions', 'modules', 'advanced_modules']
        helpers_manager.ArgumentHelperManager.ParseOptions(
            options, self, names=argument_helper_names)

        self.list_modules = self._module_filter_expression == 'list'
        self.list_advanced_modules = self._advanced_module_filter_expression == 'list'
        self.case_id = getattr(options, 'case_id', 'case01')
        self.evidence_id = getattr(options, 'evidence_id', 'evd01')

        self.sector_size = getattr(options, 'sector_size', 512)
        self.cluster_size = getattr(options, 'cluster_size', 4096)

        self.standalone_check = getattr(options, 'standalone_check', False)
        self.signature_check = getattr(options, 'signature_check', False)
        self.rds_check = getattr(options, 'rds_check', False)
        self.show_info = getattr(options, 'show_info', False)
        self.show_troubleshooting = getattr(options, 'show_troubleshooting', False)
        self.dependencies_check = getattr(options, 'dependencies_check', True)

        if (self.list_modules or self.show_info or self.show_troubleshooting or
                self.list_timezones or self.list_advanced_modules):
            return

        self._ParseTimezoneOption(options)
        self._ParseInformationalOptions(options)
        self._ParseLogFileOptions(options)
        self._ParseStorageMediaOptions(options)

    def ExtractDataFromSources(self):

        self._output_writer.Write('Processing started.\n')
        investigator = {'investigator1': 'CARPE-Release',
                        'department': 'DFRC'
                        }

        self.AddInvestigatorInformation(investigator)

        # Create a database connection
        try:
            if self.standalone_check:
                self._cursor = database_sqlite.Database(
                    self.case_id,
                    self.evidence_id,
                    self._source_path,
                    self._output_file_path)
                self._cursor.initialize()
                self._output_writer.Write("Standalone version\n")
            else:
                self._cursor = database.Database()
            self._cursor.open()
        except Exception as exception:
            self._output_writer.Write('Failed for connect to the database: {0!s}'.format(exception))
            return

        if platform.system() == 'Windows':
            self._root_tmp_path = self._output_file_path + os.sep + 'tmp'
            if not os.path.exists(self._root_tmp_path):
                os.mkdir(self._root_tmp_path)

        # set storage path and temp path
        try:
            self.CreateStorageAndTempPath(
                cursor=self._cursor,
                case_id=self.case_id,
                evd_id=self.evidence_id)
        except Exception as exception:
            self._output_writer.Write(str(exception))
            return False

        # scan source
        scan_context = self.ScanSource(self._source_path)
        self._source_type = scan_context.source_type

        # set configuration
        configuration = self._CreateProcessingConfiguration()

        now = datetime.now()
        print('\n[%s-%s-%s %s:%s:%s] Start Analyze Image' % (
            now.year, now.month, now.day, now.hour, now.minute, now.second))

        # set signature check options
        if self.signature_check:
            self._signature_tool.ParseSignatureOptions()
            self._signature_tool.SetScanner(self._signature_tool.signature_specifications)

        now = datetime.now()
        print('\n[%s-%s-%s %s:%s:%s] Start Analyze Image' % (
            now.year, now.month, now.day, now.hour, now.minute, now.second))

        if self.rds_check:
            self.LoadReferenceDataSet()

        # # After analyzing of an IMAGE, Put the partition information into the partition_info TABLE.

        self.InsertImageInformation()

        # check partition_list
        if not self._partition_list:
            raise errors.BadConfigObject('partition does not exist.\n')

        # print partition_list
        print(self._partition_list)

        # After analyzing of filesystem, Put the block and file information into the block_info and file_info TABLE.

        self.InsertFileInformation()


        # create process
        engine = process_engine.ProcessEngine()

        # determine operating system and set time zone
        self._Preprocess(engine)

        # set modules
        engine.SetProcessModules(module_filter_expression=configuration.module_filter_expression)

        # parse Artifacts
        engine.Process(configuration)


        # set advanced modules
        engine.SetProcessAdvancedModules(advanced_module_filter_expression=configuration.advanced_module_filter_expression)

        engine.ProcessAdvancedModules(configuration)

        self._cursor.close()

        now = datetime.now()
        print('[%s-%s-%s %s:%s:%s] Finish Analyze Image' % (
            now.year, now.month, now.day, now.hour, now.minute, now.second))

    def ShowInfo(self):
        """Show information about available modules, options, etc."""

        self._output_writer.Write('{0:=^80s}\n'.format(' CARPE Forensics information '))

        module_list = self._GetModuleData()
        for header, data in module_list.items():
            self._output_writer.Write('[ {0:s} ]\n'.format(header))
            for name, desc in sorted(data):
                if header == 'Modules':
                    name = name[:-10]

                _column_width = len(name)
                _maximum_row_width = 80 - _column_width -4

                format_string = ' {{0:>{0:d}s}} : {{1:s}}\n'.format(_column_width)
                desc = desc.replace('\n', '')
                if len(desc) < _maximum_row_width:
                    self._output_writer.Write(format_string.format(name, desc))
                else:
                    format_string2 = ' {{0:<{0:d}s}}{{1:s}}\n'.format(_column_width + 3)
                    words = desc.split()
                    current = 0

                    lines = []
                    word_buffer = []
                    for word in words:
                        current += len(word) + 1
                        if current >= _maximum_row_width:
                            current = len(word)
                            lines.append(' '.join(word_buffer))
                            word_buffer = [word]
                        else:
                            word_buffer.append(word)
                    lines.append(' '.join(word_buffer))
                    self._output_writer.Write(format_string.format(name, lines[0]))
                    for line in lines[1:]:
                        self._output_writer.Write(format_string2.format('', line))
            self._output_writer.Write('\n')

    def _GetModuleData(self):
        """Retrieves the version and various module information

        Returns:
            dict[str, list[str]]: available modules.
        """
        return_dict = {}

        return_dict['Versions'] = [
            ('CARPE Forensics', self.VERSION),
            ('python', sys.version)]

        modules_information = modules_manager.ModulesManager.GetModulesInformation()

        return_dict['Modules'] = modules_information

        return return_dict

    def carve_data_from_source(self):

        self._output_writer.Write('Processing started.\n')

        # Create a database connection
        try:
            if self.standalone_check:
                self._cursor = database_sqlite.Database(
                    self.case_id,
                    self.evidence_id,
                    self._source_path,
                    self._output_file_path)
                self._cursor.initialize()
                self._output_writer.Write("Standalone version\n")
            else:
                self._cursor = database.Database()
            self._cursor.open()
        except Exception as exception:
            self._output_writer.Write('Failed for connect to the database: {0!s}'.format(exception))
            return

        if platform.system() == 'Windows':
            self._root_tmp_path = self._output_file_path + os.sep + 'tmp'
            if not os.path.exists(self._root_tmp_path):
                os.mkdir(self._root_tmp_path)

        # set storage path and temp path
        try:
            self.CreateStorageAndTempPath(
                cursor=self._cursor,
                case_id=self.case_id,
                evd_id=self.evidence_id)
        except Exception as exception:
            self._output_writer.Write(str(exception))
            return False

        # scan source
        scan_context = self.ScanSource(self._source_path)
        self._source_type = scan_context.source_type

        # set configuration
        configuration = self._CreateProcessingConfiguration()

        now = datetime.now()
        print('\n[%s-%s-%s %s:%s:%s] Start Carve Image' % (
            now.year, now.month, now.day, now.hour, now.minute, now.second))

        # After analyzing of an IMAGE, Put the partition information into the partition_info TABLE.
        self.InsertImageInformation()

        # create process
        engine = process_engine.ProcessEngine()
        self._Preprocess(engine)
        engine.SetProcessModules(module_filter_expression=configuration.module_filter_expression)

        # check partition_list
        if not self._partition_list:
            print("There is no partition")
            engine.process_carve(configuration, is_partition=False)

        else:
            print(self._partition_list)
            engine.process_carve(configuration, is_partition=True)

        now = datetime.now()
        print('[%s-%s-%s %s:%s:%s] Finish Carve Image' % (
            now.year, now.month, now.day, now.hour, now.minute, now.second))

    def extract_data_from_source(self):

        self._output_writer.Write('Processing started.\n')

        # set root_path
        if platform.system() == 'Windows':
            self._root_tmp_path = self._output_file_path + os.sep + 'tmp'
            if not os.path.exists(self._root_tmp_path):
                os.mkdir(self._root_tmp_path)

        # set tmp_path
        self._tmp_path = os.path.join(os.path.join(self._root_tmp_path, self.case_id), self.evidence_id)
        if not os.path.isdir(self._tmp_path):
            os.mkdir(self._tmp_path)

        # scan source
        scan_context = self.ScanSource(self._source_path)
        self._source_type = scan_context.source_type

        # set configuration
        configuration = self._CreateProcessingConfiguration()

        now = datetime.now()
        print('\n[%s-%s-%s %s:%s:%s] Start Extract Data' % (
            now.year, now.month, now.day, now.hour, now.minute, now.second))

        # create process
        engine = process_engine.ProcessEngine()
        self._Preprocess(engine)
        engine.SetProcessModules(module_filter_expression=configuration.module_filter_expression)
        for source_path_spec in configuration.source_path_specs:
            print(source_path_spec.comparable)
        module = engine._modules.get('extract', None)
        module.ExtractTargetDirToPath()

        now = datetime.now()
        print('[%s-%s-%s %s:%s:%s] Finish Extract Data' % (
            now.year, now.month, now.day, now.hour, now.minute, now.second))

    def create_db_connection(self):
        try:
            if self.standalone_check:
                self._cursor = database_sqlite.Database(
                    self.case_id,
                    self.evidence_id,
                    self._source_path,
                    self._output_file_path)
                self._cursor.initialize()
                self._output_writer.Write("Standalone version\n")
            else:
                self._cursor = database.Database()
            self._cursor.open()
        except Exception as exception:
            self._output_writer.Write('Failed for connect to the database: {0!s}'.format(exception))
            return
