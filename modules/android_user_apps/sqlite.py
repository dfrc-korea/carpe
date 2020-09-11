# -*- coding: utf-8 -*-
"""SQLite parser."""

import os
import tempfile
import sqlite3

from modules import logger

class SQLiteDatabase(object):
    """SQLite database.

    Attributes:
        schema (dict[str, str]): schema as an SQL query per table name,
            for example {'Users': 'CREATE TABLE Users ("id" INTEGER PRIMARY KEY, ...)'}.
    """

    _READ_BUFFER_SIZE = 65536

    SCHEMA_QUERY = (
        'SELECT tbl_name, sql '
        'FROM sqlite_master '
        'WHERE type = "table" AND tbl_name != "xp_proc" '
        'AND tbl_name != "sqlite_sequence"')

    def __init__(self, filename, temporary_directory=None):
        """Initializes the database object.

        Args:
            filename (str): name of the file entry.
            temporary_directory (Optional[str]): path of the directory for temporary files.
        """
        self._database = None
        self._filename = filename
        self._is_open = False
        self._temp_db_file_path = ''
        self._temporary_directory = temporary_directory
        self._temp_wal_file_path = ''

        self.schema = {}
        self.columns_per_tables = {}

    @property
    def tables(self):
        """list[str]: names of all the tables."""
        if self._is_open:
            return self.schema.keys()

        return []

    def _CopyFileObjectToTemporaryFile(self, file_object, temporary_file):
        """Copies the contents of the file-like object to a temporary file.

        Args:
              file_object (dfvfs.FileIO): file-like object.
              temporary_file (file): temporary file.
        """
        file_object.seek(0, os.SEEK_SET)
        data = file_object.read(self._READ_BUFFER_SIZE)
        while data:
            temporary_file.write(data)
            data = file_object.read(self._READ_BUFFER_SIZE)

    def Close(self):
        """Closes the database connection and cleans up the temporary file."""
        self.schema = {}

        if self._is_open:
            self._database.close()
        self._database = None

        if os.path.exists(self._temp_db_file_path):
            try:
                os.remove(self._temp_db_file_path)
            except (OSError, IOError) as exception:
                logger.warning((
                    'Unable to remove temporary copy: {0:s} of SQLite database: '
                    '{1:s} with error: {2!s}').format(
                    self._temp_db_file_path, self._filename, exception))

        self._temp_db_file_path = ''

        if os.path.exists(self._temp_wal_file_path):
            try:
                os.remove(self._temp_wal_file_path)
            except (OSError, IOError) as exception:
                logger.warning((
                    'Unable to remove temporary copy: {0:s} of SQLite database: '
                    '{1:s} with error: {2!s}').format(
                    self._temp_wal_file_path, self._filename, exception))

        self._temp_wal_file_path = ''

        self._is_open = False

    def Open(self, file_object, wal_file_object=None):
        """Opens a SQLite database file.

        Since pysqlite cannot read directly from a file-like object a temporary
        copy of the file is made. After creating a copy the database file this
        function sets up a connection with the database and determines the names
        of the tables.

        Args:
            file_object (dfvfs.FileIO): file-like object.
            wal_file_object (Optional[dfvfs.FileIO]): file-like object for the
            Write-Ahead Log (WAL) file.

        Raises:
            IOError: if the file-like object cannot be read.
            OSError: if the file-like object cannot be read.
            sqlite3.DatabaseError: if the database cannot be parsed.
            ValueError: if the file-like object is missing.
        """
        if not file_object:
            raise ValueError('Missing file object.')

        # TODO: Current design copies the entire file into a buffer
        # that is parsed by each SQLite parser. This is not very efficient,
        # especially when many SQLite parsers are ran against a relatively
        # large SQLite database. This temporary file that is created should
        # be usable by all SQLite parsers so the file should only be read
        # once in memory and then deleted when all SQLite parsers have completed.

        # TODO: Change this into a proper implementation using APSW
        # and virtual filesystems when that will be available.
        # Info: http://apidoc.apsw.googlecode.com/hg/vfs.html#vfs and
        # http://apidoc.apsw.googlecode.com/hg/example.html#example-vfs
        # Until then, just copy the file into a tempfile and parse it.
        temporary_file = tempfile.NamedTemporaryFile(
            delete=False, dir=self._temporary_directory)

        try:
            self._CopyFileObjectToTemporaryFile(file_object, temporary_file)
            self._temp_db_file_path = temporary_file.name

        except IOError:
            os.remove(temporary_file.name)
            raise

        finally:
            temporary_file.close()

        if wal_file_object:
            # Create WAL file using same filename so it is available for
            # sqlite3.connect()
            temporary_filename = '{0:s}-wal'.format(self._temp_db_file_path)
            temporary_file = open(temporary_filename, 'wb')
            try:
                self._CopyFileObjectToTemporaryFile(wal_file_object, temporary_file)
                self._temp_wal_file_path = temporary_filename

            except IOError:
                os.remove(temporary_filename)
                raise

            finally:
                temporary_file.close()

        self._database = sqlite3.connect(self._temp_db_file_path)
        try:
            self._database.row_factory = sqlite3.Row
            cursor = self._database.cursor()

            sql_results = cursor.execute(self.SCHEMA_QUERY)

            self.schema = {
                table_name: ' '.join(query.split())
                for table_name, query in sql_results}

            for table_name in self.schema.keys():
                self.columns_per_table.setdefault(table_name, [])
                pragma_results = cursor.execute('PRAGMA table_info({0:s})'
                                                .format(table_name))

                for pragma_result in pragma_results:
                    self.columns_per_table[table_name].append(pragma_result['name'])

        except sqlite3.DatabaseError as exception:
            self._database.close()
            self._database = None

            os.remove(self._temp_db_file_path)
            self._temp_db_file_path = ''
            if self._temp_wal_file_path:
                os.remove(self._temp_wal_file_path)
                self._temp_wal_file_path = ''

            logger.debug(
                'Unable to parse SQLite database: {0:s} with error: {1!s}'.format(
                    self._filename, exception))
            raise

        self._is_open = True

    def Query(self, query):
        """Queries the database.

        Args:
            query (str): SQL query.

        Returns:
            sqlite3.Cursor: results.

        Raises:
            sqlite3.DatabaseError: if querying the database fails.
        """
        cursor = self._database.cursor()
        cursor.execute(query)
        return cursor

class SQLiteParser(object):
    """Parses SQLite database files."""

    def Parse(self, filename, file_object, configuration):
        """Parses a SQLite database file entry.

        Args:
            filename (str): name of the file.
            file_object (dfvfs.FileIO): file-like object.
            configuration: configuration values.

        Raises:
            UnableToParseFile: when the file cannot be parsed.
        """
        temporary_directory_path = configuration.root_tmp_path + os.sep + 'and_smsmms'
        database = SQLiteDatabase(
            filename, temporary_directory=temporary_directory_path)

        try:
            database.Open(file_object)

        except (IOError, ValueError, sqlite3.DatabaseError) as exception:
            logger.warning('unable to open SQLite database with error: {0!s}'.format(exception))
            file_object.close()
            return

        database_wal, wal_file_entry = self._OpenDatabaseWithWAL(

        )