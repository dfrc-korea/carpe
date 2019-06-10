#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os, subprocess

from utility import carpe_db
from image_analyzer import split_disk
from image_analyzer import scan_disk
from filesystem_analyzer import carpe_fs_analyzer

class CARPE_AM:
	def __init__(self):
		self.case_name = None
		self.evd_name = None
		self.inv_name = None
		self.src_path = None
		self.dst_path = None

	def init_module(self, case_no, evd_no, inv_no):
		# Connect Carpe Database
		db = carpe_db.Mariadb()
		db.open()

		# Get Source Path
		query = 'SELECT evd_name, file_path FROM tn_evidence WHERE case_no = ' + str(case_no) + ' and evd_no = ' + str(evd_no) + ';'
		(self.evd_name, self.src_path) = db.execute_query(db._conn, query)

		# Get Case & Evidence Name
		query = 'SELECT case_name FROM tn_case WHERE case_no = ' + str(case_no) + ';'
		self.case_name = db.execute_query(db._conn, query)

		db.close()

		# Create directory to store splitted image
		self.dst_path = '/data/share/image' + '/' + self.case_name + '/' + self.evd_name + '/splitted'

	def Preprocess(self, case_no, evd_no, inv_no):
		'''
			Module to analyze the image file.
			This module parse the partition list in image file.
			And split image by partition.
		'''
		if not os.path.exists(self.dst_path):
			os.mkdir(self.dst_path)
		
		# Get partition list in image file
		output_writer = split_disk.FileOutputWriter(self.dst_path)
		mediator = scan_disk.DiskScannerMediator()
		disk_scanner = scan_disk.DiskScanner(mediator=mediator)
		
		base_path_specs = disk_scanner.GetBasePathSpecs(self.src_path)
		disk_info = disk_scanner.ScanDisk(base_path_specs)
		
		# Insert partition list

		# Split image file
		disk_spliter = split_disk.DiskSpliter(disk_info)
		disk_spliter.SplitDisk(output_writer)

	def FileSystem_Analysis(self, case_no, evd_no, user_id):
		# Conenct Carpe Database
		db = carpe_db.Mariadb()
		db.open()

		# Get image file list
		query = 'SELECT file_path  FROM tn_evidence_splitted WHERE case_no = ' + str(case_no) + ' and evd_no = ' + str(evd_no) + ';'
		image_list = db.execute_query(db._conn, query)
		db.close()
		
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
	
	def ParseFilesystem(self, options):
		if not options.images:
			print('No storage media image or device was provided.')
			print('')
			print('')
			return False

		#fls = carpe_fs_analyzer.Fls()
		#fls.open_image('raw', image)
		#fls.open_file_system(0)
		#directory = fls.open_directory('?')
		#fls.list_directory(directory, [], [])

		#####------#####
		fs = carpe_fs_analyzer.Carpe_FS_Analyze()
		#fs_alloc_info = carpe_fs_alloc_info.Carpe_FS_Alloc_Info()

		fs.parse_options(options)

		fs.open_image("raw", options.images)
		 
		fs.open_file_system(0)

		fs.fs_info(options.partition_id)

		#fs_alloc_info = fs.block_alloc_status()
		  
		#fs_alloc_info._p_id = options.partition_id

		directory = fs.open_directory(options.inode)

		db_connector = carpe_db.Mariadb()

		db_connector.open()
		#db_connector.initialize()
		# Iterate over all files in the directory and print their name.
		# What you get in each iteration is a proxy object for the TSK_FS_FILE
		# struct - you can further dereference this struct into a TSK_FS_NAME
		# and TSK_FS_META structs.
		fs.list_directory(directory, [], [], db_connector)
		return True


	def SysLogAndUserData_Analysis(self, case_no, evd_no, inv_no):
		# Conenct Carpe Database
		db = carpe_db.Mariadb()
		db.open()

		# Get image file list
		query = 'SELECT file_name, file_path FROM tn_evidence_splitted WHERE case_no = ' + str(case_no) + ' and evd_no = ' + str(evd_no) + ';'
		image_name, image_list = db.execute_query(db._conn, query)
		db.close()

		# Temporary code
		for name, image in image_name, image_list:
			subprocess.call(['python3.6', '../plaso_tool/log2timeline.py', name + '.plaso', image])

		for name in image_name:
			subprocess.call(['python3.6', '../plaso_tool/psort.py', '-o', '4n6time_mariadb', name + '.plaso'])