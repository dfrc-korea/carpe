import os, time, logging, subprocess
import json

import pymysql
import plaso
from utility import mariadb
from image_analyzer import split_disk

import pdb

class CARPE_AM:
	src_path = None
	dst_path = None

	def __init__(self):
		self.src_path = None
		self.dst_path = None

	def Preprocess(self, case_id, evd_id, user_id):
		# Connect MariaDB
		db = mariadb.Mariadb()
		conn = db.open()

		# Get Source Path
		query = 'SELECT file_path FROM tn_evidence WHERE evd_no = ' + str(evd_id) + ';'
		self.src_path = db.execute_query(conn, query)

		# Get Case & Evidence Name
		query = 'SELECT case_name FROM tn_case WHERE case_no = ' + str(case_id) + ';'
		case_name = db.execute_query(conn, query)

		query = 'SELECT evd_name FROM tn_evidence WHERE evd_no = ' + str(evd_id) + ';'
		evd_name = db.execute_query(conn, query)
		db.close(conn)

		# Create directory to store splitted image
		self.dst_path = '/data/share/image' + '/' + case_name + '/' + evd_name + '/split'

		if not os.path.exists(self.dst_path):
			os.mkdir(self.dst_path)
		
		# Get partition list in image file
		mediator = split_disk.DiskSpliterMediator()
		disk_spliter = split_disk.DiskSpliter(mediator=mediator)
		base_path_specs = disk_spliter.GetBasePathSpecs(self.src_path)

	def Image_Analysis(self, case_id, evd_id, user_id):
		print('Image Analyis')

	def FileSystem_Analysis(self, case_id, evd_id):
		print('FileSystem Analyis')
	
	def SysLogAndUserData_Analysis(self, case_id, evd_id):
		print('SysLogAndUserData_Analysis')	


def main():
	try:
		carpe_manager = CARPE_AM()
		carpe_manager.Preprocess(1,1,1)
	except KeyboardInterrupt:
		print('Stop')

if __name__ == '__main__':
	main()
