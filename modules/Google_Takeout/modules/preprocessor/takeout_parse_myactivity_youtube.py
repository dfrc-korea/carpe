import os
import logging
from bs4 import BeautifulSoup
from urllib.parse import urlparse, unquote
from ..utils.takeout_html_parser import TakeoutHtmlParser


class MyActivityYouTube(object):
    def parse_youtube_log_body(dic_my_activity_youtube, youtube_logs):
        list_youtube_event_logs = TakeoutHtmlParser.find_log_body(youtube_logs)

        if list_youtube_event_logs:
            idx = 0
            for content in list_youtube_event_logs:
                content = str(content).strip()
                content = content.replace(u'\xa0', ' ')
                if idx == 0:
                    if content == 'Searched for':
                        dic_my_activity_youtube['type'] = 'Search'
                    elif content.startswith('Watched'):
                        dic_my_activity_youtube['type'] = 'Watch'
                        if len(content) >= 8 and content.find(' ') >= 1:
                            dic_my_activity_youtube['keyword'] = TakeoutHtmlParser.remove_special_char(content)
                    elif content.startswith('Visited'):
                        dic_my_activity_youtube['type'] = 'Visit'
                        if len(content) >= 8 and content.find(' ') >= 1:
                            dic_my_activity_youtube['keyword'] = TakeoutHtmlParser.remove_special_char(content)
                    else:
                        dic_my_activity_youtube['type'] = content
                else:
                    if idx == 1:
                        if content.startswith('<a href="'):
                            idx2 = content.find('">')
                            keyword = content[idx2+2:content.find('</a>')]
                            dic_my_activity_youtube['keyword'] = TakeoutHtmlParser.remove_special_char(keyword)
                            url = content[9:idx2]
                            url = unquote(url)
                            dic_my_activity_youtube['keyword_url'] = TakeoutHtmlParser.remove_special_char(url)
                    else:
                        if dic_my_activity_youtube['type'] == 'Watch':
                            if content.startswith('<a href="'):
                                idx2 = content.find('">')
                                channel_name = content[idx2+2:content.find('</a>')]
                                dic_my_activity_youtube['channel_name'] = TakeoutHtmlParser.remove_special_char(channel_name)
                                url = content[9:idx2]
                                url = unquote(url)
                                dic_my_activity_youtube['channel_url'] = TakeoutHtmlParser.remove_special_char(url)
                        if content.endswith('UTC'):
                            dic_my_activity_youtube['timestamp'] = TakeoutHtmlParser.convert_datetime_to_unixtime(content)
                idx += 1

    def parse_youtube_log_title(dic_my_activity_youtube, youtube_logs):
        list_youtube_title_logs = TakeoutHtmlParser.find_log_title(youtube_logs)

        if list_youtube_title_logs:
            for content in list_youtube_title_logs:
                content = str(content).strip()
                dic_my_activity_youtube['service'] = content.split('>')[1].split('<br')[0]

    def parse_youtube(case):
        file_path = case.takeout_my_activity_youtube_path

        if not os.path.exists(file_path):
            return False

        result = []
        with open(file_path, 'r', encoding='utf-8') as f:
            file_contents = f.read()
            soup = BeautifulSoup(file_contents, 'lxml')
            list_youtube_logs = TakeoutHtmlParser.find_log(soup)

            if list_youtube_logs:
                for i in range(len(list_youtube_logs)):
                    dic_my_activity_youtube = {'service':"", 'type':"", 'keyword_url':"", 'keyword':"", 'channel_url':"", 'channel_name':"", 'timestamp':""}
                    MyActivityYouTube.parse_youtube_log_title(dic_my_activity_youtube, list_youtube_logs[i])
                    MyActivityYouTube.parse_youtube_log_body(dic_my_activity_youtube, list_youtube_logs[i])

                    result.append((dic_my_activity_youtube['service'], int(dic_my_activity_youtube['timestamp']), dic_my_activity_youtube['type'],
                                   dic_my_activity_youtube['keyword'], dic_my_activity_youtube['keyword_url'],
                                   dic_my_activity_youtube['channel_name'], dic_my_activity_youtube['channel_url']))

        return result

