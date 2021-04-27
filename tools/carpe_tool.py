# -*- coding: utf-8 -*-

import os
import sys
import argparse
import textwrap
import platform
import pytz

from tools.helpers import manager as helpers_manager
from tools import extraction_tool, case_manager
from engine import process_engine
from modules import manager as modules_manager
from datetime import datetime

from utility import database
from utility import database_sqlite  # for standalone version
from utility import errors
from utility import loggers
from utility import definitions
from utility import csv_export


class CarpeTool(extraction_tool.ExtractionTool,
                case_manager.CaseManager):
    """Carpe CLI tool.

    Attributes:
        dependencies_check (bool): 나중에 넣자

    """
    NAME = 'CARPE Forensics'
    VERSION = '1.0'
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
        '    --modules shellbag_connector --cid c1c16a681937b345f1990d10a9d0fdfcc8 --eid e666666666666666666666666666666668',
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
        self.partition_id = None
        self.ignore = False
        self.csv_check = False

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

        ### Info argument group
        info_group = argument_parser.add_argument_group('informational arguments')

        self.AddInformationalOptions(info_group)

        ### Moudule argument group
        module_group = argument_parser.add_argument_group(
            'module arguments')

        argument_helper_names = ['artifact_definitions', 'modules', 'advanced_modules']
        helpers_manager.ArgumentHelperManager.AddCommandLineArguments(
            module_group, names=argument_helper_names)

        self.AddTimeZoneOption(module_group)
        self.AddStorageMediaImageOptions(module_group)
        self.AddVSSProcessingOptions(module_group)
        self.AddCredentialOptions(module_group)
        self.add_extract_option(module_group)
        self.add_carve_option(module_group)

        argument_parser.add_argument(
            '--cid', '--case_id', action='store', dest='case_id', type=str,
            help='Enter your case id')

        argument_parser.add_argument(
            '--eid', '--evdnc_id', '--evidence_id', action='store', dest='evidence_id', type=str,
            help='Enter your evidence id')

        # Allow only standalone mode
        argument_parser.add_argument(
            '--csv', '--export_csv', action='store_true', dest='csv_check', default=False, help=(
                'Define process mode to be processed.'
            )
        )

        # Export CSV at Standalone
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

        argument_parser.add_argument(
            '--ignore', action='store_true', dest='ignore',
            default=False, help=(
                'Get partition id from existing database'
            )
        )
        argument_parser.add_argument(
            '--case-name', '--case_name', action='store', dest='case_name', type=str, help='Enter your case name',
            default=''
        )
        argument_parser.add_argument(
            '--investigator', action='store', dest='investigator', type=str, help='Enter investigator name',
            default=''
        )
        argument_parser.add_argument(
            '--case_desc', '--case_description', '--case-desc', '--case-description', action='store',
            dest='case_description', type=str, help='Enter case description', default=''
        )
        ### source path
        argument_parser.add_argument(
            'source', action='store', metavar='SOURCE', nargs='?',
            default=None, type=str, help=(
                'Path to a source device, file or directory. If the source is '
                'a supported storage media device or image file, archive file '
                'or a directory, the files within are processed recursively.'))

        ### output path
        argument_parser.add_argument(
            'output_file', metavar='OUTPUT', nargs='?', type=str,
            default=None, help='Path to a output file.')

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
            self._output_writer.Write('{0!s}\n'.format(exception))
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

        self.standalone_check = getattr(options, 'standalone_check', False)
        self.csv_check = getattr(options, 'csv_check', False)
        self.signature_check = getattr(options, 'signature_check', False)
        self.rds_check = getattr(options, 'rds_check', False)
        self.show_info = getattr(options, 'show_info', False)
        self.show_troubleshooting = getattr(options, 'show_troubleshooting', False)
        self.dependencies_check = getattr(options, 'dependencies_check', True)
        self.ignore = getattr(options, 'ignore', False)

        self._ParseTimezoneOption(options)

        if (self.list_modules or self.show_info or self.show_troubleshooting or
                self.list_timezones or self.list_advanced_modules):
            return

        self._ParseInformationalOptions(options)
        self._ParseLogFileOptions(options)
        self._ParseStorageMediaOptions(options)
        self.parse_extract_options(options)
        self.parse_carve_options(options)

    def ExtractDataFromSources(self, mode):

        self._output_writer.Write('Processing started.\n')

        investigator = {'investigator1': 'test', 'department': 'DFRC'}
        self.AddInvestigatorInformation(investigator)

        if not self.case_id or not self.evidence_id:
            raise errors.BadConfigOption('case_id or evidence_id does not exist.\n')

        # Set database connection and make root, tmp path
        try:
            self.set_conn_and_path()
        except errors.BadConfigOption as exception:
            self._output_writer.Write('ERROR: {0!s}\n'.format(exception))
            return False

        # update process state
        self.update_process_state(definitions.PROCESS_STATE_PROCESSING)

        # scan source
        scan_context = self.ScanSource(self._source_path)
        self._source_type = scan_context.source_type

        # set partition_list
        if self.ignore:
            self.set_partition_list()

        # set configuration
        configuration = self._CreateProcessingConfiguration()

        # set signature check options
        if self.signature_check:
            self._signature_tool.ParseSignatureOptions()
            self._signature_tool.SetScanner(self._signature_tool.signature_specifications)

        if self.rds_check:
            self.LoadReferenceDataSet()

        self.print_now_time(f'Start {mode} Image')

        disk_info = []
        if not self.ignore:
            # After analyzing of an IMAGE, Put the partition information into the partition_info TABLE.
            disk_info = self.InsertImageInformation()

        # check partition_list
        if mode == 'Analyze' and not self._partition_list:
            if configuration.source_path_specs[0].type_indicator == 'APFS':
                pass
            # else:
            #     raise errors.BadConfigObject('partition does not exist.\n')

        # print partition_list
        print(f"\nThe number of partition : {len(self._partition_list)}")
        for key, value in self._partition_list.items():
            print(f"Partition ({configuration.source_path_specs[int(key[1:]) - 1].type_indicator}) \'{key}\' : \'{value}\'")
        print()  # for line feed

        if mode == 'Analyze' and not self.ignore:
            self.print_now_time(f'Insert File Information')
            # After analyzing of filesystem, Put the block and file information into the block_info and file_info TABLE.
            self.InsertFileInformation()

        # create process
        engine = process_engine.ProcessEngine()

        # determine operating system
        self.print_now_time(f'Determine Operation System')
        self._Preprocess(engine)

        # set timezone
        self.print_now_time(f'Set Timezone')
        if self._time_zone is not pytz.UTC:
            engine.knowledge_base.SetTimeZone(self._time_zone)

        # set modules
        self.print_now_time(f'Set Modules')
        engine.SetProcessModules(module_filter_expression=configuration.module_filter_expression)

        # carpe.py
        if mode == 'Analyze':
            # parse Artifacts
            engine.Process(configuration)

            # set advanced modules
            engine.SetProcessAdvancedModules(
               advanced_module_filter_expression=configuration.advanced_module_filter_expression)

            # parse advanced modules
            engine.ProcessAdvancedModules(configuration)
                
            if configuration.source_path_specs[0].type_indicator == 'APFS':
                pass
            else:
                # carve
                print("Carving Start")
                if not self._partition_list:
                    print("No partition")
                    engine.process_carve(configuration, is_partition=False)
                else:
                    print(self._partition_list)
                    engine.process_carve(configuration, is_partition=True)

        # carpe_carve.py
        elif mode == 'Carve':
            # check partition_list
            if not self._partition_list:
                print("No partition")
                engine.process_carve(configuration, is_partition=False)
            else:
                print(self._partition_list)
                engine.process_carve(configuration, is_partition=True)

        # carpe_extract.py
        elif mode == 'Extract':
            for par in disk_info:
                if par['length'] != 0:
                    par['length'] /= (1024 * 1024)  # byte to MB
                info = ""
                info += "vol_name: " + par['vol_name'] + "\n"
                info += "filesystem: " + str(par['filesystem']) + "\n"
                info += "par_label: " + par['par_label'] + "\n"
                info += "size: " + str(int(par['length'])) + "MB\n"
                print(info)

            self.print_now_time(f'Start Extract File/Directory')
            module = engine._modules.get('extract_connector', None)
            module.ExtractTargetDirToPath(
                source_path_spec=configuration.source_path_specs[int(self.par_num[1:]) - 1],
                configuration=configuration,
                dir_path=self.extract_path,
                output_path=self._output_file_path)
            self.print_now_time(f'Finish Extract File/Directory')

        # update process state
        self.update_process_state(definitions.PROCESS_STATE_COMPLETE)

        self._cursor.close()
        if self.csv_check:
            self.print_now_time(f'Start Exporting CSV')
            self.t_list = csv_export.export_table_list(self._output_file_path + os.sep + self.case_id + '.db')
            csv_export.export_csv(self._output_file_path, self.case_id + '.db', self.t_list)

            self.print_now_time(f'Finish Exporting CSV')
        self.print_now_time(f'Finish {mode} Image')

    def set_conn_and_path(self):
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

        # set root path
        if platform.system() == 'Windows':
            if self._output_file_path is None:
                raise errors.BadConfigOption('Missing output file path.')
            self._root_tmp_path = self._output_file_path + os.sep + 'tmp'
            if not os.path.exists(self._root_tmp_path):
                os.mkdir(self._root_tmp_path)
        else:  # for linux
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
                _maximum_row_width = 80 - _column_width - 4

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

    def print_now_time(self, phrase=""):
        print('[' + datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3] + '] ' + phrase)

    def update_process_state(self, state):
        self._cursor.execute_query(f"UPDATE evidence_info SET process_state={state} WHERE case_id like \'{self.case_id}\' and evd_id like \'{self.evidence_id}\';")
