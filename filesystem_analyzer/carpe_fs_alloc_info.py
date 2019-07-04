from __future__ import print_function
import sys
import re

class Carpe_FS_Alloc_Info(object):
	"""docstring for Carpe_FS_Alloc_Info"""
	def __init__(self):
		super(Carpe_FS_Alloc_Info, self).__init__()
		self._p_id = None
		self._unallock_blocks = []
