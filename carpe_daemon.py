#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os, sys, time, subprocess
from datetime import datetime
import pika
import functools
import threading
import json

import carpe_am_module
# Debugging Module
import pdb

def ack_message(channel, delivery_tag):
	if channel.is_open:
		channel.basic_ack(delivery_tag)
	else:
		pass

def do_work(connection, channel, delivery_tag, body):
	request = json.loads(body.decode('utf-8').replace("'", "\""))
	req_type = request['req_type']
	case_id = request['case_id']
	evd_id = request['evd_id']
	options = request['options']
	
	print('[' + datetime.today().strftime("%Y-%m-%d %H:%M:%S") + '] New Request !')
	print('\t\t\tCase ID : ' + case_id)
	print('\t\t\tEvd ID : ' + evd_id)
	print('\t\t\tRequest Type : ' + req_type)
	
	if req_type == 'analyze':
		carpe_am = carpe_am_module.CARPE_AM()
		carpe_am.SetModule(case_id, evd_id)
		pdb.set_trace()
		carpe_am.ParseImage(options)
		carpe_am.ParseFilesystem()
		carpe_am.SysLogAndUserData_Analysis()
		print('[' + datetime.today().strftime("%Y-%m-%d %H:%M:%S") + '] Complete Evidence File Analysis !')


	cb = functools.partial(ack_message, channel, delivery_tag)
	connection.add_callback_threadsafe(cb)

def on_message(channel, method_frame, header_frame, body, args):
	(connection, threads) = args
	delivery_tag = method_frame.delivery_tag
	t = threading.Thread(target=do_work, args=(connection, channel, delivery_tag, body))
	t.start()
	threads.append(t)

url = os.environ.get('CARPE_URL', 'amqp://carpe_rest:dfrc4738@218.145.27.67:5672/Request')
params = pika.URLParameters(url)
connection = pika.BlockingConnection(params)
channel = connection.channel()
channel.queue_declare(queue='carpe_request', durable=True)
channel.basic_qos(prefetch_count=1)

threads = []
on_message_callback = functools.partial(on_message, args=(connection, threads))
channel.basic_consume('carpe_request', on_message_callback)

try:
	channel.start_consuming()
except KeyboardInterrupt:
	channel.stop_consuming()

for thread in threads:
	thread.join()

connection.close()
