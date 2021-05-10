import os
import logging
from bs4 import BeautifulSoup
from urllib.parse import urlparse, unquote
from ..utils.takeout_html_parser import TakeoutHtmlParser


class MyActivityMaps(object):
    def parse_maps_log_caption(dic_my_activity_maps, maps_logs):
        list_maps_logs = TakeoutHtmlParser.find_log_caption(maps_logs)

        if list_maps_logs:
            for content in list_maps_logs:
                content = str(content).strip()
                if content == '<br/>':  continue
                elif content.startswith('<a href="https://www.google.com/maps/'):
                    idx2 = content.find('">')
                    url = content[9:idx2]
                    o = urlparse(url)
                    list_query_value = o.query.split(';')

                    if list_query_value:
                        for query_value in list_query_value:
                            if query_value.startswith('center='):
                                geodata = query_value.lstrip('center=').rstrip('&amp')
                                dic_my_activity_maps['latitude'] = geodata.split(',')[0]
                                dic_my_activity_maps['longitude'] = geodata.split(',')[1]
                            elif query_value.startswith('query='):
                                geodata = query_value.lstrip('query=')
                                dic_my_activity_maps['latitude'] = geodata.split(',')[0]
                                dic_my_activity_maps['longitude'] = geodata.split(',')[1]
                    dic_my_activity_maps['geodata_description'] = content[idx2+2:content.find('</a>')]
                elif content == '- From your device':
                    dic_my_activity_maps['used_device'] = 'mobile'

    def parse_maps_log_body(dic_my_activity_maps, maps_logs):
        list_maps_event_logs = TakeoutHtmlParser.find_log_body(maps_logs)

        if list_maps_event_logs != []:
            idx = 0
            for content in list_maps_event_logs:
                content = str(content).strip()
                content = content.replace(u'\xa0', ' ')
                if idx == 0:                    
                    if content.startswith('<a href="'):
                        url = content[9:content.find('">')]
                        keyword = content.split('>')[1].split('</a')[0]
                        dic_my_activity_maps['keyword'] = keyword.replace("\"", "\'")

                        if keyword.startswith('View'):
                            dic_my_activity_maps['type'] = 'View'
                        else:
                            dic_my_activity_maps['type'] = 'Search'
                        url = unquote(url)
                        dic_my_activity_maps['keyword_url'] = TakeoutHtmlParser.remove_special_char(url)
                        o = urlparse(url)
                        if o.path.startswith('/maps/@'):
                            list_value = o.path.lstrip('/maps/@').split(',')
                            if list_value != []:
                                latitude = list_value[0]
                                longitude = list_value[1]
                                dic_my_activity_maps['keyword_latitude'] = latitude
                                dic_my_activity_maps['keyword_longitude'] = longitude
                        elif o.path.find('@') >= 1:
                            list_value = o.path.split('@')[1].split(',')
                            if list_value != []:
                                latitude = list_value[0]
                                longitude = list_value[1]
                                dic_my_activity_maps['keyword_latitude'] = latitude
                                dic_my_activity_maps['keyword_longitude'] = longitude
                        elif o.query.find('sll=') >= 1:
                            list_value = o.query.split('sll=', 1)[1].split(',')
                            if list_value != []:
                                latitude = list_value[0]
                                longitude = list_value[1].split('&')[0]
                                dic_my_activity_maps['keyword_latitude'] = latitude
                                dic_my_activity_maps['keyword_longitude'] = longitude
                    else:
                        if content == 'Searched for':
                            dic_my_activity_maps['type'] = 'Search'
                        elif content.startswith('Shared'):
                            dic_my_activity_maps['type'] = 'Share'
                        elif content.startswith('Viewed'):
                            dic_my_activity_maps['type'] = 'View'
                            if content == 'Viewed For you':
                                dic_my_activity_maps['keyword'] = TakeoutHtmlParser.remove_special_char(content)
                        elif content == 'Used Maps':
                            dic_my_activity_maps['type'] = 'Use'
                            dic_my_activity_maps['keyword'] = TakeoutHtmlParser.remove_special_char(content)
                        elif content.startswith('Answered'):
                            dic_my_activity_maps['type'] = 'Answer'
                            dic_my_activity_maps['keyword'] = TakeoutHtmlParser.remove_special_char(content)
                        else:
                            dic_my_activity_maps['type'] = content
                else:
                    if idx == 1:
                        if content.startswith('<a href="'):
                            idx2 = content.find('">')
                            keyword = content[idx2+2:content.find('</a>')]
                            dic_my_activity_maps['keyword'] = TakeoutHtmlParser.remove_special_char(keyword)
                            url = content[9:idx2]
                            url = unquote(url)
                            dic_my_activity_maps['keyword_url'] = TakeoutHtmlParser.remove_special_char(url)
                            o = urlparse(url)
                            if o.path.startswith('/maps/') and o.path.find('@') >= 1:
                                list_value = o.path.split('@')[1].split(',')
                                if list_value != []:
                                    latitude = list_value[0]
                                    longitude = list_value[1]
                                    dic_my_activity_maps['keyword_latitude'] = latitude
                                    dic_my_activity_maps['keyword_longitude'] = longitude
                            elif o.query.find('sll=') >= 1:
                                list_value = o.query.split('sll=', 1)[1].split(',')
                                if list_value != []:
                                    latitude = list_value[0]
                                    longitude = list_value[1].split('&')[0]
                                    dic_my_activity_maps['keyword_latitude'] = latitude
                                    dic_my_activity_maps['keyword_longitude'] = longitude
                    else:
                        if content.endswith('UTC'):
                            dic_my_activity_maps['timestamp'] = TakeoutHtmlParser.convert_datetime_to_unixtime(content)
                        elif idx == 4 and dic_my_activity_maps['type'] == '1 notification':
                            dic_my_activity_maps['keyword'] = TakeoutHtmlParser.remove_special_char(content)
                idx += 1

    def parse_maps_log_title(dic_my_activity_maps, maps_logs):
        list_maps_title_logs = TakeoutHtmlParser.find_log_title(maps_logs)

        if list_maps_title_logs:
            for content in list_maps_title_logs:
                content = str(content).strip()
                dic_my_activity_maps['service'] = content.split('>')[1].split('<br')[0]

    def parse_maps(case):
        file_path = case.takeout_my_activity_maps_path

        if not os.path.exists(file_path):
            return False

        result = []
        with open(file_path, 'r', encoding='utf-8') as f:
            file_contents = f.read()
            soup = BeautifulSoup(file_contents, 'lxml')
            list_maps_logs = TakeoutHtmlParser.find_log(soup)

            if list_maps_logs:
                for i in range(len(list_maps_logs)):
                    dic_my_activity_maps = {'timestamp':"", 'service':"", 'type':"", 'keyword':"", 'keyword_url':"", \
                    'keyword_latitude':"", 'keyword_longitude':"", 'latitude':"", 'longitude':"", 'geodata_description':"", \
                    'used_device':""}
                    MyActivityMaps.parse_maps_log_title(dic_my_activity_maps, list_maps_logs[i])
                    MyActivityMaps.parse_maps_log_body(dic_my_activity_maps, list_maps_logs[i])
                    MyActivityMaps.parse_maps_log_caption(dic_my_activity_maps, list_maps_logs[i])

                    result.append((dic_my_activity_maps['timestamp'], dic_my_activity_maps['service'], dic_my_activity_maps['type'],
                                   dic_my_activity_maps['keyword'], dic_my_activity_maps['keyword_url'], dic_my_activity_maps['keyword_latitude'],
                                   dic_my_activity_maps['keyword_longitude'], dic_my_activity_maps['latitude'], dic_my_activity_maps['longitude'],
                                   dic_my_activity_maps['geodata_description'], dic_my_activity_maps['used_device']))

        return result
