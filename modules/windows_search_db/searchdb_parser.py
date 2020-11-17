# -*- coding: utf-8 -*-

import pyesedb


class WindowsSearchDBParser:
    def parse(self, database):
        esedb_file = pyesedb.file()
        if isinstance(database, str):
            esedb_file.open(database)
        else:
            esedb_file.open_file_object(database)

        result = dict()

        systemindex_gthr = esedb_file.get_table_by_name('SystemIndex_Gthr')
        systemindex_gthr_result = list()

        ### get column ###
        column_name_list = list()
        num_of_values = systemindex_gthr.records[0].number_of_values
        if num_of_values != 20:
            print("It supports only Windows 10")
            return None
        for value_entry in range(0, num_of_values):
            column_name = systemindex_gthr.records[0].get_column_name(value_entry)
            column_name_list.append(column_name)
        systemindex_gthr_result.append(column_name_list)

        ### get systemindex_gthr data ###
        for record in systemindex_gthr.records:
            value_list = list()
            for value_entry in range(0, record.number_of_values):
                if column_name_list[value_entry] == 'ScopeID' \
                        or column_name_list[value_entry] == 'DocumentID' \
                        or column_name_list[value_entry] == 'SDID' \
                        or column_name_list[value_entry] == 'TransactionFlags' \
                        or column_name_list[value_entry] == 'TransactionExtendedFlags' \
                        or column_name_list[value_entry] == 'CrawlNumberCrawled' \
                        or column_name_list[value_entry] == 'StartAddressIdentifier' \
                        or column_name_list[value_entry] == 'Priority' \
                        or column_name_list[value_entry] == 'AppOwnerId' \
                        or column_name_list[value_entry] == 'RequiredSIDs' \
                        or column_name_list[value_entry] == 'DeletedCount' \
                        or column_name_list[value_entry] == 'RunTime' \
                        or column_name_list[value_entry] == 'FailureUpdateAttempts' \
                        or column_name_list[value_entry] == 'ClientID' \
                        or column_name_list[value_entry] == 'LastRequestedRunTime' \
                        or column_name_list[value_entry] == 'StorageProviderId' \
                        or column_name_list[value_entry] == 'CalculatedPropertyFlags':
                    if record.get_value_data(value_entry) is None:
                        value_data = None
                    else:
                        value_data = record.get_value_data_as_integer(value_entry)
                elif column_name_list[value_entry] == 'LastModified' or column_name_list[value_entry] == 'UserData':
                    if record.get_value_data(value_entry) is None:
                        value_data = None
                    else:
                        value_data = record.get_value_data(value_entry)
                elif column_name_list[value_entry] == 'FileName':
                    if record.get_value_data(value_entry) is None:
                        value_data = None
                    else:
                        value_data = record.get_value_data_as_string(value_entry)
                value_list.append(value_data)
            systemindex_gthr_result.append(value_list)
        result['SystemIndex_Gthr'] = systemindex_gthr_result

        systemindex_gthrpth = esedb_file.get_table_by_name('SystemIndex_GthrPth')
        systemindex_gthrpth_result = list()

        ### get column ###
        column_name_list = list()
        for value_entry in range(0, systemindex_gthrpth.records[0].number_of_values):
            column_name = systemindex_gthrpth.records[0].get_column_name(value_entry)
            column_name_list.append(column_name)
        systemindex_gthrpth_result.append(column_name_list)

        ### get systemindex_gthrpth data ###
        for record in systemindex_gthrpth.records:
            value_list = list()
            for value_entry in range(0, record.number_of_values):
                if column_name_list[value_entry] == 'Scope' or column_name_list[value_entry] == 'Parent':
                    if record.get_value_data(value_entry) is None:
                        value_data = None
                    else:
                        value_data = record.get_value_data_as_integer(value_entry)
                elif column_name_list[value_entry] == 'Name':
                    if record.get_value_data(value_entry) is None:
                        value_data = None
                    else:
                        value_data = record.get_value_data_as_string(value_entry)
                value_list.append(value_data)
            systemindex_gthrpth_result.append(value_list)
        result['SystemIndex_GthrPth'] = systemindex_gthrpth_result

        esedb_file.close()
        return result


def main(database=None):
    parser = WindowsSearchDBParser()
    if parser is None:
        return None
    result = parser.parse(database=database)
    return result
