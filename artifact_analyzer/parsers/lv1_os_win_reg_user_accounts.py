# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import os, sys, re
from datetime import datetime

sys.path.append(os.path.join(os.path.abspath(os.path.dirname(__file__)), "parsers"))

import parser_interface
from utility import carpe_db

class User_Information:
    def __init__(self):
        self.par_id = ''
        self.case_id = ''
        self.evd_id = ''
        self.user_name = ''
        self.full_name = ''
        self.type_of_user = ''
        self.account_description = ''
        self.security_identifier = ''
        self.user_group = ''
        self.login_script = ''
        self.profile_path = ''
        self.last_login_time = ''
        self.last_password_change_time = ''
        self.last_incorrect_password_login_time = ''
        self.login_count = ''
        self.account_disabled = ''
        self.password_required = ''
        self.password_hint = ''
        self.lm_hash = ''
        self.ntlm_hash = ''

class USERACCOUNTS(parser_interface.ParserInterface):
    """
      User Accounts Information Parser.
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

        '''
        query = "SELECT par_id FROM partition_info WHERE evd_id='" + evd_id + "';"
        par_list = db.execute_query_mul(query)
        '''

        for par in par_list:
            query = r"SELECT count(*) FROM log2timeline WHERE par_id LIKE '%" + par[0] + "%'"
            if db.execute_query_mul(query)[0][0] != 0:
                for art in self.ARTIFACTS:
                    name = art['Name']
                    desc = art['Desc']
                    values = art['Values']

                    if name == "USERACCOUNTS":
                        # TODO : Fix a Chorme Cache plugin -> lack information
                        user_list = []
                        user_count = 0

                        #Select Default OS
                        query = r"SELECT sourcetype, type, user, description, datetime FROM log2timeline WHERE sourcetype like '%User Account Information%' or description like '%Microsoft#\\Windows NT#\\CurrentVersion#\\ProfileList%' escape '#' and filename not like '%SafeOS%'"
                        result_query = db.execute_query_mul(query)
                        try:
                            for result_data in result_query:
                                result_data_sep = result_data[3].decode('utf-8').replace(r"|`"," ")
                                user_information = User_Information()
                                if 'User Account Information' in str(result_data[0]) and str(result_data[1]) == 'Content Modification Time' and str(result_data[2]) is not None:
                                    user_list.append(user_information)
                                    user_list[user_count].type_of_user = 'Local User'
                                    if 'Comments' in result_data_sep:
                                        dataInside = r"Username: (.*) Comments: (.*) RID: ([\d]*) Login count: ([\d]*)"
                                        m = re.search(dataInside, result_data_sep)
                                        user_list[user_count].user_name = m.group(1)
                                        user_list[user_count].account_description = m.group(2)
                                        user_list[user_count].security_identifier = m.group(3)
                                        user_list[user_count].login_count = m.group(4)
                                        user_count = user_count + 1
                                    else:
                                        if 'Full name' in result_data_sep:
                                            dataInside = r"Username: (.*) Full name: (.*) RID: ([\d]*) Login count: ([\d]*)"
                                            m = re.search(dataInside, result_data_sep)
                                            user_list[user_count].user_name = m.group(1)
                                            user_list[user_count].full_name = m.group(2)
                                            user_list[user_count].security_identifier = m.group(3)
                                            user_list[user_count].login_count = m.group(4)
                                            user_count = user_count + 1
                                        else:
                                            dataInside = r"Username: (.*) RID: ([\d]*) Login count: ([\d]*)"
                                            m = re.search(dataInside, result_data_sep)
                                            user_list[user_count].user_name = m.group(1)
                                            user_list[user_count].security_identifier = m.group(2)
                                            user_list[user_count].login_count = m.group(3)
                                            user_count = user_count + 1

                                if 'S-1-5-18' in result_data_sep:
                                    user_list.append(user_information)
                                    user_list[user_count].security_identifier = 'S-1-5-18'
                                    dataInside = r"ProfileImagePath: \[REG_EXPAND_SZ\] (.*) RefCount:"
                                    m = re.search(dataInside, result_data_sep)
                                    user_list[user_count].profile_path = m.group(1)
                                    user_list[user_count].type_of_user = 'Built-in'
                                    user_count = user_count + 1

                                if 'S-1-5-19' in result_data_sep:
                                    user_list.append(user_information)
                                    user_list[user_count].security_identifier = 'S-1-5-19'
                                    dataInside = r"ProfileImagePath: \[REG_EXPAND_SZ\] (.*) State:"
                                    m = re.search(dataInside, result_data_sep)
                                    user_list[user_count].profile_path = m.group(1)
                                    user_list[user_count].type_of_user = 'Built-in'
                                    user_count = user_count + 1

                                if 'S-1-5-20' in result_data_sep:
                                    user_list.append(user_information)
                                    user_list[user_count].Security_Identifier = 'S-1-5-20'
                                    dataInside = r"ProfileImagePath: \[REG_EXPAND_SZ\] (.*) State:"
                                    m = re.search(dataInside, result_data_sep)
                                    user_list[user_count].profile_path = m.group(1)
                                    user_list[user_count].type_of_user = 'Built-in'
                                    user_count = user_count + 1
                        except:
                            print("MAX-USERACCOUNT-error")

                        for result_data in result_query:
                            if 'Last Login Time' == result_data[1]:
                                for user in user_list:
                                    if result_data[2] == user.user_name:
                                        user.last_login_time = result_data[4]
                            if 'Last Password Reset' == result_data[1]:
                                for user in user_list:
                                    if result_data[2] == user.user_name:
                                        user.last_password_change_time = result_data[4]
                            if 'S-1-5-21' in result_data[3].decode('utf-8'):
                                dataInside = r"ProfileList\\(.*)\] Flags:(.*)ProfileImagePath: \[REG_EXPAND_SZ\] (.*)\\(.*) ProfileLoadTimeHigh:"
                                m = re.search(dataInside, result_data[3].decode('utf-8'))
                                for user in user_list:
                                    if m.group(4) == user.user_name:
                                        user.security_identifier = m.group(1)
                                        user.profile_path = m.group(3)+ "\\" +m.group(4)


                for user in user_list:
                    insert_values = (par[0], case_id, evd_id,
                                     str(user.user_name), str(user.full_name), str(user.type_of_user),
                                     str(user.account_description), str(user.security_identifier), str(user.user_group),
                                     str(user.login_script), str(user.profile_path), str(user.last_login_time),
                                     str(user.last_password_change_time), str(user.last_incorrect_password_login_time), str(user.login_count),
                                     str(user.account_disabled), str(user.password_required), str(user.password_hint),
                                     str(user.lm_hash), str(user.ntlm_hash))
                    self.InsertQuery(db, insert_values)
        db.close()
        now = datetime.now()
        print(
            '[%s-%s-%s %s:%s:%s] USER ACCOUNTS DONE' % (now.year, now.month, now.day, now.hour, now.minute, now.second))

    def InsertQuery(self, _db, _insert_values_tuple):
        query = self.GetQuery('I', _insert_values_tuple)
        _db.execute_query(query)

