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
  print('e1' + str(uuid.uuid4()).replace('-', ''))

# Case, Evidence ID
case_id = sys.argv[1]
evd_id = sys.argv[2]

options = {
  'Artifacts' : 'Default',
  'vss' : 'False'
}

# log2timeline filter option
#filter_option = sys.argv[4]

# Analysis Request
carpe_am = carpe_am_module.CARPE_AM()

# Set Module Information
carpe_am.SetModule(case_id, evd_id)

# Analyze
carpe_am.ParseImage(options)
carpe_am.ParseFilesystem()
carpe_am.SysLogAndUserData_Analysis()

#Init_Dummy_Case()
carpe_am.Analyze_Artifacts(options)

"""
  c16011ffad0b3a44e78aed17b366023f9c
  e1c1004619edb24ffcb5ca1e48ec3c73cf
  Windows10x64.E01
  
  python3.6 carpe_tester.py 'c16011ffad0b3a44e78aed17b366023f9c' 'e1c1004619edb24ffcb5ca1e48ec3c73cf'
"""