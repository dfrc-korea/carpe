import os
import logging
from bs4 import BeautifulSoup
from urllib.parse import urlparse, unquote
from ..utils.takeout_html_parser import TakeoutHtmlParser


class MyActivityChrome(object):
    def parse_chrome_log_body(dic_my_activity_chrome, chrome_logs):
        list_chrome_event_logs = TakeoutHtmlParser.find_log_body(chrome_logs)

        if list_chrome_event_logs:
            idx = 0
            for content in list_chrome_event_logs:
                content = str(content).strip()
                content = content.replace(u'\xa0', ' ')
                if idx == 0:
                    if content.startswith('Visited'):
                        dic_my_activity_chrome['type'] = 'Visit'
                    elif content.startswith('Used'):
                        dic_my_activity_chrome['type'] = 'Use'
                        if len(content) >= 5 and content.find(' ') >= 1:
                            keyword = content.split(' ', 1)[1]
                            dic_my_activity_chrome['keyword'] = TakeoutHtmlParser.remove_special_char(keyword)
                    else:
                        dic_my_activity_chrome['type'] = content
                else:
                    if idx == 1:
                        if content.startswith('<a href="'):
                            idx2 = content.find('">')
                            keyword = content[idx2+2:content.find('</a>')]
                            dic_my_activity_chrome['keyword'] = TakeoutHtmlParser.remove_special_char(keyword)
                            url = content[9:idx2]
                            url = unquote(url)
                            dic_my_activity_chrome['keyword_url'] = TakeoutHtmlParser.remove_special_char(url)
                            o = urlparse(url)
                            if o.query.startswith('q=') and o.query.find('&amp;'):
                                real_url = o.query[2:o.query.find('&amp;')]
                                real_url = unquote(real_url)
                                dic_my_activity_chrome['keyword_url'] = TakeoutHtmlParser.remove_special_char(real_url)
                                o = urlparse(real_url)
                                if o.netloc.startswith('m.'):
                                    dic_my_activity_chrome['used_device'] = 'mobile'
                    elif content.endswith('UTC'):
                        dic_my_activity_chrome['timestamp'] = TakeoutHtmlParser.convert_datetime_to_unixtime(content)
                idx += 1

    def parse_chrome_log_title(dic_my_activity_chrome, chrome_logs):
        list_chrome_title_logs = TakeoutHtmlParser.find_log_title(chrome_logs)

        if list_chrome_title_logs:
            for content in list_chrome_title_logs:
                content = str(content).strip()
                dic_my_activity_chrome['service'] = content.split('>', 1)[1].split('<br')[0]

    def parse_chrome(case):
        file_path = case.takeout_my_activity_chrome_path

        if not os.path.exists(file_path):
            return False

        result = []
        with open(file_path, 'r', encoding='utf-8') as f:
            file_contents = f.read()
            soup = BeautifulSoup(file_contents, 'lxml')
            list_chrome_logs = TakeoutHtmlParser.find_log(soup)

            if list_chrome_logs:
                for i in range(len(list_chrome_logs)):
                    dic_my_activity_chrome = {'service':"", 'type':"", 'keyword_url':"", 'keyword':"", 'timestamp':"", "used_device":""}
                    MyActivityChrome.parse_chrome_log_title(dic_my_activity_chrome, list_chrome_logs[i])
                    MyActivityChrome.parse_chrome_log_body(dic_my_activity_chrome, list_chrome_logs[i])

                    result.append((dic_my_activity_chrome['timestamp'], dic_my_activity_chrome['service'], dic_my_activity_chrome['type'],
                                   dic_my_activity_chrome['keyword'], dic_my_activity_chrome['keyword_url'], dic_my_activity_chrome['used_device']))
        return result
