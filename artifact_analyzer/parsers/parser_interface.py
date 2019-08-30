# -*- coding: utf-8 -*-
from __future__ import unicode_literals
#from plaso.lib import errors
from abc import *
import os, sys
sys.path.append(os.path.join(os.path.join(os.path.abspath(os.path.dirname('__file__')), "artifact_analyzer"), "parsers"))
from utility import carpe_db
import yaml

class ParserInterface(metaclass=ABCMeta):
    def __init__(self):
        # Formatter Attribute
        self.NAME       = ""
        self.DESC       = ""
        self.TABLE      = ""
        self.COLUMNS    = []
        self.TYPES      = []
        self.ARTIFACTS  = []
    
    def __del__(self):
        pass

    def LoadYAML(self, data):
        # Read YAML Data Stream
        d = yaml.load(data)

        # Set Formatter
        self.NAME       = d['Name']
        self.DESC       = d['Desc']
        self.TABLE      = d['Table'][0]['TableName']
        self.COLUMNS    = d['Table'][0]['Columns']
        self.TYPES      = d['Table'][0]['Types']
        self.ARTIFACTS  = d['Artifacts']

    def CheckTable(self):
        db = carpe_db.Mariadb()
        db.open()

        query = "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='" + self.TABLE + "';"
        ret = db.execute_query(query)
        db.close()

        return True if ret == 1 else False

    def CreateTable(self):
        q_list = []
        q_list.append("CREATE TABLE ")
        q_list.append(self.TABLE)
        q_list.append("(")

        for i in range(len(self.COLUMNS)):
            q_list.append(self.COLUMNS[i] + " ")
            q_list.append(self.TYPES[i][0] + " ")
            q_list.append(self.TYPES[i][1])

            if i != (len(self.COLUMNS) - 1):
                q_list.append(",")
            else:
                q_list.append(");")
        
        query = ''.join(q_list)

        db = carpe_db.Mariadb()
        db.open()
        db.execute_query(query)
        db.close()

    def GetQuery(self, _type):
        if _type == "S":
            return "SELECT * FROM " + self.TABLE
        elif _type == "I":
            q_list = []
            q_list.append("INSERT INTO ")
            q_list.append(self.TABLE)
            q_list.append(" VALUES (")

            for i in range(len(self.COLUMNS)):
                q_list.append("'{" + self.COLUMNS[i] + "}'")

                if i != (len(self.COLUMNS) - 1):
                    q_list.append(",")
                else:
                   q_list.append(");")

            return ''.join(q_list)    
        elif _type == "D":
            return "DELETE FROM " + self.TABLE + "WHERE par_id='{par_id}';"
        else:
            #raise errors.InvalidQueryType('Unsupported Query Type.')
            pass
        
    @abstractmethod
    def Parse(self, case_id, evd_id):
        pass