#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os, sys, subprocess
import uuid

from utility import carpe_db
from utility import carpe_file_extractor
from image_analyzer import split_disk
from image_analyzer import scan_disk
from filesystem_analyzer import carpe_fs_analyzer
from artifact_analyzer import artifact_analyzer

# 카빙 import 에러로 인해 잠시 주석처리
#from FIVE.plugin_carving import CarvingManager
from moduleInterface.interface import ModuleComponentInterface

#sys.path.append(os.path.join(os.path.dirname(os.path.abspath(os.path.dirname('__file__')), 'READ')))
from DEFA import P3_Manager
from DEFA import MappingDocuments

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
		#pdb.set_trace()
		self.path = os.path.join("/home/carpe/storage", db.execute_query(query)[0])
		db.close()
		
		t_path_1 = os.path.join("/home/carpe/tmp", self.case_id)
		if not os.path.isdir(t_path_1):
			os.mkdir(t_path_1)
			
		self.tmp_path = os.path.join(t_path_1, self.evd_id)
		
		if not os.path.isdir(self.tmp_path):
			os.mkdir(self.tmp_path)

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

	def ParseFilesystem(self):
		fs = carpe_fs_analyzer.CARPE_FS_Analyze()

		db = carpe_db.Mariadb()
		db.open()
		query = "SELECT sub_type FROM evidence_info WHERE evd_id='" + self.evd_id + "';"
		image_format = str(db.execute_query(query)[0]).lower()
		fs.open_image(image_format, self.path)

		query = "SELECT par_id, sector_size, start_sector FROM partition_info WHERE evd_id='" + self.evd_id + "';"
		par_info = db.execute_query_mul(query)
		
		for par in par_info:
			par_id = str(par[0])
			#print(par_id)
			sector_size = int(str(par[1]))
			start_sector = int(str(par[2]))
			ret = fs.open_file_system((sector_size * start_sector))
			if ret == -1:
				print(par_id)
				continue
			fs.fs_info(par_id)

			#unalloc

			fs_alloc_info = fs.block_alloc_status()
			fs_alloc_info._p_id = par_id
			for i in fs_alloc_info._unallock_blocks:
				query = db.insert_query_builder("block_info")
				query = (query + " values ('" + str(i[1]) + "','" + par_id + "','" +
                                str(i[0]) + "');")
				db.execute_query(query)
			db.commit()

			directory = fs.open_directory(None)	
			fs.list_directory(directory, [], [], db)

		db.close()
		return True

	def SysLogAndUserData_Analysis(self):
		# connect CARPE Database
		db = carpe_db.Mariadb()
		db.open()

		# Get image file list
		query = "SELECT par_id, par_name FROM partition_info WHERE evd_id='" + self.evd_id + "' ORDER BY start_sector;"
		par_infos = db.execute_query_mul(query)
		db.close()
        
		# Call Log2Timeline & Psort Tool
		for par_info in par_infos:
			p_id = str(par_info[0])
			p_name = str(par_info[1])
			storage_path = os.path.join(self.tmp_path, (p_id + ".plaso"))

			print(p_id)
			if p_id == 'p194e18781ce5b4e94a90d4591e3264b5a':
				print("pass!!!")
				continue
			# test
			subprocess.call(['python3.6', '/home/barley/CARPE/plaso_tool/carpe_l2t.py', '--no_vss', '--hashers', 'None',
							 storage_path, self.path, p_name])
			print('l2t end')
			if os.path.exists(storage_path):
				subprocess.call(
					['python3.6', '/home/barley/CARPE/plaso_tool/carpe_psort.py', '-o', '4n6time_maria', '--server',
					 '127.0.0.1', '--port', '3306', '--user', 'root', '--password', 'dfrc4738', '--db_name', 'carpe',
					 '--case_id', str(self.case_id), '--evd_id', str(self.evd_id), '--par_id', p_id, storage_path])

			# server
			#subprocess.call(['python3.6', '/home/carpe/carpe/plaso_tool/carpe_l2t.py', '--no_vss', '--hashers', 'None',  storage_path, self.path, p_name])
			#subprocess.call(['python3.6', '/home/carpe/carpe/plaso_tool/carpe_psort.py', '-o', '4n6time_maria', '--server', '127.0.0.1', '--port', '23306', '--user', 'root', '--password', 'dfrc4738', '--db_name', 'carpe', '--case_id', str(self.case_id), '--evd_id', str(self.evd_id), '--par_id', p_id, storage_path])

	def Analyze_Artifacts(self, options):
		analyzer = artifact_analyzer.ArtifactAnalyzer()
		analyzer.Init_Module(self.case_id, self.evd_id, options['Artifacts'])
		analyzer.Analyze()

	def Analyze_Documents(self):
		# connect Carpe Database
		db = carpe_db.Mariadb()
		db.open()

		data = MappingDocuments.MappingDocuments()
		
		# Get Case Information
		# query = "SELECT * FROM case_info where administrator = 'jung byeongchan'"
		# case = db.execute_query(query)
		
		data.case_id = self.case_id
		query = "SELECT case_name FROM case_info where case_id ='%s';" % self.case_id
		case = db.execute_query(query)
		data.case_name = case[0]

		# Get Evidence Information
		query = "SELECT * FROM evidence_info where case_id='" + self.case_id + "' and evd_id='" + self.evd_id +"';"
		evidence = db.execute_query(query)
		
		data.evdnc_id = evidence[0]
		data.evdnc_name = evidence[1]
		evdnc_path = self.path
		data.sha1_hash = evidence[11]
		
		# ole object save path
		#work_dir = "/home/carpe/tmp/" + self.case_id + "/" + self.evd_id + "/documents"

		data.work_dir = "/home/carpe/defa_temp" + os.sep + self.case_id
		if not os.path.exists(data.work_dir):
			os.mkdir(data.work_dir)

		data.work_dir = "/home/carpe/defa_temp" + os.sep + self.case_id + os.sep + self.evd_id
		if not os.path.exists(data.work_dir):
			os.mkdir(data.work_dir)

		# Get Partition List
		query = "SELECT par_id, sector_size, start_sector, par_size FROM partition_info WHERE evd_id='" + self.evd_id + "' ORDER BY start_sector;"
		par_info = db.execute_query_mul(query)
                
		for par in par_info:
			# Get Document List
			query = "SELECT * FROM file_info WHERE extension in ('pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'hwp') and par_id='" + par[0] + "' ORDER BY file_id;"
			document_files = db.execute_query_mul(query)

			if len(document_files):
				data.work_dir = "/home/carpe/defa_temp" + os.sep + self.case_id + os.sep + self.evd_id + os.sep + par[0]
				if not os.path.exists(data.work_dir):
					os.mkdir(data.work_dir)
								
				data.work_dir = "/home/carpe/defa_temp" + os.sep + self.case_id + os.sep + self.evd_id + os.sep + par[0] + os.sep + "documents/"
				if not os.path.exists(data.work_dir):
					os.mkdir(data.work_dir)

				data.ole_path = "/home/carpe/defa_temp" + os.sep + self.case_id + os.sep + self.evd_id + os.sep + par[0] + os.sep + "documents/"
				file_list = [list(doc) for doc in document_files]
				tuple = []
				tuple_list = []
				
				for idx in range(len(file_list)):
					file_list[idx].append(data.work_dir+file_list[idx][4])
					tuple = [file_list[idx][4], file_list[idx][1]]
					tuple_list.append(tuple)
			
				fileExpoter = carpe_file_extractor.Carpe_File_Extractor()
				fileExpoter.setConfig(data.work_dir, evdnc_path, (par[1] * par[2]), tuple_list)
				fileExpoter.extract()
			
				P3_Manager.run_daemon(data, file_list)
				print()
		db.close()

	def Carving(self, option):
		manage = CarvingManager(debug=True,out="carving.log",table="carving_result")
		res = manage.execute(manage.Instruction.LOAD_MODULE)

		if(res==False):
			return manage.Return.EIOCTL

		manage.execute(manage.Instruction.POLICY,
		{
			"enable":True,
			"save":True
		})

		db = carpe_db.Mariadb()
		db.open()
		manage.carpe_connect_master(db)

		# Get image file list
		query = "SELECT par_id, sector_size, start_sector, par_size FROM partition_info WHERE evd_id='" + self.evd_id + "' ORDER BY start_sector;"
		par_infos = db.execute_query_mul(query)

		for par_info in par_infos:
			desti = self.tmp_path + os.sep + par_info[0]
			if(os.path.exists(desti) == False):
				os.mkdir(desti)

			manage.execute(manage.Instruction.PARAMETER,
			{
				"p_id":par_info[0],
				"block": 8 * int(par_info[1]),
				"sector":par_info[1],
				"start":par_info[2],
				"path":self.path,
				"dest":desti+"{0}data_carving".format(os.sep),
				"end":par_info[3]
			})
			manage.execute(manage.Instruction.EXEC)
			manage.execute(manage.Instruction.EXPORT_CACHE_TO_DB)

		manage.execute(manage.Instruction.DISCONNECT_DB)
