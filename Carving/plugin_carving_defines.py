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
        LOAD_MODULE         = 0b00000000

        PARAMETER           = 0b01000001
        POLICY              = 0b01000101
        
        CONNECT_DB          = 0b01000010
        DISCONNECT_DB       = 0b10000010

        EXEC                = 0b00000110
        REPLAY              = 0b00010110
        SELECT_ONE          = 0b00001100
        SELECT_LIST         = 0b00010100

        EXPORT_CACHE        = 0b00101000
        EXPORT_CACHE_TO_CSV = 0b00101100
        REMOVE_CACHE        = 0b10100000
        FILTER_LIST         = 0b00111000

    class CATEGORY(object):
        document  = {'docx','pptx','xlsx','doc','ppt','xls','hwp'}
    
    class Signature(object) :
        Sig = {
            # 추가 검증 알고리즘이 존재하는 파일 포맷
            'aac_1'    : (b'fff1',0,2,"music"),
            'aac_2'    : (b'fff9',0,2,"music"),
            # Sector 내 단일 시그니처를 확인하는 포맷
            'avi'      : (b'52494646',0,4,"video"),
            'bzip2'    : (b'425a68',0,3,"archive"),
            'compound' : (b'd0cf11e0a1b11ae1',0,8,"document{0}compound".format(os.sep)),
            'fax'      : (b'49492a00',0,4,"document{0}etc".format(os.sep)),
            'flv'      : (b'464c5601',0,4,"music"),
            'gif_1'    : (b'4946383761',0,5,"picture"),
            'gif_2'    : (b'4749463839',0,5,"picture"),
            'exif'     : (b'ffd8ffe1',0,4,"picture"),
            'jfif'     : (b'ffd8ffe0',0,4,"picture"),
            'mp3'      : (b'49443303',0,4,"music"),
            'mp4'      : (b'66747970',3,7,"video"),
            'MFT'      : (b'46494c45',0,4,"windows{0}mft".format(os.sep)),
            'pdf'      : (b'25504446',0,4,"document{0}pdf".format(os.sep)),
            'zip'      : (b'504b0304',0,4,"archive"),
            'png'      : (b'89504e47',0,4,"picture"),
            'wmv'      : (b'3026b2758e66cf11',0,8,"music"),
            'h264'     : (b'00000001',0,4,"video"),
            'jbig'     : (b'974a42320d0a1a0a',0,8,"music"),
            'xml_1'    : (b'3c3f786d6c',0,5,"text"),
            'xml_2'    : (b'3c3f584d4c',0,5,"text"),
            'html_1'   : (b'3c21646f63747970',0,8,"html"),
            'html_2'   : (b'3c21646f6374797065',0,8,"html"),
            'html_3'   : (b'3c68746d6c',0,5,"html"),
            'html_4'   : (b'3c48544d4c',0,5,"html"),
            'alz'      : (b'414c5a01',0,4,"archive"),
            'bmp'      : (b'424d',0,2,"picture"),
            'dbx'      : (b'cfad12fe',0,4,"mail"),
            'eml'      : (b'46726f6d',0,4,"mail"),
            'evt'      : (b'300000004c664c65',0,8,"event"),
            'lnk'      : (b'4c000000',0,4,"windows{0}link".format(os.sep)),
            'pf'       : (b'53434341',4,4,"windows{0}prefetch".format(os.sep)),
            'pst'      : (b'2142444e',0,4,"mail"),
            'wav'      : (b'52494646',0,4,"music"),
            'reg'      : (b'66676572',0,4,"windows{0}registry".format(os.sep)),
            #'idx'
        }
