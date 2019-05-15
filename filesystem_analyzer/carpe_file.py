from __future__ import print_function
import sys
import re

class Carpe_File(object):
	def __init__(self):
		super(Carpe_File, self).__init__()
		self._p_id = None
		#self._attr_type = None
		#self._attr_id = None
		self._inode = None
		self._name = None
		#self._meta_addr = None
		self._meta_seq = 0
		self._type = None
		self._dir_type = 0
		self._meta_type = 0
		self._meta_flags = 0
		self._size = None
		self._si_mtime = 0
		self._si_atime = 0
		self._si_ctime = 0
		self._si_etime = 0
		self._si_mtime_nano = 0
		self._si_atime_nano = 0
		self._si_ctime_nano = 0
		self._si_etime_nano = 0
		self._fn_mtime = 0
		self._fn_atime = 0
		self._fn_ctime = 0
		self._fn_etime = 0		
		self._fn_mtime_nano = 0
		self._fn_atime_nano = 0
		self._fn_ctime_nano = 0
		self._fn_etime_nano = 0
		self._mode = None
		self._uid = None
		self._gid = None
		self._hash = ""
		self._parent_path = None
		self._extension = None

	def toTuple(self):
		var_list = sorted([x for x in dir(self) if (re.match(r'(^[_][a-z])', x))])
		temp = self.__dict__
		ret = []
		for i in var_list:
			if(type(temp[i]) is long):
				ret.append(int(str(temp[i]).rstrip("L")))
			elif(type(temp[i]) is unicode):
				ret.append(temp[i].encode("utf-8"))
			else :
				ret.append(temp[i])
		return tuple(ret)
