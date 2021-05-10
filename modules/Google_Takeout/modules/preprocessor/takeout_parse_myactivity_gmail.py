import os
from bs4 import BeautifulSoup
from ..utils.takeout_html_parser import TakeoutHtmlParser


class MyActivityGmail(object):
    def parse_gmail_log_body(dic_my_activity_gmail, gmail_logs):
        list_gmail_search_logs = TakeoutHtmlParser.find_log_body(gmail_logs)

        if list_gmail_search_logs:
            idx = 0
            for content in list_gmail_search_logs:
                content = str(content).strip()
                content = content.replace(u'\xa0', ' ')
                if idx == 0:
                    if content == 'Searched for':
                        dic_my_activity_gmail['type'] = 'Search'
                    else:
                        dic_my_activity_gmail['type'] = content
                else:
                    if idx == 1:
                        if content.startswith('<a href="'):
                            idx2 = content.find('">')
                            dic_my_activity_gmail['keyword_url'] = content[9:idx2]
                            keyword = content[idx2+2:content.find('</a>')]
                            dic_my_activity_gmail['keyword'] = TakeoutHtmlParser.remove_special_char(keyword)
                    elif content.endswith('UTC'):
                        dic_my_activity_gmail['timestamp'] = TakeoutHtmlParser.convert_datetime_to_unixtime(content)
                idx += 1

    def parse_gmail_log_title(dic_my_activity_gmail, gmail_logs):
        list_gmail_title_logs = TakeoutHtmlParser.find_log_title(gmail_logs)

        if list_gmail_title_logs:
            for content in list_gmail_title_logs:
                content = str(content).strip()
                dic_my_activity_gmail['service'] = content.split('>')[1].split('<br')[0]

    def insert_log_info_to_analysis_db(dic_my_activity_gmail, analysis_db_path):
        query = 'INSERT INTO parse_my_activity_gmail \
                (service, timestamp, type, keyword, keyword_url) \
                VALUES("%s", %d, "%s", "%s", "%s")' % \
                (dic_my_activity_gmail['service'], int(dic_my_activity_gmail['timestamp']), dic_my_activity_gmail['type'], \
                dic_my_activity_gmail['keyword'], dic_my_activity_gmail['keyword_url'])
        SQLite3.execute_commit_query(query, analysis_db_path)

    def parse_gmail(case):
        file_path = case.takeout_my_activity_gmail_path

        if not os.path.exists(file_path):
            return False

        result = []
        with open(file_path, 'r', encoding='utf-8') as f:
            file_contents = f.read()
            soup = BeautifulSoup(file_contents, 'lxml')
            list_gmail_logs = TakeoutHtmlParser.find_log(soup)

            if list_gmail_logs:
                for i in range(len(list_gmail_logs)):
                    dic_my_activity_gmail = {'service':"", 'type':"", 'keyword_url':"", 'keyword':"", 'timestamp':""}
                    MyActivityGmail.parse_gmail_log_title(dic_my_activity_gmail, list_gmail_logs[i])
                    MyActivityGmail.parse_gmail_log_body(dic_my_activity_gmail, list_gmail_logs[i])

                    result.append((dic_my_activity_gmail['service'], int(dic_my_activity_gmail['timestamp']), dic_my_activity_gmail['type'],
                                   dic_my_activity_gmail['keyword'], dic_my_activity_gmail['keyword_url']))

        return result
