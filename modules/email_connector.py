# -*- coding: utf-8 -*-
"""module for E-mail."""
import os
import configparser
from elasticsearch import Elasticsearch

from modules import manager
from modules import interface
#from modules.app_email.lib.yjSysUtils import *
#from modules.app_email.lib.delphi import *

class EMAILConnector(interface.ModuleConnector):

    NAME = 'email_connector'
    DESCRIPTION = 'Moudle for E-mail'

    _plugin_classes = {}

    def __init__(self):
        super(EMAILConnector, self).__init__()

    def Connect(self, configuration, source_path_spec, knowledge_base):
        print('[MODULE]: E-mail Connect')

        if source_path_spec.parent.type_indicator != dfvfs_definitions.TYPE_INDICATOR_TSK_PARTITION:
            par_id = configuration.partition_list['p1']
        else:
            par_id = configuration.partition_list[getattr(source_path_spec.parent, 'location', None)[1:]]

        if par_id == None:
            return False

        # extension -> sig_type 변경해야 함

        query = f"SELECT name, parent_path, extension FROM file_info WHERE par_id='{par_id}' and " \
                f"(extension = 'eml' or " \
                f"extension = 'mbox' or " \
                f"extension = 'msg' or " \
                f"extension = 'ost' or " \
                f"extension = 'pst');"

        # query = f"SELECT name, parent_path, extension FROM file_info WHERE par_id='{par_id}' and " \
        #         f"(extension = 'eml');"

        email_files = configuration.cursor.execute_query_mul(query)

        if len(email_files) == 0:
            return False

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

        for email in email_files:
            email_path = email[1][email[1].find('/'):] + '/' + email[0]  # document full path
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
                print('\n' + EmailBox.fileName)
                result = EmailBox.parse(fileExt)
            except Exception as e:
                continue

            os.remove(EmailBox.fileName)

            if not result:
                continue

            #print(result)
            try:
                if fileExt == "mbox" or fileExt == "pst" or fileExt == "ost":
                    for r in result:
                        es.index(index=_index_name, doc_type=_type_name, body=r)
                elif fileExt == "msg" or fileExt == "eml":
                    es.index(index=_index_name, doc_type=_type_name, body=result)
            except Exception as e:
                print("Error : " + str(e))


manager.ModulesManager.RegisterModule(EMAILConnector)