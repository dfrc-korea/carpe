from __future__ import print_function
import sys
import re

class Carpe_FS_Alloc_Info(object):
	"""docstring for Carpe_FS_Alloc_Info"""
	def __init__(self, arg):
		super(Carpe_FS_Alloc_Info, self).__init__()
		self._p_id = None
		self._seq_num = None
		self._alloc_status =None
