#-*- coding: utf-8 -*-

import os
import subprocess
import io
import logging

logger = logging.getLogger('andForensics')
#JADX_PATH = os.getcwd() + os.sep + 'tools' + os.sep + 'jadx' + os.sep + 'bin' + os.sep

class JADX(object):
	def decompile(apk_path, decompiled_path):
		if os.path.exists(decompiled_path):
			return True

		#cmd = JADX_PATH + "jadx -d \"%s\" \"%s\"" % (decompiled_path, apk_path)
		cmd = "/home/dfrc/Desktop/jadx -d \"%s\" \"%s\"" % (decompiled_path, apk_path)
		ret = subprocess.Popen(cmd, shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
		ret_code = ret.stdout.read()
		f = io.StringIO(str(ret_code))
		result_msg = f.readline()
		if result_msg.split("processing ...")[1].split(" ")[0].find("ERROR") == 4:
			logger.error('JADX error. APK path: \"%s\", error message: \"%s\"' % (apk_path, result_msg)) 
		f.close()
		return True


