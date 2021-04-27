# -*- coding: utf-8 -*-
"""module for kakaotalk mobile decrypt."""
import os
import sqlite3

from modules import logger
from modules import manager
from modules import interface
from modules.kakaotalk_mobile_decrypt import kakaotalk_mobile_decrypt
from dfvfs.lib import definitions as dfvfs_definitions


class KakaotalkMobileDecryptConnector(interface.ModuleConnector):

	NAME = 'kakaotalk_mobile_decrypt_connector'
	DESCRIPTION = 'Module for Kakaotalk Mobile Decrypt'
	TABLE_NAME = 'lv1_kakaotalk_mobile_decrypt'

	_plugin_classes = {}

	def __init__(self):
		super(KakaotalkMobileDecryptConnector, self).__init__()

	def Connect(self, par_id, configuration, source_path_spec, knowledge_base):

		# Check Filesystem
		query = f"SELECT filesystem FROM partition_info WHERE par_id like '{par_id}'"
		filesystem = configuration.cursor.execute_query(query)

		if filesystem == None or filesystem[0] != "TSK_FS_TYPE_EXT4":
			#print("No EXT filesystem.")
			return False

		this_file_path = os.path.dirname(os.path.abspath(__file__)) + os.sep + 'schema' + os.sep + 'kakaotalk_mobile'

		# Load schema
		yaml_list = [this_file_path + 'lv1_app_kakaotalk_mobile_chatlogs.yaml',
					 this_file_path + 'lv1_app_kakaotalk_mobile_chatrooms.yaml',
					 this_file_path + 'lv1_app_kakaotalk_mobile_friends.yaml',
					 this_file_path + 'lv1_app_kakaotalk_mobile_channel_history.yaml',
					 this_file_path + 'lv1_app_kakaotalk_mobile_block_friends.yaml']

		table_list = ['lv1_app_kakaotalk_mobile_chatlogs',
					  'lv1_app_kakaotalk_mobile_chatrooms',
					  'lv1_app_kakaotalk_mobile_friends',
					  'lv1_app_kakaotalk_mobile_channel_history',
					  'lv1_app_kakaotalk_mobile_block_friends']

		# Create all table
		for count in range(0, len(yaml_list)):
			if not self.LoadSchemaFromYaml(yaml_list[count]):
				logger.error('cannot load schema from yaml: {0:s}'.format(table_list[count]))
				return False
			# If table is not existed, create table
			if not configuration.cursor.check_table_exist(table_list[count]):
				ret = self.CreateTable(configuration.cursor)
				if not ret:
					logger.error('cannot create database table name: {0:s}'.format(table_list[count]))
					return False
				query = f"ALTER TABLE {table_list[count]} CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
				configuration.cursor.execute_query(query)

		# extension -> sig_type 변경해야 함

		query = f"SELECT name, parent_path, extension, ctime, ctime_nano FROM file_info WHERE par_id like '{par_id}' and " \
				f"(name like 'Kakaotalk.db' or name like 'Kakaotalk2.db') and parent_path = 'root/data/com.kakao.talk/databases';"

		kakaotalk_db_files = configuration.cursor.execute_query_mul(query)

		if len(kakaotalk_db_files) == 0:
			return False

		kakaotalk_db_list = list()
		for kakaotalk_db in kakaotalk_db_files:
			kakaotalk_db_path = kakaotalk_db[1][kakaotalk_db[1].find('/'):] + '/' + kakaotalk_db[0]  # document full path
			fileExt = kakaotalk_db[2]
			fileName = kakaotalk_db[0]
			output_path = configuration.root_tmp_path + os.sep + configuration.case_id + os.sep + configuration.evidence_id + os.sep + par_id
			self.ExtractTargetFileToPath(
				source_path_spec=source_path_spec,
				configuration=configuration,
				file_path=kakaotalk_db_path,
				output_path=output_path)

			self.ExtractTargetFileToPath(
				source_path_spec=source_path_spec,
				configuration=configuration,
				file_path=kakaotalk_db_path + '-wal',
				output_path=output_path)

			self.ExtractTargetFileToPath(
				source_path_spec=source_path_spec,
				configuration=configuration,
				file_path=kakaotalk_db_path + '-journal',
				output_path=output_path)

			self.ExtractTargetFileToPath(
				source_path_spec=source_path_spec,
				configuration=configuration,
				file_path=kakaotalk_db_path + '-shm',
				output_path=output_path)

			kakaotalk_db_list.append(output_path + os.path.sep + fileName)  # for file deletion

		kakaotalk_mobile_decrypt.main(kakaotalk_db_list[0], kakaotalk_db_list[1])

		### Kakaotalk.db ###
		con = sqlite3.connect(kakaotalk_db_list[0])
		cur = con.cursor()

		# chatlogs
		cur.execute("SELECT * FROM chat_logs_dec;")
		data_chatlogs = cur.fetchall()
		insert_kakaotalk_mobile_chatlogs = []

		for row in data_chatlogs:
			insert_kakaotalk_mobile_chatlogs.append(tuple(
				[par_id, configuration.case_id, configuration.evidence_id, row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9], row[10], row[11]]))

		query = "Insert into lv1_app_kakaotalk_mobile_chatlogs values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"
		configuration.cursor.bulk_execute(query, insert_kakaotalk_mobile_chatlogs)

		# chatrooms
		cur.execute("SELECT * FROM chat_rooms_dec;")
		data_chatrooms = cur.fetchall()
		insert_kakaotalk_mobile_chatrooms = []

		for row in data_chatrooms:
			insert_kakaotalk_mobile_chatrooms.append(tuple(
				[par_id, configuration.case_id, configuration.evidence_id, row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9], row[10], row[11], row[12], row[13], row[14], row[15], row[16], row[17], row[18], row[19], row[20], row[21], row[22], row[23], row[24], row[25], row[26], row[27], row[28]]))

		query = "Insert into lv1_app_kakaotalk_mobile_chatrooms values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"
		configuration.cursor.bulk_execute(query, insert_kakaotalk_mobile_chatrooms)

		### Kakaotalk2.db ###
		con2 = sqlite3.connect(kakaotalk_db_list[1])
		cur2 = con2.cursor()

		# friends
		cur2.execute("SELECT * FROM friends_dec;")
		data_friends = cur2.fetchall()
		insert_kakaotalk_mobile_friends = []

		for row in data_friends:
			insert_kakaotalk_mobile_friends.append(tuple(
				[par_id, configuration.case_id, configuration.evidence_id, row[0], row[1], row[2], row[3], row[4],
				 row[5], row[6], row[7], row[8], row[9], row[10], row[11], row[12], row[13], row[14], row[15], row[16],
				 row[17], row[18], row[19], row[20], row[21], row[22], row[23], row[24], row[25], row[26], row[27],
				 row[28], row[29], row[30], row[31], row[32], row[33], row[34], row[35], row[36]]))

		query = "Insert into lv1_app_kakaotalk_mobile_friends values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"
		configuration.cursor.bulk_execute(query, insert_kakaotalk_mobile_friends)

		# block_friends
		cur2.execute("SELECT * FROM block_friends;")
		data_block_friends = cur2.fetchall()
		insert_kakaotalk_mobile_block_friends = []

		for row in data_block_friends:
			insert_kakaotalk_mobile_block_friends.append(tuple(
				[par_id, configuration.case_id, configuration.evidence_id, row[0], row[1], row[2], row[3]]))

		query = "Insert into lv1_app_kakaotalk_mobile_block_friends values (%s, %s, %s, %s, %s, %s, %s);"
		configuration.cursor.bulk_execute(query, insert_kakaotalk_mobile_block_friends)

		# channel_history
		cur2.execute("SELECT * FROM channel_history;")
		data_channel_history = cur2.fetchall()
		insert_kakaotalk_mobile_channel_history = []

		for row in data_channel_history:
			insert_kakaotalk_mobile_channel_history.append(tuple(
				[par_id, configuration.case_id, configuration.evidence_id, row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7]]))

		query = "Insert into lv1_app_kakaotalk_mobile_channel_history values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"
		configuration.cursor.bulk_execute(query, insert_kakaotalk_mobile_channel_history)


		os.remove(kakaotalk_db_list[0])
		os.remove(kakaotalk_db_list[1])

		pass


manager.ModulesManager.RegisterModule(KakaotalkMobileDecryptConnector)