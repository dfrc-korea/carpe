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


# 정적 설정
# 동적인 설정은 ModuleConfiguration을 이용하여 config.txt에 기록!
# --> module_config.py

        #@staticmethod
        #def isin(format):
        #    return True if format.split('_',1)[0] in C_defy.Category.__CATEGORY else False

class C_defy(object):

    COLUMNS =["EXTENSION","START","LAST","SIZE","CATEGORY"]

    # Error
    class Return(object):
        SUCCESS          = 0   # 성공
        EFAIL_DB         = -1  # Fail to connect DB
        EIOCTL           = -99 # Unsupport command

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

    class WorkLoad(object):
        LOAD_MODULE         = 0b00000000    # 모듈 로드 및 생성자

        PARAMETER           = 0b01000001    # 운영 파라미터 설정
        POLICY              = 0b01000101    # 정책 설정
        
        CONNECT_DB          = 0b01000010    # DB 연결
        DISCONNECT_DB       = 0b10000010    # DB 연결 종료

        EXEC                = 0b00000110    # 카빙 작업 실행
        REGISTER_QUEUE      = 0b01000110    # Queue 등록
        REPLAY              = 0b00010110
        SELECT_ONE          = 0b00001100
        SELECT_LIST         = 0b00010100

        EXPORT_CACHE        = 0b00101000
        EXPORT_CACHE_TO_CSV = 0b00101100
        EXPORT_CACHE_TO_DB  = 0b01101110
        REMOVE_CACHE        = 0b10100000
        FILTER_LIST         = 0b00111000

    class CATEGORY(object):
        document  = {'docx','pptx','xlsx','doc','ppt','xls','hwp'}
    
    class Signature(object) :
        Sig = {
            # 추가 검증 알고리즘이 존재하는 파일 포맷
            'aac_1'     : (b'fff1',0,2,"music"),
            'aac_2'     : (b'fff9',0,2,"music"),
            'avi'       : (b'52494646',0,4,"video"),
            'wav'       : (b'52494646',0,4,"music"),
            # Sector 내 단일 시그니처를 확인하는 포맷
            'bzip2'     : (b'425a68',0,3,"archive"),
            'flv'       : (b'464c5601',0,4,"music"),
            'exif'      : (b'ffd8ffe1',0,4,"picture"),
            'jfif'      : (b'ffd8ffe0',0,4,"picture"),
            'gif_1'     : (b'4749463837',0,5,"picture"),
            'gif_2'     : (b'4749463839',0,5,"picture"),
            #'fax'       : (b'49492a00',0,4,"document{0}etc".format(os.sep)),
            'tif_1'     : (b'49492a',0,3,"picture"),
            'tif_2'     : (b'4d4d2a',0,3,"picture"),
            'tif_3'     : (b'4d4d002a',0,4,"picture"),
            'tif_4'     : (b'4d4d002b',0,4,"picture"),
            'pcx_1'     : (b'0a0201',0,3,"picture"),
            'pcx_2'     : (b'0a0301',0,3,"picture"),
            'pcx_3'     : (b'0a0501',0,3,"picture"),
            'dcx'       : (b'b168de3a',0,4,"picture"),
            'mp3_1'     : (b'494433',0,3,"music"),
            'mp3_2'     : (b'544147',0,3,"music"),
            'mp4'       : (b'66747970',3,7,"video"),
            'png'       : (b'89504e47',0,4,"picture"),
            'wmv'       : (b'3026b2758e66cf11',0,8,"music"),
            'h264'      : (b'00000001',0,4,"video"),
            'jbig'      : (b'974a42320d0a1a0a',0,8,"music"),
            'xml_1'     : (b'3c3f786d6c',0,5,"text"),
            'xml_2'     : (b'3c3f584d4c',0,5,"text"),
            'html_1'    : (b'3c21646f63747970',0,8,"html"),
            'html_2'    : (b'3c21646f6374797065',0,8,"html"),
            'html_3'    : (b'3c68746d6c',0,5,"html"),
            'html_4'    : (b'3c48544d4c',0,5,"html"),
            'bmp'       : (b'424d',0,2,"picture"),
            'dbx'       : (b'cfad12fe',0,4,"mail"),
            'eml'       : (b'46726f6d',0,4,"mail"),
            'pst'       : (b'2142444e',0,4,"mail"),
            'gzip'      : (b'1f8b08',0,3,"archive"),
            'tar.z'     : (b'1f9d90',0,3,"archive"),
            '7z'        : (b'377abcaf271c',0,6,"archive"),
            'tar'       : (b'7573746172',0x101,0x106,"archive"),
            'compound'  : (b'd0cf11e0a1b11ae1',0,8,"document{0}compound".format(os.sep)),
            'pdf'       : (b'25504446',0,4,"document{0}pdf".format(os.sep)),
            'zip'       : (b'504b0304',0,4,"archive"),
            'alz'       : (b'414c5a01',0,4,"archive"),
            'rar'       : (b'52617221',0,4,"archive"),
            'pf'        : (b'53434341',4,4,"windows{0}prefetch".format(os.sep)),
            'MFT'       : (b'46494c45',0,4,"windows{0}mft".format(os.sep)),
            'lnk'       : (b'4c000000',0,4,"windows{0}link".format(os.sep)),
            'reg'       : (b'66676572',0,4,"windows{0}registry".format(os.sep)),
            'evt'       : (b'300000004c664c65',0,8,"windows{0}event".format(os.sep)),
            #'idx'       : (b'494e4458',0,4,"windows{0}index".format(os.sep)),
        }
