# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import os, sys, re

sys.path.append(
  os.path.join(os.path.join(os.path.abspath(os.path.dirname('__file__')), "artifact_analyzer"), "parsers"))

import parser_interface
from utility import carpe_db


class WebCache(parser_interface.ParserInterface):
  """
    Web Browser Cache Parser.
  """

  def __init__(self):
    # Initialize Formatter Interface
    super().__init__()

  def Parse(self, case_id, evd_id):
    """
      Analyzes records related to Web Browser Cache
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
          # TODO : Fix a Chorme Cache plugin -> lack information

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
              time = _datetime.strftime('%Y-%m-%d %H:%M:%S')
              browser_type = chromium
              time_type = _type

              result = self.GetChromiumCache(_description.decode())

              if result == False:
                (cache_url, cache_name, cache_size, mime_type) = ("None", "None", "None", "None")

              else:
                (cache_url, cache_name, cache_size, mime_type) = (result, "None", "None", "None")

              insert_values = (par[0], case_id, evd_id, browser_type, time_type,
                               time, cache_url, cache_name, cache_size, mime_type)
              self.InsertQuery(db, insert_values)

        # elif name == "Firefox":
        #
        # TODO : Fix a FireFox Cache plugin
        #
        #   (source, sourcetype, timetype) = values[0]
        #
        #   query = """ SELECT  sourcetype, type, datetime, description
        #         FROM  log2timeline
        #         WHERE   par_id = '%s' AND
        #             source = '%s' AND
        #             sourcetype = '%s' AND
        #             type = '%s'
        #       """ % (par[0], source, sourcetype, timetype)
        #
        #   result = db.execute_query_mul(query)
        #   for _sourcetype, _type, _datetime, _description in result:
        #     visit_time = _datetime

        # elif name == "Internet Explorer index.dat":
        #  # TODO : Fix a Index.dat parser
        #  (sourcetype, browser_artifact_type, format) = values[0]
        #
        #  query = """ SELECT  sourcetype, type, datetime, description
        #          FROM  log2timeline
        #          WHERE   par_id   = '%s' AND
        #              sourcetype = '%s' AND
        #              filename LIKE '%%%s%%' AND
        #              format = '%s'
        #        """ % (par[0], sourcetype, browser_artifact_type, format)
        #  print(query)
        #
        #  result = db.execute_query_mul(query)
        #  if result == -1:
        #    break
        #
        #  for _sourcetype, _type, _datetime, _description in result:
        #    time = _datetime.strftime('%Y-%m-%d %H:%M:%S')
        #    time_type = _type
        #    browser_type = "Internet Explorer (~9)"
        #
        #    #self.GetMSIECF(_description, _extra)

        # elif name == "Internet Explorer WebCacheV##.dat":
        #  TODO : Description Parsing
        #  pass
    db.close()

  def GetChromiumCache(self, _desc):
    if _desc.find("Original URL: ") == -1:
      return False

    cache_url = _desc.replace("Original URL: ", "")
    return cache_url

  def GetGetMSIECFCache(self, _desc):
    pass


  def InsertQuery(self, _db, _insert_values_tuple):
    query = self.GetQuery('I', _insert_values_tuple)
    _db.execute_query(query)
