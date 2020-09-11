# -*- coding: utf-8 -*-

import os
import sys
import argparse
import textwrap
import platform

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

    def ParseArguments(self, arguments):
        """Parses the command line arguments.

        Args:
            arguments (list[str]): command line arguments.

        """
        #TODO: logger 설정
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

        argument_parser.add_argument(
            '--cid', '--case_id',  action='store', dest='case_id', type=str,
            default=None,  help='Enter your case id')

        argument_parser.add_argument(
            '--eid', '--evdnc_id', '--evidence_id', action='store', dest='evidence_id', type=str,
            default=None, help='Enter your evidence id')

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
            ))

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
        self.case_id = getattr(options, 'case_id', False)
        self.evidence_id = getattr(options, 'evidence_id', False)

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

        investigator = {'investigator1': 'jeong byeongchan',
                        'investigator2': 'joun jihun',
                        'investigator3': 'kim junho',
                        'investigator4': 'youn woosung',
                        'department': 'DFRC'
                        }

        self.AddInvestigatorInformation(investigator)

        #  Create a database connection
        try:
            if self.standalone_check:
                self._cursor = database_sqlite.Database(
                    self.case_id,
                    self.evidence_id,
                    self._source_path,
                    self._output_file_path)
                self._cursor.initialize()
                self._output_writer.Write("Standalone version")
            else:
                self._cursor = database.Database()
            self._cursor.open()
        except Exception as exception:
            self._output_writer.Write('Failed tor connect to the database: {0!s}'.format(exception))
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

        # detect operating_system
        # # skpark(lnk) e111111111111111111111111111111111
        # self._partition_list = {'p1': 'p19cadd320aefe40dfa5c85ebc38ff7613',
        #                         'p2': 'p143490fa32b8a4f00a4b21d0ca1ac9530',
        #                         'p3': 'p1ac280f9e9d864f84ab2bf4d68b5088ab',
        #                         'p4': 'p1cdd828002bec46c6843905786daaac6f'}

        ## skpark(ewf) e111111111111111111111111111111114
        #self._partition_list = {'p1': 'p18e6c2dd56b5c405fb7c6738a9d7241ba',
        #                        'p2': 'p13eac5c34d91b480da914d8b3e309bda0',
        #                        'p3': 'p1b9fd2dda0cf4499e99902bbed321ad74',
        #                        'p4': 'p10377ea5b2dad4aa3a22fbbac2a7574e6'}

        ## email - test  e222222222222222222222222222222222
        #self._partition_list = {'p1': 'p1f7af5047f1674818abc63de056ab1939',
        #                        'p2': 'p1e3748f626c224f41ab513f782c37e5c7'}

        ## email - test  e222222222222222222222222222222223
        #self._partition_list = {'p1': 'p1bf219158859742a5a939ab2c51873161',
        #                        'p2': 'p1a0229b45eaf341c8b81153d445b538c4'}

        ## defa - test  e222222222222222222222222222222224
        #self._partition_list = {'p1': 'p15ef2746ec60b4943a70ac79f5fcb3606',
        #                        'p2': 'p1d09897bb7b334b79a2e1c21aa3ea2896'}

        ## filehistory - e111111111111111111111111111111117
        #self._partition_list = {'p1': 'p10acede86e2a747578712f5facf06abe6',
        #                        'p2': 'p1951b89fd680d4ac390a5803e7ef75f26'}

        ## skpark(RAW) e111111111111111111111111111111118
        #self._partition_list = {'p1': 'p14b939fec88c5402180526f248b13b061',
        #                        'p2': 'p15b56b52b93aa4792ac5e52cf88862425',
        #                        'p3': 'p174739d4e0f774e2996f918818e2895b1',
        #                        'p4': 'p110675c58eb344fdfbe0a34ff2fd7a15b'}

        # # 미나레지스트리 e666666666666666666666666666666667
        # self._partition_list = {'p1': 'p1eda9ba33b1104c34af8547f1202a8568'}

        ## superfetch - e222222222222222222222222222222225
        #self._partition_list = {'p1': 'p1fcf83303585e4bafb1c9fc2ec8db05a9',
        #                        'p2': 'p1efe18b8b20094fc18177741a6b994728'}

        # Opera
        # self._partition_list = {'p1' : 'p195955defbb674458850527ac4e85d969'}

        # # Web
        # self._partition_list = {'p1': 'p1bb5a0d873b874c40a04f9ee80158dad4',
        #                        'p2': 'p1f1a5000d57b04ea59aea665acd5c3ba4'}

        # # mobile_test
        # self._partition_list = {'p1': 'p10c82e8a81d3541a2a86f1b5f55c146aa'}

        # skpark(RAW) e111111111111111111111111111111118
        self._partition_list = {'p1': 'p1606ca11e8b9444f5bc55a266b0211962',
                                'p2': 'p1b2e2f08896cb4c4885d2e8f9f6cdd21b',
                                'p3': 'p13b32b5dbfc1840bab7890aa1c4f8fb66',
                                'p4': 'p12de9eb3fb63540678af72b208242dab1'}

        # set configuration
        configuration = self._CreateProcessingConfiguration()

        # set signature check options
        if self.signature_check:
            self._signature_tool.ParseSignatureOptions()
            self._signature_tool.SetScanner(self._signature_tool.signature_specifications)

        from datetime import datetime

        now = datetime.now()
        print('\n[%s-%s-%s %s:%s:%s] Start Analyze Image' % (
            now.year, now.month, now.day, now.hour, now.minute, now.second))

        if self.rds_check:
            self.LoadReferenceDataSet()

        # # After analyzing of an IMAGE, Put the partition information into the partition_info TABLE.
        #self.InsertImageInformation()

        # print partition_list
        print(self._partition_list)

        # # After analyzing of filesystem, Put the block and file information into the block_info and file_info TABLE.
        #self.InsertFileInformation()

        # create process
        engine = process_engine.ProcessEngine()

        # determine operating system
        self._Preprocess(engine)


        # set modules
        engine.SetProcessModules(module_filter_expression=configuration.module_filter_expression)

        # parse Artifacts
        engine.Process(configuration)


        # # set advanced modules
        engine.SetProcessAdvancedModules(advanced_module_filter_expression=configuration.advanced_module_filter_expression)
        #
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

            #self._output_writer.Write(data)
    def _GetModuleData(self):
        """Retrieves the version vand various module information


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