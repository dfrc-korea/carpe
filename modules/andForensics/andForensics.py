import argparse
import os
import sys
import logging
import shutil
import time
from modules.andForensics.modules.utils.android_case import Case
from modules.andForensics.modules.utils.android_TSK import TSK
from modules.andForensics.modules.scanner.android_image_info_extractor import ImageInfo
from modules.andForensics.modules.scanner.android_system_log_info_extractor import SystemLog
from modules.andForensics.modules.preprocessor.android_data_classifier import Classifier
from modules.andForensics.modules.preprocessor.android_file_extractor import FileExtractor
from modules.andForensics.modules.preprocessor.android_apk_decompiler import APKDecompiler
from modules.andForensics.modules.preprocessor.android_sqlitedb_analyzer import SQLiteAnalyzer
from modules.andForensics.modules.analyzer.android_data_analyzer import DataAnalyzer

logger = logging.getLogger('andForensics')

def main(args):
    logging.basicConfig(format = '[%(asctime)s] [%(levelname)s] %(message)s', stream = sys.stdout)
    logger.setLevel(logging.DEBUG if args.v else logging.INFO)

    logger.info('Start...')
    t1 = time.perf_counter()
    start_time = time.ctime()

    case = Case(args)
    if not case.check_number_process():
        logger.error('Please input a valid processes number. This system have %d processes but your input value is %d' % (case.number_of_system_processes, case.number_of_input_processes))
        exit(0)

    list_image_file_path = case.find_list_image_file_path()
    if not list_image_file_path:
        logger.error('Please input a valid INPUT_DIR argument.')
        exit(0)

    for image_file_path in list_image_file_path:
        log_file_path = case.set_file_path(args, image_file_path)
        logger.addHandler(logging.FileHandler(log_file_path))

        if (args.phase is None) | (args.phase == "scan"):
            logger.info('[1/3] Scanning...')
            case.create_preprocess_db()
            ImageInfo.extract_fs_information(case)
            ImageInfo.extract_fs_status(case)
            SystemLog.extract_system_log_information(case)

        if (args.phase is None) | (args.phase == "preproc"):
            logger.info('[2/3] Pre-processing...')
            Classifier.data_grouping_appdata_with_package_filesystem_path(case)
            Classifier.data_classify_all_files_with_signature(case)
            Classifier.data_classify_all_files_with_file_name(case)
            FileExtractor.extract_files_with_format(case, "SQLITEDB")
            FileExtractor.extract_files_with_format(case, "APK")
            if int(args.decompile_apk) == 1:
                APKDecompiler.decompile_with_jadx(case)
            SQLiteAnalyzer.analyze_sqlitedb(case)

        if (args.phase is None) | (args.phase == "analysis"):
            logger.info('[3/3] Analyzing...')
            case.create_analysis_db()
            DataAnalyzer.analyze_system_log(case)
            DataAnalyzer.analyze_application_log(case)
            DataAnalyzer.analyze_files(case)

    logger.info('End...')
    end_time = time.ctime()
    t2 = time.perf_counter()
    logger.info('elapsed time : %0.2f min (%0.2f sec)' %  ((t2-t1)/60, t2-t1))
    logger.info('Process End')

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description = 'andForensics - Android Forensic Tool \nsimple usage example: python3 andForensics.py -i <INPUT_DIR> -o <OUTPUT_DIR> -proc <NUMBER OF PROCESS FOR MULTIPROCESSING>', formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('-i', action = "store", dest = "input_dir",
                        help = "Input directory containing the Android image file with EXT4 file system. \nIt can have multiple image files.")
    parser.add_argument('-o', action = "store", dest = "output_dir",
                        help = "Output directory to store analysis result files.")
    parser.add_argument('-p', action = "store", dest = "phase",
                        help = "Select a single investigation phase. (default: all phases) \n - [1/3] Scanning: \"scan\"\n - [2/3] Pre-processing: \"preproc\" (only after \"Scanning\" phase) \n - [3/3] Analyzing: \"analysis\" (only after \"Pre-processing\" phase) \n e.g., andForensics.py -i <INPUT_DIR> -o <OUTPUT_DIR> -p preproc")
    parser.add_argument('-d', action = "store", dest = "decompile_apk", default = 0,
                        help = "Select whether to decompile the APK file. This operation is time-consuming and requires a large capacity. \n(1:enable, 0:disable, default:disable)")
    parser.add_argument('-proc', action = "store", dest = "number_process",
                        help = "Input the number of processes for multiprocessing. (default: single processing)")
    parser.add_argument('-v', action = "store_true", 
    					help = "Show verbose (debug) output.")
    print(sys.argv)
    args = parser.parse_args()

    print('''   
                                                          


                       888 8888888888                                         d8b                   
                       888 888                                                Y8P                   
                       888 888                                                                      
 8888b.  88888b.   .d88888 8888888  .d88b.  888d888 .d88b.  88888b.  .d8888b  888  .d8888b .d8888b  
    "88b 888 "88b d88" 888 888     d88""88b 888P"  d8P  Y8b 888 "88b 88K      888 d88P"    88K      
.d888888 888  888 888  888 888     888  888 888    88888888 888  888 "Y8888b. 888 888      "Y8888b. 
888  888 888  888 Y88b 888 888     Y88..88P 888    Y8b.     888  888      X88 888 Y88b.         X88 
"Y888888 888  888  "Y88888 888      "Y88P"  888     "Y8888  888  888  88888P' 888  "Y8888P  88888P' 
                                                                                                    



   	''')
    if (args.input_dir is None) | (args.output_dir is None):
    	parser.print_help()
    	exit(0)
    if (args.phase is not None) & ((args.phase != "scan") & (args.phase != "preproc") & (args.phase != "analysis")):
        parser.print_help()
        exit(0)


    main(args)

