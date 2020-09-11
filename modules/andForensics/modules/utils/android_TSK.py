#-*- coding: utf-8 -*-

import os
import shutil
import subprocess
import io
import shutil
import logging

logger = logging.getLogger('andForensics')
TSK_PATH = os.getcwd() + os.sep + 'tools' + os.sep + 'sleuthkit' + os.sep

class TSK(object):
	def loaddb(image_file_path, load_db_path):
		if os.path.exists(load_db_path):
			return load_db_path

		#cmd = TSK_PATH + "tsk_loaddb \"%s\" " % image_file_path
		cmd = "/usr/local/bin/tsk_loaddb \'%s\' " % image_file_path
		ret = subprocess.Popen(cmd, shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
		ret_code = ret.stdout.read()
		f = io.StringIO(str(ret_code))
		result_msg = f.readline()
		f.close()
		if result_msg.split(':', 2)[0] == "b'Database stored at":
			shutil.move(image_file_path + '.db', load_db_path)
			return True
		else:
			return False
	
#---------------------------------------------------------------------------------------------------------------
	def icat_for_extract_file(image_file_path, inode, extracted_file_path):
		#cmd = TSK_PATH + "icat \"%s\" %d > \"%s\" " %(image_file_path, inode, extracted_file_path)
		cmd = "/usr/local/bin/icat \'%s\' %d > \'%s\' " % (image_file_path, inode, extracted_file_path)
		ret = subprocess.Popen(cmd, shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
		ret_code = ret.stdout.read()
		f = io.StringIO(str(ret_code))
		result_msg = f.readline()
		f.close()
		if result_msg != "b''":
			logger.error('\"icat %s %d > %s\" failed.' % (image_file_path, inode, extracted_file_path))
			return False
		else:
			return True

#---------------------------------------------------------------------------------------------------------------
	def get_file_buffer(src_image_path, inode, size_buf):
		#cmd = TSK_PATH + "icat.exe \"%s\" %d" % (src_image_path, inode)
		cmd = "/usr/local/bin/icat \"%s\" %d" % (src_image_path, inode)
		ret = subprocess.Popen(cmd, shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
		file_buffer = ret.stdout.read(size_buf)
		ret.kill()
		return file_buffer
