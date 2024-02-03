from __future__ import unicode_literals
import os, sys, re
from datetime import datetime
import numpy as np

from utility import database


class Usage_Year_Information:
    year = ''
    month = ''
    cnt = ''
    case_id = ''

def USAGEYEAR(configuration):
    db = configuration.cursor

    usage_history_list = []
    usage_history_count = 0

    existed_list = []
    existed_year = []

    try:
        query = f"SELECT regdate FROM usage_day_detail WHERE (evd_id='{configuration.evidence_id}')"
        result_query = db.execute_query_mul(query)

        for result_data in result_query:
            existed_list.append(result_data[0][0:7])
            existed_year.append(result_data[0][0:4])

        existed_year = list(set(existed_year))

        groupby = list(set(existed_list))
        result = dict()
        for ip in groupby:
            result[ip] = existed_list.count(ip)

        for year in existed_year:
            for month in range(1, 13):
                target_year = year+'-'+str(month).zfill(2)
                if target_year not in result.keys():
                    result[target_year] = 0

        for r, k in sorted(result.items()):
            usage_year_information = Usage_Year_Information()
            usage_history_list.append(usage_year_information)
            usage_history_list[usage_history_count].year = r[0:4]
            usage_history_list[usage_history_count].month = r[5:7]
            usage_history_list[usage_history_count].cnt = k
            usage_history_count = usage_history_count + 1
    except:
        print('-----USAGE_YEAR not found')

    return usage_history_list