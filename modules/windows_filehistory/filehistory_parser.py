# -*- coding: utf-8 -*-

import pyesedb

class WindowsFileHistoryParser():
    def parse(self, database):
        esedb_file = pyesedb.file()
        if isinstance(database, str):
            esedb_file.open(database)
        else:
            esedb_file.open_file_object(database)

        result = dict()


        namespace = esedb_file.get_table_by_name('namespace')
        namespace_result = list()

        try:
            ### get column ###
            column_name_list = list()
            for value_entry in range(0, namespace.records[0].number_of_values):
                column_name = namespace.records[0].get_column_name(value_entry)
                column_name_list.append(column_name)
            namespace_result.append(column_name_list)
        except Exception as e:
            pass

        try:
            ### get namespace data ###
            for record in namespace.records:
                value_list = list()
                for value_entry in range(0, record.number_of_values):
                    if record.get_value_data(value_entry) == None:
                        value_data = None
                    else:
                        value_data = record.get_value_data_as_integer(value_entry)
                    value_list.append(value_data)
                namespace_result.append(value_list)
        except Exception as e:
            pass

        result['namespace'] = namespace_result





        file = esedb_file.get_table_by_name('file')
        file_result = list()

        try:
            ### get column ###
            column_name_list = list()
            for value_entry in range(0, file.records[0].number_of_values):
                column_name = file.records[0].get_column_name(value_entry)
                column_name_list.append(column_name)
            file_result.append(column_name_list)
        except Exception as e:
            pass

        try:
            ### get file data ###
            for record in file.records:
                value_list = list()
                for value_entry in range(0, record.number_of_values):
                    if record.get_value_data(value_entry) == None:
                        value_data = None
                    else:
                        value_data = record.get_value_data_as_integer(value_entry)
                    value_list.append(value_data)
                file_result.append(value_list)
        except Exception as e:
            pass
        result['file'] = file_result



        string = esedb_file.get_table_by_name('string')
        string_result = list()
        try:
            ### get column ###
            column_name_list = list()
            for value_entry in range(0, string.records[0].number_of_values):
                column_name = string.records[0].get_column_name(value_entry)
                column_name_list.append(column_name)
            string_result.append(column_name_list)
        except Exception as e:
            pass

        try:
            ### get string data ###
            for record in string.records:
                value_list = list()
                for value_entry in range(0, record.number_of_values):
                    if column_name_list[value_entry] == 'id':
                        if record.get_value_data(value_entry) == None:
                            value_data = None
                        else:
                            value_data = record.get_value_data_as_integer(value_entry)
                    elif column_name_list[value_entry] == 'string':
                        if record.get_value_data(value_entry) == None:
                            value_data = None
                        else:
                            value_data = record.get_value_data_as_string(value_entry)
                    value_list.append(value_data)
                string_result.append(value_list)
        except Exception as e:
            pass
        result['string'] = string_result

        return result

def main(database=None):

    parser = WindowsFileHistoryParser()
    result = parser.parse(database=database)
    return result


