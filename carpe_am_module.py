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

from Carving.plugin_carving import CarvingManager
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
		self.manage = None

	def SetModule(self, _case_id, _evd_id):
		self.case_id = _case_id
		self.evd_id = _evd_id

		db = carpe_db.Mariadb()
		db.open()
		query = "SELECT evd_path FROM evidence_info WHERE case_id='" + _case_id + "' AND evd_id='" + _evd_id + "';"
		#self.path = "/data/share/" + db.execute_query(query)[0]
		#self.tmp_path = "/data/share/temp/" + self.case_id + "/" + self.evd_id + "/"
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

			#unalloc 
			fs_alloc_info = fs.block_alloc_status()
			fs_alloc_info._p_id = par_id
			for i in fs_alloc_info._unallock_blocks:
				query = db.insert_query_builder("block_info")
				query = (query + "\n values " + "%s" % (i, ))
				data=db.execute_query(query)
			db.commit()

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
			#subprocess.call(['python3.6', '/data/carpe/plaso_tool/carpe_l2t.py', '--hashers', 'None',  storage_path, self.path, p_name])
			#subprocess.call(['python3.6', '/data/carpe/plaso_tool/carpe_psort.py', '-o', '4n6time_maria', '--server', '218.145.27.66', '--port', '23306', '--user', 'root', '--password', 'dfrc4738',
			#	'--db_name', 'carpe', '--case_id', str(self.case_id), '--evd_id', str(self.evd_id), '--par_id', p_id, storage_path])
			subprocess.call(['python3.6', '/mnt/hgfs/carpe/plaso_tool/carpe_l2t.py', '--hashers', 'None',  storage_path, self.path, p_name])
			subprocess.call(['python3.6', '/mnt/hgfs/carpe/plaso_tool/carpe_psort.py', '-o', '4n6time_maria', '--server', '218.145.27.66', '--port', '23306', '--user', 'root', '--password', 'dfrc4738',
				'--db_name', 'carpe', '--case_id', str(self.case_id), '--evd_id', str(self.evd_id), '--par_id', p_id, storage_path])
	
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
		#print(query)
		data.case_name = case[0]
		#print(case)
		# Get Evidence Information
		query = "SELECT * FROM evidence_info where case_id='" + self.case_id + "' and evd_id='" + self.evd_id +"';"
		evidence = db.execute_query(query)
		#print(query)
		data.evdnc_id = evidence[0]
		data.evdnc_name = evidence[1]
		evdnc_path = "/data/part3_test/" + evidence[2]
		data.sha1_hash = evidence[11]
		

		# ole object save path
		#work_dir = "/home/carpe/tmp/" + self.case_id + "/" + self.evd_id + "/documents"
		data.work_dir = "/data/part3_test/" + self.case_id + "/" + self.evd_id + "/documents/"
		#print(work_dir)
		# Get document FileList
		query = "SELECT * FROM file_info WHERE extension in ('pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'hwp') ORDER BY file_id" 
		document_files = db.execute_query_mul(query)
		#print(document_files)
		file_list = [list(doc) for doc in document_files]
		
		tuple = []
		tuple_list = []
		for idx in range(len(file_list)):
			file_list[idx].append(data.work_dir+file_list[idx][4])
			tuple = [file_list[idx][4], file_list[idx][1]]
			tuple_list.append(tuple)
		
		fileExpoter = carpe_file_extractor.Carpe_File_Extractor()
		#fileExpoter.setConfig(work_dir, '/data/share/source/carpe/examples/test_img/[NTFS]_win1064_1.001', tuple_list)
		fileExpoter.setConfig(data.work_dir, evdnc_path, tuple_list)
		
		fileExpoter.extract()
		
		P3_Manager.run_daemon(data, file_list)
		
		db.close()

	def Carving(self, option):
		db = carpe_db.Mariadb()
        db.open()

        # Get image file list
        query = "SELECT par_id FROM partition_info WHERE evd_id='" + self.evd_id + "' ORDER BY start_sector;"
        par_infos = db.execute_query_mul(query)
        db.close()

        if(self.manage==None and option[0]==0):
            self.manage = CarvingManager(debug=False,out="carving.log")
            res = self.manage.execute(self.manage.Instruction.LOAD_MODULE)
            if(res==False):
                return self.manage.Return.EIOCTL
            
            """ For Regular Version """
            #res = self.manage.execute(self.manage.Instruction.CONNECT_DB,self.db_credentials)
            #if(res==self.manage.Return.EFAIL_DB):
            #    return self.manage.Return.EFAIL_DB
            
            self.manage.execute(self.manage.Instruction.POLICY,
                {
                    "enable":True,      # 카빙 추출 기능 활성화
                    "save":False        # 카빙 캐시 정보 저장 안함
                }
            )
            return self.manage.Return.SUCCESS

        if(self.manage==None):
            return None

        for par_info in par_infos:
            desti = self.path + "/" + self.case_id + "/" + self.evd_id + "/" + par_info[0] + "/"       
            self.manage.execute(self.manage.Instruction.PARAMETER,
                {
                        "p_id"  :self.case_id,
                        "block" :0x1000,
                        "sector":0x200,
                        "start" :0x0,
                        "path"  :desti,
                        "dest"  :desti+"{0}result".format(os.sep)
                }
            )
            self.manage.execute(self.manage.Instruction.EXEC,None)