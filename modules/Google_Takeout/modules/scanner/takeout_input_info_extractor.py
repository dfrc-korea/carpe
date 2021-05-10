import os
import logging

logger = logging.getLogger('gtForensics')

TAKEOUT_DATA_PATH = os.getcwd() + os.sep + 'config' + os.sep + 'TAKEOUT_DATA_PATH.conf'

class InputDataInfo(object):
	def get_list_takeout_file_path_information():
		if os.path.exists(TAKEOUT_DATA_PATH) == False:
			logger.error('Not exist the config (\"%s\").' % TAKEOUT_DATA_PATH)
			return False

		with open(TAKEOUT_DATA_PATH, 'r') as f:
			list_takeout_file_path = []
			for line in f:
				if (line.startswith("#") == True) | (line == "\n"):    continue
				line = line.replace("\t", "")
				line = line.replace("\n", "")

				# print(line)
				list_item = line.split(",")
				print('len: %d' % len(list_item))

				takeout_file_path = []
				for item in list_item:
					item = item.lstrip()
					item = item.rstrip()
					print(item)

					# takeout_file_path += item + os.sep

				print(takeout_file_path)

				list_takeout_file_path.append(takeout_file_path)

					# item.lstrip()
					# item.rstrip()
					# print(item)

			# line = f.readline()
			# print(line)


	def find_takeout_file_path(case):
		if os.path.exists(case.takeout_path) == False:
			print(case.takeout_path)
			logger.error('Takeout data not exist.')
			return False

		# InputDataInfo.get_list_takeout_file_path_information()


		takout_service_dirs = os.listdir(case.takeout_path)
		if takout_service_dirs == []:
			logger.error('Takeout data not exist.')
			return False

		# print(takout_service_dirs)
		# for takeout_service_path in takout_service_dirs:



		# 	print(takeout_service_path)





# if os.path.exists(case.takeout_archive_browser_path):
		# 	print("[!] find archive_browser.html file.")


