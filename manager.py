import os, time, logging, subprocess
import json

import pymysql
import plaso
from utility import carpe_db
from image_analyzer import split_disk

import pdb

class CARPE_AM:
	def __init__(self):
		print('Class init')

	def Image_Analysis(self, case_id, evd_id, user_id):
		pdb.set_trace()
		source = '/data/share/carpe/ntfs_par.001' 
		output_dir = os.getcwd()

		mediator = split_disk.DiskSpliterMediator()
		disk_spliter = split_disk.DiskSpliter(mediator=mediator)

		base_path_specs = disk_spliter.GetBasePathSpecs(source)

	def FileSystem_Analysis(self, case_id, evd_id):
		print('FileSystem Analyis')
	
	def SysLogAndUserData_Analysis(self, case_id, evd_id):
		print('SysLogAndUserData_Analysis')	


def main():
	try:
		carpe_manager = CARPE_AM()
		carpe_manager.Image_Analysis(1,2,3)
		print('Start')
	except KeyboardInterrupt:
		print('Stop')

if __name__ == '__main__':
	main()
