import os
from bs4 import BeautifulSoup
from urllib.parse import urlparse, unquote
from ..utils.takeout_html_parser import TakeoutHtmlParser


class MyActivityGoogleAnalytics(object):
    def parse_analytics_log_body(dic_my_activity_google_analytics, analytics_logs):
        list_analytics_event_logs = TakeoutHtmlParser.find_log_body(analytics_logs)

        if list_analytics_event_logs:
            idx = 0
            for content in list_analytics_event_logs:
                content = str(content).strip()
                content = content.replace(u'\xa0', ' ')
                if idx == 0:
                    if content == 'Used':
                        dic_my_activity_google_analytics['type'] = 'Use'
                    elif content == 'Visited':
                        dic_my_activity_google_analytics['type'] = 'Visit'
                    else:
                        dic_my_activity_google_analytics['type'] = content
                else:
                    if idx == 1:
                        if content.startswith('<a href="'):
                            idx2 = content.find('">')
                            keyword = content[idx2+2:content.find('</a>')]
                            dic_my_activity_google_analytics['keyword'] = TakeoutHtmlParser.remove_special_char(keyword)
                            url = content[9:idx2]
                            url = unquote(url)
                            dic_my_activity_google_analytics['keyword_url'] = url
                            o = urlparse(url)
                            if o.query.startswith('q=') and o.query.find('&amp;'):
                                real_url = o.query[2:o.query.find('&amp;')]
                                real_url = unquote(real_url)
                                dic_my_activity_google_analytics['keyword_url'] = real_url
                                o = urlparse(real_url)
                                if o.netloc.startswith('m.'):
                                    dic_my_activity_google_analytics['used_device'] = 'mobile'

                            if o.netloc.startswith('m.'):
                                dic_my_activity_google_analytics['used_device'] = 'mobile'
                    elif content.endswith('UTC'):
                        dic_my_activity_google_analytics['timestamp'] = TakeoutHtmlParser.convert_datetime_to_unixtime(content)
                idx += 1

    def parse_ganalytics_log_title(dic_my_activity_google_analytics, analytics_logs):
        list_analytics_title_logs = TakeoutHtmlParser.find_log_title(analytics_logs)

        if list_analytics_title_logs:
            for content in list_analytics_title_logs:
                content = str(content).strip()
                dic_my_activity_google_analytics['service'] = content.split('>')[1].split('<br')[0]

    def parse_google_analytics(case):
        file_path = case.takeout_my_activity_google_analytics_path

        if not os.path.exists(file_path):
            return False

        result = []
        with open(file_path, 'r', encoding='utf-8') as f:
            file_contents = f.read()
            soup = BeautifulSoup(file_contents, 'lxml')
            list_analytics_logs = TakeoutHtmlParser.find_log(soup)

            if list_analytics_logs:
                for i in range(len(list_analytics_logs)):
                    dic_my_activity_google_analytics = {'service':"", 'type':"", 'keyword_url':"", 'keyword':"", 'timestamp':"", 'used_device':""}
                    MyActivityGoogleAnalytics.parse_ganalytics_log_title(dic_my_activity_google_analytics, list_analytics_logs[i])
                    MyActivityGoogleAnalytics.parse_analytics_log_body(dic_my_activity_google_analytics, list_analytics_logs[i])

                    result.append((dic_my_activity_google_analytics['timestamp'], dic_my_activity_google_analytics['service'], dic_my_activity_google_analytics['type'],
                                   dic_my_activity_google_analytics['keyword'], dic_my_activity_google_analytics['keyword_url'], dic_my_activity_google_analytics['used_device']))

        return result
