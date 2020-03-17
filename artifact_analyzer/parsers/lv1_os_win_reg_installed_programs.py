# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import os, sys, re
from datetime import datetime

sys.path.append(os.path.join(os.path.abspath(os.path.dirname(__file__)), "parsers"))

import parser_interface
from utility import carpe_db

class Program_Information:
    def __init__(self):
        self.par_id = ''
        self.case_id = ''
        self.evd_id = ''
        self.program_name = ''
        self.company = ''
        self.created_date = ''
        self.key_last_updated_time = ''
        self.install_size = ''
        self.version = ''
        self.potential_location = ''

class INSTALLEDPROGRAMS(parser_interface.ParserInterface):
    """
      Installed Programs Parser.
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

                if name == "InstalledPrograms":
                    # TODO : Fix a Chorme Cache plugin -> lack information

                    #Select all installed programs
                    query = r"SELECT description, datetime FROM log2timeline WHERE description like '%CurrentVersion#\\Uninstall#\%' escape '#' and description like '%DisplayName%'"
                    result_query = db.execute_query_mul(query)
                    programs_list = []
                    program_count = 0
                    if len(result_query) < 1:
                        break
                    else:
                        for result_data in result_query:
                            program_information = Program_Information()
                            try:
                                dataInside = r"DisplayName: \[REG_SZ\] (.*) DisplayVersion:"
                                m = re.search(dataInside, result_data[0].decode('utf-8'))
                                programs_list.append(program_information)
                                programs_list[program_count].program_name = m.group(1)
                                if 'DisplayVersion' in result_data[0].decode('utf-8'):
                                    dataInside = r"DisplayVersion: \[REG_SZ\] ([\d\W]*)"
                                    m = re.search(dataInside, result_data[0].decode('utf-8'))
                                    programs_list[program_count].version = m.group(1)
                                if 'Publisher' in result_data[0].decode('utf-8'):
                                    if 'Microsoft Corporation' in result_data[0].decode('utf-8'):
                                        programs_list[program_count].company = 'Microsoft Corporation'
                                    else:
                                        if 'Readme' in result_data[0].decode('utf-8'):
                                            dataInside = r"Publisher: \[REG_SZ\] (.*) Readme:"
                                            m = re.search(dataInside, result_data[0].decode('utf-8'))
                                            programs_list[program_count].company = m.group(1)
                                        elif 'RegCompany' in result_data[0].decode('utf-8') and 'Readme' not in result_data[0].decode('utf-8'):
                                            dataInside = r"Publisher: \[REG_SZ\] (.*) RegCompany:"
                                            m = re.search(dataInside, result_data[0].decode('utf-8'))
                                            programs_list[program_count].company = m.group(1)
                                        elif 'Readme' not in result_data[0].decode('utf-8') and 'RegCompany' not in result_data[0].decode('utf-8') and 'URLInfoAbout' in result_data[0].decode('utf-8'):
                                            dataInside = r"Publisher: \[REG_SZ\] (.*) URLInfoAbout"
                                            m = re.search(dataInside, result_data[0].decode('utf-8'))
                                            programs_list[program_count].company = m.group(1)
                                        elif 'Readme' not in result_data[0].decode('utf-8') and 'RegCompany' not in result_data[0].decode('utf-8') and 'URLInfoAbout' not in result_data[0].decode('utf-8'):
                                            dataInside = r"Publisher: \[REG_SZ\] (.*) UninstallString"
                                            m = re.search(dataInside, result_data[0].decode('utf-8'))
                                            programs_list[program_count].company = m.group(1)
                                        else:
                                            dataInside = r"Publisher: \[REG_SZ\] ([\w]*)"
                                            m = re.search(dataInside, result_data[0].decode('utf-8'))
                                            programs_list[program_count].company = m.group(1)
                                if 'EstimatedSize' in result_data[0].decode('utf-8'):
                                    dataInside = r"EstimatedSize: \[REG_DWORD_LE\] ([\d]*)"
                                    m = re.search(dataInside, result_data[0].decode('utf-8'))
                                    programs_list[program_count].install_size = m.group(1)
                                if 'InstallDate' in result_data[0].decode('utf-8'):
                                    dataInside = r"InstallDate: \[REG_SZ\] ([\d]*)"
                                    m = re.search(dataInside, result_data[0].decode('utf-8'))
                                    programs_list[program_count].created_date = m.group(1)
                                if 'DisplayIcon' in result_data[0].decode('utf-8'):
                                    if ' UninstallString: [REG_SZ]' in result_data[0].decode('utf-8'):
                                        dataInside = r" UninstallString: \[REG_SZ\] (.*)\\(.*).exe"
                                        m = re.search(dataInside, result_data[0].decode('utf-8'))
                                        if m.group(1)[0] == '"':
                                            programs_list[program_count].potential_location = m.group(1)[1:]
                                        else:
                                            programs_list[program_count].potential_location = m.group(1)
                                    elif ' UninstallString: [REG_EXPAND_SZ]' in result_data[0].decode('utf-8'):
                                        dataInside = r" UninstallString: \[REG_EXPAND_SZ\] (.*)\\(.*).exe"
                                        m = re.search(dataInside, result_data[0].decode('utf-8'))
                                        if m.group(1)[0] == '"':
                                            programs_list[program_count].potential_location = m.group(1)[1:]
                                        else:
                                            programs_list[program_count].potential_location = m.group(1)
                                programs_list[program_count].key_last_updated_time = result_data[1]
                                program_count = program_count + 1
                            except:
                                print("MAX-REG_INSTALLED_PROGRAMS"+result_data[0].decode('utf-8')+"error")

            for program in programs_list:
                insert_values = (par[0], case_id, evd_id,
                                 str(program.program_name), str(program.company), str(program.created_date),
                                 str(program.key_last_updated_time), str(program.install_size), str(program.version),
                                 str(program.potential_location))
                self.InsertQuery(db, insert_values)
        db.close()
        now = datetime.now()
        print('[%s-%s-%s %s:%s:%s] INSTALLED_PROGRAM DONE' % (now.year, now.month, now.day, now.hour, now.minute, now.second))

    def InsertQuery(self, _db, _insert_values_tuple):
        query = self.GetQuery('I', _insert_values_tuple)
        _db.execute_query(query)



