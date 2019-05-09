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
	request = json.loads(body)
	req_type = request['req_type']
	case_no = request['case_no']
	evd_no = request['evd_no']
	inv_no = request['inv_no']

	carpe_am = CARPE_AM()
	carpe_am.init_module(case_no, evd_no, inv_no)
	pdb.set_trace()
	# Preprocess
	if req_type == 'Preprocess':
		carpe_am.Preprocess(case_no, evd_no, inv_no)
	elif req_type == 'Filesystem':
		carpe_am.FileSystem_Analysis(case_no, evd_no, inv_no)
	elif req_type == 'SysLogAndUserData':
		carpe_am.SysLogAndUserData_Analysis(case_no, evd_no, inv_no)

	cb = functools.partial(ack_message, channel, delivery_tag)
	connection.add_callback_threadsafe(cb)

def on_message(channel, method_frame, header_frame, body, args):
	(connection, threads) = args
	delivery_tag = method_frame.delivery_tag
	t = threading.Thread(target=do_work, args=(connection, channel, delivery_tag, body))
	t.start()
	threads.append(t)

url = os.environ.get('CARPE_URL', 'amqp://carpe_rest:dfrc4738@192.168.1.2:5672/Request')
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
