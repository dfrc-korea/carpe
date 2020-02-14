# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import os, sys
from datetime import datetime, timezone

sys.path.append(os.path.join(os.path.abspath(os.path.dirname(__file__)), "parsers"))

import parser_interface
from utility import carpe_db

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
    # Check Table
    if not self.CheckTable():
      self.CreateTable()
        
    # Connect Database
    db = carpe_db.Mariadb()
    db.open()
      
    # Parse Data
    query = "SELECT par_id FROM partition_info WHERE evd_id='" + evd_id + "';"
    par_list = db.execute_query_mul(query)
      
    for par in par_list:
      for art in self.ARTIFACTS:
        name = art['Name']
        desc = art['Desc']
        values = art['Values']
          
        for value in values:
          val_type = value[0]
          val_data = value[1]
            
          query = "SELECT description, filename FROM log2timeline WHERE par_id='" + par[0] + "' and " + val_type + "='" + val_data + "';"
          results = db.execute_query_mul(query)
            
          if len(results) == 0:
            continue
          else:
            for result in results:
              data = (result[0].decode('utf8')).split('|`')
            
              _data = []
              _data.append(par[0])  # par_id
              _data.append(case_id) # case_id
              _data.append(evd_id)  # evd_id
              _data.append('Windows')  # os_type
              _data.append(data[1].split(':')[1])  # product_name
              _data.append(data[3].split(':')[1])  # os_version
              _data.append(data[4].split(':')[1])  # build_version
              _data.append(data[5].split(':')[1])  # product_id
              _data.append(data[2].split(':')[1])  # release_id
              _data.append(data[6].split(':')[1])  # owner
              _data.append(data[7].split(':')[1])  # install_date
              _data.append(data[0][1:-1])  # source
                  
              query = self.GetQuery('I', _data)
              db.execute_query(query)
    db.close()