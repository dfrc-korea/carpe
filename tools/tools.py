# -*- coding: utf-8 -*-

import sys
import codecs
import locale
import abc
import datetime

from utility import errors
from tools import logger


class CLITool(object):
    _PREFERRED_ENCODING = 'utf-8'

    NAME = ''
    VERSION = ''

    def __init__(self, input_reader=None, output_writer=None):
        super(CLITool, self).__init__()

        preferred_encoding = locale.getpreferredencoding()
        if not input_reader:
            input_reader = StdinInputReader(encoding=preferred_encoding)
        if not output_writer:
            output_writer = StdoutOutputWriter(encoding=preferred_encoding)

        self._debug_mode = False
        self._quiet_mode = False
        self._input_reader = input_reader
        self._output_writer = output_writer
        self._log_file = None

        # carpe_extract
        self.par_num = None
        self.extract_path = None

        # carpe_carve
        self.sector_size = None
        self.cluster_size = None

        self.preferred_encoding = preferred_encoding
        self.show_troubleshooting = False

    def GetVersionInformation(self):
        return '{0:s} v{1:s}'.format(self.NAME, self.VERSION)

    def AddBasicOptions(self, argument_group):
        version_string = self.GetVersionInformation()

        argument_group.add_argument(
            '-h', '--help', action='help',
            help='Show this help message and exit.')

        argument_group.add_argument(
            '--troubles', dest='show_troubleshooting', action='store_true',
            default=False, help='Show troubleshooting information.')

        argument_group.add_argument(
            '-V', '--version', dest='version', action='version',
            version=version_string, help='Show the version information.')

    def AddInformationalOptions(self, argument_group):
        argument_group.add_argument(
            '-d', '--debug', dest='debug', action='store_true', default=False,
            help='Enable debug output.')

        argument_group.add_argument(
            '-q', '--quiet', dest='quiet', action='store_true', default=False,
            help='Disable informational output.')

        argument_group.add_argument(
            '--info', dest='show_info', action='store_true', default=False,
            help='Print out information about supported plugins and parsers.')

        argument_group.add_argument(
            '--no_dependencies_check', '--no-dependencies-check',
            dest='dependencies_check', action='store_false', default=True,
            help='Disable the dependencies check.')

    def _ParseInformationalOptions(self, options):
        self._debug_mode = getattr(options, 'debug', False)
        self._quiet_mode = getattr(options, 'quiet', False)

        if self._debug_mode and self._quiet_mode:
            # logger 설정
            pass

    def ParseStringOption(self, options, argument_name, default_value=None):
        argument_value = getattr(options, argument_name, None)
        if not argument_value:
            return default_value

        if isinstance(argument_value, bytes):
            encoding = sys.stdin.encoding

            # Note that sys.stdin.encoding can be None.
            if not encoding:
                encoding = self.preferred_encoding

            try:
                argument_value = codecs.decode(argument_value, encoding)
            except UnicodeDecodeError as exception:
                raise errors.BadConfigOption((
                                                 'Unable to convert option: {0:s} to Unicode with error: '
                                                 '{1!s}.').format(argument_name, exception))

        elif not isinstance(argument_value, str):
            raise errors.BadConfigOption(
                'Unsupported option: {0:s} string type required.'.format(
                    argument_name))

        return argument_value

    def _ParseLogFileOptions(self, options):
        """Parses the log file options.

        Args:
          options (argparse.Namespace): command line arguments.
        """
        self._log_file = self.ParseStringOption(options, 'log_file')
        if not self._log_file:
            local_date_time = datetime.datetime.now()
            self._log_file = (
                '{0:s}-{1:04d}{2:02d}{3:02d}T{4:02d}{5:02d}{6:02d}.log.gz').format(
                self.NAME, local_date_time.year, local_date_time.month,
                local_date_time.day, local_date_time.hour, local_date_time.minute,
                local_date_time.second)

    def parse_extract_options(self, options):
        self.extract_path = getattr(options, 'extract_path', None)
        self.par_num = getattr(options, 'par_num', None)

    def parse_carve_options(self, options):
        self.sector_size = getattr(options, 'sector_size', 512)
        self.cluster_size = getattr(options, 'cluster_size', 2048)

    def ListModules(self):
        # TODO: Modules List 출력해줘야함
        pass

    def ListParsers(self):
        # TODO: Modules List 출력해줘야함
        pass


class CLIInputReader(object):
    """Command line interface input reader interface."""

    def __init__(self, encoding='utf-8'):
        """Initializes an input reader.

    Args:
      encoding (Optional[str]): input encoding.
    """
        super(CLIInputReader, self).__init__()
        self._encoding = encoding

    # pylint: disable=redundant-returns-doc
    @abc.abstractmethod
    def Read(self):
        """Reads a string from the input.

    Returns:
      str: input.
    """


class CLIOutputWriter(object):
    """Command line interface output writer interface."""

    def __init__(self, encoding='utf-8'):
        """Initializes an output writer.

    Args:
      encoding (Optional[str]): output encoding.
    """
        super(CLIOutputWriter, self).__init__()
        self._encoding = encoding

    @abc.abstractmethod
    def Write(self, string):
        """Writes a string to the output.

    Args:
      string (str): output.
    """


class FileObjectInputReader(CLIInputReader):
    """File object command line interface input reader.

  This input reader relies on the file-like object having a readline method.
  """

    def __init__(self, file_object, encoding='utf-8'):
        """Initializes a file object command line interface input reader.

    Args:
      file_object (file): file-like object to read from.
      encoding (Optional[str]): input encoding.
    """
        super(FileObjectInputReader, self).__init__(encoding=encoding)
        self._errors = 'strict'
        self._file_object = file_object

    def Read(self):
        """Reads a string from the input.

    Returns:
      str: input.
    """
        encoded_string = self._file_object.readline()

        if isinstance(encoded_string, str):
            return encoded_string

        try:
            string = codecs.decode(encoded_string, self._encoding, self._errors)
        except UnicodeDecodeError:
            if self._errors == 'strict':
                logger.error(
                    'Unable to properly read input due to encoding error. '
                    'Switching to error tolerant encoding which can result in '
                    'non Basic Latin (C0) characters to be replaced with "?" or '
                    '"\\ufffd".')
                self._errors = 'replace'

            string = codecs.decode(encoded_string, self._encoding, self._errors)

        return string


class StdinInputReader(FileObjectInputReader):
    """Stdin command line interface input reader."""

    def __init__(self, encoding='utf-8'):
        """Initializes an stdin input reader.

    Args:
      encoding (Optional[str]): input encoding.
    """
        super(StdinInputReader, self).__init__(sys.stdin, encoding=encoding)


class FileObjectOutputWriter(CLIOutputWriter):
    """File object command line interface output writer.

  This output writer relies on the file-like object having a write method.
  """

    def __init__(self, file_object, encoding='utf-8'):
        """Initializes a file object command line interface output writer.

    Args:
      file_object (file): file-like object to read from.
      encoding (Optional[str]): output encoding.
    """
        super(FileObjectOutputWriter, self).__init__(encoding=encoding)
        self._errors = 'strict'
        self._file_object = file_object

    def Write(self, string):
        """Writes a string to the output.

    Args:
      string (str): output.
    """
        try:
            # Note that encode() will first convert string into a Unicode string
            # if necessary.
            encoded_string = codecs.encode(string, self._encoding, self._errors)
        except UnicodeEncodeError:
            if self._errors == 'strict':
                logger.error(
                    'Unable to properly write output due to encoding error. '
                    'Switching to error tolerant encoding which can result in '
                    'non Basic Latin (C0) characters to be replaced with "?" or '
                    '"\\ufffd".')
                self._errors = 'replace'

            encoded_string = codecs.encode(string, self._encoding, self._errors)

        self._file_object.write(encoded_string)


class StdoutOutputWriter(FileObjectOutputWriter):
    """Stdout command line interface output writer."""

    def __init__(self, encoding='utf-8'):
        """Initializes a stdout output writer.

    Args:
      encoding (Optional[str]): output encoding.
    """
        super(StdoutOutputWriter, self).__init__(sys.stdout, encoding=encoding)

    def Write(self, string):
        """Writes a string to the output.

    Args:
      string (str): output.
    """
        if sys.version_info[0] < 3:
            super(StdoutOutputWriter, self).Write(string)
        else:
            # sys.stdout.write() on Python 3 by default will error if string is
            # of type bytes.
            sys.stdout.write(string)
