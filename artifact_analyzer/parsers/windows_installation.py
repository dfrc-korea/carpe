# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import os, sys
sys.path.append(os.path.join(os.path.join(os.path.abspath(os.path.dirname('__file__')), "artifact_analyzer"), "parsers"))

import parser_interface
from utility import carpe_db
import pdb
class WindowsInstallation(parser_interface.ParserInterface):
    """
        Windows Operating System Installation information parser.
    """
    def __init__(self):
        # Initialize Formatter Interface
        super().__init__()
    
    def Parse(self, case_id, evd_id):
        """
            Analyzes records related to Windows operating system
            installation information in Psort result.
        """
        db = carpe_db.Mariadb()
        db.open()

        query = "SELECT par_id FROM partition_info WHERE evd_id='" + evd_id + "';"
        par_list = db.execute_query_mul(query)
        pdb.set_trace()
        for par in par_list:
            for art in self.ARTIFACTS:
                name = art['Name']
                desc = art['Desc']
                values = art['values']

                for value in values:
                    val_type = value[0]
                    val_data = value[1]
                    pdb.set_trace()
                    if val_type == 'REG_KEY':
                        query = "SELECT description, datetime FROM log2timeline WHERE par_id='" + par[0] + "' and description like '[" + val_data + "]%';"
                        result = db.execute_query_mul(query)

        db.close()
