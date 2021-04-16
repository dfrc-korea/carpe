from .takeout_parse_contacts import Contacts
from .takeout_parse_drive import Drive

from .takeout_parse_myactivity_android import MyActivityAndroid
from .takeout_parse_myactivity_assistant import MyActivityAssistant
from .takeout_parse_myactivity_gmail import MyActivityGmail
from .takeout_parse_myactivity_chrome import MyActivityChrome
from .takeout_parse_myactivity_google_analytics import MyActivityGoogleAnalytics
from .takeout_parse_myactivity_maps import MyActivityMaps
from .takeout_parse_myactivity_video_search import MyActivityVideoSearch
from .takeout_parse_myactivity_voice_audio import MyActivityVoiceAudio
from .takeout_parse_myactivity_youtube import MyActivityYouTube


class DataParser(object):
	def parse_takeout_data(case):
		result = {}

		result['Contacts'] = Contacts.parse_contacts(case)
		result['Drive'] = Drive.parse_drive(case)
		result['myAndroid'] = MyActivityAndroid.parse_android(case)
		result['myAssistant'] = MyActivityAssistant.parse_assistant(case)
		result['myGmail'] = MyActivityGmail.parse_gmail(case)
		result['myChrome'] = MyActivityChrome.parse_chrome(case)
		result['myGoogleAnalytics'] = MyActivityGoogleAnalytics.parse_google_analytics(case)
		result['myMap'] = MyActivityMaps.parse_maps(case)
		result['myVideoSearch'] = MyActivityVideoSearch.parse_video_search(case)
		result['myVoiceAudio'] = MyActivityVoiceAudio.parse_voice_audio(case)
		result['myYouTube'] = MyActivityYouTube.parse_youtube(case)

		return result
