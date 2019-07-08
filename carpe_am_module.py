#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os, subprocess
import uuid

from utility import carpe_db
from image_analyzer import split_disk
from image_analyzer import scan_disk
from filesystem_analyzer import carpe_fs_analyzer

# Debuggin Module
import pdb

class CARPE_AM:
	def __init__(self):
		self.case_id = None
		self.evd_id = None
		self.path = None
		self.tmp_path = None

	def SetModule(self, _case_id, _evd_id):
		self.case_id = _case_id
		self.evd_id = _evd_id

		db = carpe_db.Mariadb()
		db.open()
		query = "SELECT evd_path FROM evidence_info WHERE case_id='" + _case_id + "' AND evd_id='" + _evd_id + "';"
		self.path = "/mnt/hgfs/carpe/share/" + db.execute_query(query)[0]
		self.tmp_path = "/mnt/hgfs/carpe/share/temp/" + self.case_id + "/" + self.evd_id + "/"
		db.close()

	def ParseImage(self, options):
		'''
			Module to analyze the image file.
			This module parse the partition list in image file.
		'''
		# Get Partition list in image file
		disk_scanner = scan_disk.DiskScanner()
		disk_info = disk_scanner.Analyze(self.path)

		# Insert Partition info
		db = carpe_db.Mariadb()
		db.open()

		for disk in disk_info:
			par_id = 'p1' + str(uuid.uuid4()).replace('-', '')
			par_name = str(disk['vol_name'])
			par_type = str(disk['type_indicator'])
			sector_size = str(disk['bytes_per_sector'])
			par_size = str(disk['length'])
			start_sector = str(disk['start_sector'])

			if par_type == 'VSHADOW' and options['vss'] != 'True':
				continue
			else:
				query = "INSERT INTO partition_info(par_id, par_name, evd_id, par_type, sector_size, par_size, start_sector) VALUES('" + par_id + "', '" + par_name + "', '" + self.evd_id + "', '" + par_type + "', '" + sector_size + "', '" + par_size + "', '" + start_sector + "');"
				db.execute_query(query)
			
		db.close()

		# Split VSS Partition
		if options['vss'] == 'True':
			output_writer = split_disk.FileOutputWriter(self.path)
			disk_spliter = split_disk.DiskSpliter(disk_info)
			disk_spliter.SplitDisk(output_writer)

		print('[#] Image Analysis Finish!')

	def VSSAnalysis(self):
		print('Analyze Volume Shadow Copy!')
	
	def ParseFilesystem(self):
		fs = carpe_fs_analyzer.Carpe_FS_Analyze()

		db = carpe_db.Mariadb()
		db.open()
		query = "SELECT sub_type FROM evidence_info WHERE evd_id='" + self.evd_id + "';"
		image_format = str(db.execute_query(query)[0]).lower()
		fs.open_image(image_format, self.path)

		query = "SELECT par_id, sector_size, start_sector FROM partition_info WHERE evd_id='" + self.evd_id + "';"
		par_info = db.execute_query_mul(query)
		db.close()
		
		for par in par_info:
			par_id = str(par[0])
			sector_size = int(str(par[1]))
			start_sector = int(str(par[2]))
			fs.open_file_system((sector_size * start_sector))
			fs.fs_info(par_id)

			directory = fs.open_directory(None)
			db_connector = carpe_db.Mariadb()

			db_connector.open()
			fs.list_directory(directory, [], [], db_connector)

			print('[#] FileSystem Analysis : ' + par_id + ' Finish!')

		return True

	def SysLogAndUserData_Analysis(self):
		# Conenct Carpe Database
		db = carpe_db.Mariadb()
		db.open()

		# Get image file list
		query = "SELECT par_id, par_name FROM partition_info WHERE evd_id='" + self.evd_id + "' ORDER BY start_sector;"
		par_infos = db.execute_query_mul(query)
		db.close()

		# Call Log2Timeline & PSort Tool
		for par_info in par_infos:
			p_id = str(par_info[0])
			p_name = str(par_info[1])
			storage_path = self.tmp_path + p_id + ".plaso"
			subprocess.call(['python', '/mnt/hgfs/carpe/plaso_tool/carpe_l2t.py',  storage_path, self.path, p_name])
			subprocess.call(['python', '/mnt/hgfs/carpe/plaso_tool/carpe_psort.py', '-o', '4n6time_maria', '--server', '218.145.27.66', '--port', '23306', '--user', 'root', '--password', 'dfrc4738',
				'--db_name', 'carpe2', '--case_id', str(self.case_id), '--evd_id', str(self.evd_id), '--par_id', p_id, storage_path])
