import os
from .takeout_sqlite3 import SQLite3
import multiprocessing

CONTACTS = 'Contacts' + os.sep + 'All Contacts' + os.sep + 'All Contacts.vcf'
DRIVE = 'Drive'

MY_ACTIVITY_ASSISTANT_PATH = 'My Activity' + os.sep + 'Assistant' + os.sep + 'MyActivity.html'
MY_ACTIVITY_GMAIL_PATH = 'My Activity' + os.sep + 'Gmail' + os.sep + 'MyActivity.html'
MY_ACTIVITY_GOOGLE_ANALYTICS_PATH = 'My Activity' + os.sep + 'Google Analytics' + os.sep + 'MyActivity.html'
MY_ACTIVITY_YOUTUBE_PATH = 'My Activity' + os.sep + 'YouTube' + os.sep + 'MyActivity.html'
MY_ACTIVITY_VIDEO_SEARCH_PATH = 'My Activity' + os.sep + 'Video Search' + os.sep + 'MyActivity.html'
MY_ACTIVITY_VOICE_AUDIO_PATH = 'My Activity' + os.sep + 'Voice and Audio' + os.sep + 'MyActivity.html'
MY_ACTIVITY_MAPS_PATH = 'My Activity' + os.sep + 'Maps' + os.sep + 'MyActivity.html'
MY_ACTIVITY_ANDROID_PATH = 'My Activity' + os.sep + 'Android' + os.sep + 'MyActivity.html'
MY_ACTIVITY_CHROME_PATH = 'My Activity' + os.sep + 'Chrome' + os.sep + 'MyActivity.html'


class Case(object):
	def __init__(self, input_dir):
		self.number_of_system_processes = 1
		self.number_of_input_processes = 1
		self.input_dir_path = input_dir

		self.set_file_path()

	def set_file_path(self):
		if self.input_dir_path[-1] == os.sep:
			self.input_dir_path = self.input_dir_path[:-1]

		self.takeout_path = self.input_dir_path + os.sep + 'Takeout'
		if not os.path.exists(self.takeout_path):
			return False

		self.takeout_contacts_path = self.takeout_path + os.sep + CONTACTS
		self.takeout_drive_path = self.takeout_path + os.sep + DRIVE
		self.takeout_my_activity_assistant_path = self.takeout_path + os.sep + MY_ACTIVITY_ASSISTANT_PATH
		self.takeout_my_activity_gmail_path = self.takeout_path + os.sep + MY_ACTIVITY_GMAIL_PATH
		self.takeout_my_activity_google_analytics_path = self.takeout_path + os.sep + MY_ACTIVITY_GOOGLE_ANALYTICS_PATH
		self.takeout_my_activity_youtube_path = self.takeout_path + os.sep + MY_ACTIVITY_YOUTUBE_PATH
		self.takeout_my_activity_video_search_path = self.takeout_path + os.sep + MY_ACTIVITY_VIDEO_SEARCH_PATH
		self.takeout_my_activity_voice_audio_path = self.takeout_path + os.sep + MY_ACTIVITY_VOICE_AUDIO_PATH
		self.takeout_my_activity_maps_path = self.takeout_path + os.sep + MY_ACTIVITY_MAPS_PATH
		self.takeout_my_activity_android_path = self.takeout_path + os.sep + MY_ACTIVITY_ANDROID_PATH
		self.takeout_my_activity_chrome_path = self.takeout_path + os.sep + MY_ACTIVITY_CHROME_PATH
