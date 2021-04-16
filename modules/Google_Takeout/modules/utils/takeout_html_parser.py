import logging
from bs4 import BeautifulSoup
from datetime import datetime
import time

logger = logging.getLogger('gtForensics')

class TakeoutHtmlParser(object):
    def convert_datetime_to_unixtime(datetime_takeout):
        datetime_component = datetime_takeout.split(' ')
        month = datetime_component[0].rstrip(',')
        if month.upper() == 'JAN':      month = 1
        elif month.upper() == 'FEB':    month = 2
        elif month.upper() == 'MAR':    month = 3
        elif month.upper() == 'APR':    month = 4
        elif month.upper() == 'MAY':    month = 5
        elif month.upper() == 'JUN':    month = 6
        elif month.upper() == 'JUL':    month = 7
        elif month.upper() == 'AUG':    month = 8
        elif month.upper() == 'SEP':    month = 9
        elif month.upper() == 'OCT':    month = 10
        elif month.upper() == 'NOV':    month = 11
        elif month.upper() == 'DEC':    month = 12
        day = datetime_component[1].rstrip(',')
        year = datetime_component[2].rstrip(',')
        time_component = datetime_component[3].split(':')
        hour = time_component[0]
        minute = time_component[1]
        second = time_component[2]
        flag = datetime_component[4]
        str_time = str(year) + '-' + str(month) + '-' + str(day) + ' ' + str(hour) + ':' + str(minute) + ':' + str(second)
        unixtime = time.mktime(datetime.strptime(str_time, '%Y-%m-%d %H:%M:%S').timetuple())
        seconds_12hours = 60*60*12
        if flag == 'PM':    unixtime = unixtime + seconds_12hours
        return str(unixtime).split('.')[0]
        
#---------------------------------------------------------------------------------------------------------------
    def remove_special_char(str):
        return str.replace("\"", "\'").replace("&amp;", "&")

#---------------------------------------------------------------------------------------------------------------    
    def find_category_title(soup):
        return soup.find_all('h3', class_ ={"category-title"})

#---------------------------------------------------------------------------------------------------------------
    def find_log(soup):
        return soup.find_all('div', class_ ={"outer-cell mdl-cell mdl-cell--12-col mdl-shadow--2dp"})

#---------------------------------------------------------------------------------------------------------------
    def find_log_title(logs):
        return logs.find('div', class_ ={"header-cell mdl-cell mdl-cell--12-col"})
        # return logs.find('div', class_ ={"mdl-typography--title"})

#---------------------------------------------------------------------------------------------------------------
    def find_log_body(logs):
        return logs.find('div', class_ ={"content-cell mdl-cell mdl-cell--6-col mdl-typography--body-1"})

#---------------------------------------------------------------------------------------------------------------
    def find_log_body_text(logs):
        return logs.find('div', class_ ={"content-cell mdl-cell mdl-cell--6-col mdl-typography--body-1 mdl-typography--text-right"})

#---------------------------------------------------------------------------------------------------------------
    def find_log_caption(logs):
        return logs.find('div', class_ ={"content-cell mdl-cell mdl-cell--12-col mdl-typography--caption"})


