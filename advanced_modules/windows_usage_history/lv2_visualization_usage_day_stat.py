from __future__ import unicode_literals
import os, sys, re
from datetime import datetime

from utility import database

class Usage_Day_Stat_Information:
    year = ''
    month = ''
    day = ''
    hour = ''
    min = ''
    act = ''
    case_id = ''

def USAGEDAYSTAT(configuration):
    db = configuration.cursor

    usage_history_list = []
    usage_history_count = 0

    existed_list = []
    existed_day = []
    try:
        query = f"SELECT regdate FROM usage_day_detail WHERE (evd_id='{configuration.evidence_id}')"
        result_query = db.execute_query_mul(query)

        for result_data in result_query:
            existed_list.append(result_data[0][:16])
            existed_day.append(result_data[0][:10])

        existed_day = list(set(existed_day))

        groupby = list(set(existed_list))
        result = dict()
        for ip in groupby:
            result[ip] = existed_list.count(ip)

        for wow in existed_day:
            for hour in range(1,25):
                for min in range(0, 60):
                    target_day = wow+' '+str(hour).zfill(2)+':'+str(min).zfill(2)
                    if target_day not in result.keys():
                        result[target_day] = 0

        for r,k in sorted(result.items()):
            if r[0:4].isdigit() and r[5:7].isdigit() and r[8:10].isdigit() and r[11:13].isdigit() and r[14:16].isdigit():
                pass
            else:
                continue

            usage_day_stat_information = Usage_Day_Stat_Information()
            usage_history_list.append(usage_day_stat_information)
            usage_history_list[usage_history_count].year = r[0:4]
            usage_history_list[usage_history_count].month = int(r[5:7])
            usage_history_list[usage_history_count].day = int(r[8:10])
            usage_history_list[usage_history_count].hour = r[11:13]
            usage_history_list[usage_history_count].min = r[14:16]
            usage_history_list[usage_history_count].act = k
            usage_history_count = usage_history_count + 1

    except:
        print('-----USAGE_DAY_STAT not found')

    return usage_history_list