# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import os, sys, re
from datetime import datetime

sys.path.append(os.path.join(os.path.abspath(os.path.dirname(__file__)), "parsers"))

import parser_interface
from utility import carpe_db

class File_Information:
    def __init__(self):
        self.par_id = ''
        self.case_id = ''
        self.evd_id = ''
        self.file_name = ''
        self.key_last_updated_time = ''
        self.file_extension = ''
        self.program_name = ''
        self.program_id = ''
        self.key_id = ''
        self.sha1_hash = ''
        self.os_component_flag = ''
        self.full_path = ''
        self.link_date = ''
        self.product_name = ''
        self.size = ''
        self.version = ''
        self.product_version = ''
        self.long_path_hash = ''
        self.binary_type = ''
        self.pe_file_flag = ''
        self.binary_file_version = ''
        self.binary_product_version = ''
        self.language_code = ''
        self.usn = ''
        self.legacy_flag = 3
        self.volume_guid = ''
        self.publisher = ''
        self.switch_back_context = ''
        self.description = ''
        self.last_modified_time = ''
        self.created_time = ''
        self.last_modified_2_time = ''
        self.pe_header_field_size_of_image = ''
        self.pe_header_hash = ''
        self.pe_header_checksum = ''

class AMCACHEFILEENTRIES(parser_interface.ParserInterface):
    """
      Amcache file entries Parser.
    """

    def __init__(self):
        # Initialize Formatter Interface
        super().__init__()

    def Parse(self, case_id, evd_id, par_list):
        """
          Analyzes records related to usb all device
          in Psort result.
        """
        # Check Table
        if not self.CheckTable():
            self.CreateTable()

        db = carpe_db.Mariadb()
        db.open()

        for par in par_list:
            for art in self.ARTIFACTS:
                name = art['Name']
                desc = art['Desc']
                values = art['Values']

                if name == "AMCACHE_FILE":
                    # TODO : Fix a Chorme Cache plugin -> lack information
                    file_list = []
                    file_count = 0

                    query = r"SELECT description, datetime FROM log2timeline WHERE description like '%Root#\\InventoryApplicationFile#\\%' escape '#' or description like '%Root#\\InventoryApplication#\\%' escape '#' or description like '%Root#\\File#\\%' escape '#' or description like '%Root#\\Programs#\\%' escape '#'"
                    result_query = db.execute_query_mul(query)
                    try:
                        for result_data in result_query:
                            # Current
                            result_data_sep = result_data[0].decode('utf-8').replace(r"|`", " ")
                            if 'Root\\InventoryApplicationFile\\' in result_data_sep and 'empty' not in result_data_sep:
                                file_information = File_Information()
                                file_list.append(file_information)
                                file_list[file_count].key_last_updated_time = result_data[1]
                                file_list[file_count].legacy_flag = 0
                                if 'BinFileVersion' in result_data_sep:
                                    dataInside = r"\[\\Root\\InventoryApplicationFile\\(.*)\] BinFileVersion: \[REG_SZ\] (.*) BinProductVersion: \[REG_SZ\] (.*) BinaryType: \[REG_SZ\] (.*) FileId: \[REG_SZ\] (.*) IsOsComponent:"
                                    m = re.search(dataInside, result_data_sep)
                                    file_list[file_count].key_id = m.group(1)
                                    file_list[file_count].binary_file_version = m.group(2)
                                    file_list[file_count].binary_product_version = m.group(3)
                                    file_list[file_count].binary_type = m.group(4)
                                    file_list[file_count].sha1_hash = m.group(5)
                                    if 'IsOsComponent' in result_data_sep:
                                        dataInside = r" IsOsComponent: \[REG_DWORD_LE\] ([\d])"
                                        m = re.search(dataInside, result_data_sep)
                                        if m.group(1) == '0':
                                            file_list[file_count].os_component_flag = 'False'
                                        else:
                                            file_list[file_count].os_component_flag = 'True'
                                    if 'IsPeFile' in result_data_sep:
                                        dataInside = r" IsPeFile: \[REG_DWORD_LE\] ([\d])"
                                        m = re.search(dataInside, result_data_sep)
                                        if m.group(1) == '0':
                                            file_list[file_count].pe_file_flag = 'False'
                                        else:
                                            file_list[file_count].pe_file_flag = 'True'
                                    if 'Language' in result_data_sep:
                                        dataInside = r" Language: \[REG_DWORD_LE\] ([\d]*)"
                                        m = re.search(dataInside, result_data_sep)
                                        file_list[file_count].language_code = m.group(1)
                                    if 'LinkDate' in result_data_sep:
                                        dataInside = r" LinkDate: \[REG_SZ\] (.*) LongPathHash:"
                                        m = re.search(dataInside, result_data_sep)
                                        file_list[file_count].link_date = m.group(1)
                                    if 'LongPathHash' in result_data_sep:
                                        dataInside = r" LongPathHash: \[REG_SZ\] (.*) LowerCaseLongPath:"
                                        m = re.search(dataInside, result_data_sep)
                                        file_list[file_count].long_path_hash = m.group(1)
                                    if 'LowerCaseLongPath' in result_data_sep:
                                        dataInside = r" LowerCaseLongPath: \[REG_SZ\] (.*)\.(.*) Name:"
                                        m = re.search(dataInside, result_data_sep)
                                        file_list[file_count].long_path_hash = m.group(1)
                                        file_list[file_count].full_path = m.group(1) + '.' + m.group(2)
                                        file_list[file_count].file_extension = m.group(2)
                                    if 'ProductName' in result_data_sep:
                                        dataInside = r" ProductName: \[REG_SZ\] (.*) ProductVersion:"
                                        m = re.search(dataInside, result_data_sep)
                                        file_list[file_count].product_name = m.group(1)
                                    if 'ProductVersion' in result_data_sep:
                                        dataInside = r" ProductVersion: \[REG_SZ\] (.*) ProgramId:"
                                        m = re.search(dataInside, result_data_sep)
                                        file_list[file_count].product_version = m.group(1)
                                    if 'ProgramId' in result_data_sep:
                                        dataInside = r" ProgramId: \[REG_SZ\] (.*) Publisher:"
                                        m = re.search(dataInside, result_data_sep)
                                        file_list[file_count].program_id = m.group(1)
                                    if 'Publisher' in result_data_sep:
                                        dataInside = r" Publisher: \[REG_SZ\] (.*) Size:"
                                        m = re.search(dataInside, result_data_sep)
                                        file_list[file_count].usn = m.group(1)
                                    if 'Size' in result_data_sep:
                                        dataInside = r" Size: \[REG_QWORD\] (.*) Usn:"
                                        m = re.search(dataInside, result_data_sep)
                                        file_list[file_count].size = m.group(1)
                                    if 'Usn' in result_data_sep:
                                        dataInside = r" Usn: \[REG_QWORD\] (.*) Version:"
                                        m = re.search(dataInside, result_data_sep)
                                        file_list[file_count].usn = m.group(1)
                                    if 'Version' in result_data_sep:
                                        dataInside = r" Version: \[REG_SZ\] (.*)"
                                        m = re.search(dataInside, result_data_sep)
                                        file_list[file_count].version = m.group(1)
                                else:
                                    dataInside = r"\[\\Root\\InventoryApplicationFile\\(.*)\] BinaryType: \[REG_SZ\] (.*) FileId: \[REG_SZ\] (.*) LongPathHash: \[REG_SZ\] (.*) LowerCaseLongPath: \[REG_SZ\] (.*)\.(.*) ProgramId: \[REG_SZ\] (.*) Size: \[REG_SZ\] (.*)"
                                    m = re.search(dataInside, result_data_sep)
                                    file_list[file_count].key_id = m.group(1)
                                    file_list[file_count].binary_type = m.group(2)
                                    file_list[file_count].sha1_hash = m.group(3)
                                    file_list[file_count].long_path_hash = m.group(4)
                                    file_list[file_count].full_path = m.group(5) + '.' + m.group(6)
                                    file_list[file_count].file_extension = m.group(6)
                                    file_list[file_count].program_id = m.group(7)
                                    file_list[file_count].size = m.group(8)

                                for result_data in result_query:
                                    if '\\Root\\InventoryApplication\\' in result_data_sep and file_list[file_count].program_id in result_data_sep:
                                        dataInside = r"Name: \[REG_SZ\] (.*) OSVersionAtInstallTime:"
                                        m = re.search(dataInside, result_data_sep)
                                        file_list[file_count].program_name = m.group(1)
                                        break
                                file_count = file_count + 1

                            # Legaxy
                            if 'Root\\File\\' in result_data_sep and 'empty' not in result_data_sep:
                                try:
                                    if ' 0:' in result_data_sep:
                                        file_information = File_Information()
                                        file_list.append(file_information)
                                        file_list[file_count].key_last_updated_time = result_data[1]
                                        file_list[file_count].legacy_flag = 1
                                        dataInside = r"\[\\Root\\File\\(.*)\\(.*) 0: \[REG_SZ\] (.*) 1: \[REG_SZ\] (.*) 10: (.*) 100: \[REG_SZ\] (.*) 101: \[REG_SZ\] (.*) 11: \[REG_QWORD\] (.*) 12: \[REG_QWORD\] (.*) 15: \[REG_SZ\] (.*)\\(.*)\.(.*) 16: (.*) 17: \[REG_QWORD\] (.*) 2: \[REG_SZ\] (.*) 3: \[REG_DWORD_LE\] (.*) 4: \[REG_QWORD\] (.*) 5: \[REG_SZ\] (.*) 6: \[REG_DWORD_LE\] (.*) 7: \[REG_DWORD_LE\] (.*) 8: \[REG_SZ\] (.*) 9: \[REG_DWORD_LE\] (.*) a: (.*) c: \[REG_SZ\] (.*) d: (.*) f: \[REG_DWORD_LE\] (.*)"
                                        m = re.search(dataInside, result_data_sep)
                                        file_list[file_count].volume_guid = m.group(1)
                                        file_list[file_count].key_id = m.group(1)+'\\'+m.group(2)
                                        file_list[file_count].product_name = m.group(3)
                                        file_list[file_count].publisher = m.group(4)
                                        file_list[file_count].program_id = m.group(6)
                                        file_list[file_count].sha1_hash = m.group(7)
                                        file_list[file_count].last_modified_time = m.group(8)
                                        file_list[file_count].created_time = m.group(9)
                                        file_list[file_count].full_path = m.group(10) + '\\' + m.group(11) + '.' + m.group(12)
                                        file_list[file_count].file_name = m.group(11) + '.' + m.group(12)
                                        file_list[file_count].file_extension = '.' + m.group(12)
                                        file_list[file_count].last_modified_2_time = m.group(14)
                                        file_list[file_count].product_version = m.group(15)
                                        file_list[file_count].language_code = m.group(16)
                                        file_list[file_count].switch_back_context = m.group(17)
                                        file_list[file_count].version = m.group(18)
                                        file_list[file_count].size = m.group(19)
                                        file_list[file_count].pe_header_field_size_of_image = m.group(20)
                                        file_list[file_count].pe_header_hash = m.group(21)
                                        file_list[file_count].pe_header_checksum = m.group(22)
                                        file_list[file_count].description = m.group(24)
                                        file_list[file_count].link_date = m.group(26)
                                        file_count = file_count + 1

                                    if ' 0:' not in result_data_sep:
                                        file_information = File_Information()
                                        file_list.append(file_information)
                                        file_list[file_count].key_last_updated_time = result_data[1]
                                        file_list[file_count].legacy_flag = 1
                                        dataInside = r"\[\\Root\\File\\(.*)\\(.*) 100: \[REG_SZ\] (.*) 15: \[REG_SZ\] (.*)\\(.*)\.(.*) 17: \[REG_QWORD\] (.*)"
                                        m = re.search(dataInside, result_data_sep)
                                        file_list[file_count].volume_guid = m.group(1)
                                        file_list[file_count].key_id = m.group(1) + '\\' + m.group(2)
                                        file_list[file_count].program_id = m.group(3)
                                        file_list[file_count].full_path = m.group(4) + '\\' + m.group(5) + '.' + m.group(6)
                                        file_list[file_count].file_name = m.group(5) + '.' + m.group(6)
                                        file_list[file_count].file_extension = '.' + m.group(6)
                                        file_list[file_count].last_modified_2_time = m.group(7)
                                        for result_data in result_query:
                                            if '\\Root\\Programs\\' in result_data_sep and file_list[file_count].program_id in result_data_sep:
                                                dataInside = r" 0: \[REG_SZ\] (.*) 1:"
                                                m = re.search(dataInside, result_data_sep)
                                                file_list[file_count].program_name = m.group(1)
                                                break
                                        file_count = file_count + 1
                                except:
                                    print("MAX-AMCAHCE-error")
                    except:
                        print("MAX-AMCAHCE-error")

                    for file in file_list:
                        insert_values = (par[0], case_id, evd_id,
                                         str(file.file_name), str(file.key_last_updated_time), str(file.file_extension),
                                         str(file.program_name), str(file.program_id), str(file.key_id),
                                         str(file.sha1_hash), str(file.os_component_flag), str(file.full_path),
                                         str(file.link_date), str(file.product_name), str(file.size),
                                         str(file.version), str(file.product_version), str(file.long_path_hash),
                                         str(file.binary_type), str(file.pe_file_flag), str(file.binary_file_version),
                                         str(file.binary_product_version), str(file.language_code), str(file.usn),
                                         str(file.legacy_flag), str(file.volume_guid), str(file.publisher),
                                         str(file.switch_back_context), str(file.description), str(file.last_modified_time),
                                         str(file.created_time), str(file.last_modified_2_time), str(file.pe_header_field_size_of_image),
                                         str(file.pe_header_hash), str(file.pe_header_checksum))
                        self.InsertQuery(db, insert_values)
        db.close()
        now = datetime.now()
        print(
            '[%s-%s-%s %s:%s:%s] AmCache File DONE' % (now.year, now.month, now.day, now.hour, now.minute, now.second))

    def InsertQuery(self, _db, _insert_values_tuple):
        query = self.GetQuery('I', _insert_values_tuple)
        _db.execute_query(query)

