#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os, time, subprocess
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
	body = body.replace("'", "\"")
	request = json.loads(body)
	req_id = request['req_id']
	req_type = request['req_type']
	case_id = request['case_id']
	evd_id = request['evd_id']
	options = request['options']

	if req_id == '1':
		# Analysis Request
		carpe_am = carpe_am_module.CARPE_AM()

		# Set Module Information
		carpe_am.SetModule(case_id, evd_id)

		if req_type == 'analyze':
			carpe_am.SysLogAndUserData_Analysis(case_id, evd_id)
			print('Request Analysis!')
		
		else:
			print('Request Type Error!')

	elif req_id == '2':
		# Visualzation Request
		print('Visualzation Request')

	cb = functools.partial(ack_message, channel, delivery_tag)
	connection.add_callback_threadsafe(cb)

def on_message(channel, method_frame, header_frame, body, args):
	(connection, threads) = args
	delivery_tag = method_frame.delivery_tag
	t = threading.Thread(target=do_work, args=(connection, channel, delivery_tag, body))
	t.start()
	threads.append(t)
'''
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


TEST SET

delete from partition_info where evd_id='e1c1004619edb24ffcb5ca1e48ec3c73cf';
'''
case_id = 'c16011ffad0b3a44e78aed17b366023f9c'
evd_id = 'e1c1004619edb24ffcb5ca1e48ec3c73cf'

option = {
	'vss':'false'
}

carpe_am = carpe_am_module.CARPE_AM()
carpe_am.SetModule(case_id, evd_id)
carpe_am.ParseImage(option)
#carpe_am.ParseFilesystem()
carpe_am.SysLogAndUserData_Analysis()
