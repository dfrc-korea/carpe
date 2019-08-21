# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import os, sys
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname('__file__'))))

from parsers import parser_interface
from utility import carpe_db

class WindowsUserAccount(parser_interface.ParserInterface):
    """
        Windows User Accountinformation parser.
    """ 
    def __init__(self):
        # Initialize Formatter Interface
        super().__init__()
    
    def Parse(self, case_id, evd_id):
        """
            Analyzes records related to Windows operating system
            installation information in Psort result.
        """
        print("-----------------------------------")
        print("Parser Module : WindowsUserAccount")
        print(self.NAME)
        print(self.DESC)
        print("-----------------------------------")
