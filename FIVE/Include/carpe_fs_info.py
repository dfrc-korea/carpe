from __future__ import print_function

class Carpe_FS_Info(object):
	def __init__(self):
		super(Carpe_FS_Info, self).__init__()
		self._fs_id = None
		self._p_id = None
		self._block_size = None
		self._block_count = None
		self._root_inum = None
		self._first_inum = None
		self._last_inum = None
		