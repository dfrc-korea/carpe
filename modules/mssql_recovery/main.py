import sys

from .Parser.mssql import MSSQL
from .Parser.mssql import MSSQLRecovery


def main(input_path, output_path):
    print('MSSQL Record Recovery Tool (version 1.0)')
    mssql_class = MSSQL()
    mssql_class.open(input_path)
    mssql_class.read(0, 512)
    mssql_recovery = MSSQLRecovery(mssql_class)

    #### Meta data parsing
    mssql_recovery.scanPages(input_path)
    mssql_recovery.getSystemTableColumnInfo()
    if not mssql_recovery.getTableInfo():
        sys.exit()
    mssql_recovery.getColumnInfo()
    mssql_recovery.getKeyColumnInfo()
    mssql_recovery.getPageObjectId()

    #### Recovery
    mssql_recovery.recovery(output_path)

