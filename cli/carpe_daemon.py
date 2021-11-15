#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys
import configparser
from datetime import datetime
import pika
import functools
import threading
import json

sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
from tools import carpe_tool


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
        tool = carpe_tool.CarpeTool()
        args = []
        args.append("--cid")
        args.append(case_id)
        args.append("--eid")
        args.append(evd_id)
        if not tool.ParseArguments(args):
            return False

        tool.ExtractDataFromSources(mode='Analyze')

        print('[' + datetime.today().strftime("%Y-%m-%d %H:%M:%S") + '] Complete Evidence File Analysis !')

    cb = functools.partial(ack_message, channel, delivery_tag)
    connection.add_callback_threadsafe(cb)


def on_message(channel, method_frame, header_frame, body, args):
    print(f'on_message : \n{channel}, \n{method_frame}, \n{header_frame}, \n{body}, \n{args}')
    (connection, threads) = args
    delivery_tag = method_frame.delivery_tag
    t = threading.Thread(target=do_work, args=(connection, channel, delivery_tag, body))
    t.start()
    threads.append(t)


config = configparser.ConfigParser()
conf_file = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))) + os.sep + 'config' + os.sep + 'carpe.conf'
if not os.path.exists(conf_file):
    raise Exception('%s file does not exist.\n' % conf_file)
config.read(conf_file)
_id = config.get('rabbitmq', 'id')
_passwd = config.get('rabbitmq', 'passwd')
_host = config.get('rabbitmq', 'host')
_virtual_host = config.get('rabbitmq', 'virtual_host')
_port = config.get('rabbitmq', 'port')

credentials = pika.PlainCredentials(_id, _passwd)  # id, pw
params = pika.ConnectionParameters(credentials=credentials,
                                   host=_host,
                                   virtual_host=_virtual_host,
                                   port=_port)

connection = pika.BlockingConnection(params)
channel = connection.channel()
channel.queue_declare(queue='carpe_request', durable=True)
# channel.basic_qos(prefetch_count=1)

threads = []
# on_message_callback = functools.partial(on_message, args=(connection, threads))
# channel.basic_consume('carpe_request', on_message_callback)

on_message_callback = functools.partial(on_message, args=(connection, threads))
channel.basic_consume('carpe_request', on_message_callback)

try:
    channel.start_consuming()
except KeyboardInterrupt:
    channel.stop_consuming()

for thread in threads:
    thread.join()

connection.close()