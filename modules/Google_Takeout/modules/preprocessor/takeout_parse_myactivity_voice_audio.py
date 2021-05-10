import os
import logging
from bs4 import BeautifulSoup
from urllib.parse import urlparse, unquote
from ..utils.takeout_html_parser import TakeoutHtmlParser


class MyActivityVoiceAudio(object):
    def parse_voice_audio_log_body_text(dic_my_activity_voice_audio, voice_audio_logs, file_path):
        list_assistant_trained_logs = TakeoutHtmlParser.find_log_body_text(voice_audio_logs)

        if list_assistant_trained_logs:
            for content in list_assistant_trained_logs:
                content = str(content).strip()
                if content.startswith('<audio controls'):
                    attachment = content.split('>')[2].split('<')[0].lstrip('Audio file: ').split(' ')[0]
                    attachment_path = os.path.dirname(file_path) + os.sep + attachment
                    if os.path.exists(attachment_path):
                        dic_my_activity_voice_audio['attachment'] = attachment_path

    def parse_voice_audio_log_body(dic_my_activity_voice_audio, voice_audio_logs):
        list_voice_audio_event_logs = TakeoutHtmlParser.find_log_body(voice_audio_logs)

        if list_voice_audio_event_logs:
            idx = 0
            for content in list_voice_audio_event_logs:
                content = str(content).strip()
                content = content.replace(u'\xa0', ' ')
                if idx == 0:
                    if content.startswith('Said'):
                        dic_my_activity_voice_audio['type'] = 'Search'
                        if content != 'Said':
                            dic_my_activity_voice_audio['keyword'] = content[4:].lstrip()
                    else:
                        dic_my_activity_voice_audio['type'] = content
                else:
                    if idx == 1 and dic_my_activity_voice_audio['type'] == 'Search':
                        if content.startswith('<a href="'):
                            idx2 = content.find('">')
                            keyword = content[idx2+2:content.find('</a>')]
                            dic_my_activity_voice_audio['keyword'] = TakeoutHtmlParser.remove_special_char(keyword)
                            url = content[9:idx2]
                            url = unquote(url)
                            dic_my_activity_voice_audio['keyword_url'] = url
                    elif content.endswith('UTC'):
                        dic_my_activity_voice_audio['timestamp'] = TakeoutHtmlParser.convert_datetime_to_unixtime(content)
                idx += 1

    def parse_voice_audio_log_title(dic_my_activity_voice_audio, voice_audio_logs):
        list_voice_audio_title_logs = TakeoutHtmlParser.find_log_title(voice_audio_logs)

        if list_voice_audio_title_logs:
            for content in list_voice_audio_title_logs:
                content = str(content).strip()
                dic_my_activity_voice_audio['service'] = content.split('>')[1].split('<br')[0]
                dic_my_activity_voice_audio['used_device'] = 'mobile'

    def parse_voice_audio(case):
        file_path = case.takeout_my_activity_voice_audio_path

        if not os.path.exists(file_path):
            return False

        result = []
        with open(file_path, 'r', encoding='utf-8') as f:
            file_contents = f.read()
            soup = BeautifulSoup(file_contents, 'lxml')
            list_voice_audio_logs = TakeoutHtmlParser.find_log(soup)

            if list_voice_audio_logs:
                for i in range(len(list_voice_audio_logs)):
                    dic_my_activity_voice_audio = {'service':"", 'type':"", 'keyword_url':"", 'keyword':"", 'timestamp':"", 'attachment':"", 'used_device':""}
                    MyActivityVoiceAudio.parse_voice_audio_log_title(dic_my_activity_voice_audio, list_voice_audio_logs[i])
                    MyActivityVoiceAudio.parse_voice_audio_log_body(dic_my_activity_voice_audio, list_voice_audio_logs[i])
                    MyActivityVoiceAudio.parse_voice_audio_log_body_text(dic_my_activity_voice_audio, list_voice_audio_logs[i], file_path)

                    result.append((dic_my_activity_voice_audio['timestamp'], dic_my_activity_voice_audio['service'], dic_my_activity_voice_audio['type'],
                                   dic_my_activity_voice_audio['keyword'], dic_my_activity_voice_audio['keyword_url'], dic_my_activity_voice_audio['attachment'],
                                   dic_my_activity_voice_audio['used_device']))

        return result
