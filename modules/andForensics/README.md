# andForensics
## *Introduction*
andForensics is a open-source **Mobile forensic tool for Android device**, written python 3.7.4, runs in Windows environment. This tool used several open-source projects, [TSK](https://www.sleuthkit.org/sleuthkit/download.php) (The Sleuth Kit) bianries for file system analysis, and [JADX](https://github.com/skylot/jadx) (Dex to Java decompiler) for APK decompilation.

## *Features*
andForensics is composed 3 phases.
### 1. Scanning
 - File system analyzing with `tsk_loaddb.exe` binary of TSK (The Sleuth Kit).
 - Extracting the file system status.
 - Extracting Android system log information.
### 2. Pre-processing
 - Grouping all files in a file system by application (system, third party).
 - Classifying all files in the filesystem by signature, file name, and extension.
 - Decompiling APK files using `JADX`. (optional)
 - Extracting user information (timestamp, ID, geodata, etc.) by analyzing all app logs in SQLite database format.
### 3. Analyzing
 - Analyzing system logs and file system information to extract all app information installed on userdata image file of Android device(including deleted apps).
 - Extracting information about the original files in the compressed file. (For now, only analyzes the APK file format)
 - Analyzing all app logs existing in userdata image file and extracting contents including user information as below.
   - Extracting contents containing the user account. (ID, PW, etc)
   - Extracting contents containing the call history.
   - Extracting contents containing the geodata(latitude, longitude).
   - Extracting contents containing the web browser history.
   - Extracting contents containing the file history.
   - *Items will continue to be added...*
 
## *Dependencies*
- `Python3.x` for overall procedure.
- `JAVA` for APK decompiling with [JADX](https://github.com/skylot/jadx).

## *Usage*
```
usage: andForensics.py [-h] [-i INPUT_DIR] [-o OUTPUT_DIR] [-p PHASE]
                       [-d DECOMPILE_APK] [-proc NUMBER_PROCESS] [-v]

optional arguments:
  -h, --help            show this help message and exit
  -i INPUT_DIR          Input directory containing the Android image file with EXT4 file system. 
                        It can have multiple image files.
  -o OUTPUT_DIR         Output directory to store analysis result files.
  -p PHASE              Select a single investigation phase. (default: all phases)
                         - [1/3] Scanning: "scan"
                         - [2/3] Pre-processing: "preproc" (only after "Scanning" phase)
                         - [3/3] Analyzing: "analysis" (only after "Pre-processing" phase)
                         e.g., andForensics.py -i <INPUT_DIR> -o <OUTPUT_DIR> -p preproc
  -d DECOMPILE_APK      Select whether to decompile the APK file. This operation is time-consuming and 
                        requires a large capacity. (1:enable, 0:disable, default:disable)
  -proc NUMBER_PROCESS  Input the number of processes for multiprocessing. (default: single processing)
  -v                    Show verbose (debug) output.
```

> *A simple example is as follows:*
```
python3 andForensics.py -i c:\case_image_dir\ -o c:\output_dir -proc 8
```
The above command means:
- The **<c:\case_image_dir>** directory contains the image file of the userdata partition on the Android device with the Ext4 filesystem.
- andForensics will save the output files to the **<c:\output_dir>** directory.
- andForensics will multiprocess using **eight processors**.


> *An example of the execution screen of andForensics is as follows:*

The input data is a userdata partition of the SM-N920S (Samsung GalaxyS6) 64GB model.

```
exdus@DOHYUN-LEGIONC7 C:\GIT\andForensics
$ python3 andForensics.py -i C:\Case\SM-N920S_GalaxyS6 -o c:\output -proc 10




                       888 8888888888                                         d8b
                       888 888                                                Y8P
                       888 888
 8888b.  88888b.   .d88888 8888888  .d88b.  888d888 .d88b.  88888b.  .d8888b  888  .d8888b .d8888b
    "88b 888 "88b d88" 888 888     d88""88b 888P"  d8P  Y8b 888 "88b 88K      888 d88P"    88K
.d888888 888  888 888  888 888     888  888 888    88888888 888  888 "Y8888b. 888 888      "Y8888b.
888  888 888  888 Y88b 888 888     Y88..88P 888    Y8b.     888  888      X88 888 Y88b.         X88
"Y888888 888  888  "Y88888 888      "Y88P"  888     "Y8888  888  888  88888P' 888  "Y8888P  88888P'





[2020-01-11 15:47:59,050] [INFO] Start...
[2020-01-11 15:47:59,053] [INFO] [1/3] Scanning...
[2020-01-11 15:47:59,079] [INFO]     - File system information with TSK (loaddb)...
[2020-01-11 15:48:08,379] [INFO]     - File system status...
[2020-01-11 15:48:08,617] [INFO]     - Extracting the system log information (/data/system/packages.xml)...
[2020-01-11 15:48:17,088] [INFO]     - Extracting the system log information (/data/system/packages.list)...
[2020-01-11 15:48:17,089] [INFO]     - Extracting the AID information...
[2020-01-11 15:48:17,604] [INFO] [2/3] Pre-processing...
[2020-01-11 15:48:17,633] [INFO]     - Data grouping with package name information...
[2020-01-11 15:48:45,461] [INFO]     - Data grouping with app name information...
[2020-01-11 15:48:51,933] [INFO]     - Data classifying with file signature...
[2020-01-11 15:56:37,921] [INFO]     - Data classifying with file name (SQLite-journal)...
[2020-01-11 15:56:37,993] [INFO]     - Data classifying with file name (APK)...
[2020-01-11 15:56:38,036] [INFO]     - Extracting the SQLITEDB files...
[2020-01-11 15:56:56,664] [INFO]     - Extracting the APK files...
[2020-01-11 15:56:58,984] [INFO]     - Analyzing all SQLite databases for searching user information...
[2020-01-11 15:57:09,660] [INFO] [3/3] Analyzing...
[2020-01-11 15:57:09,718] [INFO]     - Analyze the application list...
[2020-01-11 15:57:16,435] [INFO]     - Analyze the ID and Password data...
[2020-01-11 15:57:16,883] [INFO]     - Analyze the call history data...
[2020-01-11 15:57:36,021] [INFO]     - Analyze the geodata...
[2020-01-11 15:57:45,248] [INFO]     - Analyze the web browser history data...
[2020-01-11 16:00:11,388] [INFO]     - Analyze the file history data...
[2020-01-11 16:03:01,321] [INFO]     - Analyze the embedded data...
[2020-01-11 16:03:01,322] [INFO]     - Analyze the APK files...
[2020-01-11 16:12:20,217] [INFO] End...
[2020-01-11 16:12:20,218] [INFO] elapsed time : 24.35 min (1461.17 sec)

```


## *List of test phones*
No. | OEM | Model | Name | Description
--- | ----|-------|------|-------------
1|	Samsung|	SHV-E210S|	Galaxy S3 LTE|  
2|	Samsung|	SHV-E250K|	Galaxy Note2|
3|	Samsung|	SHV-E250L|	Galaxy Note2|   [DFRWS 2017-2018 Forensic Challenge](https://jijames.github.io/DFRWS2018Challenge/)
4|	Samsung|	SHV-E250S|	Galaxy Note2|   [DFRWS 2017-2018 Forensic Challenge](https://jijames.github.io/DFRWS2018Challenge/)
5|	Samsung|	SHV-E250S|	Galaxy Note2|   
6|	Samsung|	SHV-E270L|	Galaxy Grand|   
7|	Samsung|	SHV-E300K|	Galaxy S4|      
8|	Samsung|	SHV-E300S|	Galaxy S4|      
9|	Samsung|	SHV-E330S|	Galaxy S4 LTE-A|
10|	Samsung|	SHV-E370K|	Galaxy S4 Mini| 
11|	Samsung|	SHV-E500L|	Galaxy Win|     
12|	Samsung|	SHV-E500S|	Galaxy Win|     
13|	Samsung|	SHW-M440S|	Galaxy S3|      
14|	Samsung|	SM-G900L|	Galaxy S5|      
15|	Samsung|	SM-G920S|	Galaxy S6|      
16|	Samsung|	SM-N900K|	Galaxy Note3|   
17|	Samsung|	SM-N900S|	Galaxy Note3|   
18|	Samsung|	SM-N910K|	Galaxy Note4|   
19|	Samsung|	SM-N910L|	Galaxy Note4|   
20|	Samsung|	SM-N910S|	Galaxy Note4|   
21|	Samsung|	SM-N920S|	Galaxy Note5|   
22|	Samsung|	SM-T255S|	Galaxy W|       
23|	LG|	     LG-F160S|	Optimus LTE2|   
24|	LG|     	LG-F200K|	Optimus Vu2|    
25|	LG|     	LG-F240S|	Optimus G pro|  
26|	LG|     	LG-F310L|	LG GX|          
27|	LG|     	LG-F320L|	LG G2|          
28|	LG|     	LG-F350S|	LG G Pro2|      
29|	LG|     	LG-F400K|	LG G3|          
30|	Pantech|	IM-A830K|	Vega Racer2|    
31|	Pantech|	IM-A850S|	Vega R3|        
32|	Pantech|	IM-A870L|	Vega Iron|      
33|	Pantech|	IM-A890S|	Vega Secret Note|
