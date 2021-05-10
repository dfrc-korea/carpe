import os
import logging
from bs4 import BeautifulSoup
from urllib.parse import urlparse, unquote
from ..utils.takeout_html_parser import TakeoutHtmlParser

class MyActivityAndroid(object):
    def parse_android_log_caption(dic_my_activity_android, android_logs):
        list_android_logs = TakeoutHtmlParser.find_log_caption(android_logs)
        if list_android_logs:
            for content in list_android_logs:
                content = str(content).strip()
                if content.startswith('This'):
                    dic_my_activity_android['keyword'] += ': ' + TakeoutHtmlParser.remove_special_char(content)

    def parse_android_log_body(dic_my_activity_android, android_logs):
        list_android_event_logs = TakeoutHtmlParser.find_log_body(android_logs)
        if list_android_event_logs:
            idx = 0
            for content in list_android_event_logs:
                content = str(content).strip()
                content = content.replace(u'\xa0', ' ')
                if idx == 0:
                    if content.startswith('Used'):
                        dic_my_activity_android['type'] = 'Use'
                        if len(content) >= 5 and content.find(' ') >= 1:
                            keyword = content.split(' ', 1)[1]
                            dic_my_activity_android['keyword'] = TakeoutHtmlParser.remove_special_char(keyword)
                            dic_my_activity_android['package_name'] = keyword
                    elif content.startswith('Interacted'):
                        dic_my_activity_android['type'] = 'Interact'
                        dic_my_activity_android['keyword'] = TakeoutHtmlParser.remove_special_char(content)
                    elif content.startswith('Viewed'):
                        dic_my_activity_android['type'] = 'View'
                        if len(content) >= 7 and content.find(' ') >= 1:
                            keyword = content.split(' ', 1)[1]
                            dic_my_activity_android['keyword'] = TakeoutHtmlParser.remove_special_char(keyword)
                    elif content.startswith('Listened to'):
                        dic_my_activity_android['type'] = 'Listen'
                        if len(content) >= 12 and content.find(' ') >= 2:
                            keyword = content.split(' ', 2)[2]
                            dic_my_activity_android['keyword'] = TakeoutHtmlParser.remove_special_char(keyword)
                    else:
                        dic_my_activity_android['type'] = content
                else:
                    if idx == 1:
                        if content.startswith('<a href="'):
                            idx2 = content.find('">')
                            keyword = content[idx2+2:content.find('</a>')]
                            dic_my_activity_android['keyword'] = TakeoutHtmlParser.remove_special_char(keyword)
                            url = content[9:idx2]
                            url = unquote(url)
                            dic_my_activity_android['keyword_url'] = url
                            o = urlparse(url)
                            if dic_my_activity_android['type'] == 'Use':
                                if o.query.find('=') >= 1:
                                    dic_my_activity_android['package_name'] = o.query.split('=')[1]
                    elif content.endswith('UTC'):
                        dic_my_activity_android['timestamp'] = TakeoutHtmlParser.convert_datetime_to_unixtime(content)
                idx += 1

    def parse_android_log_title(dic_my_activity_android, android_logs):
        list_android_title_logs = TakeoutHtmlParser.find_log_title(android_logs)
        if list_android_title_logs != []:
            for content in list_android_title_logs:
                content = str(content).strip().replace("&amp;", "&")
                dic_my_activity_android['service'] = content.split('>')[1].split('<br')[0]
                dic_my_activity_android['used_device'] = 'mobile'

    def parse_android(case):
        file_path = case.takeout_my_activity_android_path

        if not os.path.exists(file_path):
            return False

        result = []
        with open(file_path, 'r', encoding='utf-8') as f:
            file_contents = f.read()
            soup = BeautifulSoup(file_contents, 'lxml')
            list_android_logs = TakeoutHtmlParser.find_log(soup)

            if list_android_logs:
                for i in range(len(list_android_logs)):
                    dic_my_activity_android = {'service':"", 'type':"", 'keyword_url':"", 'keyword':"", 'timestamp':"", 'package_name':"", 'used_device':""}
                    MyActivityAndroid.parse_android_log_title(dic_my_activity_android, list_android_logs[i])
                    MyActivityAndroid.parse_android_log_body(dic_my_activity_android, list_android_logs[i])
                    MyActivityAndroid.parse_android_log_caption(dic_my_activity_android, list_android_logs[i])

                    result.append((dic_my_activity_android['timestamp'], dic_my_activity_android['service'], dic_my_activity_android['type'],
                                   dic_my_activity_android['keyword'], dic_my_activity_android['keyword_url'], dic_my_activity_android['package_name'],
                                   dic_my_activity_android['used_device']))

        return result
