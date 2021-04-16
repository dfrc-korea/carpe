import os
import logging
from bs4 import BeautifulSoup
from urllib.parse import urlparse, unquote
from ..utils.takeout_html_parser import TakeoutHtmlParser


class MyActivityAssistant(object):
    def parse_assistant_log_caption(dic_my_activity_assistant, assistant_logs):
        list_assistant_geodata_logs = TakeoutHtmlParser.find_log_caption(assistant_logs)

        if list_assistant_geodata_logs:
            for content in list_assistant_geodata_logs:
                content = str(content).strip()
                if content == '<br/>':
                    continue
                if content.startswith('<a href="https://www.google.com/maps/'):
                    idx = content.find('">')
                    url = content[9:idx]
                    o = urlparse(url)
                    list_query_value = o.query.split(';')

                    if list_query_value:
                        for query_value in list_query_value:
                            if query_value.startswith('center='):
                                geodata = query_value.lstrip('center=').rstrip('&amp')
                                dic_my_activity_assistant['latitude'] = geodata.split(',', 1)[0]
                                dic_my_activity_assistant['longitude'] = geodata.split(',', 1)[1]
                            elif query_value.startswith('query='):
                                geodata = query_value.lstrip('query=')
                                dic_my_activity_assistant['latitude'] = geodata.split(',', 1)[0]
                                dic_my_activity_assistant['longitude'] = geodata.split(',', 1)[1]

                    if dic_my_activity_assistant['geodata_description'] == "":
                        dic_my_activity_assistant['geodata_description'] = content[idx+2:content.find('</a>')]

    def parse_assistant_log_body_text(dic_my_activity_assistant, assistant_logs, file_path):
        list_assistant_trained_logs = TakeoutHtmlParser.find_log_body_text(assistant_logs)

        if list_assistant_trained_logs:
            for content in list_assistant_trained_logs:
                content = str(content).strip()

                if content.startswith('<audio controls'):                    
                    attachment = content.split('>')[2].split('<')[0].lstrip('Audio file: ').split(' ')[0]
                    attachment_path = os.path.dirname(file_path) + os.sep + attachment
                    if os.path.exists(attachment_path):
                        dic_my_activity_assistant['attachment'] = attachment_path

    def parse_assistant_log_body(dic_my_activity_assistant, assistant_logs):
        list_assistant_search_logs = TakeoutHtmlParser.find_log_body(assistant_logs)

        if list_assistant_search_logs:
            idx = 0
            for content in list_assistant_search_logs:
                content = str(content).strip()
                content = content.replace(u'\xa0', ' ')
                if idx == 0:
                    if content.startswith('Said'):
                        dic_my_activity_assistant['type'] = 'Search'
                        if len(content) >= 5 and content.find(' ') >= 1:
                            keyword = content.split(' ', 1)[1]
                            dic_my_activity_assistant['keyword'] = TakeoutHtmlParser.remove_special_char(keyword)
                    elif content.startswith('Used'):
                        dic_my_activity_assistant['type'] = 'Use'
                        if len(content) >= 5 and content.find(' ') >= 1:
                            keyword = content.split(' ', 1)[1]
                            dic_my_activity_assistant['keyword'] = TakeoutHtmlParser.remove_special_char(keyword)
                    elif content.startswith('Trained'):
                        dic_my_activity_assistant['type'] = 'Train'
                        if len(content) >= 8 and content.find(' ') >= 1:
                            keyword = content.split(' ', 1)[1]
                            dic_my_activity_assistant['keyword'] = TakeoutHtmlParser.remove_special_char(keyword)
                    elif content.startswith('Selected') or content.startswith('Listened'):
                        dic_my_activity_assistant['type'] = 'Use'
                        if len(content) >= 9 and content.find(' ') >= 1:
                            dic_my_activity_assistant['keyword'] = TakeoutHtmlParser.remove_special_char(content)
                else:
                    if idx == 1:
                        if content.startswith('<a href="'):
                            idx2 = content.find('">')
                            keyword = content[idx2+2:content.find('</a>')]
                            dic_my_activity_assistant['keyword'] = TakeoutHtmlParser.remove_special_char(keyword)
                            url = content[9:idx2]
                            url = unquote(url)
                            dic_my_activity_assistant['keyword_url'] = url
                    elif content.endswith('UTC'):
                        dic_my_activity_assistant['timestamp'] = TakeoutHtmlParser.convert_datetime_to_unixtime(content)
                    elif idx != 1 and content != '<br/>':
                        if content.startswith('<a href="'):
                            idx2 = content.find('">')
                            keyword = content[idx2+2:content.find('</a>')]
                            dic_my_activity_assistant['result'] = TakeoutHtmlParser.remove_special_char(keyword)
                            url = content[9:idx2]
                            url = unquote(url)
                            dic_my_activity_assistant['result_url'] = url
                            o = urlparse(url)
                        else:
                            dic_my_activity_assistant['result'] += TakeoutHtmlParser.remove_special_char(content)
                idx += 1

    def parse_assistant_log_title(dic_my_activity_assistant, assistant_logs):
        list_assistant_title_logs = TakeoutHtmlParser.find_log_title(assistant_logs)

        if list_assistant_title_logs:
            for content in list_assistant_title_logs:
                content = str(content).strip()
                dic_my_activity_assistant['service'] = content.split('>')[1].split('<br')[0]
                dic_my_activity_assistant['used_device'] = 'mobile'

    def parse_assistant(case):
        file_path = case.takeout_my_activity_assistant_path

        if not os.path.exists(file_path):
            return False

        result = []
        with open(file_path, 'r', encoding='utf-8') as f:
            file_contents = f.read()
            soup = BeautifulSoup(file_contents, 'lxml')
            list_assistant_logs = TakeoutHtmlParser.find_log(soup)

            if list_assistant_logs:
                for i in range(len(list_assistant_logs)):
                    dic_my_activity_assistant = {'timestamp':"", 'service':"", 'type':"", 'keyword':"", 'keyword_url':"", 'result':"", 'result_url':"", 'latitude':"", 'longitude':"", 'geodata_description':"", 'attachment':"", 'used_device':""}
                    MyActivityAssistant.parse_assistant_log_title(dic_my_activity_assistant, list_assistant_logs[i])
                    MyActivityAssistant.parse_assistant_log_body(dic_my_activity_assistant, list_assistant_logs[i])
                    MyActivityAssistant.parse_assistant_log_body_text(dic_my_activity_assistant, list_assistant_logs[i], file_path)
                    MyActivityAssistant.parse_assistant_log_caption(dic_my_activity_assistant, list_assistant_logs[i])

                    result.append((dic_my_activity_assistant['timestamp'], dic_my_activity_assistant['service'], dic_my_activity_assistant['type'],
                                   dic_my_activity_assistant['keyword'], dic_my_activity_assistant['keyword_url'], dic_my_activity_assistant['result'],
                                   dic_my_activity_assistant['result_url'], dic_my_activity_assistant['latitude'], dic_my_activity_assistant['longitude'],
                                   dic_my_activity_assistant['geodata_description'], dic_my_activity_assistant['attachment'], dic_my_activity_assistant['used_device']))

        return result
