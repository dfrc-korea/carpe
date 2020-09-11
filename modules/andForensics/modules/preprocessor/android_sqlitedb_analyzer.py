#-*- coding: utf-8 -*-
import os
import logging
import math
from modules.andForensics.modules.utils.android_sqlite3 import SQLite3
from multiprocessing import Process, Queue, Lock
import sqlite3
import binascii
import base64
import time
import re
import sys


logger = logging.getLogger('andForensics')
logging.basicConfig(format = '[%(asctime)s] [%(levelname)s] %(message)s', stream = sys.stdout)


UNIXTIME_1YEAR	= 31536000
# UNIXTIME_START 	= 1262304000 # 2010-01-01 00:00:00 (GMT 0)
UNIXTIME_START	= 1199145600 # 2008-01-01 00:00:00 (GMT 0)
UNIXTIME_END	= 1609459199 # 2020-12-31 11:59:59 (GMT 0)

PHONENUM_LENGTH_MIN = 7
# PHONENUM_LENGTH_MAX = 31
PHONENUM_LENGTH_MAX = 15
LATITUDE_START 	= 31
LATITUDE_END 	= 40
LONGITUDE_START = 123
LONGITUDE_END 	= 133

#USER_INFO_TYPE_COL_NAME_CONF_PATH = os.getcwd() + os.sep + 'config' + os.sep + 'USER_INFO_TYPE_COL_NAME.conf'
USER_INFO_TYPE_COL_NAME_CONF_PATH = '/home/byeongchan/modules/andForensics/config/USER_INFO_TYPE_COL_NAME.conf'
LIST_USER_INFO_TIMESTAMP = list()
LIST_USER_INFO_TIMEDURATION = list()
LIST_USER_INFO_ID_ACCOUNT = list()
LIST_USER_INFO_ID_ADDRESS = list()
LIST_USER_INFO_ID_PHONENUMBER = list()
LIST_USER_INFO_URL = list()
LIST_USER_INFO_GEODATA = list()
LIST_USER_INFO_FILE = list()
LIST_USER_INFO_PASSWORD = list()
LIST_USER_INFO_CIPHER = list()
LIST_USER_INFO_PACKAGE = list()

## Column value type
CONTENTS_DIGIT_POSITIVE	= 1
CONTENTS_DIGIT_NEGATIVE	= 2
CONTENTS_FLOAT_POSITIVE	= 3
CONTENTS_FLOAT_NEGATIVE	= 4
CONTENTS_ALPHA			= 5
# CONTENTS_ALPHANUM		= 6
CONTETNS_BYTES			= 8
CONTENTS_UNKNOWN		= 10

## User information type
USER_INFO_TYPE_UNKNOWN			= -1
USER_INFO_TYPE_TIMESTAMP		= 1
USER_INFO_TYPE_TIMEDURATION		= 2
USER_INFO_TYPE_ID_PHONENUMBER	= 3
USER_INFO_TYPE_ID_ACCOUNT		= 4
USER_INFO_TYPE_ID_IPADDRESS		= 5
USER_INFO_TYPE_ID_MACADDRESS	= 6
USER_INFO_TYPE_URL				= 7
USER_INFO_TYPE_GEODATA			= 8
USER_INFO_TYPE_FILE				= 9
USER_INFO_TYPE_CONTENTS			= 10
USER_INFO_TYPE_PASSWORD			= 11
USER_INFO_TYPE_CIPHER			= 12

## User information format per type
TIME_FORMAT_UNIXTIME				= "unixtime"
TIME_FORMAT_UNIXTIME_MILLISEC		= "unixtime_millisec"
TIME_FORMAT_UNIXTIME_MICROSEC		= "unixtime_microsec"
TIME_FORMAT_UNIXTIME_NANOSEC		= "unixtime_nanosec"
TIME_FORMAT_CHROMETIME				= "chrometime"
TIME_FORMAT_DATETIME_YYYYMMDD		= "datetime_yyyymmdd"
TIME_FORMAT_DATETIME_YYYYMMDDHHMMSS	= "datetime_yyyymmddhhmmss"
TIME_FORMAT_DATETIME_TEXT			= "datetime_text"
TIME_FORMAT_DURATION_INT			= "time_duration"
ID_FORMAT_EMAIL						= "id_email"
ID_FORMAT_PHONENUMBER				= "id_phonenumber"
ID_FORMAT_IPADDRESS					= "id_ip_address"
ID_FORMAT_MACADDRESS				= "id_mac_address"
URL_FORMAT_HTTP						= "url_http"
GEODATA_FORMAT_LATITUDE				= "latitude"
GEODATA_FORMAT_LONGITUDE			= "longitude"
FILE_FORMAT_SIZE					= "file_size"
FILE_FORMAT_PATH					= "file_path"
FILE_FORMAT_URI						= "file_uri"
# CONTENTS_FORMAT_UNKNOWN     	= "unknown"
CONTENTS_FORMAT_STRING				= "string"			# CONTENTS_ALPHA
CONTENTS_FORMAT_STRING_NUM			= "string_num"		# CONTENTS_ALPHA + NUMBER
CONTENTS_FORMAT_STRING_NUM_MIXED	= "string_num_mixed"
CONTENTS_FORMAT_DIGIT_POSITIVE		= "digit_positive"	# CONTENTS_DIGIT_POSITIVE
CONTENTS_FORMAT_DIGIT_NEGATIVE		= "digit_negative"	# CONTENTS_DIGIT_NEGATIVE
CONTENTS_FORMAT_FLOAT_POSITIVE 		= "float_positive"	# CONTENTS_FLOAT_POSITIVE
CONTENTS_FORMAT_FLOAT_NEGATIVE 		= "float_negative"	# CONTENTS_FLOAT_NEGATIVE
CONTENTS_FORMAT_BIN	      			= "bianry"			# CONTETNS_BYTES
CONTENTS_FORMAT_PACKAGE    			= "package"			
# CONTENTS_FORMAT_BASE64     			= "base64"
CONTENTS_FORMAT_UNKNOWN				= "unknown"
PASSWORD_FORMAT_PASSWORD			= "password"
# PASSWORD_FORMAT_CREDENTIAL			= "credential"
CIPHER_FORMAT_HASH					= "hash"

## RE
RE_DATETIME_INT8_YYYYMMDD			= '^(20[0-9]{2})([0-1]{1}[0-9]{1})([0-3]{1}[0-9]{1})$'
RE_DATETIME_INT14_YYYYMMDDHHMMSS	='^(20[0-9]{2})([0-1]{1}[0-9]{1})([0-3]{1}[0-9]{1})([0-2]{1}[0-9]{1})([0-5]{1}[0-9]{1})([0-5]{1}[0-9]{1})$'

RE_DATETIME_TEXT 		= '^\d{4}[/:-]*[.]*\d{2}[/:-]*[.]*\d{2}.\d{2}[/:-]*[.]*\d{2}[/:-]*[.]*\d{2}'
RE_DATETIME_TEXT2 		= '^\d{4}[/:-]*[.]*\d{2}[/:-]*[.]*\d{2}'

RE_SPECIALCHAR = '[=+,#/\?^$@*\"※~&%ㆍ!{}』\\‘|\(\)\[\]\<\>`\'…》]'
# RE_EMAIL        = '^[a-zA-Z0-9.!#$%&\'*+\/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*'
# RE_EMAIL        = '^[a-zA-Z0-9.!#$%&\'*+\/=?^_`{|}~-]+@[A-Z0-9.-]+\.[A-Z]{2,}$'
RE_EMAIL = '^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'

RE_PHONENUM     = '^0?\d{7,10}$'
RE_PHONENUM2    = '^0?10\d{8}$'
RE_PHONENUM3     = '^\d{2,3}0?10\d{8}$'
RE_PHONENUM4     = '^\d{2,3}0?\d{7,10}$'

RE_IP_ADDRESS   = '^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$'
RE_MAC_ADDRESS = '^[\d\w]{2}\:[\d\w]{2}\:[\d\w]{2}\:[\d\w]{2}\:[\d\w]{2}\:[\d\w]{2}'
RE_URL          = '^(https?:\/\/)'
RE_URL2          = '^(https?:\/\/)?([a-z\d\.-]+)\.([a-z\.]{2,6})([\/\w\.-]*)*\/?$'
RE_PACKAGENAME = '^[a-zA-Z0-9]*\.[a-zA-Z0-9]*.?[a-zA-Z0-9]*.?[a-zA-Z0-9]*.?[a-zA-Z0-9]*.?[a-zA-Z0-9]*.?[a-zA-Z0-9]*.?[a-zA-Z0-9]*$'

class SQLiteAnalyzer(object):
	def exception_rule_column_type(col_name, col_type_sqlite):
		if (col_type_sqlite == "BOOLEAN") | (col_type_sqlite == "BIT"):
			return True
		return False

#---------------------------------------------------------------------------------------------------------------
	def exception_rule_table_column(table_name, col_name):
		if ((table_name == "raw_contacts") & (col_name == "sort_key")) | ((table_name == "raw_contacts") & (col_name == "sort_key_alt")):
			return True
		if (table_name == "contacts") & (col_name == "phone_numbers"):
			return True
		# if (col_name == "usage_time") | (col_name == "id") | (col_name == "_id"):
		if (col_name == "id") | (col_name == "_id"):
			return True
		if (table_name == "INFOALARM_WEATHER_CITY"):
			return True
		return False

#---------------------------------------------------------------------------------------------------------------
	def exception_rule_db_table(db_name, table_name):
		if (db_name == "telephony.db") & (table_name == "carriers"):
			return True
		if db_name == "roadplus_data.sqlite":
			return True
		return False

#---------------------------------------------------------------------------------------------------------------
	def exception_rule_contents(col_name, col_value, col_value_size, col_value_type):
		if col_value_size <= 3:
			return True
		if (col_value == "") | (col_value == 0) | (col_value == None) | (col_value == "0") | (col_value == "1") :
			return True
		if col_value_type == CONTENTS_FLOAT_POSITIVE:
			col_value = str(col_value)
			col_value_l = int(col_value.split(".")[0])
			col_value_r = col_value.split(".")[1]
			if len(col_value_r) <= 10:
				col_value_r = int(col_value_r)
				if (col_value_r == 0) & (col_value_l == 0):
					return True
				else:
					return False
			else:
				return False
		# if (col_value.upper() == "TRUE") | (col_value.upper() == "FALSE"):
		# 	return True
		if (col_value_type == CONTENTS_DIGIT_NEGATIVE) | (col_value_type == CONTENTS_FLOAT_NEGATIVE):
			return True
		if ("_ID" in col_name.upper()) & (col_value_type == CONTENTS_DIGIT_POSITIVE):
			return True
		if (col_name[-2:].upper() == "ID") & (col_value_type == CONTENTS_DIGIT_POSITIVE):
			return True
		if col_value_type == CONTENTS_ALPHA:
			if (col_value.upper() == "TRUE") | (col_value.upper() == "FALSE") | (col_value.upper() == "NULL") | (col_value.upper() == "NONE"):
				return True
			else:
				return False
		return False

#---------------------------------------------------------------------------------------------------------------
	def isBase64(data):
	    try:
	        return base64.b64encode(base64.b64decode(data)).decode('utf-8') == data
	    except Exception:
	        return False

#---------------------------------------------------------------------------------------------------------------
	def Base64Decode(data):
		try:
			return base64.b64decode(data).decode('utf-8')
		except Exception:
			return base64.b64decode(data).decode('utf-16')

#---------------------------------------------------------------------------------------------------------------
	def check_col_value_info(col_value):
		col_value_type = type(col_value)
		if col_value_type == int:
			col_value_size = len(str(col_value))
			if col_value < 0:
				return col_value, col_value_size-1, CONTENTS_DIGIT_NEGATIVE
			else:
				return col_value, col_value_size, CONTENTS_DIGIT_POSITIVE
		elif col_value_type == float:
			col_value_size = len(str(col_value))
			if col_value < 0:
				return col_value, col_value_size-1, CONTENTS_FLOAT_NEGATIVE
			else:
				return col_value, col_value_size, CONTENTS_FLOAT_POSITIVE
		elif col_value_type == bytes:
			col_value_size = len(col_value)
			return col_value, col_value_size, CONTETNS_BYTES
		else: # str, depends on text_factory, str by default
			col_value = "%s" % col_value
			col_value_size = len(col_value)

			if col_value.isdigit(): 
				col_value = int(col_value)
				return col_value, col_value_size, CONTENTS_DIGIT_POSITIVE
			elif col_value.isalpha():
				return col_value, col_value_size, CONTENTS_ALPHA
			else:
				if col_value.startswith("-"): # negative digit (int, long)
					if col_value.lstrip('-').isdigit(): 
						col_value = int(col_value)
						return col_value, col_value_size-1, CONTENTS_DIGIT_NEGATIVE
					elif col_value.lstrip('-').replace('.', '', 1).isdigit():
						col_value = float(col_value)
						return col_value, col_value_size-1, CONTENTS_FLOAT_NEGATIVE
					else:
						return col_value, col_value_size, CONTENTS_UNKNOWN
				else:
					if col_value.replace('.', '', 1).isdigit():
						col_value = float(col_value)
						return col_value, col_value_size, CONTENTS_FLOAT_POSITIVE
					else:
						return col_value, col_value_size, CONTENTS_UNKNOWN

#---------------------------------------------------------------------------------------------------------------
	def get_col_value(table_name, col_name, col_type_sqlite, sqlite_file_path, cnt):
		query = 'SELECT "%s" FROM "%s" ORDER BY "%s" DESC LIMIT %d' % (col_name, table_name, col_name, cnt)
		query2 = 'SELECT "%s" FROM "%s" LIMIT %d' % (col_name, table_name, cnt)
		return SQLite3.execute_fetch_query_multi_values_order(query, query2, sqlite_file_path)

#---------------------------------------------------------------------------------------------------------------
	def get_user_info_type():
		if os.path.exists(USER_INFO_TYPE_COL_NAME_CONF_PATH) == False:
			logger.error('Not exist the config file (\"%s\").' % USER_INFO_TYPE_COL_NAME_CONF_PATH)
			return False
		try:
			f = open(USER_INFO_TYPE_COL_NAME_CONF_PATH, 'r')
		except Exception as e:
			logger.error("Fail to open file [%s]" % USER_INFO_TYPE_COL_NAME_CONF_PATH)
			return False

		while True:
			line = f.readline()
			if not line: break
			line = line.strip()
			line = line.rstrip()
			if (line.startswith("#") == True) | (line == ""):    continue
			line = line.replace(" ", "")
			line = line.replace("\t", "")
			line = line.replace("\n", "")
			info_type = str(line.split(",")[0]).upper()
			info_keyword = str(line.split(",")[3]).upper()

			if info_type == "TIMESTAMP":
				LIST_USER_INFO_TIMESTAMP.append(info_keyword)
			elif info_type == "TIMEDURATION":
				LIST_USER_INFO_TIMEDURATION.append(info_keyword)
			elif info_type == "ID_ACCOUNT":
				LIST_USER_INFO_ID_ACCOUNT.append(info_keyword)
			elif info_type == "ID_ADDRESS":
				LIST_USER_INFO_ID_ADDRESS.append(info_keyword)
			elif info_type == "ID_PHONENUMBER":
				LIST_USER_INFO_ID_PHONENUMBER.append(info_keyword)
			elif info_type == "URL":
				LIST_USER_INFO_URL.append(info_keyword)
			elif info_type == "GEODATA":
				LIST_USER_INFO_GEODATA.append(info_keyword)
			elif info_type == "FILE":
				LIST_USER_INFO_FILE.append(info_keyword)
			elif info_type == "PASSWORD":
				LIST_USER_INFO_PASSWORD.append(info_keyword)
			elif info_type == "CIPHER":
				LIST_USER_INFO_CIPHER.append(info_keyword)
			elif info_type == "PACKAGE":
				LIST_USER_INFO_PACKAGE.append(info_keyword)
		f.close()

#---------------------------------------------------------------------------------------------------------------
	def searching_timestamp_int(col_value, col_value_size, col_value_type, sqlite_file_path, table_name, col_name):
		# print("col_value: %s, db: %s, table_name: %s, col_name: %s" % (col_value, sqlite_file_path, table_name, col_name))
		if (col_value_size < 8) | (col_value_size > 19):
			return USER_INFO_TYPE_UNKNOWN, col_value_type, col_value_size
		if col_value_size == 8: # YYYYMMDD
			col_value = "%s" % col_value
			if re.match(RE_DATETIME_INT8_YYYYMMDD, col_value):
				return USER_INFO_TYPE_TIMESTAMP, TIME_FORMAT_DATETIME_YYYYMMDD
			else:
				return USER_INFO_TYPE_UNKNOWN, CONTENTS_DIGIT_POSITIVE, col_value_size
		elif col_value_size == 10: # unixtime or phonenumber
			if (int(col_value) < UNIXTIME_START) | (int(col_value) > int(time.time())): # not timestamp
				if "EXPIR" in col_name.upper():
					return USER_INFO_TYPE_TIMESTAMP, TIME_FORMAT_UNIXTIME
				else:
					return USER_INFO_TYPE_UNKNOWN, CONTENTS_DIGIT_POSITIVE, col_value_size
			else:
				return USER_INFO_TYPE_TIMESTAMP, TIME_FORMAT_UNIXTIME
		elif col_value_size == 13: # unixtime_millsec
			if (int(col_value)/1000 < UNIXTIME_START) | (int(col_value)/1000 > int(time.time())): # not timestamp
				if "EXPIR" in col_name.upper():
					return USER_INFO_TYPE_TIMESTAMP, TIME_FORMAT_UNIXTIME_MILLISEC
				else:
					return USER_INFO_TYPE_UNKNOWN, CONTENTS_DIGIT_POSITIVE, col_value_size
			else:
				return USER_INFO_TYPE_TIMESTAMP, TIME_FORMAT_UNIXTIME_MILLISEC
		elif col_value_size == 14: # YYYYMMDDHHMMSS
			col_value = "%s" % col_value
			if re.match(RE_DATETIME_INT14_YYYYMMDDHHMMSS, col_value):
				return USER_INFO_TYPE_TIMESTAMP, TIME_FORMAT_DATETIME_YYYYMMDDHHMMSS
			else:
				return USER_INFO_TYPE_UNKNOWN, CONTENTS_DIGIT_POSITIVE, col_value_size
		elif col_value_size == 16: # unixtime_microsec
			if (int(col_value)/1000000 < UNIXTIME_START) | (int(col_value)/1000000 > int(time.time())): # not timestamp
				if "EXPIR" in col_name.upper():
					return USER_INFO_TYPE_TIMESTAMP, TIME_FORMAT_UNIXTIME_MICROSEC	
				else:
					return USER_INFO_TYPE_UNKNOWN, CONTENTS_DIGIT_POSITIVE, col_value_size
			else:
				return USER_INFO_TYPE_TIMESTAMP, TIME_FORMAT_UNIXTIME_MICROSEC
		elif col_value_size == 17: # chrome time (chrome app)			
			if (int(col_value)/1000000-11644473600 < UNIXTIME_START) | (int(col_value)/1000000-11644473600 > int(time.time())): # not timestamp
				if "EXPIR" in col_name.upper():					
					return USER_INFO_TYPE_TIMESTAMP, TIME_FORMAT_CHROMETIME
				else:
					return USER_INFO_TYPE_UNKNOWN, CONTENTS_DIGIT_POSITIVE, col_value_size
			else:
				return USER_INFO_TYPE_TIMESTAMP, TIME_FORMAT_CHROMETIME
		elif col_value_size == 19: # unixtime_nanosec
			if (int(col_value)/1000000000 < UNIXTIME_START) | (int(col_value)/1000000000 > int(time.time())): # not timestamp
				if "EXPIR" in col_name.upper():
					return USER_INFO_TYPE_TIMESTAMP, TIME_FORMAT_UNIXTIME_NANOSEC
				else:
					return USER_INFO_TYPE_UNKNOWN, CONTENTS_DIGIT_POSITIVE, col_value_size
			else:
				return USER_INFO_TYPE_TIMESTAMP, TIME_FORMAT_UNIXTIME_NANOSEC
		else:
			return USER_INFO_TYPE_UNKNOWN, CONTENTS_DIGIT_POSITIVE, col_value_size

#---------------------------------------------------------------------------------------------------------------
	def searching_timestamp(col_value, col_value_size, col_value_type, sqlite_file_path, table_name, col_name):
		# print("col_value: %s, db: %s, table_name: %s, col_name: %s" % (col_value, sqlite_file_path, table_name, col_name))
		if (col_value_size < 8) | (col_value_size > 25):
			return USER_INFO_TYPE_UNKNOWN, col_value_type, col_value_size
		elif (col_value_type == CONTENTS_DIGIT_POSITIVE):
			col_value = "%s" % col_value
			return SQLiteAnalyzer.searching_timestamp_int(col_value, col_value_size, col_value_type, sqlite_file_path, table_name, col_name)
		elif col_value_type == CONTENTS_FLOAT_POSITIVE:
			col_value = math.trunc(col_value)
			col_value_size = len(str(col_value))
			return SQLiteAnalyzer.searching_timestamp_int(col_value, col_value_size, col_value_type, sqlite_file_path, table_name, col_name)
		elif col_value_type == CONTENTS_UNKNOWN:
			if re.search(RE_SPECIALCHAR, col_value):
				return USER_INFO_TYPE_UNKNOWN, col_value_type, col_value_size
			if re.match(RE_DATETIME_TEXT, col_value):
				return USER_INFO_TYPE_TIMESTAMP, TIME_FORMAT_DATETIME_TEXT
			elif re.match(RE_DATETIME_TEXT2, col_value):
				return USER_INFO_TYPE_TIMESTAMP, TIME_FORMAT_DATETIME_TEXT
			else:
				return USER_INFO_TYPE_UNKNOWN, col_value_type, col_value_size
		else:
			return USER_INFO_TYPE_UNKNOWN, col_value_type, col_value_size

#---------------------------------------------------------------------------------------------------------------
	def searching_timeduration(col_value, col_value_size, col_value_type, sqlite_file_path, table_name, col_name):
		if col_value_type == CONTENTS_DIGIT_POSITIVE:
			return USER_INFO_TYPE_TIMEDURATION, TIME_FORMAT_DURATION_INT
		else:
			return USER_INFO_TYPE_UNKNOWN, col_value_type, col_value_size

#---------------------------------------------------------------------------------------------------------------
	def searching_id_account(col_value, col_value_size, col_value_type, sqlite_file_path, table_name, col_name):
		if (col_value_size > 50) | (col_value_size < 10):
			return USER_INFO_TYPE_UNKNOWN, col_value_type, col_value_size
		elif col_value_type == CONTENTS_DIGIT_POSITIVE:
			return SQLiteAnalyzer.searching_id_phonenumber(col_value, col_value_size, col_value_type, sqlite_file_path, table_name, col_name)
		elif col_value_type == CONTENTS_UNKNOWN:
			# if (col_value.count("@") != 1) | (col_value.find(" ") >= 1):
			if (col_value.count("@") == 1) & (col_value.count(" ") == 0):
				if re.search(RE_EMAIL, col_value):					
					return USER_INFO_TYPE_ID_ACCOUNT, ID_FORMAT_EMAIL
				else:
					return USER_INFO_TYPE_UNKNOWN, col_value_type, col_value_size
			else:
				return USER_INFO_TYPE_UNKNOWN, col_value_type, col_value_size
		else:
			return USER_INFO_TYPE_UNKNOWN, col_value_type, col_value_size

#---------------------------------------------------------------------------------------------------------------
	def searching_id_phonenumber_int(col_value, col_value_size, col_value_type, sqlite_file_path, table_name, col_name):
		if (col_value_size <= PHONENUM_LENGTH_MIN) | (col_value_size >= PHONENUM_LENGTH_MAX):
			return USER_INFO_TYPE_UNKNOWN, col_value_type, col_value_size
		if ("TIME" in col_name.upper()) | ("VERSION" in col_name.upper()) | ("KEY" in col_name.upper()):
			return USER_INFO_TYPE_UNKNOWN, col_value_type, col_value_size
		col_value = "%s" % col_value
		if re.match(RE_PHONENUM, col_value):
			return USER_INFO_TYPE_ID_PHONENUMBER, ID_FORMAT_PHONENUMBER
		elif re.match(RE_PHONENUM2, col_value):
			return USER_INFO_TYPE_ID_PHONENUMBER, ID_FORMAT_PHONENUMBER
		elif re.match(RE_PHONENUM3, col_value):
			return USER_INFO_TYPE_ID_PHONENUMBER, ID_FORMAT_PHONENUMBER
		elif re.match(RE_PHONENUM4, col_value):
			return USER_INFO_TYPE_ID_PHONENUMBER, ID_FORMAT_PHONENUMBER
		else:
			return USER_INFO_TYPE_UNKNOWN, col_value_type, col_value_size
	
#---------------------------------------------------------------------------------------------------------------
	def searching_id_phonenumber(col_value, col_value_size, col_value_type, sqlite_file_path, table_name, col_name):		
		if (col_value_size <= PHONENUM_LENGTH_MIN) | (col_value_size >= PHONENUM_LENGTH_MAX):
			return USER_INFO_TYPE_UNKNOWN, col_value_type, col_value_size
		elif col_value_type == CONTENTS_DIGIT_POSITIVE:
			return SQLiteAnalyzer.searching_id_phonenumber_int(col_value, col_value_size, col_value_type, sqlite_file_path, table_name, col_name)
		elif col_value_type == CONTENTS_UNKNOWN:
			if col_value.count("-") >= 2:
				col_value = col_value.replace("-", "")
				if col_value.isdigit(): # 82-123-4567
					return SQLiteAnalyzer.searching_id_phonenumber_int(col_value, col_value_size, col_value_type, sqlite_file_path, table_name, col_name)
				elif (col_value.startswith("+")) & (col_value.count("+") == 1): # +82-123-4567
					col_value = col_value.replace("+", "")
					if col_value.isdigit(): 
						return SQLiteAnalyzer.searching_id_phonenumber_int(col_value, col_value_size, col_value_type, sqlite_file_path, table_name, col_name)
					else:
						return USER_INFO_TYPE_UNKNOWN, col_value_type, col_value_size
				else:
					return USER_INFO_TYPE_UNKNOWN, col_value_type, col_value_size
			elif (col_value.startswith("+")) & (col_value.count("+") == 1): # +821234567
				col_value = col_value.replace("+", "")
				if col_value.isdigit(): 
					return SQLiteAnalyzer.searching_id_phonenumber_int(col_value, col_value_size, col_value_type, sqlite_file_path, table_name, col_name)
				else:
					return USER_INFO_TYPE_UNKNOWN, col_value_type, col_value_size
			# elif re.match(RE_EMAIL, col_value):
			# 	return USER_INFO_TYPE_ID_ACCOUNT, ID_FORMAT_EMAIL
			elif (col_value.count("@") == 1) & (col_value.count(" ") == 0):
				# if re.search(RE_EMAIL, col_value):
				if re.search(RE_EMAIL, col_value):
					return USER_INFO_TYPE_ID_ACCOUNT, ID_FORMAT_EMAIL
				if re.search(RE_SPECIALCHAR, col_value):
					return USER_INFO_TYPE_UNKNOWN, col_value_type, col_value_size
				else:
					return USER_INFO_TYPE_UNKNOWN, col_value_type, col_value_size

			# elif (col_value.count("@") != 1) | (col_value.count(" ") >= 1):
			# 	return USER_INFO_TYPE_UNKNOWN, col_value_type, col_value_size
			else:
				return USER_INFO_TYPE_UNKNOWN, col_value_type, col_value_size
		else:
			return USER_INFO_TYPE_UNKNOWN, col_value_type, col_value_size

#---------------------------------------------------------------------------------------------------------------
	def searching_address(col_value, col_value_size, col_value_type, sqlite_file_path, table_name, col_name):
		if col_value_type == CONTENTS_UNKNOWN:
			col_value = "%s" % col_value
			if col_value.count('.') == 3:
				if re.match(RE_IP_ADDRESS, col_value):
					return USER_INFO_TYPE_ID_IPADDRESS, ID_FORMAT_IPADDRESS
				else:
					return USER_INFO_TYPE_UNKNOWN, col_value_type, col_value_size
			elif (col_value.count(":") == 5) & (len(col_value) <= 20):
				if re.match(RE_MAC_ADDRESS, col_value):
					return USER_INFO_TYPE_ID_MACADDRESS, ID_FORMAT_MACADDRESS
				else:
					return USER_INFO_TYPE_UNKNOWN, col_value_type, col_value_size
			else:
				return USER_INFO_TYPE_UNKNOWN, col_value_type, col_value_size
		else:
			return USER_INFO_TYPE_UNKNOWN, col_value_type, col_value_size

#---------------------------------------------------------------------------------------------------------------
	def searching_url(col_value, col_value_size, col_value_type, sqlite_file_path, table_name, col_name):
		if col_value_type == CONTENTS_UNKNOWN:
			if (col_value_size < 15):
				return USER_INFO_TYPE_UNKNOWN, col_value_type, col_value_size			
			if col_value.upper().startswith("HTTP"):
				return USER_INFO_TYPE_URL, URL_FORMAT_HTTP
			elif col_value.upper().startswith("WWW."):
				return USER_INFO_TYPE_URL, URL_FORMAT_HTTP			
			elif re.search(RE_URL, col_value):
				return USER_INFO_TYPE_URL, URL_FORMAT_HTTP
			else:
				return USER_INFO_TYPE_UNKNOWN, col_value_type, col_value_size			
		else:
			return USER_INFO_TYPE_UNKNOWN, col_value_type, col_value_size

#---------------------------------------------------------------------------------------------------------------
	def searching_geodata(col_value, col_value_size, col_value_type, sqlite_file_path, table_name, col_name):
		if col_value_type == CONTENTS_FLOAT_POSITIVE:
			col_value = "%s" % col_value
			data = col_value.split('.')[0]
			if data.isdigit():
				data = float(data)
				if (data >= LONGITUDE_START) & (data <= LONGITUDE_END):
					return USER_INFO_TYPE_GEODATA, GEODATA_FORMAT_LONGITUDE
				elif (data >= LATITUDE_START) & (data <= LATITUDE_END):
					return USER_INFO_TYPE_GEODATA, GEODATA_FORMAT_LATITUDE
				else:
					return USER_INFO_TYPE_UNKNOWN, col_value_type, col_value_size
			else:
				return USER_INFO_TYPE_UNKNOWN, col_value_type, col_value_size
		elif col_value_type == CONTENTS_DIGIT_POSITIVE:
			if "LATITUDE" in col_name.upper():
				if col_value_size >=2:
					col_value = "%s" % col_value
					data = int(col_value[:2])
					if (data >= -90) & (data <= 90):
						return USER_INFO_TYPE_GEODATA, GEODATA_FORMAT_LATITUDE
					else:
						return USER_INFO_TYPE_UNKNOWN, col_value_type, col_value_size
				else:
					return USER_INFO_TYPE_UNKNOWN, col_value_type, col_value_size
			elif "LONGITUDE" in col_name.upper():
				if col_value_size >=3:
					col_value = "%s" % col_value
					data = int(col_value[:3])
					if (data >= -180) & (data <= 180):
						return USER_INFO_TYPE_GEODATA, GEODATA_FORMAT_LONGITUDE
					else:
						return USER_INFO_TYPE_UNKNOWN, col_value_type, col_value_size
				else:
					return USER_INFO_TYPE_UNKNOWN, col_value_type, col_value_size
			else:
				return USER_INFO_TYPE_UNKNOWN, col_value_type, col_value_size
		else:
			return USER_INFO_TYPE_UNKNOWN, col_value_type, col_value_size

#---------------------------------------------------------------------------------------------------------------
	def searching_file(col_value, col_value_size, col_value_type, sqlite_file_path, table_name, col_name):
		if (col_value_type == CONTENTS_ALPHA) | (col_value_type == CONTENTS_UNKNOWN):	# for filepath
			if "FILE_PATH" == col_name.upper():
				return USER_INFO_TYPE_FILE, FILE_FORMAT_PATH
			elif "PATH" in col_name.upper():
				# col_value = "%s" % col_value
				if (col_value.upper().startswith("/STORAGE/")) | (col_value.upper().startswith("/DATA/")) | (col_value.upper().startswith("/SYSTEM/")) | (col_value.upper().startswith("FILE:/")):
					return USER_INFO_TYPE_FILE, FILE_FORMAT_PATH
				elif col_value.count('/') >= 2:
					return USER_INFO_TYPE_FILE, FILE_FORMAT_PATH
				else:
					return USER_INFO_TYPE_UNKNOWN, col_value_type, col_value_size
			else:
				if (col_value.upper().startswith("/STORAGE/")) | (col_value.upper().startswith("/DATA/")) | (col_value.upper().startswith("/SYSTEM/")) | (col_value.upper().startswith("FILE:/")):
					return USER_INFO_TYPE_FILE, FILE_FORMAT_PATH
				elif col_value.upper().startswith("CONTENT://"):
					return USER_INFO_TYPE_FILE, FILE_FORMAT_URI
				else:
					return USER_INFO_TYPE_UNKNOWN, col_value_type, col_value_size
		elif (col_value_type == CONTENTS_DIGIT_POSITIVE) | (col_value_type == CONTENTS_FLOAT_POSITIVE):	# for file size
			return USER_INFO_TYPE_FILE, FILE_FORMAT_SIZE
		else:
			return USER_INFO_TYPE_UNKNOWN, col_value_type, col_value_size

#---------------------------------------------------------------------------------------------------------------
	def searching_password(col_value, col_value_size, col_value_type, sqlite_file_path, table_name, col_name):
		return USER_INFO_TYPE_PASSWORD, PASSWORD_FORMAT_PASSWORD

#---------------------------------------------------------------------------------------------------------------
	def searching_cipher(col_value, col_value_size, col_value_type, sqlite_file_path, table_name, col_name):
		return USER_INFO_TYPE_CIPHER, CIPHER_FORMAT_HASH

#---------------------------------------------------------------------------------------------------------------
	def searching_package(col_value, col_value_size, col_value_type, sqlite_file_path, table_name, col_name):
		if col_value_type == CONTENTS_UNKNOWN:
			if (col_value.count('.') >= 1) & (col_value.count('.') <= 7) & (col_value_size <= 60) & (col_value.count(' ') == 0):
				if re.match(RE_PACKAGENAME, col_value):
					return USER_INFO_TYPE_CONTENTS, CONTENTS_FORMAT_PACKAGE
				else:
					return USER_INFO_TYPE_UNKNOWN, col_value_type, col_value_size
			else:
				return USER_INFO_TYPE_UNKNOWN, col_value_type, col_value_size
		else:
			return USER_INFO_TYPE_UNKNOWN, col_value_type, col_value_size

#---------------------------------------------------------------------------------------------------------------
	def analyze_col_value_with_col_name(col_name, col_value, col_value_size, col_value_type, table_name, sqlite_file_path):
		# print("col_name: %s, col_value: %s" % (col_name, col_value))
		if col_name.upper() in LIST_USER_INFO_TIMESTAMP:	# match searching
			if (col_name.upper()[-2:] != "ID") & (col_name.upper()[:3] != "ID_"):
				return SQLiteAnalyzer.searching_timestamp(col_value, col_value_size, col_value_type, sqlite_file_path, table_name, col_name)
		elif col_name.upper() in LIST_USER_INFO_TIMEDURATION:
			return SQLiteAnalyzer.searching_timeduration(col_value, col_value_size, col_value_type, sqlite_file_path, table_name, col_name)
		elif col_name.upper() in LIST_USER_INFO_ID_PHONENUMBER:
			return SQLiteAnalyzer.searching_id_phonenumber(col_value, col_value_size, col_value_type, sqlite_file_path, table_name, col_name) 
		elif col_name.upper() in LIST_USER_INFO_ID_ACCOUNT:
			return SQLiteAnalyzer.searching_id_account(col_value, col_value_size, col_value_type, sqlite_file_path, table_name, col_name)
		elif col_name.upper() in LIST_USER_INFO_ID_ADDRESS:
			return SQLiteAnalyzer.searching_address(col_value, col_value_size, col_value_type, sqlite_file_path, table_name, col_name)
		elif col_name.upper() in LIST_USER_INFO_URL:
			return SQLiteAnalyzer.searching_url(col_value, col_value_size, col_value_type, sqlite_file_path, table_name, col_name)
		elif col_name.upper() in LIST_USER_INFO_GEODATA:
			return SQLiteAnalyzer.searching_geodata(col_value, col_value_size, col_value_type, sqlite_file_path, table_name, col_name)
		elif col_name.upper() in LIST_USER_INFO_FILE:
			return SQLiteAnalyzer.searching_file(col_value, col_value_size, col_value_type, sqlite_file_path, table_name, col_name)
		elif col_name.upper() in LIST_USER_INFO_PASSWORD:
			return SQLiteAnalyzer.searching_password(col_value, col_value_size, col_value_type, sqlite_file_path, table_name, col_name)
		elif col_name.upper() in LIST_USER_INFO_CIPHER:
			return SQLiteAnalyzer.searching_cipher(col_value, col_value_size, col_value_type, sqlite_file_path, table_name, col_name)
		elif col_name.upper() in LIST_USER_INFO_PACKAGE:
			return SQLiteAnalyzer.searching_package(col_value, col_value_size, col_value_type, sqlite_file_path, table_name, col_name)
		else: # include searching
			if (col_name.upper()[-2:] != "ID") & (col_name.upper()[:3] != "ID_"):
				for USER_INFO_TIMESTAMP in LIST_USER_INFO_TIMESTAMP:
					if USER_INFO_TIMESTAMP in col_name.upper():
						return SQLiteAnalyzer.searching_timestamp(col_value, col_value_size, col_value_type, sqlite_file_path, table_name, col_name)
				for USER_INFO_TIMEDURATION in LIST_USER_INFO_TIMEDURATION:
					if USER_INFO_TIMEDURATION in col_name.upper():
						return SQLiteAnalyzer.searching_timeduration(col_value, col_value_size, col_value_type, sqlite_file_path, table_name, col_name)
			for USER_INFO_ID_PHONENUMBER in LIST_USER_INFO_ID_PHONENUMBER:
				if USER_INFO_ID_PHONENUMBER in col_name.upper():
					return SQLiteAnalyzer.searching_id_phonenumber(col_value, col_value_size, col_value_type, sqlite_file_path, table_name, col_name)
			for USER_INFO_ID_ACCOUNT in LIST_USER_INFO_ID_ACCOUNT:
				if USER_INFO_ID_ACCOUNT in col_name.upper():
					return SQLiteAnalyzer.searching_id_account(col_value, col_value_size, col_value_type, sqlite_file_path, table_name, col_name)
			# if "DESCRIPTION" in col_name.upper() == False:	# don't include ip, ex: description
			for USER_INFO_ID_ADDRESS in LIST_USER_INFO_ID_ADDRESS:
				if USER_INFO_ID_ADDRESS in col_name.upper():
					return SQLiteAnalyzer.searching_address(col_value, col_value_size, col_value_type, sqlite_file_path, table_name, col_name)
			for USER_INFO_URL in LIST_USER_INFO_URL:
				if USER_INFO_URL in col_name.upper():
					return SQLiteAnalyzer.searching_url(col_value, col_value_size, col_value_type, sqlite_file_path, table_name, col_name)
			for USER_INFO_GEODATA in LIST_USER_INFO_GEODATA:
				if USER_INFO_GEODATA in col_name.upper():
					return SQLiteAnalyzer.searching_geodata(col_value, col_value_size, col_value_type, sqlite_file_path, table_name, col_name)
			for USER_INFO_FILE in LIST_USER_INFO_FILE:
				if USER_INFO_FILE in col_name.upper():
					return SQLiteAnalyzer.searching_file(col_value, col_value_size, col_value_type, sqlite_file_path, table_name, col_name)
			for USER_INFO_PASSWORD in LIST_USER_INFO_PASSWORD:
				if USER_INFO_PASSWORD in col_name.upper():
					return SQLiteAnalyzer.searching_password(col_value, col_value_size, col_value_type, sqlite_file_path, table_name, col_name)
			for USER_INFO_CIPHER in LIST_USER_INFO_CIPHER:
				if USER_INFO_CIPHER in col_name.upper():
					return SQLiteAnalyzer.searching_cipher(col_value, col_value_size, col_value_type, sqlite_file_path, table_name, col_name)
			for USER_INFO_PACKAGE in LIST_USER_INFO_PACKAGE:
				if USER_INFO_PACKAGE in col_name.upper():
					return SQLiteAnalyzer.searching_package(col_value, col_value_size, col_value_type, sqlite_file_path, table_name, col_name)
			return USER_INFO_TYPE_UNKNOWN, col_value_type, col_value_size

#---------------------------------------------------------------------------------------------------------------
	def analyze_col_value_with_col_value(col_name, col_value, col_value_size, col_value_type, table_name, sqlite_file_path):
		if col_value_type == CONTENTS_DIGIT_POSITIVE: # timestamp, phonenumber
			ret_col_schema = SQLiteAnalyzer.searching_timestamp_int(col_value, col_value_size, col_value_type, sqlite_file_path, table_name, col_name)
			if ret_col_schema[0] == USER_INFO_TYPE_UNKNOWN:
				return SQLiteAnalyzer.searching_id_phonenumber_int(col_value, col_value_size, col_value_type, sqlite_file_path, table_name, col_name)
			else:
				return ret_col_schema
		elif col_value_type == CONTENTS_FLOAT_POSITIVE:
			return SQLiteAnalyzer.searching_geodata(col_value, col_value_size, col_value_type, sqlite_file_path, table_name, col_name)
		elif col_value_type == CONTENTS_UNKNOWN:
			while True:
				ret_col_schema = SQLiteAnalyzer.searching_timestamp(col_value, col_value_size, col_value_type, sqlite_file_path, table_name, col_name)
				if ret_col_schema[0] != USER_INFO_TYPE_UNKNOWN:	return ret_col_schema					
				ret_col_schema = SQLiteAnalyzer.searching_id_phonenumber(col_value, col_value_size, col_value_type, sqlite_file_path, table_name, col_name)
				if ret_col_schema[0] != USER_INFO_TYPE_UNKNOWN:	return ret_col_schema					
				ret_col_schema = SQLiteAnalyzer.searching_id_account(col_value, col_value_size, col_value_type, sqlite_file_path, table_name, col_name)
				if ret_col_schema[0] != USER_INFO_TYPE_UNKNOWN:	return ret_col_schema					
				ret_col_schema = SQLiteAnalyzer.searching_address(col_value, col_value_size, col_value_type, sqlite_file_path, table_name, col_name)
				if ret_col_schema[0] != USER_INFO_TYPE_UNKNOWN:	return ret_col_schema					
				ret_col_schema = SQLiteAnalyzer.searching_url(col_value, col_value_size, col_value_type, sqlite_file_path, table_name, col_name)
				if ret_col_schema[0] != USER_INFO_TYPE_UNKNOWN:	return ret_col_schema
				ret_col_schema = SQLiteAnalyzer.searching_geodata(col_value, col_value_size, col_value_type, sqlite_file_path, table_name, col_name)
				if ret_col_schema[0] != USER_INFO_TYPE_UNKNOWN:	return ret_col_schema
				ret_col_schema = SQLiteAnalyzer.searching_file(col_value, col_value_size, col_value_type, sqlite_file_path, table_name, col_name)
				if ret_col_schema[0] != USER_INFO_TYPE_UNKNOWN:	return ret_col_schema
				return ret_col_schema
		else:	#CONTENTS_ALPHA
			return USER_INFO_TYPE_UNKNOWN, col_value_type, col_value_size

#---------------------------------------------------------------------------------------------------------------
	def identify_contents_type(col_value, col_value_type):
		if col_value_type == CONTENTS_ALPHA:
			return USER_INFO_TYPE_CONTENTS, CONTENTS_FORMAT_STRING
		elif col_value_type == CONTENTS_UNKNOWN:
			if col_value.replace(" ", "").isalpha():
				return USER_INFO_TYPE_CONTENTS, CONTENTS_FORMAT_STRING
			elif col_value.replace(" ", "").isalnum():
				return USER_INFO_TYPE_CONTENTS, CONTENTS_FORMAT_STRING_NUM
			else:
				return USER_INFO_TYPE_CONTENTS, CONTENTS_FORMAT_STRING_NUM_MIXED
		elif col_value_type == CONTENTS_DIGIT_POSITIVE:
			return USER_INFO_TYPE_CONTENTS, CONTENTS_FORMAT_DIGIT_POSITIVE
		elif col_value_type == CONTENTS_FLOAT_POSITIVE:
			return USER_INFO_TYPE_CONTENTS, CONTENTS_FORMAT_FLOAT_POSITIVE
		elif col_value_type == CONTETNS_BYTES:
			return USER_INFO_TYPE_CONTENTS, CONTENTS_FORMAT_BIN
		else:
			return USER_INFO_TYPE_CONTENTS, CONTENTS_FORMAT_UNKNOWN

#---------------------------------------------------------------------------------------------------------------
	def set_table_schema_info(dic_table_info, col_name, col_num, list_ret_col_schema):
		for col_schema in list_ret_col_schema:
			contents_type = col_schema[0]
			contents_format = col_schema[1]
			arg = ''
			arg2 = ''
			if contents_type == USER_INFO_TYPE_TIMESTAMP:
				arg = 'timestamp'
				arg2 = 'cnt_timestamp'
				dic_table_info[arg2] += 1
			if contents_type == USER_INFO_TYPE_TIMEDURATION:
				arg = 'time_duration'
				arg2 = 'cnt_time_duration'
				dic_table_info[arg2] += 1
			elif contents_type == USER_INFO_TYPE_ID_PHONENUMBER:
				arg = 'phonenumber'
				arg2 = 'cnt_phonenumber'
				dic_table_info[arg2] += 1
			elif contents_type == USER_INFO_TYPE_ID_ACCOUNT:
				arg = 'account'
				arg2 = 'cnt_account'
				dic_table_info[arg2] += 1
			elif contents_type == USER_INFO_TYPE_URL:
				arg = 'url'
				arg2 = 'cnt_url'
				dic_table_info[arg2] += 1
			elif contents_type == USER_INFO_TYPE_GEODATA:				
				if (contents_format == GEODATA_FORMAT_LATITUDE) | (contents_format == GEODATA_FORMAT_LONGITUDE):
					arg = 'geodata'
					arg2 = 'cnt_geodata'
					dic_table_info[arg2] += 1
			elif contents_type == USER_INFO_TYPE_ID_IPADDRESS:
				arg = 'ip'
				arg2 = 'cnt_ip'
				dic_table_info[arg2] += 1
			elif contents_type == USER_INFO_TYPE_ID_MACADDRESS:
				arg = 'mac'
				arg2 = 'cnt_mac'
				dic_table_info[arg2] += 1
			elif contents_type == USER_INFO_TYPE_CONTENTS:
				if contents_format == CONTENTS_FORMAT_DIGIT_POSITIVE:
					arg = 'digit_positive'
					arg2 = 'cnt_digit_positive'
					dic_table_info[arg2] += 1
				elif (contents_format == CONTENTS_FORMAT_STRING) | (contents_format == CONTENTS_FORMAT_STRING_NUM) | (contents_format == CONTENTS_FORMAT_STRING_NUM_MIXED):
					arg = 'contents'
					arg2 = 'cnt_contents'
					dic_table_info[arg2] += 1	
				elif contents_format == CONTENTS_FORMAT_BIN:
					arg = 'bin'
					arg2 = 'cnt_bin'
					dic_table_info[arg2] += 1
				elif contents_format == CONTENTS_FORMAT_PACKAGE:
					arg = 'pkg'
					arg2 = 'cnt_pkg'
					dic_table_info[arg2] += 1
			elif contents_type == USER_INFO_TYPE_FILE:
				if (contents_format == FILE_FORMAT_SIZE) | (contents_format == FILE_FORMAT_PATH) | (contents_format == FILE_FORMAT_URI):
					arg = 'file'
					arg2 = 'cnt_file'
					dic_table_info[arg2] += 1	
				elif contents_format == CONTENTS_FORMAT_BIN:
					arg = 'bin'
					arg2 = 'cnt_bin'
					dic_table_info[arg2] += 1
			elif contents_type == USER_INFO_TYPE_PASSWORD:
				arg = 'pwd'
				arg2 = 'cnt_pwd'
				dic_table_info[arg2] += 1
			elif contents_type == USER_INFO_TYPE_CIPHER:
				arg = 'cipher'
				arg2 = 'cnt_cipher'
				dic_table_info[arg2] += 1

			if (arg != '') & (arg2 != ''):
				dic_table_info['has_data'] = 1
				if dic_table_info[arg] == "":
					dic_table_info[arg] = (col_name + '(' + contents_format + ')' + '(' + str(col_num) + ')')
				else:
					dic_table_info[arg] += (',' + col_name + '(' + contents_format + ')' + '(' + str(col_num) + ')')

#---------------------------------------------------------------------------------------------------------------
	def analyze_table_info(dic_table_info, sqlite_file_path):
		table_name = dic_table_info['table_name']

		# get all column list
		query = 'PRAGMA TABLE_INFO({})'.format("'%s'") % table_name
		list_col_info = SQLite3.execute_fetch_query_multi_values(query, sqlite_file_path)
		if list_col_info == False:
			logger.error('corrupted table_name: "%s", db: "%s"' % (table_name, sqlite_file_path))
			return False

		for col_info in list_col_info:
			col_name = col_info[1]
			col_num = col_info[0] + 1
			col_type_sqlite = col_info[2].upper()
			if SQLiteAnalyzer.exception_rule_table_column(table_name, col_name):
				continue
			if SQLiteAnalyzer.exception_rule_column_type(col_name, col_type_sqlite):
				continue

			list_ret_col_schema = list()
			list_col_value = SQLiteAnalyzer.get_col_value(table_name, col_name, col_type_sqlite, sqlite_file_path, 50)
			if list_col_value == False:
				logger.error('corrupted column: "%s", table_name: "%s", db: "%s"' % (col_name, table_name, sqlite_file_path))
				return False

# debugging -----------------------------------------------------------
				# if (table_name == "package_list") & (col_name == "name"):
				# 	print(col_value_type, list_col_value)
# debugging -----------------------------------------------------------				

			for col_value in list_col_value:
				# print("col_value: %s, col_name: %s, table_name: %s, sqlite_file_path: %s" % (col_value, col_name, table_name, sqlite_file_path))
				if (col_value[0] == None) | (col_value[0] == "") | (col_value[0] == '0') | (col_value[0] == 0):
					continue
								
				if (col_type_sqlite == "BLOB") | (col_type_sqlite == "BYTE"):
					ret_col_schema = USER_INFO_TYPE_CONTENTS, CONTENTS_FORMAT_BIN
					list_ret_col_schema.append(ret_col_schema)
					continue

				ret_col_value_info = SQLiteAnalyzer.check_col_value_info(col_value[0])
				col_value = ret_col_value_info[0]
				col_value_size = ret_col_value_info[1]
				col_value_type = ret_col_value_info[2]

# debugging -----------------------------------------------------------
				# if (table_name == "AppUsage") & (col_name == "GnDate"):
				# 	print(col_value_type, col_value)
# debugging -----------------------------------------------------------

				if SQLiteAnalyzer.exception_rule_contents(col_name, col_value, col_value_size, col_value_type):
					continue
				ret_col_schema = SQLiteAnalyzer.analyze_col_value_with_col_name(col_name, col_value, col_value_size, col_value_type, table_name, sqlite_file_path)
				if ret_col_schema[0] != USER_INFO_TYPE_UNKNOWN:
					list_ret_col_schema.append(ret_col_schema)
				else:
					ret_col_schema = SQLiteAnalyzer.analyze_col_value_with_col_value(col_name, col_value, col_value_size, col_value_type, table_name, sqlite_file_path)
					if ret_col_schema[0] != USER_INFO_TYPE_UNKNOWN:
						list_ret_col_schema.append(ret_col_schema)
					else:
						ret_col_schema = SQLiteAnalyzer.identify_contents_type(col_value, ret_col_schema[1])
						list_ret_col_schema.append(ret_col_schema)

			dic_table_info['last'] = col_num
			list_ret_col_schema = list(set(list_ret_col_schema))
			SQLiteAnalyzer.set_table_schema_info(dic_table_info, col_name, col_num, list_ret_col_schema)


#---------------------------------------------------------------------------------------------------------------
	def insert_table_info_to_preprocessdb(dic_table_info, preprocess_db_path):
		query = 'INSERT INTO sqlitedb_table_preprocess(inode, table_name, cnt_records, cnt_timestamp, cnt_time_duration, cnt_phonenumber, cnt_account, cnt_pwd, cnt_url, cnt_geodata, cnt_ip, cnt_mac, cnt_digit_positive, cnt_contents, cnt_bin, cnt_file, cnt_cipher, cnt_pkg, timestamp, time_duration, phonenumber, account, pwd, url, geodata, ip, mac, digit_positive, contents, bin, file, cipher, pkg, last_col)\
                 VALUES(%d, "%s", %d, %d, %d, %d, %d, %d, %d, %d, %d, %d, %d, %d, %d, %d, %d, %d, "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", %d)' % (int(dic_table_info['file_inode']), dic_table_info['table_name'], int(dic_table_info['cnt_records']), int(dic_table_info['cnt_timestamp']), int(dic_table_info['cnt_time_duration']), int(dic_table_info['cnt_phonenumber']), int(dic_table_info['cnt_account']), int(dic_table_info['cnt_pwd']), int(dic_table_info['cnt_url']), int(dic_table_info['cnt_geodata']), int(dic_table_info['cnt_ip']), int(dic_table_info['cnt_mac']), int(dic_table_info['cnt_digit_positive']), int(dic_table_info['cnt_contents']), int(dic_table_info['cnt_bin']), int(dic_table_info['cnt_file']), int(dic_table_info['cnt_cipher']), int(dic_table_info['cnt_pkg']), dic_table_info['timestamp'], dic_table_info['time_duration'], dic_table_info['phonenumber'], dic_table_info['account'], dic_table_info['pwd'], dic_table_info['url'], dic_table_info['geodata'], dic_table_info['ip'], dic_table_info['mac'], dic_table_info['digit_positive'], dic_table_info['contents'], dic_table_info['bin'], dic_table_info['file'], dic_table_info['cipher'], dic_table_info['pkg'], int(dic_table_info['last']))
		SQLite3.execute_commit_query(query, preprocess_db_path)

#---------------------------------------------------------------------------------------------------------------
	def do_analyze(list_sqlite, case, result):
		SQLiteAnalyzer.get_user_info_type()		
		for sqlite_inode_path_name in list_sqlite:
			inode = sqlite_inode_path_name[0]
			sqlite_file_path = sqlite_inode_path_name[1]
			db_name = sqlite_inode_path_name[2]

# debugging -----------------------------------------------------------
			# if sqlite_file_path != "c:\Result\20150123_SM-N910L_data\extracted_files\format_sqlitedb\data\com.apusapps.launcher\databases\b_r.db":
			if db_name == "b_r.db":
				continue
# debugging -----------------------------------------------------------

			# if there are no tables, skip the sqlitedb
			query = "SELECT tbl_name FROM sqlite_master WHERE type='table' and sql LIKE '%CREATE TABLE%' and tbl_name!='sqlite_sequence' and tbl_name!='android_metadata'"
			list_table = SQLite3.execute_fetch_query_multi_values(query, sqlite_file_path)
			if (list_table == False) | (list_table == []):
				continue

			for table_info in list_table:
				# if there are no records, skip the table
				query = 'SELECT count(*) FROM "%s"' % table_info[0]
				ret = SQLite3.execute_fetch_query(query, sqlite_file_path)
				if ret == False:
					logger.error('corrupted table: "%s", db: "%s"' % (table_info[0], sqlite_file_path))
					continue
				else:
					cnt_records = ret[0]
					if cnt_records == 0:
						continue

				dic_table_info = {'file_inode':0, 'file_name':"", 'table_name':"", 'cnt_records':0, 'cnt_timestamp':0, 'cnt_time_duration':0, 'cnt_phonenumber':0, 'cnt_account':0, 'cnt_pwd':0, 'cnt_url':0, 'cnt_geodata':0, 'cnt_ip':0, 'cnt_mac':0, 'cnt_digit_positive':0, 'cnt_contents':0, 'cnt_bin':0, 'cnt_file':0, 'cnt_cipher':0, 'cnt_pkg':0, 'timestamp':"", 'time_duration':"", 'phonenumber':"", 'account':"", 'pwd':"", 'url':"", 'geodata':"", 'ip':"", 'mac':"", 'digit_positive':"", 'contents':"", 'bin':"", 'file':"", 'cipher':"", 'pkg':"", 'table_signature':"", 'table_info':"", 'last':0, 'has_data':0}
				dic_table_info['file_inode'] = inode
				dic_table_info['file_name'] = db_name
				dic_table_info['table_name'] = table_info[0]
				dic_table_info['cnt_records'] = cnt_records

				if SQLiteAnalyzer.exception_rule_db_table(db_name, dic_table_info['table_name']):
					continue

				SQLiteAnalyzer.analyze_table_info(dic_table_info, sqlite_file_path)
				if dic_table_info['has_data'] == 1:
					SQLiteAnalyzer.insert_table_info_to_preprocessdb(dic_table_info, case.preprocess_db_path)
		result.put(len(list_sqlite))

#---------------------------------------------------------------------------------------------------------------
	def analyze_sqlitedb(case):
		logger.info('    - Analyzing all SQLite databases for searching user information...')
		query = "SELECT inode, extracted_path, name FROM sqlitedb_info"
		list_sqlite = SQLite3.execute_fetch_query_multi_values(query, case.preprocess_db_path)
		if list_sqlite == False:
			return False

# for single-processing -----------------------------------------------------------------------------		
		# result = Queue()
		# SQLiteAnalyzer.do_analyze(list_sqlite, case, result)
# for single-processing -----------------------------------------------------------------------------

		length = len(list_sqlite)
		NUMBER_OF_PROCESSES = case.number_of_input_processes

		MAX_NUMBER_OF_PROCESSES_THIS_MODULE = math.ceil(length/2)
		if NUMBER_OF_PROCESSES*2 > length:
			NUMBER_OF_PROCESSES = MAX_NUMBER_OF_PROCESSES_THIS_MODULE

		if length < NUMBER_OF_PROCESSES:
			result = Queue()
			SQLiteAnalyzer.do_analyze(list_sqlite, case, result)
		else:
			num_item_per_list = math.ceil(length/NUMBER_OF_PROCESSES)
			start_pos = 0
			divied_list = list()
			for idx in range(start_pos, length, num_item_per_list):
				out = list_sqlite[start_pos:start_pos+num_item_per_list]
				if out != []:
					divied_list.append(out)
				start_pos += num_item_per_list

			result = Queue()
			procs = []

			for i in range(len(divied_list)):
				proc = Process(target=SQLiteAnalyzer.do_analyze, args=(divied_list[i], case, result))
				procs.append(proc)
				proc.start()

			for proc in procs:
				proc.join()

			result.put('STOP')
			while True:
				tmp = result.get()
				if tmp == 'STOP':
					break


