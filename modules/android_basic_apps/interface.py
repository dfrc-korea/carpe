# -*- coding: utf-8 -*-
"""The SQLite parser interface."""

class SQLiteInterface(object):
    """SQLite parser apps."""

    NAME = 'sqlite'
    DESCRIPTION = 'Parser for SQLite database files.'

    # Dictionary of frozensets containing the columns in tables that must be
    # present in the database for the plugin to run.
    # This generally should only include tables/columns that are used in SQL
    # queries by the plugin and not include extraneous tables/columns to better
    # accommodate future application database versions. The exception to this is
    # when extra tables/columns are needed to identify the target database from
    # others with a similar structure.
    REQUIRED_STRUCTURE = {}

    # Queries to be executed.
    # Should be a list of tuples with two entries, SQLCommand and callback
    # function name.
    QUERIES = []

    # Database schemas this plugin was originally designed for.
    # Should be a list of dictionaries with {table_name: SQLCommand} format.
    SCHEMAS = []

    # Value to indicate the schema of the database must match one of the schemas
    # defined by the plugin.
    REQUIRES_SCHEMA_MATCH = False

    def __init__(self):
        """Initializes a SQLite parser apps."""
        super(SQLiteInterface, self).__init__()
        