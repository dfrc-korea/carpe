import os, time, logging, subprocess
import json

import pymysql
import plaso
from utility import mariadb
from image_analyzer import split_disk
from image_analyzer import scan_disk
from filesystem_analyzer import carpe_fls

import pdb

class CARPE_AM:
	src_path = None
	dst_path = None

	def __init__(self):
		self.src_path = None
		self.dst_path = None

	def Preprocess(self, case_no, evd_no, user_id):
		'''
			Module to analyze the image file.
			This module parse the partition list in image file.
			And split image by partition.
		'''

		# Connect Carpe Database
		db = mariadb.Mariadb()
		conn = db.open()

		# Get Source Path
		query = 'SELECT file_path FROM tn_evidence WHERE evd_no = ' + str(evd_no) + ';'
		self.src_path = db.execute_query(conn, query)

		# Get Case & Evidence Name
		query = 'SELECT case_name FROM tn_case WHERE case_no = ' + str(case_no) + ';'
		case_name = db.execute_query(conn, query)

		query = 'SELECT evd_name FROM tn_evidence WHERE evd_no = ' + str(evd_no) + ';'
		evd_name = db.execute_query(conn, query)
		db.close(conn)

		# Create directory to store splitted image
		self.dst_path = '/data/share/image' + '/' + case_name + '/' + evd_name + '/splitted'

		if not os.path.exists(self.dst_path):
			os.mkdir(self.dst_path)
		
		# Get partition list in image file
		output_writer = split_disk.FileOutputWriter(self.dst_path)
		mediator = scan_disk.DiskScannerMediator()
		disk_scanner = scan_disk.DiskScanner(mediator=mediator)
		
		base_path_specs = disk_scanner.GetBasePathSpecs(self.src_path)
		disk_info = disk_scanner.ScanDisk(base_path_specs)
		
		# Split image file
		disk_spliter = split_disk.DiskSpliter(disk_info)
		disk_spliter.SplitDisk(output_writer)

	def FileSystem_Analysis(self, case_no, evd_no, user_id):
		# Conenct Carpe Database
		db = mariadb.Mariadb()
		conn = db.open()

		# Get image file list
		query = 'SELECT file_path FROM tn_evidence_splitted WHERE case_no = ' + str(case_no) + ' and evd_no = ' + str(evd_no) + ';'
		image_list = db.execute_query(conn, query)
		db.close(conn)
		
		# Temporary code
		for image in image_list:
			subprocess.call(['python', '../filesystem_analyzer/carpe_fls', 'option'])

		'''
		# Parse file and directory list in image file
		procs = []
		for image in image_list:
			proc = Process(target=self.ParseFilesystem, args=(image))
			proc.start()
			procs.append(proc)

		for proc in procs:
			proc.join()

		'''
	
	def ParseFilesystem(self, image):
		fls = carpe_fls.Fls()
		fls.open_image('raw', image)
		fls.open_file_system(0)
		directory = fls.open_directory('?')
		fls.list_directory(directory, [], [])

	def SysLogAndUserData_Analysis(self, case_no, evd_no, user_id):
		# Conenct Carpe Database
		db = mariadb.Mariadb()
		conn = db.open()

		# Get image file list
		query = 'SELECT file_path FROM tn_evidence_splitted WHERE case_no = ' + str(case_no) + ' and evd_no = ' + str(evd_no) + ';'
		image_list = db.execute_query(conn, query)
		db.close(conn)

		# Call log2timeline module
		for image in image_list:
		
def main():
	try:
		carpe_manager = CARPE_AM()
		carpe_manager.Preprocess(1,1,1)
	except KeyboardInterrupt:
		print('Stop')

if __name__ == '__main__':
	main()
