# -*- coding: utf-8 -*-
"""This file contains a parser for the Android SMS database.

Android SMS messages are stored in SQLite database files named mmssms.dbs.
"""
import os
import sqlite3
import pathlib
import datetime

from modules.android_basic_apps import logger


mms_query = \
'''
    SELECT pdu._id as mms_id, 
        thread_id, 
        CASE WHEN date>0 THEN pdu.date
             ELSE 0
        END as date,
        CASE WHEN date_sent>0 THEN pdu.date_sent
             ELSE 0
        END as date_sent,
        read,
        (SELECT address FROM addr WHERE pdu._id=addr.msg_id and addr.type=0x89)as "FROM",
        (SELECT address FROM addr WHERE pdu._id=addr.msg_id and addr.type=0x97)as "TO",
        (SELECT address FROM addr WHERE pdu._id=addr.msg_id and addr.type=0x82)as "CC",
        (SELECT address FROM addr WHERE pdu._id=addr.msg_id and addr.type=0x81)as "BCC",
        CASE WHEN msg_box=1 THEN "Received" 
             WHEN msg_box=2 THEN "Sent" 
             ELSE msg_box 
        END as msg_box,
        part._id as part_id, seq, ct, cl, _data, text 
    FROM pdu LEFT JOIN part ON part.mid=pdu._id
    ORDER BY pdu._id, date, part_id 
'''
'''
        CASE WHEN date>0 THEN datetime(pdu.date, 'UNIXEPOCH')
             ELSE ""
        END as date,
        CASE WHEN date_sent>0 THEN datetime(pdu.date_sent, 'UNIXEPOCH')
             ELSE ""
        END as date_sent,
'''
sms_query =\
'''
    SELECT _id as msg_id, thread_id, address, person, 
        CASE WHEN date>0 THEN date
             ELSE 0
        END as date,
        CASE WHEN date_sent>0 THEN date_sent
             ELSE 0
        END as date_sent,
        read,
        CASE WHEN type=1 THEN "Received"
             WHEN type=2 THEN "Sent"
             ELSE type 
        END as type,
        body, service_center, error_code
    FROM sms
    ORDER BY date
'''
'''
        CASE WHEN date>0 THEN datetime(date/1000, 'UNIXEPOCH')
             ELSE ""
        END as date,
        CASE WHEN date_sent>0 THEN datetime(date_sent/1000, 'UNIXEPOCH')
             ELSE ""
        END as date_sent,
'''
def _search(target_directory, pattern):
    """Directory search using pattern.

    Args:
        target_directory (str): target directory.
        pattern (str): pattern.
    """
    pathlist = []
    for file in pathlib.Path(target_directory).rglob(pattern):
        pathlist.append(file)
    return pathlist

def parse_smsmms(target_files, result_path):
    """Parse SMS and MMS databases.

    Args:
        target_files (list): target files.
        result_path (str): result path.
    """
    logger.info('Parse SMS and MMS databases.')
    results = []
    for file in target_files:
        if str(file).endswith('mmssms.db'):
            database = sqlite3.connect(str(file))
            database.row_factory = sqlite3.Row

            sms_data = _parse_sms(database, result_path)
            if sms_data:
                results.append(sms_data)

            mms_data = _parse_mms(database, result_path)
            if mms_data:
                results.append(mms_data)

    return results

def _parse_sms(database, result_path):
    """Parse SMS messages.

    Args:
        database (SQLite3): target SQLite3 database.
        result_path (str): result path.
    """
    cursor = database.cursor()
    cursor.execute(sms_query)
    results = cursor.fetchall()
    num_of_results = len(results)

    data = {}
    data['title'] = 'sms'
    header = ('msg_id', 'thread_id', 'address', 'contact_id', 'date',
            'date_sent', 'read', 'type', 'body', 'service_center', 'error_code')
    data['number_of_data_headers'] = len(header)
    data['number_of_data'] = num_of_results
    data['data_header'] = header
    data_list = []
    if num_of_results >0:
        for row in results:
            if row['date_sent'] != 0:
                data_list.append((row['msg_id'], row['thread_id'], row['address'], row['person'],
                    datetime.datetime.fromtimestamp(row['date'] / 1000, datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
                    datetime.datetime.fromtimestamp(row['date_sent'] / 1000, datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
                    row['read'], row['type'], row['body'], row['service_center'], row['error_code']))
            else:
                data_list.append((row['msg_id'], row['thread_id'], row['address'], row['person'],
                    datetime.datetime.fromtimestamp(row['date'] / 1000, datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
                    '', row['read'], row['type'], row['body'], row['service_center'], row['error_code']))

        data['data'] = data_list
    else:
        logger.warning('NO SMS Messages found!')

    return data

def _parse_mms(database, result_path):
    """Parse MMS messages.

    Args:
        database (SQLite3): target SQLite3 database.
        result_path (str): result path.
    """
    parent_path = pathlib.Path(result_path)
    parent_path = parent_path.parent

    cursor = database.cursor()
    cursor.execute(mms_query)
    results = cursor.fetchall()
    num_of_results = len(results)

    data = {}
    data['title'] = 'mms'
    header = ('mms_id', 'thread_id', 'date', 'date_sent', 'read',
            'from', 'to', 'cc', 'bcc', 'body')
    data['number_of_data_headers'] = len(header)
    data['number_of_data'] = num_of_results
    data['data_header'] = header
    data_list = []

    if num_of_results >0:
        for row in results:
            if row['date_sent'] != 0:
                msg = MmsMessage(row['mms_id'], row['thread_id'],
                    datetime.datetime.fromtimestamp(row['date'], datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
                    datetime.datetime.fromtimestamp(float(row['date_sent']) / 1000, datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
                    row['read'], row['FROM'], row['TO'], row['CC'], row['BCC'], row['msg_box'], row['part_id'],
                    row['seq'], row['ct'], row['cl'],row['_data'], row['text'])
            else:
                msg = MmsMessage(row['mms_id'], row['thread_id'],
                    datetime.datetime.fromtimestamp(row['date'], datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
                    '', row['read'], row['FROM'], row['TO'], row['CC'], row['BCC'], row['msg_box'], row['part_id'],
                    row['seq'], row['ct'], row['cl'],row['_data'], row['text'])

            if row['_data'] == None:
                msg.body = row['text']
            else:
                #TODO: attachment is existed!
                result = _search(parent_path, '**'+os.sep+os.path.basename(row['_data']))
                if result:
                    msg.filename = str(result[0])
                    msg.body = msg.filename
                else:
                    logger.info('Attachment file is not found!'.format(row['_data']))


            temp = (msg.mms_id, msg.thread_id,
                        msg.date, msg.date_sent, msg.read,
                        msg.From, msg.to, msg.cc, msg.bcc,
                        msg.body)
            data_list.append(temp)
        data['data'] = data_list

    return data

class MmsMessage:
    def __init__(self, mms_id, thread_id, date, date_sent, read, From, to, cc, bcc, type, part_id, seq, ct, cl, data, text):
        self.mms_id = mms_id
        self.thread_id = thread_id
        self.date = date
        self.date_sent = date_sent
        self.read = read
        self.From = From
        self.to = to
        self.cc = cc
        self.bcc = bcc
        self.type = type
        self.part_id = part_id
        self.seq = seq
        self.ct = ct
        self.cl = cl
        self.data = data
        self.text = text
        # Added
        self.body = ''
        self.filename = ''