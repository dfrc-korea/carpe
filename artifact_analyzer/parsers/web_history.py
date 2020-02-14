# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import os, sys, re
from datetime import datetime

sys.path.append(os.path.join(os.path.abspath(os.path.dirname(__file__)), "parsers"))

import parser_interface
from utility import carpe_db

import pdb

class WebHistory(parser_interface.ParserInterface):
  """
    Web Browser History Parser.
  """
  def __init__(self):
    # Initialize Formatter Interface
    super().__init__()

  def Parse(self, case_id, evd_id):
    """
      Analyzes records related to Web Browser History
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
        values = art['Values']

        if name == "Chrome Family":
          chromium_list = ["Chrome", "Opera", "Edge"]
          (source, sourcetype, timetype) = values[0]

          for chromium in chromium_list:
            query = """ SELECT  sourcetype, type, datetime, description
                        FROM    log2timeline
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
              visit_time = _datetime.strftime('%Y-%m-%d %H:%M:%S')
              browser_type = chromium
              time_type = "Visit Time"
              visit_title = "None"

              (visit_url, count) = self.GetChromiumRecentOpened(_description.decode('utf-8'))
              if count == "None":
                (visit_url, visit_title, count) = self.GetVisitedURL(_description.decode('utf-8'))

              insert_values = ( par[0], case_id,  evd_id, browser_type, time_type,
                                visit_time, visit_url, visit_title.replace("\'", "\'\'"), count )
              self.InsertQuery(db, insert_values)

        elif name == "Firefox":
          (source, sourcetype, timetype) = values[0]
          query = """ SELECT  sourcetype, type, datetime, description
                      FROM    log2timeline
                      WHERE   par_id = '%s' AND
                              source = '%s' AND
                              sourcetype = '%s' AND
                              type = '%s'
                  """ % (par[0], source, sourcetype, timetype)

          result = db.execute_query_mul(query)

          if result == -1:
            break

          for _sourcetype, _type, _datetime, _description in result:
            visit_time = _datetime.strftime('%Y-%m-%d %H:%M:%S')
            browser_type = name
            time_type = "Visit Time"

            (visit_url, visit_title, count) = self.GetFirefoxRecentOpened(_description.decode('utf-8'))
            if count == "None":
              (visit_url, visit_title, count) = self.GetVisitedURL(_description.decode('utf-8'))

            insert_values = (par[0], case_id, evd_id, browser_type, time_type,
                             visit_time, visit_url, visit_title.replace("\'", "\'\'"), count)
            self.InsertQuery(db, insert_values)

        elif name == "Internet Explorer index.dat":
          (sourcetype, browser_artifact_type, format) = values[0]

          query = """ SELECT  sourcetype, type, datetime, description
                      FROM    log2timeline
                      WHERE   par_id     = '%s' AND
                              sourcetype = '%s' AND
                              filename LIKE '%%%s%%' AND
                              format = '%s'
                  """ % (par[0], sourcetype, browser_artifact_type, format)

          result = db.execute_query_mul(query)

          if result == -1:
            break

          for _sourcetype, _type, _datetime, _description in result:
            visit_time = _datetime.strftime('%Y-%m-%d %H:%M:%S')
            browser_type = "Internet Explorer (~9)"
            time_type = "Visit Time"
            visit_title = "None"

            (visit_url, count) = self.GetMSIECFHistory(_description.decode('utf-8'))

            insert_values = (par[0], case_id, evd_id, browser_type, time_type,
                             visit_time, visit_url, visit_title.replace("\'", "\'\'"), count)
            self.InsertQuery(db, insert_values)

    db.close()


  def GetChromiumRecentOpened(self, _desc):
    pattern = "(file://.+)\|`\[count: (.+)\]"
    parsed = re.findall(pattern, _desc)

    if len(parsed) == 0:
      return ("None", "None")

    (tmp_recent, tmp_count) = parsed[0]
    recent = tmp_recent.replace("file:///", "")
    count  = tmp_count.split("]")[0]

    return recent, count
    

  def GetVisitedURL(self, _desc):
    pattern = "(https?://.+)\|`\[count: (.+)\]"
    parsed = re.findall(pattern, _desc)

    if len(parsed) == 0:
      return ("None, None", "None")

    tmp_title = parsed[0][0].split("|`")
    tmp_count = parsed[0][1]

    url = tmp_title[0]
    if len(tmp_title) == 1:
      title = "None"
    else:
      title = ''.join(tmp_title[1:])[1:-1]
    count = tmp_count.split("]")[0]

    return url, title, count

  def GetFirefoxRecentOpened(self, _desc):
    pattern = "(file://.+)\|`\[count: (.+)\]"
    parsed = re.findall(pattern, _desc)

    if len(parsed) == 0:
      return "None", "None", "None"

    (tmp_recent, tmp_count) = parsed[0]
    recent = tmp_recent.replace("file:///", "").split("|`")
    count = tmp_count.split("]")[0]

    recent_path = recent[0]
    recent_title = ' '.join(recent[1:])[1:-1]

    return recent_path, recent_title, count

  def GetMSIECFHistory(self, _desc):
    pattern = "Location: (.+)\|`Number of hits: ([0-9]+)\|`Cached"

    for line in _desc.split("\n"):
      (url, count) = re.findall(pattern, line)[0]

      return url, count

  def InsertQuery(self, _db, _insert_values_tuple):
    query = self.GetQuery('I', _insert_values_tuple)
    #print(_insert_values_tuple)
    _db.execute_query(query)
