# -*- coding: utf-8 -*-
"""module for E-mail."""
import os, json
import configparser
from elasticsearch import Elasticsearch

from modules import manager
from modules import interface
#from modules.app_email.lib.yjSysUtils import *
#from modules.app_email.lib.delphi import *

class EMAILConnector(interface.ModuleConnector):

    NAME = 'email_connector'
    DESCRIPTION = 'Module for E-mail'

    _plugin_classes = {}

    def __init__(self):
        super(EMAILConnector, self).__init__()

    def Connect(self, par_id, configuration, source_path_spec, knowledge_base):

        if configuration.standalone_check:
            this_file_path = os.path.dirname(os.path.abspath(__file__)) + os.sep + 'schema' + os.sep
            # 모든 yaml 파일 리스트
            yaml_list = [this_file_path + 'lv1_app_email.yaml']

            # 모든 테이블 리스트
            table_list = ['lv1_app_email']

            if not self.check_table_from_yaml(configuration, yaml_list, table_list):
                return False

        # extension -> sig_type 변경해야 함

        query = f"SELECT name, parent_path, extension FROM file_info WHERE par_id='{par_id}' and " \
                f"(extension = 'eml' or " \
                f"extension = 'mbox' or " \
                f"extension = 'msg' or " \
                f"extension = 'ost' or " \
                f"extension = 'pst');"

        email_files = configuration.cursor.execute_query_mul(query)

        if type(email_files) == int or len(email_files) == 0:
            # print("There are no email files")
            return False

        if configuration.standalone_check:
            insert_email = list()
        else:
            config = configparser.ConfigParser()
            conf_file = os.path.dirname(
                os.path.dirname(os.path.abspath(__file__))) + os.sep + 'config' + os.sep + 'carpe.conf'
            if not os.path.exists(conf_file):
                raise Exception('%s file does not exist.\n' % conf_file)
            config.read(conf_file)
            _host = config.get('elasticsearch', 'host')
            _port = config.getint('elasticsearch', 'port')
            _index_name = config.get('email', 'index')
            _type_name = config.get('email', 'type')
            es = Elasticsearch(hosts=_host, port=_port)
        path_separator = self.GetPathSeparator(source_path_spec)
        for email in email_files:
            email_path = email[1][email[1].find(path_separator):] + path_separator + email[0]  # document full path
            fileExt = email[2]
            fileName = email[0]
            """
            if fileExt == "msg":
                file_object = self.LoadTargetFileToMemory(
                    source_path_spec=source_path_spec,
                    configuration=configuration,
                    file_path=email_path)

                from modules.app_email.EmailBoxClass import EmailBox

                EmailBox.fileName = configuration.root_tmp_path + os.sep + configuration.case_id + os.path.sep + \
                                configuration.evidence_id + os.path.sep + par_id + os.path.sep+ fileName
                EmailBox.fp = file_object
                EmailBox.appDir = os.path.dirname(os.path.realpath(__file__)) + os.path.sep + 'app_email'
                EmailBox.exportDir = configuration.tmp_path + os.path.sep + par_id + os.path.sep + "email" + os.path.sep
                try:
                    result = EmailBox.parse(fileExt)
                    file_object.close()
                except Exception as e:
                    print(EmailBox.fileName+" "+str(e))
                    file_object.close()
            elif fileExt == "mbox" or fileExt == "pst" or fileExt == "eml":
                self.ExtractTargetFileToPath(
                    source_path_spec=source_path_spec,
                    configuration=configuration,
                    file_path=email_path,
                    output_path=configuration.root_tmp_path + os.sep + configuration.case_id + os.sep +
                                configuration.evidence_id + os.sep + par_id)

                from modules.app_email.EmailBoxClass import EmailBox


                EmailBox.appDir = os.path.dirname(os.path.realpath(__file__)) + os.path.sep + 'app_email'
                EmailBox.exportDir = configuration.tmp_path + os.path.sep + par_id + os.path.sep + "email" + os.path.sep
                EmailBox.fileName = configuration.root_tmp_path + os.sep + configuration.case_id + os.path.sep + \
                                configuration.evidence_id + os.path.sep + par_id + os.path.sep+ fileName
                try:
                    result = EmailBox.pars\\e(fileExt)
                except Exception as e:
                    continue


                os.remove(EmailBox.fileName)
            """

            self.ExtractTargetFileToPath(
                source_path_spec=source_path_spec,
                configuration=configuration,
                file_path=email_path,
                output_path=configuration.root_tmp_path + os.sep + configuration.case_id + os.sep +
                            configuration.evidence_id + os.sep + par_id)

            from modules.app_email.EmailBoxClass import EmailBox

            EmailBox.appDir = os.path.dirname(os.path.realpath(__file__)) + os.path.sep + 'app_email'
            EmailBox.exportDir = configuration.tmp_path + os.path.sep + par_id + os.path.sep + "email" + os.path.sep
            EmailBox.fileName = configuration.root_tmp_path + os.sep + configuration.case_id + os.path.sep + \
                                configuration.evidence_id + os.path.sep + par_id + os.path.sep + fileName
            try:
                # print('\n' + EmailBox.fileName)
                result = EmailBox.parse(fileExt)
            except Exception as e:
                continue

            os.remove(EmailBox.fileName)

            if not result:
                continue

            if configuration.standalone_check:
                if fileExt == "mbox" or fileExt == "pst" or fileExt == "ost":
                    for r in result:
                        received_lines = ''
                        header = r['EmailMessageObject']['Header']

                        try:
                            for received_line in header['Received_Lines']:
                                received_lines += json.dumps(received_line) + ','
                            if received_lines[-1] == ',':
                                received_lines = received_lines[:-1]
                        except Exception:
                            pass

                        to = ''
                        try:
                            for tmp_to in header['To']:
                                to += tmp_to + ','
                            if to[-1] == ',':
                                to = to[:-1]
                        except Exception:
                            continue

                        if to == '':
                            continue

                        cc = ''
                        try:
                            for tmp_cc in header['CC']:
                                cc += tmp_cc + ','
                            if cc[-1] == ',':
                                cc = cc[:-1]
                        except Exception:
                            pass

                        bcc = ''
                        try:
                            for tmp_bcc in header['BCC']:
                                bcc += tmp_bcc + ','
                            if bcc[-1] == ',':
                                bcc = bcc[:-1]
                        except Exception:
                            pass
                        try:
                            h_from = ''
                            if type(header['From']) == str:
                                h_from = header['From']

                            h_subject = ''
                            if type(header['Subject']) == str:
                                h_subject = header['Subject']

                            h_in_reply_to = ''
                            if type(header['In_Reply_to']) == str:
                                h_in_reply_to = header['In_Reply_to']

                            h_date = ''
                            if type(header['Date']) == str:
                                h_date = header['Date']

                            h_message_id = ''
                            if type(header['Message_ID']) == str:
                                h_message_id = header['Message_ID']

                            h_sender = ''
                            if type(header['Sender']) == str:
                                h_sender = header['Sender']

                            h_reply_to = ''
                            if type(header['Reply_To']) == str:
                                h_reply_to = header['Reply_To']

                            h_errors_to = ''
                            if type(header['Errors_To']) == str:
                                h_errors_to = header['Errors_To']

                            h_boundary = ''
                            if type(header['Boundary']) == str:
                                h_boundary = header['Boundary']

                            h_content_type = ''
                            if type(header['Content_Type']) == str:
                                h_content_type = header['Content_Type']

                            h_mime_version = ''
                            if type(header['MIME_Version']) == str:
                                h_mime_version = header['MIME_Version']

                            h_precedence = ''
                            if type(header['Precedence']) == str:
                                h_precedence = header['Precedence']

                            h_user_agent = ''
                            if type(header['User_Agent']) == str:
                                h_user_agent = header['User_Agent']

                            h_x_mailer = ''
                            if type(header['X_Mailer']) == str:
                                h_x_mailer = header['X_Mailer']

                            h_x_originating_ip = ''
                            if type(header['X_Originating_IP']) == str:
                                h_x_originating_ip = header['X_Originating_IP']

                            h_x_priority = ''
                            if type(header['X_Priority']) == str:
                                h_x_priority = header['X_Priority']

                            insert_email.append(tuple(
                                [par_id, configuration.case_id, configuration.evidence_id, received_lines, to,
                                 cc, bcc, h_from, h_subject, h_in_reply_to, h_date, h_message_id, h_sender,
                                 h_reply_to, h_errors_to, h_boundary, h_content_type, h_mime_version,
                                 h_precedence, h_user_agent, h_x_mailer, h_x_originating_ip, h_x_priority,
                                 r['EmailMessageObject']['Body']]))
                        except Exception:
                            pass

                elif fileExt == "msg" or fileExt == "eml":
                    received_lines = ''
                    header = result['EmailMessageObject']['Header']
                    try:
                        for received_line in header['Received_Lines']:
                            received_lines += json.dumps(received_line) + ','
                        if len(received_lines) != 0:
                            received_lines = received_lines[:-1]
                    except Exception:
                        pass

                    to = ''
                    try:
                        for tmp_to in header['To']:
                            to += tmp_to + ','
                        if len(to) != 0:  # ',' 처리
                            to = to[:-1]
                    except Exception:
                        pass

                    if to == '':
                        continue

                    cc = ''
                    try:
                        for tmp_cc in header['CC']:
                            cc += tmp_cc + ','
                        if len(cc) != 0:  # ',' 처리
                            cc = cc[:-1]
                    except Exception:
                        pass

                    bcc = ''
                    try:
                        for tmp_bcc in header['BCC']:
                            bcc += tmp_bcc + ','
                        if len(bcc) != 0:  # ',' 처리
                            bcc = bcc[:-1]
                    except Exception:
                        pass

                    try:
                        h_from = ''
                        if type(header['From']) == str:
                            h_from = header['From']

                        h_subject = ''
                        if type(header['Subject']) == str:
                            h_subject = header['Subject']

                        h_in_reply_to = ''
                        if type(header['In_Reply_to']) == str:
                            h_in_reply_to = header['In_Reply_to']

                        h_date = ''
                        if type(header['Date']) == str:
                            h_date = header['Date']

                        h_message_id = ''
                        if type(header['Message_ID']) == str:
                            h_message_id = header['Message_ID']

                        h_sender = ''
                        if type(header['Sender']) == str:
                            h_sender = header['Sender']

                        h_reply_to = ''
                        if type(header['Reply_To']) == str:
                            h_reply_to = header['Reply_To']

                        h_errors_to = ''
                        if type(header['Errors_To']) == str:
                            h_errors_to = header['Errors_To']

                        h_boundary = ''
                        if type(header['Boundary']) == str:
                            h_boundary = header['Boundary']

                        h_content_type = ''
                        if type(header['Content_Type']) == str:
                            h_content_type = header['Content_Type']

                        h_mime_version = ''
                        if type(header['MIME_Version']) == str:
                            h_mime_version = header['MIME_Version']

                        h_precedence = ''
                        if type(header['Precedence']) == str:
                            h_precedence = header['Precedence']

                        h_user_agent = ''
                        if type(header['User_Agent']) == str:
                            h_user_agent = header['User_Agent']

                        h_x_mailer = ''
                        if type(header['X_Mailer']) == str:
                            h_x_mailer = header['X_Mailer']

                        h_x_originating_ip = ''
                        if type(header['X_Originating_IP']) == str:
                            h_x_originating_ip = header['X_Originating_IP']

                        h_x_priority = ''
                        if type(header['X_Priority']) == str:
                            h_x_priority = header['X_Priority']

                        insert_email.append(tuple(
                            [par_id, configuration.case_id, configuration.evidence_id, received_lines, to, cc,
                             bcc,
                             h_from, h_subject, h_in_reply_to, h_date, h_message_id, h_sender, h_reply_to,
                             h_errors_to,
                             h_boundary, h_content_type, h_mime_version, h_precedence, h_user_agent, h_x_mailer,
                             h_x_originating_ip, h_x_priority, result['EmailMessageObject']['Body']]))
                    except Exception:
                        pass

            else:
                try:
                    if fileExt == "mbox" or fileExt == "pst" or fileExt == "ost":
                        for r in result:
                            es.index(index=_index_name, doc_type=_type_name, body=r)
                    elif fileExt == "msg" or fileExt == "eml":
                        es.index(index=_index_name, doc_type=_type_name, body=result)
                except Exception as e:
                    print("Error : " + str(e))

        if configuration.standalone_check == True:
            query = "Insert into lv1_app_email values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"
            configuration.cursor.bulk_execute(query, insert_email)

manager.ModulesManager.RegisterModule(EMAILConnector)