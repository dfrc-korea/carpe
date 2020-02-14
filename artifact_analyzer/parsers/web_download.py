# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import os, sys, re

sys.path.append(os.path.join(os.path.abspath(os.path.dirname(__file__)), "parsers"))

import parser_interface
from utility import carpe_db

class WebDownload(parser_interface.ParserInterface):
  """
    Web Browser File Downloaded History Parser.
  """

  def __init__(self):
    # Initialize Formatter Interface
    super().__init__()

  def Parse(self, case_id, evd_id):
    """
      Analyzes records related to Web Browser Download History
      in Psort result.
    """
    # Check Table
    if not self.CheckTable():
      self.CreateTable()

    db = carpe_db.Mariadb()
    db.open()
    query = "SELECT par_id FROM partition_info WHERE evd_id='" + evd_id + "';"
    par_list = db.execute_query_mul(query)

    for par in par_list:
      for art in self.ARTIFACTS:
        name = art['Name']
        desc = art['Desc']
        values = art['values']

        if name == "Chrome Family":
          chromium_list = ["Chrome", "Opera", "Edge"]

          (source, sourcetype, timetype) = values[0]

          for chromium in chromium_list:
            query = """ SELECT  sourcetype, type, datetime, description
                        FROM  log2timeline 
                        WHERE   par_id = '%s' AND
                        source = '%s' AND
                        sourcetype = '%s' AND
                        type = '%s' AND 
                        filename LIKE '%%%s%%'
                """ % (par[0], source, sourcetype, timetype, chromium)

            result = db.execute_query_mul(query)

            if result == -1:
              break

            for _sourcetype, _type, _datetime, _description in result:
              down_time = _datetime.strftime('%Y-%m-%d %H:%M:%S')
              browser_type = chromium
              time_type = "Download Time"

              (down_url, save_path, file_size) = self.GetChromiumDownload(_description.decode('utf-8'))

              insert_values = (par[0], case_id, evd_id, browser_type, time_type,
                               down_time, down_url, save_path.replace("\\", "/"), file_size)
              query = self.InsertQuery(db, insert_values)
              db.execute_query(query)

    db.close()

  def GetChromiumDownload(self, _desc):
    pattern = "(.+)\|`(.+)\|`Received: ([0-9]+) bytes\|`out of: ([0-9]+)"
    pattern_result = re.findall(pattern, _desc.strip())

    if len(pattern_result) == 0:
      return "None", "None", "None"

    (url, tmp_save_path, down_size, file_size) = pattern_result[0]
    save_path = tmp_save_path[1:-2]

    return url, save_path, file_size

  def InsertQuery(self, _db, _insert_values_tuple):
    query = self.GetQuery('I', _insert_values_tuple)
    _db.execute_query(query)