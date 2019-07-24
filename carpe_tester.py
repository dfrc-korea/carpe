#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os, sys, time, subprocess
import functools
import threading
import json
import uuid

import carpe_am_module
# Debugging Module
import pdb

def Init_Dummy_Case():
  print 'e1' + str(uuid.uuid4()).replace('-', '')
'''
# Case, Evidence ID
case_id = sys.argv[1]
evd_id = sys.argv[2]

# VSS Option
vss_option = sys.argv[3]

# log2timeline filter option
filter_option = sys.argv[4]

# Analysis Request
carpe_am = carpe_am_module.CARPE_AM()

# Set Module Information
carpe_am.SetModule(case_id, evd_id)

# Analyze
carpe_am.ParseImage(vss_option)
carpe_am.ParseFilesystem()
carpe_am.SysLogAndUserData_Analysis(filter_option)
'''

Init_Dummy_Case()