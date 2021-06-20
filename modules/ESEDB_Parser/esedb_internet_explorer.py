# -*- coding: utf-8 -*-

from . import esedb_parser
from . import logger

class ESEDBInternetExplorerParser(esedb_parser.ESEDBParser):
    """ESD database - Internet Explorer Parser."""

    NAME = "esedb_internet_explorer"
    DESCRIPTION = 'esedb - internet explorer parser'

    REQUIRED_TABLES = {
        'Containers': 'ParseContainersTable'
    }

    _CONTAINER_TABLE_VALUE_MAPPINGS = {
        'RequestHeaders': '_ConvertHeadersValues',
        'ResponseHeaders': '_ConvertHeadersValues'}

    _SUPPORTED_CONTAINER_NAMES = frozenset([
        'Content', 'Cookies', 'History', 'iedownload'])

    _IGNORED_CONTAINER_NAMES = frozenset([
      'MicrosoftEdge_DNTException', 'MicrosoftEdge_EmieSiteList',
      'MicrosoftEdge_EmieUserList'])

    _SUPPORTED_CONTAINER_NAMES = frozenset([
        'Content', 'Cookies', 'History', 'iedownload'])

    def __init__(self):
        super(ESEDBInternetExplorerParser, self).__init__()
        self._history_schema = None
        self._history_records = []
        self._content_schema = None
        self._content_records = []
        self._cookies_schema = None
        self._cookies_records = []
        self._download_schema = None
        self._download_records = []

    @property
    def GetContentSchema(self):
        """tuple[Content]: content schema."""
        return self._content_schema

    @property
    def GetContentRecords(self):
        """list[Content]: content records."""
        return self._content_records

    @property
    def GetHistorySchema(self):
        """list[History]: history schema."""
        return self._history_schema

    @property
    def GetHistoryRecords(self):
        """list[History]: history records."""
        return self._history_records

    @property
    def GetCookiesSchema(self):
        """tuple[Cookies]: cookies schema."""
        return self._cookies_schema

    @property
    def GetCookiesRecords(self):
        """list[Cookies]: cookies records."""
        return self._cookies_records

    @property
    def GetDownloadSchema(self):
        """tuple[Download]: download schema."""
        return self._download_schema

    @property
    def GetDownloadRecords(self):
        """list[Download]: download records."""
        return self._download_records

    def _ParseContainerTable(self, table, container_name):
        """Parses a Container_# table.

        Args:
          table (pyesedb.table): table.
          container_name (str): container name, which indicates the table type.

        Raises:
          ValueError: if the table value is missing.
        """
        if table is None:
            raise ValueError('Missing table value.')

        for record_index, esedb_record in enumerate(table.records):

            if container_name == 'Content':
                value_mappings = self._CONTAINER_TABLE_VALUE_MAPPINGS
            else:
                value_mappings = None

            try:
                record_values = self._GetRecordValues(
                    table.name, esedb_record, value_mappings=value_mappings)

            except UnicodeDecodeError:
                logger.error((
                    'Unable to retrieve record values from record: {0:d} '
                    'in table: {1:s}').format(record_index, table.name))
                continue

            if container_name == 'Content':
                self._content_schema = tuple(record_values.keys())
                self._content_records.append(tuple(record_values.values()))

            elif container_name == 'History':
                self._history_schema = tuple(record_values.keys())
                self._history_records.append(tuple(record_values.values()))
                # if record_values.get('EntryId') == 8 and record_values.get('ContainerId') == 18:
                #     print(record_values)

            elif container_name == 'Cookies':
                self._cookies_schema = tuple(record_values.keys())
                self._cookies_records.append(tuple(record_values.values()))

            elif container_name == 'iedownload':
                self._download_schema = tuple(record_values.keys())
                self._download_records.append(tuple(record_values.values()))

    def ParseContainersTable(self, database=None, table=None, **unused_kwargs):
        """Parses a Containers table.

        Args:
            database (Optional[pyesedb.file]): ESE database.
            table (Optional[pyesedb.table]): table.

        Raises:
            ValueError: if the database or table value is  missing.
        """
        # print("-[ESEDB_Parser]: Internet Explorer Parser Started.")

        if database is None:
            raise ValueError('Missing database value.')

        if table is None:
            raise ValueError('Missing table value.')

        for esedb_record in table.records:
            record_values = self._GetRecordValues(table.name, esedb_record)

            container_identifier = record_values.get('ContainerId', None)
            container_name = record_values.get('Name', None)

            if not container_identifier or not container_name:
                continue

            if container_name in self._IGNORED_CONTAINER_NAMES:
                logger.error(
                    'Skipped container (ContainerId: {0:d}, Name: {1:s})'.format(
                        container_identifier, container_name))
                continue

            table_name = 'Container_{0:d}'.format(container_identifier)
            esedb_table = database.get_table_by_name(table_name)
            if not esedb_table:
                logger.error('Missing table: {0:s}'.format(table_name))
                continue
            self._ParseContainerTable(esedb_table, container_name)


esedb_parser.ESEDBParser.RegisterParser(ESEDBInternetExplorerParser)