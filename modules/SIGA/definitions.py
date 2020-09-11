# -*- coding: utf-8 -*-
"""The definitions."""



# fixed
COMPOUND_SIGNATURE = b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1'
COMPOUND_BYTE_ORDER = 65534  #b'\xff\xfe'

HC_STR_VTYPE_STREAM_SYNTAX_ERROR = '스트림 구문 오류'
HC_STR_VTYPE_INCONSISTENCY ="속성 불일치"
HC_STR_VTYPE_UNUSED_AREA = "미사용 영역 존재"
HC_STR_VTYPE_ABNORMAL_RECORD = "비정상 레코드"
HC_STR_VTYPE_ABNORMAL_BINDATA = "비정상 바이너리 데이터"
HC_STR_VTYPE_UNKWNON_STREAM = "알 수 없는 스트림"

# Status 필요한 것만 체크!!
#STATUS_INDICATOR_ABORTED = 'aborted'
#STATUS_INDICATOR_ANALYZING = 'analyzing'
#STATUS_INDICATOR_COLLECTIONG = 'collecting'
#STATUS_INDICATOR_COMPLETED = 'completed'
#STATUS_INDICATOR_ERROR = 'error'
#STATUS_INDICATOR_EXPORTING = 'exporting'
#STATUS_INDICATOR_EXTRACTIONG = 'extracting'
#STATUS_INDICATOR_FINALIZING = 'finalizing'
#STATUS_INDICATOR_HASHING = 'hashing'
#STATUS_INDICATOR_IDLE = 'idle'
#STATUS_INDICATOR_INITIALIZED = 'initialized'
#STATUS_INDICATOR_KILLED = 'killed'
#STATUS_INDICATOR_MERGING = 'merging'
#STATUS_INDICATOR_NOT_RESPONDING = 'not responding'
#STATUS_INDICATOR_REPORTING = 'reporting'
#STATUS_INDICATOR_RUNNING = 'running'
#STATUS_INDICATOR_YARA_SCAN = 'yara scan'


# invalid code list

VALID_SUCCESS = 0
INVALID_SIGNATURE = 1
INVALID_ROOT_ENTRY = 2 # 얘는 조금 바꿀필요가 있음 because 모든 파일 포맷에 대하여 일반적인 invalid code를 정의해야 하기 때문에