#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function
import sys, re

class CARPE_FS_Alloc_Info(object):
	"""docstring for CARPE_FS_Alloc_Info"""
	def __init__(self):
		super(CARPE_FS_Alloc_Info, self).__init__()
		self._p_id = None
		self._unallock_blocks = []
