from __future__ import unicode_literals
from utility import database
from datetime import datetime
import os, sys, re
import numpy as np

class Timeline_Month_Information:
    evd_id = ''
    regmonth = ''
    regtime = ''
    day1 = ''
    day2 = ''
    day3 = ''
    day4 = ''
    day5 = ''
    day6 = ''
    day7 = ''
    day8 = ''
    day9 = ''
    day10 = ''
    day11 = ''
    day12 = ''
    day13 = ''
    day14 = ''
    day15 = ''
    day16 = ''
    day17 = ''
    day18 = ''
    day19 = ''
    day20 = ''
    day21 = ''
    day22 = ''
    day23 = ''
    day24 = ''
    day25 = ''
    day26 = ''
    day27 = ''
    day28 = ''
    day29 = ''
    day30 = ''
    day31 = ''

def TIMELINEMONTH(configuration):
    db = configuration.cursor

    usage_history_list = []
    usage_history_count = 0

    existed_list = []
    existed_month = []

    existed_list_systemon = []
    existed_list_systemoff = []

    try:
        query = f"SELECT regdate FROM usage_day_detail WHERE (evd_id='{configuration.evidence_id}')"
        result_query = db.execute_query_mul(query)

        # 원장님 요청으로 인해 Log On/Off, Sleep On/Off 추가 - KJH
        query_systemon = f"SELECT regdate FROM usage_day_detail WHERE (evd_id='{configuration.evidence_id}') and (evdnc_type = 'System On' or evdnc_type = 'Sleep End' or evdnc_type = 'LogOn - Success')"
        result_query_systemon = db.execute_query_mul(query_systemon)

        # 원장님 요청으로 인해 Log On/Off, Sleep On/Off 추가 - KJH
        query_systemoff = f"SELECT regdate FROM usage_day_detail WHERE (evd_id='{configuration.evidence_id}') and (evdnc_type = 'System Off' or evdnc_type = 'Sleep Start' or evdnc_type = 'LogOff')"
        result_query_systemoff = db.execute_query_mul(query_systemoff)

        for result_data in result_query:
            existed_list.append(result_data[0][:13])
            existed_month.append(result_data[0][0:7])

        for result_data_systemon in result_query_systemon:
            existed_list_systemon.append(result_data_systemon[0][0:13])

        for result_query_systemoff in result_query_systemoff:
            existed_list_systemoff.append(result_query_systemoff[0][0:13])

        existed_list = list(set(existed_list))
        existed_month = list(set(existed_month))

        existed_list_systemon = list(set(existed_list_systemon))
        existed_list_systemoff = list(set(existed_list_systemoff))


        work_time_list = []
        month_count = 0

        for i in existed_month:
            year_month = i[0:4] + i[5:7]
            work_time = np.array([
                [0, 0, '01:00', 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                 0],
                [0, 0, '02:00', 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                 0],
                [0, 0, '03:00', 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                 0],
                [0, 0, '04:00', 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                 0],
                [0, 0, '05:00', 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                 0],
                [0, 0, '06:00', 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                 0],
                [0, 0, '07:00', 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                 0],
                [0, 0, '08:00', 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                 0],
                [0, 0, '09:00', 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                 0],
                [0, 0, '10:00', 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                 0],
                [0, 0, '11:00', 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                 0],
                [0, 0, '12:00', 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                 0],
                [0, 0, '13:00', 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                 0],
                [0, 0, '14:00', 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                 0],
                [0, 0, '15:00', 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                 0],
                [0, 0, '16:00', 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                 0],
                [0, 0, '17:00', 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                 0],
                [0, 0, '18:00', 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                 0],
                [0, 0, '19:00', 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                 0],
                [0, 0, '20:00', 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                 0],
                [0, 0, '21:00', 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                 0],
                [0, 0, '22:00', 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                 0],
                [0, 0, '23:00', 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                 0],
                [0, 0, '24:00', 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                 0]])
            work_time_list.append(work_time)
            for j in work_time_list[month_count]:
                j[1] = year_month
            for k in existed_list:
                if i in k:
                    try:
                        work_time_list[month_count][int(k[11:13]) - 1, int(k[8:10]) + 2] = 1
                    except:
                        None

            for e_1 in existed_list_systemon:
                if i in e_1:
                    try:
                        work_time_list[month_count][int(e_1[11:13]) - 1, int(e_1[8:10]) + 2] = 2 # System On
                    except:
                        None

            for e_2 in existed_list_systemoff:
                if i in e_2:
                    try:
                        if work_time_list[month_count][int(e_2[11:13]) - 1, int(e_2[8:10]) + 2] == '0':
                            work_time_list[month_count][int(e_2[11:13]) - 1, int(e_2[8:10]) + 2] = 3  # System Off
                        elif work_time_list[month_count][int(e_2[11:13]) - 1, int(e_2[8:10]) + 2] == '1':
                            work_time_list[month_count][int(e_2[11:13]) - 1, int(e_2[8:10]) + 2] = 3
                        elif work_time_list[month_count][int(e_2[11:13]) - 1, int(e_2[8:10]) + 2] == '2':
                            work_time_list[month_count][int(e_2[11:13]) - 1, int(e_2[8:10]) + 2] = 4
                        elif work_time_list[month_count][int(e_2[11:13]) - 1, int(e_2[8:10]) + 2] == '3':
                            work_time_list[month_count][int(e_2[11:13]) - 1, int(e_2[8:10]) + 2] = 3
                        elif work_time_list[month_count][int(e_2[11:13]) - 1, int(e_2[8:10]) + 2] == '4':
                            work_time_list[month_count][int(e_2[11:13]) - 1, int(e_2[8:10]) + 2] = 4
                    except:
                        None

            usage_history_list.append(work_time_list[month_count].tolist())
            month_count = month_count + 1

    except:
        print('-----USAGE_DAY_STAT not found')

    return usage_history_list