import os
import logging
from modules.andForensics.modules.analyzer.android_data_analyzer_application_list import ApplicationList
from modules.andForensics.modules.analyzer.android_data_analyzer_id_pw import ID_PW_HASH
from modules.andForensics.modules.analyzer.android_data_analyzer_call_history import CallHistory
from modules.andForensics.modules.analyzer.android_data_analyzer_geodata import Geodata
from modules.andForensics.modules.analyzer.android_data_analyzer_web_browser_history import WebBrowserHistory
from modules.andForensics.modules.analyzer.android_data_analyzer_file_history import FileHistory
from modules.andForensics.modules.analyzer.android_data_analyzer_embedded_file import EmbeddedFile

logger = logging.getLogger('andForensics')

class DataAnalyzer(object):
	def analyze_files(case):
		logger.info('    - Analyze the embedded data...')
		EmbeddedFile.analyze_embedded_file(case)

#---------------------------------------------------------------------------------------------------------------
	def analyze_application_log(case):
		logger.info('    - Analyze the ID and Password data...')
		ID_PW_HASH.analyze_id_pw(case)

		logger.info('    - Analyze the call history data...')
		CallHistory.analyze_with_preprocess_db(case)

		logger.info('    - Analyze the geodata...')
		Geodata.analyze_with_preprocess_db(case)

		logger.info('    - Analyze the web browser history data...')
		WebBrowserHistory.analyze_with_preprocess_db(case)

		logger.info('    - Analyze the file history data...')
		FileHistory.analyze_with_preprocess_db(case)

#---------------------------------------------------------------------------------------------------------------
	def analyze_system_log(case):
		logger.info('    - Analyze the application list...')
		ApplicationList.analyze_applist(case)


