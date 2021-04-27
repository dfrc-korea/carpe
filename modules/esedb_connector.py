# -*- coding: utf-8 -*-
"""module for ESE database."""

import pyesedb
import datetime
import os

from modules import logger
from modules import manager
from modules import interface
from modules.ESEDB_Parser import esedb_parser
from utility import errors


class ESEDatabaseConnector(interface.ModuleConnector):
    NAME = 'esedb_connector'
    DESCRIPTION = 'Module for ESEDB'
    TABLE_NAME = 'lv1_os_win_esedb'

    _plugin_classes = {}

    def __init__(self):
        super(ESEDatabaseConnector, self).__init__()
        self._configuration = None
        self._time_zone = None

    def _format_timestamp(self, timestamp):
        if timestamp is None:
            return 'N/A'

        return timestamp.strftime('%Y-%m-%dT%H:%M:%S.%fZ')

    def DecodeFiletime(self, timestamp, DoNotRaise=True):
        """Decode the FILETIME timestamp and return the datetime object."""
        try:
            return datetime.datetime(1601, 1, 1) + datetime.timedelta(microseconds=timestamp / 10)
        except Exception:  # Allow a caller to handle an invalid timestamp.
            if not DoNotRaise:
                raise
            return

    def CreateTableWithSchema(self, _cursor, table_name=None, schema=None):
        """Create table with schema.

        Args:
            _cursor (Database object): database connection object.
            table_name (str): table name.
            schema (list): table schema.

        Returns:
            bool: True if database table was created.
        Raises:
            ValueError: If the database attribute is not valid.
        """
        if _cursor is None:
            raise ValueError('Invalid database cursor.')

        if table_name is None:
            raise ValueError('Invalid table name.')

        if schema is None:
            raise ValueError('Invalid schema.')

        query = []
        query.append("CREATE TABLE ")
        query.append(table_name)
        query.append("(")

        for i in range(len(schema)):
            if i != (len(schema) - 1):
                if schema[i] == "RequestHeaders" or schema[i] == "ResponseHeaders" or schema[i] == "ExtraData" \
                        or schema[i] == "Data" or schema[i] == "Data2":
                    query.append("`" + schema[i] + "`" + " BLOB,")
                else:
                    query.append("`" + schema[i] + "`" + " TEXT,")
            else:
                if schema[i] == "RequestHeaders" or schema[i] == "ResponseHeaders" or schema[i] == "ExtraData" \
                        or schema[i] == "Data" or schema[i] == "Data2":
                    query.append("`" + schema[i] + "`" + " BLOB);")
                else:
                    query.append("`" + schema[i] + "`" + " TEXT);")

        query = ''.join(query)

        try:
            _cursor.execute_query(query)
        except Exception as exception:
            logger.error(exception)
            return False

        return True

    def InsertQueryBuilder(self, table_name, schema, data):
        """Build Inserting query.

		Args:
			table_name(str): database table name.
			schema (list): table schema
			data (tuple): data to insert.

		Returns:
			query (str): built query string.
		"""
        TIME_COLUMNS = frozenset(['SyncTime', 'CreationTime', 'ExpiryTime', 'ModifiedTime',
                                  'AccessedTime', 'PostCheckTime'])

        query = f"Insert into {table_name} values ("
        for i in range(0, len(schema)):
            if i < len(data) - 1:
                if isinstance(data[i], bytes):
                    query += "UNHEX('%s')," % data[i].hex()
                elif schema[i] in TIME_COLUMNS and data[i] is not 0:
                    datetime = self._format_timestamp(self.DecodeFiletime(data[i]))
                    if datetime != 'N/A':
                        datetime = self._configuration.apply_time_zone(datetime, self._time_zone)
                    query += "\"" + str(datetime) + "\", "
                else:
                    query += "\"" + str(data[i]) + "\", "
            else:
                if isinstance(data[i], bytes):
                    query += "UNHEX('%s'));" % data[i].hex()
                elif schema[i] in TIME_COLUMNS and data[i] is not 0:
                    datetime = self._format_timestamp(self.DecodeFiletime(data[i]))
                    datetime = self._configuration.apply_time_zone(datetime, self._time_zone)
                    query += "\"" + str(datetime) + "\");"
                else:
                    query += "\"" + str(data[i]) + "\");"

        return query

    def Connect(self, par_id, configuration, source_path_spec, knowledge_base):
        """Connector to connect to ESE database modules.

		Args:
			configuration: configuration values.
			source_path_spec (dfvfs.PathSpec): path specification of the source file.
			knowledge_base (KnowledgeBase): knowledge base.

		"""

        self._configuration = configuration
        self._time_zone = knowledge_base.time_zone

        # Load Schema
        yaml_path = os.path.dirname(os.path.abspath(__file__)) + os.sep + 'schema' + os.sep + 'esedb' \
                    + os.sep + 'lv1_os_win_esedb.yaml'
        if not self.LoadSchemaFromYaml(yaml_path):
            logger.error('cannot load schema from yaml: {0:s}'.format(self.TABLE_NAME))
            return False

        # Search artifact paths
        paths = self._schema['Paths']
        separator = self._schema['Path_Separator']
        environment_variables = knowledge_base.GetEnvironmentVariables()

        find_specs = self.BuildFindSpecs(paths, separator, environment_variables)
        if len(find_specs) < 0:
            return False

        esedb_file = pyesedb.file()
        output_path = configuration.root_tmp_path + os.sep + configuration.case_id + os.sep + \
                                  configuration.evidence_id + os.sep + par_id + os.sep + 'esedb'
        if not os.path.exists(output_path):
            os.mkdir(output_path)
        for spec in find_specs:
            try:
                # file_object = self.LoadTargetFileToMemory(source_path_spec=source_path_spec,
                #                                           configuration=configuration,
                #                                           file_spec=spec)
                self.ExtractTargetFileToPath(
                        source_path_spec=source_path_spec,
                        configuration=configuration,
                        file_spec=spec,
                        output_path=output_path)
                name = self.GetFileNameFromSpec(
                        source_path_spec=source_path_spec,
                        configuration=configuration,
                        file_spec=spec)
                if name is not None:
                    esedb_file.open(output_path+os.sep+name)
            except IOError as exception:
                logger.debug('[{0:s}] unable to open file with error: {0!s}'.format(
                    self.NAME, exception))
                return

            path_spec_generator = self._path_spec_extractor.ExtractPathSpecs(
                [source_path_spec], find_specs=[spec], recurse_file_system=False,
                resolver_context=configuration.resolver_context)

            for path_spec in path_spec_generator:
                edb_path = path_spec.location
            try:
                esedb_parsers = esedb_parser.ESEDBParser.GetESEDBParserObjects()
                table_names = frozenset(esedb_parser.ESEDBParser.GetTableNames(esedb_file))

                for parser in esedb_parsers.values():

                    if not parser.required_tables.issubset(table_names):
                        continue

                    try:
                        parser.Process(database=esedb_file)

                        info = tuple([par_id, configuration.case_id, configuration.evidence_id])
                        # Internet Explorer
                        if 'Containers' in parser.required_tables:
                            # Internet Explorer History
                            if len(parser.GetHistoryRecords) > 0:
                                history_schema = ['par_id', 'case_id', 'evd_id'] + list(parser.GetHistorySchema) \
                                                 + ['source']
                                table_name = 'lv1_os_win_esedb_ie_history'
                                if not configuration.cursor.check_table_exist(table_name):
                                    ret = self.CreateTableWithSchema(configuration.cursor,
                                                                     table_name=table_name,
                                                                     schema=history_schema)
                                    if not ret:
                                        logger.error('cannot create database table name: {0:s}'.format(table_name))
                                        return False

                                for record in parser.GetHistoryRecords:
                                    tmp_record = list(record)
                                    if type(tmp_record) == bytes:
                                        tmp_record[17] = tmp_record[17].replace('"', '""')
                                        tmp_record[17] = tmp_record[17].replace('\'', '\'\'')
                                    result = info + tuple(tmp_record) + tuple([edb_path])
                                    query = self.InsertQueryBuilder(table_name=table_name,
                                                                    schema=history_schema,
                                                                    data=result)
                                    try:
                                        configuration.cursor.execute_query(query)
                                    except Exception as exception:
                                        logger.error('database execution failed: {0!s}'.format(
                                            exception))

                            # Internet Explorer Content
                            if len(parser.GetContentRecords) > 0:
                                content_schema = ['par_id', 'case_id', 'evd_id'] + list(parser.GetContentSchema) \
                                                 + ['source']
                                table_name = 'lv1_os_win_esedb_ie_content'
                                if not configuration.cursor.check_table_exist(table_name):
                                    ret = self.CreateTableWithSchema(configuration.cursor,
                                                                     table_name=table_name,
                                                                     schema=content_schema)
                                    if not ret:
                                        logger.error('cannot create database table name: {0!s}'.format(table_name))
                                        return False

                                for record in parser.GetContentRecords:
                                    tmp_record = list(record)
                                    if isinstance(tmp_record[17], bytes):
                                        tmp_record[17] = "Unknown"
                                    else:
                                        tmp_record[17] = tmp_record[17].replace('"', '""').replace('\'', '\'\'')
                                    result = info + tuple(tmp_record) + tuple([edb_path])
                                    query = self.InsertQueryBuilder(table_name=table_name,
                                                                    schema=content_schema,
                                                                    data=result)
                                    try:
                                        configuration.cursor.execute_query(query)
                                    except Exception as exception:
                                        logger.error('database execution failed: {0!s}'.format(
                                            exception))

                            # Internet Explorer Cookies
                            if len(parser.GetCookiesRecords) > 0:
                                cookie_schema = ['par_id', 'case_id', 'evd_id'] + list(parser.GetCookiesSchema) \
                                                + ['source']
                                table_name = 'lv1_os_win_esedb_ie_cookies'
                                if not configuration.cursor.check_table_exist(table_name):
                                    ret = self.CreateTableWithSchema(configuration.cursor,
                                                                     table_name=table_name,
                                                                     schema=cookie_schema)
                                    if not ret:
                                        logger.error('cannot create database table name: {0!s}'.format(table_name))
                                        return False

                                for record in parser.GetCookiesRecords:
                                    tmp_record = list(record)
                                    result = info + tuple(tmp_record) + tuple([edb_path])
                                    query = self.InsertQueryBuilder(table_name=table_name,
                                                                    schema=cookie_schema,
                                                                    data=result)
                                    try:
                                        configuration.cursor.execute_query(query)
                                    except Exception as exception:
                                        logger.error('database execution failed: {0!s}'.format(
                                            exception))

                            if len(parser.GetDownloadRecords) > 0:
                                download_schema = ['par_id', 'case_id', 'evd_id'] + list(parser.GetDownloadSchema) \
                                                  + ['source']
                                table_name = 'lv1_os_win_esedb_ie_download'
                                if not configuration.cursor.check_table_exist(table_name):
                                    ret = self.CreateTableWithSchema(configuration.cursor,
                                                                     table_name=table_name,
                                                                     schema=download_schema)
                                    if not ret:
                                        logger.error('cannot create database table name: {0!s}'.format(table_name))
                                        return False

                                for record in parser.GetDownloadRecords:
                                    tmp_record = list(record)
                                    tmp_record[17] = tmp_record[17].replace('"', '""')
                                    tmp_record[17] = tmp_record[17].replace('\'', '\'\'')
                                    result = info + tuple(tmp_record) + tuple([edb_path])
                                    query = self.InsertQueryBuilder(table_name=table_name,
                                                                    schema=download_schema,
                                                                    data=result)
                                    try:
                                        configuration.cursor.execute_query(query)
                                    except Exception as exception:
                                        logger.error('database execution failed: {0!s}'.format(
                                            exception))

                    except errors.UnableToParseFile as exception:
                        logger.debug('[{0:s}] unable to parse file with error: {1!s}'.format(
                            self.NAME, exception))

            finally:
                pass
                #esedb_file.close()
                #file_object.close()


manager.ModulesManager.RegisterModule(ESEDatabaseConnector)
