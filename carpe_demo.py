from image_analyzer import scan_disk
from image_analyzer import split_disk
from filesystem_analyzer import carpe_db
from filesystem_analyzer import carpe_fs_analyzer
from dfvfs.lib import errors

import sys, os, subprocess
import argparse
import pymysql

from datetime import datetime

import pdb

def Main():
    argument_parser = argparse.ArgumentParser(description=(
        'CARPE Forensics Demo Program (CLI Ver).'
    ))

    argument_parser.add_argument(
        '--output_directory', '--output-directory', dest='output_dir', action='store',
        metavar='source.hashed', default=None, help=(
            'path of the output directory.'
        )
    )

    argument_parser.add_argument(
        'case_number', nargs='?', action='store', metavar='Case Number',
        default=None, help='Case Number.'
    )

    argument_parser.add_argument(
        'case_name', nargs='?', action='store', metavar='Case Name',
        default=None, help='Case Name.'
    )

    argument_parser.add_argument(
        'administrator', nargs='?', action='store', metavar='Administrator',
        default=None, help='Administrator.'
    )

    argument_parser.add_argument(
        'source', nargs='?', action='store', metavar='image.raw',
        default=None, help='path of the directory or storage media image.'
    )

    options = argument_parser.parse_args()

    if not options.source:
        print('Source value is missing.')
        argument_parser.print_help()
        return False

    if options.output_dir:
        output_dir = options.output_dir
    else:
        output_dir = os.getcwd()
 
    # insert case info & evidence info
    db = carpe_db.Mariadb()
    db.open()
    
    # Case Info
    case_id = 0 
    case_no = options.case_number
    case_name = options.case_name
    administrator = options.administrator
    create_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    desc = 'CARPE DEMO Program.'

    query = "INSERT INTO carpe_case_info VALUES(" + str(case_id) + ",'" + case_no + "','" + case_name + "','" + administrator + "','" + create_date + "','" + desc + "');"
    db.execute_query(query)

    query = "SELECT LAST_INSERT_ID();"
    case_id = int(db.execute_query(query)[0])

    # Evidence Info
    evd_id = 0
    evd_no = options.source.split('/')[1].split('.')[0]
    type1 = 'image'
    type2 = options.source.split('/')[1].split('.')[1]
    added_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    md5 = ''
    sha1 = ''
    sha256 = ''
    path = output_dir + '/' + options.source.split('/')[1]
    time_zone = 'UTC+9'

    query = "INSERT INTO carpe_evidence_info VALUES(" + str(evd_id) + ",'" + evd_no + "','" + str(case_id) + "','" + type1 + "','" + type2 + "','" + added_date + "','" + md5 + "','" + sha1 + "','" + sha256 + "','" + path + "','" + time_zone + "');"
    db.execute_query(query)

    query = "SELECT LAST_INSERT_ID();"
    evd_id = int(db.execute_query(query)[0])

    '''
        
        Scan & Split Disk

    '''
    output_writer = split_disk.FileOutputWriter(output_dir)
 
    return_value = True
    disk_scanner = scan_disk.DiskScanner()
    
    # Scan Disk
    try:

        disk_info = disk_scanner.Analyze(options.source)
    except errors.ScannerError as exception:
        return_value = False

        print('')
        print('[ERROR] {0!s}'.format(exception))

    except KeyboardInterrupt:
        return_value = False

        print('')
        print('Aborted by user.')
    
    if disk_info is None:
        return False
    
    # Insert Partition Info
    
    for i in disk_info:
        if (i["type_indicator"] != "VSHADOW"):
            par_id = 0
            par_name = i['vol_name']
            par_path = output_dir + '/' + i['vol_name']
            par_type = i["type_indicator"]
            sector_size = str(i["bytes_per_sector"])
            par_size = str(i["length"])

            query = "INSERT INTO carpe_partition_info VALUES('" + str(par_id) + "','" + par_name + "','" + par_path + "','" + str(evd_id) + "','" + par_type + "','" + sector_size + "','" + par_size + "','" + sha1 + "','" + sha256 + "','" + time_zone + "');"
            db.execute_query(query)

    db.close()
    
    # Split Disk
    disk_spliter = split_disk.DiskSpliter(disk_info)
    #disk_spliter.SplitDisk(output_writer)

    '''

        Filesystem Analysis

    '''
    for i in disk_info:
        if (i["type_indicator"] != "VSHADOW"):
            print(i['vol_name'])
            #subprocess.call(['python', 'filesystem_analyzer/carpe_fs_analyzer.py', '-r', str(i['vol_name'])])

    '''
        System Log & User Data Analysis

    '''
    for i in disk_info:
        if(i["type_indicator"] != "VSHADOW"):
            print(i['vol_name'])
            #subprocess.call(['python', 'plaso_tool/log2timeline.py', ])
            #subprocess.call(['python', 'plaso_tool/psort.py',])
            

if __name__ == "__main__":
    if not Main():
        sys.exit(1)
    else:
        sys.exit(0)
