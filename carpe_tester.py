#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os, sys, time, subprocess
import functools
import threading
import json
import uuid

from datetime import datetime
import carpe_am_module

# Debugging Module
import pdb

# Case, Evidence ID
case_id = sys.argv[1]
evd_id = sys.argv[2]

options = {
  'Artifacts': 'Default',
  'vss': 'False'
}

# Analysis Request
carpe_am = carpe_am_module.CARPE_AM()
# Set Module Information
carpe_am.SetModule(case_id, evd_id)

# Analyze
now = datetime.now()
print('[%s-%s-%s %s:%s:%s] Start Analyze Image' % (now.year, now.month, now.day, now.hour, now.minute, now.second))
#carpe_am.ParseImage(options)
now = datetime.now()
print('[%s-%s-%s %s:%s:%s] Finish Analyze Image' % (now.year, now.month, now.day, now.hour, now.minute, now.second))

now = datetime.now()
print('[%s-%s-%s %s:%s:%s] Start Analyze Filesystem' % (now.year, now.month, now.day, now.hour, now.minute, now.second))
#carpe_am.ParseFilesystem()
now = datetime.now()
print('[%s-%s-%s %s:%s:%s] Finish Analyze Filesystem' % (now.year, now.month, now.day, now.hour, now.minute, now.second))

now = datetime.now()
print('[%s-%s-%s %s:%s:%s] Start Analyze Artifacts' % (now.year, now.month, now.day, now.hour, now.minute, now.second))
#carpe_am.SysLogAndUserData_Analysis()
now = datetime.now()
print('[%s-%s-%s %s:%s:%s] Finish Analyze Artifacts' % (now.year, now.month, now.day, now.hour, now.minute, now.second))
#carpe_am.Analyze_Artifacts(options)

#carpe_am.Analyze_Documents()
