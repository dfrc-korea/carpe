from __future__ import print_function
import argparse
import gc
import pdb
import sys
import time
import re

class Carpe_file(object):
	def __init__(self):
		super(Carpe_file, self).__init__()
		self._p_id = None
		#self._attr_type = None
		#self._attr_id = None
		self._inode = None
		self._name = None
		#self._meta_addr = None
		self._meta_seq = None
		self._type = None
		self._dir_type = None
		self._meta_type = None
		self._meta_flags = None
		self._size = None
		self._si_mtime = None
		self._si_atime = None
		self._si_ctime = None
		self._si_etime = None
		self._si_mtime_nano = None
		self._si_atime_nano = None
		self._si_ctime_nano = None
		self._si_etime_nano = None
		self._fn_mtime = None
		self._fn_atime = None
		self._fn_ctime = None
		self._fn_etime = None		
		self._fn_mtime_nano = None
		self._fn_atime_nano = None
		self._fn_ctime_nano = None
		self._fn_etime_nano = None
		self._mode = None
		self._uid = None
		self._gid = None
		self._hash = None
		self._parent_path = None
		self._extension = None

	def toTuple(self):
		var_list = [x for x in dir(self) if (re.match(r'(^[_][a-z])', x))]
		temp = self.__dict__
		ret = []
		for i in var_list:
			ret.append(temp[i])
		return tuple(ret)	