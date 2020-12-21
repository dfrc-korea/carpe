# -*- coding: utf-8 -*-

import pyesedb

from . import logger

class ESEDBParser(object):
    """ESE database Parser Interface."""

    NAME = 'esedb_connector'
    DESCRIPTION = 'The ESE database parser.'

    _esedb_parser_classes = {}

    BINARY_DATA_COLUMN_TYPES = frozenset([
        pyesedb.column_types.BINARY_DATA,
        pyesedb.column_types.LARGE_BINARY_DATA])

    FLOATING_POINT_COLUMN_TYPES = frozenset([
        pyesedb.column_types.FLOAT_32BIT,
        pyesedb.column_types.DOUBLE_64BIT])

    INTEGER_COLUMN_TYPES = frozenset([
        pyesedb.column_types.CURRENCY,
        pyesedb.column_types.DATE_TIME,
        pyesedb.column_types.INTEGER_8BIT_UNSIGNED,
        pyesedb.column_types.INTEGER_16BIT_SIGNED,
        pyesedb.column_types.INTEGER_16BIT_UNSIGNED,
        pyesedb.column_types.INTEGER_32BIT_SIGNED,
        pyesedb.column_types.INTEGER_32BIT_UNSIGNED,
        pyesedb.column_types.INTEGER_64BIT_SIGNED])

    STRING_COLUMN_TYPES = frozenset([
        pyesedb.column_types.TEXT,
        pyesedb.column_types.LARGE_TEXT])

    REQUIRED_TABLES = {}
    OPTIONAL_TABLES = {}

    def __init__(self):
        super(ESEDBParser, self).__init__()
        self._tables = {}
        self._tables.update(self.REQUIRED_TABLES)
        self._tables.update(self.OPTIONAL_TABLES)

    @property
    def required_tables(self):
        """set[str]: required table names."""
        return frozenset(self.REQUIRED_TABLES.keys())

    @classmethod
    def RegisterParser(cls, esedb_parser_class):
        """Registers a esedb parser class.

        The esedb parser classes are identified based on their lower case name.

        Args:
          esedb_parser_class (type): esedb parser class.

        Raises:
          KeyError: if parser class is already set for the corresponding name.
        """
        esedb_parser_name = esedb_parser_class.NAME.lower()
        if esedb_parser_name in cls._esedb_parser_classes:
          raise KeyError('ESE database parser class already set for name: {0:s}.'.format(
              esedb_parser_class.NAME))

        cls._esedb_parser_classes[esedb_parser_name] = esedb_parser_class

    @classmethod
    def GetESEDBParserObjects(cls):
        includes = {}
        excludes = {}

        esedb_parser_objects = {}
        for esedb_parser_name, esedb_parser_class in iter(cls._esedb_parser_classes.items()):

            if not includes and esedb_parser_name in excludes:
                continue

            if includes and esedb_parser_name not in includes:
                continue

            esedb_parser_object = esedb_parser_class()
            esedb_parser_objects[esedb_parser_name] = esedb_parser_object

        return esedb_parser_objects

    @classmethod
    def GetTableNames(self, database):
        """Retrieves the table names in a database.

        Args:
          database (pyesedb.file): ESE database.

        Returns:
          list[str]: table names.
        """
        table_names = []
        for esedb_table in database.tables:
            table_names.append(esedb_table.name)

        return table_names

    def _GetRecordValue(self, record, value_entry):
        """Retrieves a specific value from the record.

        Args:
          record (pyesedb.record): ESE record.
          value_entry (int): value entry.

        Returns:
          object: value.

        Raises:
          ValueError: if the value is not supported.
        """
        column_type = record.get_column_type(value_entry)
        long_value = None

        if record.is_long_value(value_entry):
            try:
                long_value = record.get_value_data_as_long_value(value_entry)
            except:
                return record.get_value_data(value_entry)

        if record.is_multi_value(value_entry):
            # TODO: implement
            raise ValueError('Multi value support not implemented yet.')

        if column_type == pyesedb.column_types.NULL:
            return None

        if column_type == pyesedb.column_types.BOOLEAN:
            # TODO: implement
            raise ValueError('Boolean value support not implemented yet.')

        if column_type in self.INTEGER_COLUMN_TYPES:
            if long_value:
                raise ValueError('Long integer value not supported.')
            return record.get_value_data_as_integer(value_entry)

        if column_type in self.FLOATING_POINT_COLUMN_TYPES:
            if long_value:
                raise ValueError('Long floating point value not supported.')
            return record.get_value_data_as_floating_point(value_entry)

        if column_type in self.STRING_COLUMN_TYPES:
            if long_value:
                return long_value.get_data_as_string()
            return record.get_value_data_as_string(value_entry)

        if column_type == pyesedb.column_types.GUID:
            # TODO: implement
            raise ValueError('GUID value support not implemented yet.')

        if long_value:
            return long_value.get_data()
        return record.get_value_data(value_entry)

    def _GetRecordValues(
            self, table_name, record, value_mappings=None):
        """Retrieves the values from the record.

        Args:
            table_name (str): name of the table.
            record (pyesedb.record): ESE record.
            value_mappings (Optional[dict[str, str]): value mappings, which map
            the column name to a callback method.

        Returns:
            dict[str,object]: values per column name.
        """
        record_values = {}

        for value_entry in range(0, record.number_of_values):

            column_name = record.get_column_name(value_entry)
            if column_name in record_values:
                logger.warning(
                    '[{0:s}] duplicate column: {1:s} in table: {2:s}'.format(
                        self.NAME, column_name, table_name))
                continue

            value_callback = None
            if value_mappings and column_name in value_mappings:
                value_callback_method = value_mappings.get(column_name)
                if value_callback_method:
                    value_callback = getattr(self, value_callback_method, None)
                    if value_callback is None:
                        logger.warning((
                            '[{0:s}] missing value callback method: {1:s} for column: '
                            '{2:s} in table: {3:s}').format(
                            self.NAME, value_callback_method, column_name, table_name))

            if value_callback:
                try:
                    value_data = record.get_value_data(value_entry)
                    value = value_callback(value_data)

                except Exception as exception:  # pylint: disable=broad-except
                    logger.error(exception)
                    value = None

            else:
                try:
                    value = self._GetRecordValue(record, value_entry)
                except ValueError as exception:
                    value = None

            record_values[column_name] = value

        return record_values

    def GetEntries(self, database=None, **kwargs):
        """Extracts event objects from the database.

        Args:
            database (Optional[pyesedb.file]): ESE database.

        Raises:
            ValueError: If the database attribute is not valid.
        """
        if database is None:
            raise ValueError('Invalid database.')

        for table_name, callback_method in sorted(self._tables.items()):

            if not callback_method:
                continue

            callback = getattr(self, callback_method, None)
            if callback is None:
                logger.warning(
                    '[{0:s}] missing callback method: {1:s} for table: {2:s}'.format(
                        self.NAME, callback_method, table_name))
                continue

            esedb_table = database.get_table_by_name(table_name)
            if not esedb_table:
                if table_name not in self.OPTIONAL_TABLES:
                    logger.warning('[{0:s}] missing table: {1:s}'.format(
                        self.NAME, table_name))
                continue

            # The database is passed in case the database contains table names
            # that are assigned dynamically and cannot be defined by
            # the table name-callback mechanism.
            callback(database=database, table=esedb_table, **kwargs)

    def Process(self, database=None, **kwargs):
        """Determines if this is the appropriate parser for the database.

        Args:
            database (Optional[pyesedb.file]): ESE database.

        Raises:
            ValueError: If the database attribute is not valid.
        """
        if database is None:
            raise ValueError('Invalid database.')

        # This will raise if unhandled keyword arguments are passed.
        if kwargs:
            raise ValueError('Unused keyword arguments: {0:s}.'.format(
                ', '.join(kwargs.keys())))

        self.GetEntries(database=database, **kwargs)