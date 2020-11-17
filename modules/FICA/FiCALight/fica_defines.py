"""
The default attribute of module :
    "name"   :"Carving_Management_Defines",            # Module 이름
    "author" :"Gimin Hur",              # Module 제작자
    "ver"    :"0.1",                # Module 버젼
    "param"  :None,                 # Module 파라미터
    "encode" :"utf-8",              # Module 인코딩
    "base"   :0                     # File image base to carve

"""
import os
import sys
import binascii
from collections import OrderedDict


# 정적 설정
# 동적인 설정은 ModuleConfiguration을 이용하여 config.txt에 기록!
# --> module_config.py

# @staticmethod
# def isin(format):
#    return True if format.split('_',1)[0] in _C_defy.CATEGORY.__CATEGORY else False

class _C_defy(object):
    class CATEGORY:
        ERROR = -1
        FILE = 1
        RECORD = 2
        UNKNOWN = 4
        SEPERABLE = 8


class C_defy(object):
    COLUMNS = ["EXTENSION", "START", "LAST", "SIZE", "CATEGORY", "OWNER"]

    # Error
    class Return(object):
        SUCCESS = 0  # 성공
        ADDITIONAL = 1
        EVOID = -1
        EINVAL_FILE = -2
        EFAIL_DB = -3  # Fail to connect DB
        EIOCTL = -99  # Unsupport command

    #
    """
    BIT FILED
    0 : Clear
    1 : Set
    2 : Export
    3 : Many
    4 : One
    5 : Work
    6 : Database
    7 : Attributes   
    """

    class MemSchema(object):
        default_columns = OrderedDict({
            "offset": 0,
            "signature": 1,
            "next_offset": 2,
            "flag": 3,
            "property": 4,
            "offset_info": 5,
            "file_name": 6,
            "file_size": 7,
            "file_path": 8
        }
        )
        showcase_columns = OrderedDict({
            "signature": 1,
            "offset": 0,
            "next_offset": 2,
            "flag": 3,
            "table": 4,
        })

    class WorkLoad(object):
        LOAD_MODULE = 0b00000000  # 모듈 로드 및 생성자
        ATTACH_ACTUATOR = 0b11111111  # 구동부 추가
        DETACH_ACTUATOR = 0b11111110  # 구동부 제거
        USE_PLUGIN = 0b11111100  # 플러그인 사용
        MODIFY_PARAMETER = 0b11111000

        NEW_CASE = 0b01000001  # 운영 파라미터 설정
        CLOSE_CASE = 0b01000101  # 정책 설정

        EXEC = 0b00000110  # 카빙 작업 실행
        CARV = 0b00001110  # 연속 블록 카빙 실행
        RECARV = 0b00010110  # 재카빙
        DECODE = 0b00010111
        UPDATE = 0b00100110  # 프레임 압축(트리 형성)

    class CATEGORY(object):
        document = {'docx', 'pptx', 'xlsx', 'doc', 'ppt', 'xls', 'hwp'}

    class SIGNATURE(object):
        CSIG = {
            # 추가 검증 알고리즘이 존재하는 파일 포맷
            # 'aac'     : (b'fff1',0,2,"music",_C_defy.CATEGORY.FILE),
            # 'aac_1'     : (b'fff9',0,2,"music",_C_defy.CATEGORY.FILE),
            # Sector 내 단일 시그니처를 확인하는 포맷
            'bzip2': (b'425a68', 0, 3, "archive", _C_defy.CATEGORY.FILE),
            'exif': (b'ffd8ffe1', 0, 4, "picture", _C_defy.CATEGORY.FILE),
            'jfif': (b'ffd8ffe0', 0, 4, "picture", _C_defy.CATEGORY.FILE),
            'gif': (b'4749463837', 0, 5, "picture", _C_defy.CATEGORY.FILE),
            'gif_1': (b'4749463839', 0, 5, "picture", _C_defy.CATEGORY.FILE),
            # 'fax'       : (b'49492a00',0,4,"document{0}etc".format(os.sep),_C_defy.CATEGORY.FILE),
            'tif': (b'49492a', 0, 3, "picture", _C_defy.CATEGORY.FILE),
            'tif_1': (b'4d4d2a', 0, 3, "picture", _C_defy.CATEGORY.FILE),
            'tif_2': (b'4d4d002a', 0, 4, "picture", _C_defy.CATEGORY.FILE),
            'tif_3': (b'4d4d002b', 0, 4, "picture", _C_defy.CATEGORY.FILE),
            'pcx': (b'0a0201', 0, 3, "picture", _C_defy.CATEGORY.FILE),
            'pcx_1': (b'0a0301', 0, 3, "picture", _C_defy.CATEGORY.FILE),
            'pcx_2': (b'0a0501', 0, 3, "picture", _C_defy.CATEGORY.FILE),
            'dcx': (b'b168de3a', 0, 4, "picture", _C_defy.CATEGORY.FILE),
            'png': (b'89504e47', 0, 4, "picture", _C_defy.CATEGORY.FILE),
            'bmp': (b'424d', 0, 2, "picture", _C_defy.CATEGORY.FILE),
            'riff': (b'52494646', 0, 4, "multimedia{0}container".format(os.sep), _C_defy.CATEGORY.FILE),
            'isobmff': (b'66747970', 4, 8, "multimedia{0}container".format(os.sep), _C_defy.CATEGORY.FILE),
            'mp3': (b'494433', 0, 3, "multimedia{0}music".format(os.sep), _C_defy.CATEGORY.FILE),
            'mp3_1': (b'544147', 0, 3, "multimedia{0}music".format(os.sep), _C_defy.CATEGORY.FILE),
            'flv': (b'464c5601', 0, 4, "multimedia{0}music".format(os.sep), _C_defy.CATEGORY.FILE),
            'wmv': (b'3026b2758e66cf11', 0, 8, "multimedia{0}music".format(os.sep), _C_defy.CATEGORY.FILE),
            'h264': (b'00000001', 0, 4, "multimedia{0}video".format(os.sep), _C_defy.CATEGORY.FILE),
            'jbig': (b'974a42320d0a1a0a', 0, 8, "multimedia{0}music".format(os.sep), _C_defy.CATEGORY.FILE),
            'xml': (b'3c3f786d6c', 0, 5, "text", _C_defy.CATEGORY.FILE),
            'xml_1': (b'3c3f584d4c', 0, 5, "text", _C_defy.CATEGORY.FILE),
            'html': (b'3c21646f63747970', 0, 8, "html", _C_defy.CATEGORY.FILE),
            'html_1': (b'3c21646f6374797065', 0, 8, "html", _C_defy.CATEGORY.FILE),
            'html_2': (b'3c68746d6c', 0, 5, "html", _C_defy.CATEGORY.FILE),
            'html_3': (b'3c48544d4c', 0, 5, "html", _C_defy.CATEGORY.FILE),
            'dbx': (b'cfad12fe', 0, 4, "mail", _C_defy.CATEGORY.FILE),
            'pst': (b'2142444e', 0, 4, "mail", _C_defy.CATEGORY.FILE),
            'gzip': (b'1f8b08', 0, 3, "archive", _C_defy.CATEGORY.FILE),
            'tar.z': (b'1f9d90', 0, 3, "archive", _C_defy.CATEGORY.FILE),
            '7z': (b'377abcaf271c', 0, 6, "archive", _C_defy.CATEGORY.FILE),
            'tar': (b'7573746172', 0x101, 0x106, "archive", _C_defy.CATEGORY.FILE),
            'compound': (b'd0cf11e0a1b11ae1', 0, 8, "document{0}compound".format(os.sep), _C_defy.CATEGORY.FILE),
            'pdf': (b'25504446', 0, 4, "document{0}pdf".format(os.sep), _C_defy.CATEGORY.FILE),
            'zip': (b'504b0304', 0, 4, "archive", _C_defy.CATEGORY.FILE),
            'alz': (b'414c5a01', 0, 4, "archive", _C_defy.CATEGORY.FILE),
            'rar': (b'52617221', 0, 4, "archive", _C_defy.CATEGORY.FILE),
            'pf': (b'53434341', 4, 8, "windows{0}prefetch".format(os.sep), _C_defy.CATEGORY.FILE),
            'pf_1': (b'4d414d', 0, 3, "windows{0}prefetch".format(os.sep), _C_defy.CATEGORY.FILE),
            'MFT': (b'46494c45', 0, 4, "windows{0}mft".format(os.sep), _C_defy.CATEGORY.RECORD),
            'lnk': (b'4c000000', 0, 4, "windows{0}link".format(os.sep), _C_defy.CATEGORY.FILE),
            'reg': (b'66676572', 0, 4, "windows{0}registry".format(os.sep), _C_defy.CATEGORY.FILE),
            'evt': (b'300000004c664c65', 0, 8, "windows{0}event".format(os.sep),
                    _C_defy.CATEGORY.RECORD | _C_defy.CATEGORY.SEPERABLE),
            'evt_1': (b"456c6646696c6500", 0, 8, "windows{0}event".format(os.sep),
                      _C_defy.CATEGORY.RECORD | _C_defy.CATEGORY.SEPERABLE),
            'idx': (b'494e4458', 0, 4, "windows{0}index".format(os.sep), _C_defy.CATEGORY.FILE),
        }

    HELP = """< FiCA 카빙 사용 방법 >
1. Profile 탭에서 프로파일 설정
   < Operation >
   New  : 카빙 데이터를 탐지하여 파일 추출
   Redo : 이전 결과를 이용해서 빠르게 파일 추출
   < 설정 저장 >
   Done 버튼 클릭하여 카빙에 사용할 프로파일 저장
2. File-파일 열기 (F2)/ File-디렉토리 열기 (ctrl+o)
3. Action-카빙 시작 (F3)

< FiCA 모듈 추가/제거 >
1. Settings-플러그인 추가/제거 실행 (ctrl+m)
2. config 탭 수정 후 Settings-설정 저장 (ctrl+s)
3. Settings-플러그인 리프레시 (F5)
* 각 줄 앞에 %나 #을 붙이면 해당 플러그인은 비활성화 됨
    """
