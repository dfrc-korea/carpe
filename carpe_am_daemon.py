import os, time, logging, subprocess
import pika
import functools
import threading
import json

from utility import carpe_db
from image_analyzer import split_disk
from image_analyzer import scan_disk
from filesystem_analyzer import carpe_fs_analyzer

# Debugging Module
import pdb

LOG_FORMAT = ('[%(asctime)s] %(levelname) -5s %(message)s')
LOGGER = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)

class CARPE_AM:
	def __init__(self):
		self.case_name = None
		self.evd_name = None
		self.inv_name = None
		self.src_path = None
		self.dst_path = None

	def init_module(self, case_no, evd_no, inv_no):
		# Connect Carpe Database
		db = carpe_db.Mariadb()
		db.open()

		# Get Source Path
		query = 'SELECT evd_name, file_path FROM tn_evidence WHERE case_no = ' + str(case_no) + ' and evd_no = ' + str(evd_no) + ';'
		(self.evd_name, self.src_path) = db.execute_query(db._conn, query)

		# Get Case & Evidence Name
		query = 'SELECT case_name FROM tn_case WHERE case_no = ' + str(case_no) + ';'
		self.case_name = db.execute_query(db._conn, query)

		db.close()

		# Create directory to store splitted image
		self.dst_path = '/data/share/image' + '/' + self.case_name + '/' + self.evd_name + '/splitted'

	def Preprocess(self, case_no, evd_no, inv_no):
		'''
			Module to analyze the image file.
			This module parse the partition list in image file.
			And split image by partition.
		'''
		if not os.path.exists(self.dst_path):
			os.mkdir(self.dst_path)
		
		# Get partition list in image file
		output_writer = split_disk.FileOutputWriter(self.dst_path)
		mediator = scan_disk.DiskScannerMediator()
		disk_scanner = scan_disk.DiskScanner(mediator=mediator)
		
		base_path_specs = disk_scanner.GetBasePathSpecs(self.src_path)
		disk_info = disk_scanner.ScanDisk(base_path_specs)
		
		# Insert partition list

		# Split image file
		disk_spliter = split_disk.DiskSpliter(disk_info)
		disk_spliter.SplitDisk(output_writer)

	def FileSystem_Analysis(self, case_no, evd_no, user_id):
		# Conenct Carpe Database
		db = carpe_db.Mariadb()
		db.open()

		# Get image file list
		query = 'SELECT file_path  FROM tn_evidence_splitted WHERE case_no = ' + str(case_no) + ' and evd_no = ' + str(evd_no) + ';'
		image_list = db.execute_query(db._conn, query)
		db.close()
		
		# Temporary code
		for image in image_list:
			subprocess.call(['python', '../filesystem_analyzer/carpe_fls', 'option'])

		'''
		# Parse file and directory list in image file
		procs = []
		for image in image_list:
			proc = Process(target=self.ParseFilesystem, args=(image))
			proc.start()
			procs.append(proc)

		for proc in procs:
			proc.join()

		'''
	
	def ParseFilesystem(self, image):
		fls = carpe_fs_analyzer.Fls()
		fls.open_image('raw', image)
		fls.open_file_system(0)
		directory = fls.open_directory('?')
		fls.list_directory(directory, [], [])

	def SysLogAndUserData_Analysis(self, case_no, evd_no, inv_no):
		# Conenct Carpe Database
		db = carpe_db.Mariadb()
		db.open()

		# Get image file list
		query = 'SELECT file_name, file_path FROM tn_evidence_splitted WHERE case_no = ' + str(case_no) + ' and evd_no = ' + str(evd_no) + ';'
		image_name, image_list = db.execute_query(db._conn, query)
		db.close()

		# Temporary code
		for name, image in image_name, image_list:
			subprocess.call(['python3.6', '../plaso_tool/log2timeline.py', name + '.plaso', image])

		for name in image_name:
			subprocess.call(['python3.6', '../plaso_tool/psort.py', '-o', '4n6time_mariadb', name + '.plaso'])

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
