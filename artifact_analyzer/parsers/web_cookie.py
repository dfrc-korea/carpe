# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import os, sys, re

sys.path.append(os.path.join(os.path.abspath(os.path.dirname(__file__)), "parsers"))

import parser_interface
from utility import carpe_db


class WebCookie(parser_interface.ParserInterface):
  """
    Web Browser Cookie Parser.
  """

  def __init__(self):
    # Initialize Formatter Interface
    super().__init__()

  def Parse(self, case_id, evd_id):
    """
      Analyzes records related to Web Browser Cookies
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
          (source, sourcetype) = values[0]

          for chromium in chromium_list:
            query = """ SELECT  sourcetype, type, datetime, description, extra
                        FROM  log2timeline 
                        WHERE   par_id = '%s' AND
                        source = '%s' AND
                        sourcetype = '%s' AND 
                        filename LIKE '%%%s%%'
                    """ % (par[0], source, sourcetype, chromium)
                    
            result = db.execute_query_mul(query)
            if result == -1:
              break

            for _sourcetype, _type, _datetime, _description, _extra in result:
               time = _datetime.strftime('%Y-%m-%d %H:%M:%S')
               time_type = _type
               browser_type = chromium

               result = self.GetChromiumCookie(_description.decode(), _extra)
               (host_url, path, cookie_key, cookie_value) = result

               insert_values = (par[0], case_id, evd_id, browser_type, time_type,
                                 time, host_url, path, cookie_key, cookie_value)
               self.InsertQuery(db, insert_values)

        elif name == "Firefox":
          (source, sourcetype) = values[0]

          query = """ SELECT  sourcetype, type, datetime, description, extra
                      FROM  log2timeline
                      WHERE   par_id = '%s' AND
                      source = '%s' AND
                      sourcetype = '%s'
                  """ % (par[0], source, sourcetype)

          result = db.execute_query_mul(query)
          if result == -1:
            break

          for _sourcetype, _type, _datetime, _description, _extra in result:
            time = _datetime.strftime('%Y-%m-%d %H:%M:%S')
            time_type = _type
            browser_type = "Firefox"

            result = self.GetChromiumCookie(_description.decode(), _extra)
            (host_url, path, cookie_key, cookie_value) = result

            insert_values = (par[0], case_id, evd_id, browser_type, time_type,
                             time, host_url, path, cookie_key, cookie_value)
            self.InsertQuery(db, insert_values)

        elif name == "Internet Explorer index.dat":
          # TODO : Fix a Index.dat(Cookie) parser
          (sourcetype, browser_artifact_type, format) = values[0]

          query = """ SELECT  sourcetype, type, datetime, description
                      FROM  log2timeline
                      WHERE   par_id   = '%s' AND
                      sourcetype = '%s' AND
                      filename LIKE '%%%s%%' AND
                      format = '%s'
                  """ % (par[0], sourcetype, browser_artifact_type, format)

          result = db.execute_query_mul(query)
          if result == -1:
            break

          for _sourcetype, _type, _datetime, _description in result:
            time = _datetime.strftime('%Y-%m-%d %H:%M:%S')
            time_type = _type
            browser_type = "Internet Explorer (~9)"
            (path, cookie_key, cookie_value) = ("None", "None", "None")

            host_url = self.GetMSIECFCookie(_description.decode())

            insert_values = (par[0], case_id, evd_id, browser_type, time_type,
                             time, host_url, path, cookie_key, cookie_value)
            self.InsertQuery(db, insert_values)

        # elif name == "Internet Explorer WebCacheV##.dat":
        #  TODO : Description Parsing
        #  pass
    db.close()

  def GetChromiumCookie(self, _desc, _extra):
    (url, tmp_key, *other) = _desc.split("|`")
    cookie_key = tmp_key[1:-1]

    result = re.findall("(.+)schema", _extra)[0].strip()
    (cookie_value, host_url, path) = re.findall("data: (.+) host: (.+) path: (.+)", result)[0]

    return host_url.strip(), path, cookie_key, cookie_value.strip()

  def GetMSIECFCookie(self, _desc):
    tmp_host = ''.join(_desc.split("@")[1:])
    host_url = tmp_host.split("|`")[0][:-1]

    return host_url

  def InsertQuery(self, _db, _insert_values_tuple):
    query = self.GetQuery('I', _insert_values_tuple)
    _db.execute_query(query)
