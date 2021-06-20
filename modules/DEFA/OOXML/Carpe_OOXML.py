import zipfile, os, shutil
import xml.etree.ElementTree as ET
import xlrd
from shutil import copyfile
from zipfile import BadZipFile
import olefile
import zlib

WORD_NAMESPACE = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
PARA = WORD_NAMESPACE + 'p'
TEXT = WORD_NAMESPACE + 't'
S_TEXT = WORD_NAMESPACE + 'r'
SMART_TEXT = WORD_NAMESPACE + 'smartTag'
NUM_TEXT = WORD_NAMESPACE + 'numPr'

EXCEL_NAMESPACE = '{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
SI = EXCEL_NAMESPACE + 'si'
E_TEXT = EXCEL_NAMESPACE + 't'

PPT_NAMESPACE = '{http://schemas.openxmlformats.org/presentationml/2006/main}'
TXBODY = PPT_NAMESPACE + 'txBody'
P_TEXT = '{http://schemas.openxmlformats.org/drawingml/2006/main}t'

damaged_flag = False
content_recoverable_flag = False
metadata_recoverable_flag = False

filetype  = ''

if os.path.isdir('./test'):
    shutil.rmtree('./test')

def isNumber(s):
  try:
    int(s)
    return True
  except ValueError:
    return False

class FileHeader:
    SIGNATURE = b'PK\x03\x04'

    def __init__(self, f):
        self.readHeader(f)

    def readHeader(self, f):
        sign = f.read(4)
        if sign != FileHeader.SIGNATURE:
            f.seek(-4, 1)
            raise Exception("Wrong Format")
        self.ver = int.from_bytes(f.read(2), 'little')
        self.bitflag = int.from_bytes(f.read(2), 'little')
        self.method = int.from_bytes(f.read(2), 'little')
        self.modTime = int.from_bytes(f.read(2), 'little')
        self.modDate = int.from_bytes(f.read(2), 'little')
        self.crc = int.from_bytes(f.read(4), 'little')
        self.compSize = int.from_bytes(f.read(4), 'little')
        self.rawSize = int.from_bytes(f.read(4), 'little')
        self.nameLen = int.from_bytes(f.read(2), 'little')
        self.extLen = int.from_bytes(f.read(2), 'little')
        self.name = f.read(self.nameLen)
        self.ext = f.read(self.extLen)

    def writeHeader(self, f):
        f.write(FileHeader.SIGNATURE)
        f.write(self.ver.to_bytes(2, 'little'))
        f.write(self.bitflag.to_bytes(2, 'little'))
        f.write(self.method.to_bytes(2, 'little'))
        f.write(self.modTime.to_bytes(2, 'little'))
        f.write(self.modDate.to_bytes(2, 'little'))
        f.write(self.crc.to_bytes(4, 'little'))
        f.write(self.compSize.to_bytes(4, 'little'))
        f.write(self.rawSize.to_bytes(4, 'little'))
        f.write(self.nameLen.to_bytes(2, 'little'))
        f.write(self.extLen.to_bytes(2, 'little'))
        f.write(self.name)
        f.write(self.ext)
class OOXML:

    def __init__(self, filename):
        # 초기화
        self.filename = filename
        self.is_damaged = False
        self.has_content = False
        self.has_metadata = False
        self.has_ole = False
        self.ole_path = []
        self.content = ""
        self.metadata = {}

    def parse_ooxml(self, tmp_path, filetype):
        #filetype = ''
        # 확장자 체크
        # 설명: 1: docx, 2: xlsx, 3: pptx
        """
        if self.checktype(self.filename) == 'docx':
            filetype = 'docx'
        if self.checktype(self.filename) == 'pptx':
            filetype = 'pptx'
        if self.checktype(self.filename) == 'xlsx':
            filetype = 'xlsx'
        """
        self.parse_main(self.filename, filetype, tmp_path)

    def checktype(self, filename):
        if os.path.splitext(filename)[1] == '.docx':
            return 'docx'
        elif os.path.splitext(filename)[1] == '.pptx':
            return 'pptx'
        elif os.path.splitext(filename)[1] == '.xlsx':
            return 'xlsx'

    def isDamaged(self, filename, filetype):

        '''
        필수 파일 여부를 확인 후에 없는경우 손상된 파일이라고 확정
        체크하는 총 파일의 갯수 4개. 있을 때마다 damaged_count 가 1씩 증가
        4개 중에 한개라도 없으면 "손상"
        '''

        isDamagedFlag = False  # 손상 안된 경우에 False
        damaged_count = 0
        try:
            zfile = zipfile.ZipFile(filename)

            # docx 일때
            if filetype == "docx":

                if isinstance(self.filename, str):  # 파일 포인터일 때 임시 처리
                    f = open(self.filename, "rb")
                else:
                    f = self.filename
                    f.seek(0)
                result = f.read(4)
                if result == b'\x50\x4b\x03\x04':
                    for zip_file_list in zfile.filelist:
                        if zip_file_list.filename == "word/document.xml":
                            damaged_count = damaged_count + 1
                        if zip_file_list.filename == "docProps/app.xml":
                            damaged_count = damaged_count + 1
                        if zip_file_list.filename == "docProps/core.xml":
                            damaged_count = damaged_count + 1
                        if zip_file_list.filename == "[Content_Types].xml":
                            damaged_count = damaged_count + 1
                    if damaged_count is not 4:
                        isDamagedFlag = True
                        self.is_damaged = True
                    return isDamagedFlag
                else:
                    isDamagedFlag = True
                    self.is_damaged = True
                    return isDamagedFlag
                return isDamagedFlag

            # xlsx 일때
            if filetype == "xlsx":

                if isinstance(self.filename, str):  # 파일 포인터일 때 임시 처리
                    f = open(self.filename, "rb")
                else:
                    f = self.filename
                    f.seek(0)
                result = f.read(4)
                if result == b'\x50\x4b\x03\x04':
                    for zip_file_list in zfile.filelist:
                        if zip_file_list.filename == "xl/sharedStrings.xml":
                            damaged_count = damaged_count + 1
                        if zip_file_list.filename == "docProps/app.xml":
                            damaged_count = damaged_count + 1
                        if zip_file_list.filename == "docProps/core.xml":
                            damaged_count = damaged_count + 1
                        if zip_file_list.filename == "[Content_Types].xml":
                            damaged_count = damaged_count + 1
                    if damaged_count is not 4:
                        isDamagedFlag = True
                        self.is_damaged = True
                    return isDamagedFlag
                else:
                    isDamagedFlag = True
                    self.is_damaged = True
                    return isDamagedFlag
                return isDamagedFlag

            # pptx 일때
            if filetype == "pptx":

                if isinstance(self.filename, str):  # 파일 포인터일 때 임시 처리
                    f = open(self.filename, "rb")
                else:
                    f = self.filename
                    f.seek(0)
                result = f.read(4)
                if result == b'\x50\x4b\x03\x04':
                    for zip_file_list in zfile.filelist:
                        if zip_file_list.filename == "ppt/slides/slide1.xml":
                            damaged_count = damaged_count + 1
                        if zip_file_list.filename == "docProps/app.xml":
                            damaged_count = damaged_count + 1
                        if zip_file_list.filename == "docProps/core.xml":
                            damaged_count = damaged_count + 1
                        if zip_file_list.filename == "[Content_Types].xml":
                            damaged_count = damaged_count + 1
                    if damaged_count is not 4:
                        isDamagedFlag = True
                        self.is_damaged = True
                    return isDamagedFlag
                else:
                    isDamagedFlag = True
                    self.is_damaged = True
                    return isDamagedFlag
                return isDamagedFlag

        except BadZipFile:
            isDamagedFlag = True
            self.is_damaged = True
            return isDamagedFlag

    def isRecoverable_content(self, filetype):
        # 복구가능한지 여부 확인하는 함수
        '''
        본문 영역을 담고 있는 파일들의 존재 유무에 따라서 복구여부를 판단
        파일이 있으면 recoverableFlag = True
        '''

        recovableFlag = False
        signature_last_three = b'\x4b\x03\x04'

        # docx 일때
        if filetype == "docx":
            if isinstance(self.filename, str):  # 파일 포인터일 때 임시 처리
                f = open(self.filename, "rb")
            else:
                f = self.filename
                f.seek(0)
            temp1 = 0
            fileSize = len(f.read())
            f.seek(0, 0)
            while True:
                tmp = f.read(1)
                if tmp == b'\x50':
                    if f.read(3) == signature_last_three:
                        f.seek(0xE, 1)
                        data_length = int(hex(int.from_bytes(f.read(4), 'little')), 16)
                        f.seek(4, 1)
                        data_name_length = int(hex(int.from_bytes(f.read(2), 'little')), 16)
                        data_offset = int(hex(int.from_bytes(f.read(2), 'little')), 16)

                        data_name = f.read(data_name_length).decode("utf-8")
                        if data_name == "word/document.xml":
                            self.has_content = True
                            recovableFlag = True
                            return recovableFlag

                        f.seek(data_offset, 1)

                        if f.tell() + data_length > fileSize:
                            temp_rest = fileSize - endingpoint + 1
                            f.seek(endingpoint + 1, 0)
                            lastpart = f.read(temp_rest)  # 마지막까지 읽어라
                            break
                        else:
                            f.seek(data_length, 1)

                        endingpoint = f.tell() - 1
                        temp1 = endingpoint - temp1
                elif tmp == b'':
                    break
            return recovableFlag

        # xlsx 일때
        if filetype == "xlsx":
            if isinstance(self.filename, str):  # 파일 포인터일 때 임시 처리
                f = open(self.filename, "rb")
            else:
                f = self.filename
                f.seek(0)
            temp1 = 0
            fileSize = len(f.read())
            f.seek(0, 0)
            while True:
                tmp = f.read(1)
                if tmp == b'\x50':
                    if f.read(3) == signature_last_three:
                        f.seek(0xE, 1)
                        data_length = int(hex(int.from_bytes(f.read(4), 'little')), 16)
                        f.seek(4, 1)
                        data_name_length = int(hex(int.from_bytes(f.read(2), 'little')), 16)
                        data_offset = int(hex(int.from_bytes(f.read(2), 'little')), 16)

                        data_name = f.read(data_name_length).decode("utf-8")
                        if "xl/worksheets/sheet" in data_name:
                            self.has_content = True
                            recovableFlag = True
                            return recovableFlag

                        f.seek(data_offset, 1)

                        if f.tell() + data_length > fileSize:
                            temp_rest = fileSize - endingpoint + 1
                            f.seek(endingpoint + 1, 0)
                            lastpart = f.read(temp_rest)  # 마지막까지 읽어라
                            break
                        else:
                            f.seek(data_length, 1)

                        endingpoint = f.tell() - 1
                        temp1 = endingpoint - temp1
                elif tmp == b'':
                    break

            return recovableFlag

        # pptx 일때
        if filetype == "pptx":
            if isinstance(self.filename, str):  # 파일 포인터일 때 임시 처리
                f = open(self.filename, "rb")
            else:
                f = self.filename
                f.seek(0)
            temp1 = 0
            fileSize = len(f.read())
            f.seek(0, 0)
            while True:
                tmp = f.read(1)
                if tmp == b'\x50':
                    if f.read(3) == signature_last_three:
                        f.seek(0xE, 1)
                        data_length = int(hex(int.from_bytes(f.read(4), 'little')), 16)
                        f.seek(4, 1)
                        data_name_length = int(hex(int.from_bytes(f.read(2), 'little')), 16)
                        data_offset = int(hex(int.from_bytes(f.read(2), 'little')), 16)

                        data_name = f.read(data_name_length).decode("utf-8")
                        if data_name == "ppt/slides/slide1.xml":
                            self.has_content = True
                            recovableFlag = True
                            return recovableFlag

                        f.seek(data_offset, 1)

                        if f.tell() + data_length > fileSize:
                            temp_rest = fileSize - endingpoint + 1
                            f.seek(endingpoint + 1, 0)
                            lastpart = f.read(temp_rest)  # 마지막까지 읽어라
                            break
                        else:
                            f.seek(data_length, 1)

                        endingpoint = f.tell() - 1
                        temp1 = endingpoint - temp1
                elif tmp == b'':
                    break
            return recovableFlag

        return recovableFlag

    def isRecoverable_metadata(self, filetype):
        # 복구가능한지 여부 확인하는 함수
        '''
        본문 영역을 담고 있는 파일들의 존재 유무에 따라서 복구여부를 판단
        파일이 있으면 recoverableFlag = True
        '''

        recovableFlag = False
        signature_three = b'\x4b\x03\x04'
        stop_signature_three = b'\x4b\x01\x02'
        self.has_metadata = False
        # docx 일때
        if filetype == "docx":
            if isinstance(self.filename, str):  # 파일 포인터일 때 임시 처리
                f = open(self.filename, "rb")
            else:
                f = self.filename
                f.seek(0)
            temp1 = 0
            cal_recovable_count = 0
            fileSize = f.seek(0, 2)
            f.seek(0, 0)

            while True:
                read_onebyte = f.read(1)
                if read_onebyte == b'\x50':
                    read_threebyte = f.read(3)
                    if read_threebyte == signature_three:
                        f.seek(0xE, 1)
                        data_length = int(hex(int.from_bytes(f.read(4), 'little')), 16)
                        f.seek(4, 1)
                        data_name_length = int(hex(int.from_bytes(f.read(2), 'little')), 16)
                        data_offset = int(hex(int.from_bytes(f.read(2), 'little')), 16)

                        data_name = f.read(data_name_length).decode("utf-8")
                        if data_name == "docProps/core.xml":
                            cal_recovable_count = cal_recovable_count + 1
                            self.has_metadata = True
                            recovableFlag = True
                            break

                        if f.tell() + data_length > fileSize:
                            break

                    elif read_threebyte == stop_signature_three:
                        break
                elif read_onebyte == b'':
                    break

            return recovableFlag

        # xlsx 일때
        if filetype == "xlsx":
            if isinstance(self.filename, str):  # 파일 포인터일 때 임시 처리
                f = open(self.filename, "rb")
            else:
                f = self.filename
                f.seek(0)
            temp1 = 0
            cal_recovable_count = 0
            fileSize = len(f.read())
            f.seek(0, 0)

            while True:
                read_onebyte = f.read(1)
                if read_onebyte == b'\x50':
                    read_threebyte = f.read(3)
                    if read_threebyte == signature_three:
                        f.seek(0xE, 1)
                        data_length = int(hex(int.from_bytes(f.read(4), 'little')), 16)
                        f.seek(4, 1)
                        data_name_length = int(hex(int.from_bytes(f.read(2), 'little')), 16)
                        data_offset = int(hex(int.from_bytes(f.read(2), 'little')), 16)

                        data_name = f.read(data_name_length).decode("utf-8")
                        if data_name == "docProps/core.xml":
                            cal_recovable_count = cal_recovable_count + 1
                            self.has_metadata = True
                            recovableFlag = True

                        if f.tell() + data_length > fileSize:
                            break

                    elif read_threebyte == stop_signature_three:
                        break
                elif read_onebyte == b'':
                    break

            return recovableFlag

        # pptx 일때
        if filetype == "pptx":
            if isinstance(self.filename, str):  # 파일 포인터일 때 임시 처리
                f = open(self.filename, "rb")
            else:
                f = self.filename
                f.seek(0)
            temp1 = 0
            cal_recovable_count = 0
            fileSize = f.seek(0, 2)
            f.seek(0, 0)

            while True:
                read_onebyte = f.read(1)
                if read_onebyte == b'\x50':
                    read_threebyte = f.read(3)
                    if read_threebyte == signature_three:
                        f.seek(0xE, 1)
                        data_length = int(hex(int.from_bytes(f.read(4), 'little')), 16)
                        f.seek(4, 1)
                        data_name_length = int(hex(int.from_bytes(f.read(2), 'little')), 16)
                        data_offset = int(hex(int.from_bytes(f.read(2), 'little')), 16)

                        data_name = f.read(data_name_length).decode("utf-8")
                        if data_name == "docProps/core.xml":
                            cal_recovable_count = cal_recovable_count + 1
                            self.has_metadata = True
                            recovableFlag = True
                        if f.tell() + data_length > fileSize:
                            break

                    elif read_threebyte == stop_signature_three:
                        break

                elif read_onebyte == b'':
                    break

            return recovableFlag

        return recovableFlag

    def parse_content(self, filename, filetype, isDamaged, tmp_path=None):
        lastpart = ""
        content_saved = ""
        signature_three = b'\x4b\x03\x04'
        signature_last_three = b'\x4b\x03\x04'
        stop_signature_three = b'\x4b\x01\x02'
        normal_content_data = ""
        xlsx_normal_content_data = []
        pptx_ordering_table = []
        only_data = ""
        slides_value = ""
        #xlsx
        list_word = []
        order_word = []
        final_word = ''

        if filetype == 'docx':
            #정상일 때
            if isDamaged == False:
                #print("**********본문파싱**********")
                zfile = zipfile.ZipFile(filename)
                for a in zfile.filelist:
                    if 'word/header1.xml' in a.filename:
                        form = zfile.read(a)
                        xmlroot = ET.fromstring(form)
                        for content in xmlroot.getiterator(PARA):
                            for a in content:
                                for b in a:
                                    if b.tag == TEXT:
                                        normal_content_data = normal_content_data + b.text
                                        self.content = self.content + b.text
                                    if b.tag == NUM_TEXT:
                                        normal_content_data = normal_content_data + "·"
                                        self.content = self.content + "·"
                                    if b.tag == S_TEXT:
                                        for c in b:
                                            if c.tag == TEXT:
                                                normal_content_data = normal_content_data + c.text
                                                self.content = self.content + c.text
                                    if b.tag == SMART_TEXT:
                                        for c in b:
                                            for d in c:
                                                if d.tag == TEXT:
                                                    normal_content_data = normal_content_data + d.text
                                                    self.content = self.content + d.text
                for a in zfile.filelist:
                    if 'word/document.xml' in a.filename:
                        form = zfile.read(a)
                        xmlroot = ET.fromstring(form)
                        for content in xmlroot.getiterator(PARA):
                            for a in content:
                                for b in a:
                                    if b.tag == TEXT:
                                        normal_content_data = normal_content_data + b.text
                                        self.content = self.content + b.text
                                    if b.tag == NUM_TEXT:
                                        normal_content_data = normal_content_data + "·"
                                        self.content = self.content + "·"
                                    if b.tag == S_TEXT:
                                        for c in b:
                                            if c.tag == TEXT:
                                                normal_content_data = normal_content_data + c.text
                                                self.content = self.content + c.text
                                    if b.tag == SMART_TEXT:
                                        for c in b:
                                            for d in c:
                                                if d.tag == TEXT:
                                                    normal_content_data = normal_content_data + d.text
                                                    self.content = self.content + d.text
                for a in zfile.filelist:
                    if 'word/footer1.xml' in a.filename:
                        form = zfile.read(a)
                        xmlroot = ET.fromstring(form)
                        for content in xmlroot.getiterator(PARA):
                            for a in content:
                                for b in a:
                                    if b.tag == TEXT:
                                        normal_content_data = normal_content_data + b.text
                                        self.content = self.content + b.text
                                    if b.tag == NUM_TEXT:
                                        normal_content_data = normal_content_data + "·"
                                        self.content = self.content + "·"
                                    if b.tag == S_TEXT:
                                        for c in b:
                                            if c.tag == TEXT:
                                                normal_content_data = normal_content_data + c.text
                                                self.content = self.content + c.text
                                    if b.tag == SMART_TEXT:
                                        for c in b:
                                            for d in c:
                                                if d.tag == TEXT:
                                                    normal_content_data = normal_content_data + d.text
                                                    self.content = self.content + d.text

                #self.parse_media(filename, filetype, isDamaged, tmp_path)

                return normal_content_data

            #손상일 때
            else:
                try:
                    f = open(self.filename, "rb")
                    temp1 = 0
                    fileSize = f.seek(0, 2)
                    f.seek(0, 0)
                    #print("**********본문파싱**********")
                    while True:
                        tmp = f.read(1)
                        if tmp == b'\x50':
                            if f.read(3) == signature_last_three:
                                f.seek(0xE, 1)
                                data_length = int(hex(int.from_bytes(f.read(4), 'little')), 16)
                                f.seek(4, 1)
                                data_name_length = int(hex(int.from_bytes(f.read(2), 'little')), 16)
                                data_offset = int(hex(int.from_bytes(f.read(2), 'little')), 16)

                                data_name = f.read(data_name_length).decode("utf-8")
                                f.seek(data_offset, 1)

                                if f.tell() + data_length > fileSize:
                                    temp_rest = fileSize - endingpoint + 1
                                    f.seek(endingpoint + 1, 0)
                                    lastpart = f.read(temp_rest)  # 마지막까지 읽어라
                                    break
                                else:
                                    if data_name != "word/document.xml":
                                        f.seek(data_length, 1)
                                    else:
                                        content_saved = f.read(data_length)
                                endingpoint = f.tell() - 1
                                temp1 = endingpoint - temp1

                                if data_name == "word/document.xml":
                                    break
                        elif tmp == b'':
                            break

                    if content_saved == "":
                        temp_size = lastpart[30+data_name_length:]

                        f1 = open(os.path.dirname(self.filename) + os.sep + "outputtest.zip", 'wb')
                        f1.write(b'\x78\x9C')
                        f1.write(temp_size)
                        f1.close()

                        fz = open(os.path.dirname(self.filename) + os.sep + "outputtest.zip",'rb')
                        d = fz.read()
                        fz.close()

                        zobj = zlib.decompressobj()
                        real_data = zobj.decompress(d)

                        f2 = open(os.path.dirname(self.filename) + os.sep + "test.xml",'wb')
                        f2.write(real_data)
                        f2.close()

                        f3 = open(os.path.dirname(self.filename) + os.sep + "test.xml",'r',encoding='utf-8')
                        a1 = f3.read()
                        f3.close()

                        i = 0
                        only_data = ""
                        while i < len(a1)-1:
                            if a1[i] == '<':
                                i = i+1
                                if a1[i] == 'w':
                                    i = i+1
                                    if a1[i] == ':':
                                        i = i+1
                                        if a1[i] == 't':
                                            i = i+1
                                            if a1[i] == '>':
                                                i = i+1
                                                while a1[i] != '<':
                                                    intToString = a1[i]
                                                    only_data = only_data + intToString
                                                    self.content = self.content + intToString
                                                    if i < len(a1)-1:
                                                        i = i + 1
                                                        if a1[i] == '<':
                                                            only_data = only_data + ''
                                                            self.content = self.content + ''
                                                    else:
                                                        break
                            i = i+1
                        #self.parse_media(filename, filetype, isDamaged, tmp_path)
                        return only_data
                    else:
                        f1 = open(os.path.dirname(self.filename) + os.sep + "outputtest.zip", 'wb')
                        f1.write(b'\x78\x9C')
                        f1.write(content_saved)
                        f1.close()

                        fz = open(os.path.dirname(self.filename) + os.sep + "outputtest.zip", 'rb')
                        d = fz.read()
                        fz.close()

                        zobj = zlib.decompressobj()
                        real_data = zobj.decompress(d)

                        f2 = open(os.path.dirname(self.filename) + os.sep + "test.xml", 'wb')
                        f2.write(real_data)
                        f2.close()

                        f3 = open(os.path.dirname(self.filename) + os.sep + "test.xml", 'r', encoding='utf-8')
                        a1 = f3.read()
                        f3.close()

                        i = 0
                        only_data = ""
                        while i < len(a1) - 1:
                            if a1[i] == '<':
                                i = i + 1
                                if a1[i] == 'w':
                                    i = i + 1
                                    if a1[i] == ':':
                                        i = i + 1
                                        if a1[i] == 't':
                                            i = i + 1
                                            if a1[i] == '>':
                                                i = i + 1
                                                while a1[i] != '<':
                                                    intToString = a1[i]
                                                    only_data = only_data + intToString
                                                    self.content = self.content + intToString
                                                    if i < len(a1) - 1:
                                                        i = i + 1
                                                        if a1[i] == '<':
                                                            only_data = only_data + ''
                                                            self.content = self.content + ''
                                                    else:
                                                        break
                            i = i + 1

                        #self.parse_media(filename, filetype, isDamaged, tmp_path)
                        return only_data
                except Exception as ex:
                        print(ex)

        if filetype == 'xlsx':
            if isDamaged == False:
                if isinstance(filename, str):  # 파일 포인터일 때 임시 처리
                    wb = xlrd.open_workbook(filename)
                else:
                    filename.seek(0)
                    tmp_data = filename.read()
                    wb = xlrd.open_workbook(file_contents=tmp_data)

                for i in range(0, len(wb._sheet_list)):
                    xlsx_normal_content_data.append(wb._sheet_names[i])
                    xlsx_normal_content_data.append(wb._sheet_list[i]._cell_values)

                for i in range(0,len(xlsx_normal_content_data)):
                    for j in range(0, len(xlsx_normal_content_data[i])):
                        for k in range(0, len(xlsx_normal_content_data[i][j])):
                            if isNumber(xlsx_normal_content_data[i][j][k]) == True:
                                normal_content_data = normal_content_data + str(format(int(xlsx_normal_content_data[i][j][k]),','))
                            else:
                                normal_content_data = normal_content_data + str(xlsx_normal_content_data[i][j][k])

                self.content = normal_content_data
                #self.parse_media(filename, filetype, isDamaged, tmp_path)
                return normal_content_data

            else:
                # 손상일때
                if isinstance(filename, str):  # 파일 포인터일 때 임시 처리
                    f = open(self.filename, "rb")
                else:
                    filename.seek(0)
                    f = filename
                temp1 = 0
                fileSize = len(f.read())
                f.seek(0, 0)
                #print("**********본문파싱**********")
                while True:
                    tmp = f.read(1)
                    if tmp == b'\x50':
                        if f.read(3) == signature_last_three:
                            f.seek(0xE, 1)
                            data_length = int(hex(int.from_bytes(f.read(4), 'little')), 16)
                            f.seek(4, 1)
                            data_name_length = int(hex(int.from_bytes(f.read(2), 'little')), 16)
                            data_offset = int(hex(int.from_bytes(f.read(2), 'little')), 16)

                            data_name = f.read(data_name_length).decode("utf-8")

                            f.seek(data_offset, 1)

                            if f.tell() + data_length > fileSize:
                                temp_rest = fileSize - endingpoint + 1
                                f.seek(endingpoint + 1, 0)
                                lastpart = f.read(temp_rest)  # 마지막까지 읽어라
                                break
                            else:
                                if "xl/sharedStrings.xml" == data_name:
                                    content_saved = f.read(data_length)
                                    f1 = open(os.path.dirname(self.filename) + os.sep + "outputtest.zip", 'wb')
                                    f1.write(b'\x78\x9C')
                                    f1.write(content_saved)
                                    f1.close()

                                    fz = open(os.path.dirname(self.filename) + os.sep + "outputtest.zip", 'rb')
                                    d = fz.read()
                                    fz.close()

                                    zobj = zlib.decompressobj()
                                    real_data = zobj.decompress(d)

                                    f2 = open(os.path.dirname(self.filename) + os.sep + "test.xml", 'wb')
                                    f2.write(real_data)
                                    f2.close()

                                    f3 = open(os.path.dirname(self.filename) + os.sep + "test.xml", 'r', encoding='utf-8')
                                    a1 = f3.read()
                                    f3.close()

                                    i = 0

                                    while i < len(a1) - 1:
                                        only_data = ""
                                        if a1[i] == '<':
                                            i = i + 1
                                            if a1[i] == 't':
                                                i = i + 1
                                                if a1[i] == '>':
                                                    i = i + 1
                                                    while a1[i] != '<':
                                                        intToString = a1[i]
                                                        only_data = only_data + intToString
                                                        if i < len(a1) - 1:
                                                            i = i + 1
                                                            if a1[i] == '<':
                                                                list_word.append(only_data)
                                                        else:
                                                            break
                                                elif a1[i] == ' ':
                                                        i = i + 22
                                                        while a1[i] != '<':
                                                            intToString = a1[i]
                                                            only_data = only_data + intToString
                                                            if i < len(a1) - 1:
                                                                i = i + 1
                                                                if a1[i] == '<':
                                                                    list_word.append(only_data)
                                                            else:
                                                                break
                                        i = i + 1

                                    #return only_data
                                else:
                                    f.seek(data_length, 1)
                                    if "docProps" in data_name:
                                        break
                            endingpoint = f.tell() - 1
                            temp1 = endingpoint - temp1
                    elif tmp == b'':
                        break
                #f.close()
                if isinstance(self.filename, str):
                    f = open(self.filename, "rb")
                else:
                    f = self.filename
                temp1 = 0
                fileSize = len(f.read())
                f.seek(0, 0)
                # print("**********본문파싱**********")
                while True:
                    tmp = f.read(1)
                    if tmp == b'\x50':
                        if f.read(3) == signature_last_three:
                            f.seek(0xE, 1)
                            data_length = int(hex(int.from_bytes(f.read(4), 'little')), 16)
                            f.seek(4, 1)
                            data_name_length = int(hex(int.from_bytes(f.read(2), 'little')), 16)
                            data_offset = int(hex(int.from_bytes(f.read(2), 'little')), 16)

                            data_name = f.read(data_name_length).decode("utf-8")

                            f.seek(data_offset, 1)

                            if f.tell() + data_length > fileSize:
                                temp_rest = fileSize - endingpoint + 1
                                f.seek(endingpoint + 1, 0)
                                lastpart = f.read(temp_rest)  # 마지막까지 읽어라
                                break
                            else:
                                if "xl/worksheets/sheet1.xml" == data_name:
                                    content_saved = f.read(data_length)
                                    f1 = open(os.path.dirname(self.filename) + os.sep + "outputtest.zip", 'wb')
                                    f1.write(b'\x78\x9C')
                                    f1.write(content_saved)
                                    f1.close()

                                    fz = open(os.path.dirname(self.filename) + os.sep + "outputtest.zip", 'rb')
                                    d = fz.read()
                                    fz.close()

                                    zobj = zlib.decompressobj()
                                    real_data = zobj.decompress(d)

                                    f2 = open(os.path.dirname(self.filename) + os.sep + "test.xml", 'wb')
                                    f2.write(real_data)
                                    f2.close()

                                    f3 = open(os.path.dirname(self.filename) + os.sep + "test.xml", 'r', encoding='utf-8')
                                    a1 = f3.read()
                                    f3.close()

                                    i = 0

                                    while i < len(a1) - 1:
                                        only_data = ""
                                        if a1[i] == '<':
                                            i = i + 1
                                            if a1[i] == 'f':
                                                i = i+1
                                                if a1[i] == '>':
                                                    while a1[i] != '<':
                                                        i = i+1
                                                        if a1[i] == '<':
                                                            i = i+1
                                                            if a1[i] == 'v':
                                                                i = i+1
                                                                if a1[i] == '>':
                                                                    i = i+1
                                                                    while a1[i] != '<':
                                                                        final_word = final_word + a1[i]
                                                                        i = i+1
                                                                    final_word = final_word + ' '
                                            elif a1[i] == 'v':
                                                i = i + 1
                                                if a1[i] == '>':
                                                    i = i + 1
                                                    while a1[i] != '<':
                                                        intToString = a1[i]
                                                        only_data = only_data + intToString
                                                        if i < len(a1) - 1:
                                                            i = i + 1
                                                            if a1[i] == '<':
                                                                if isNumber(only_data) == False:
                                                                    final_word = final_word + only_data + ' '
                                                                elif int(only_data) >= len(list_word):
                                                                    final_word = final_word + only_data + ' '
                                                                else:
                                                                    final_word = final_word + list_word[int(only_data)] + ' '

                                                                #order_word.append(only_data)
                                                        else:
                                                            break
                                        i = i + 1

                                    # return only_data
                                else:
                                    f.seek(data_length, 1)
                                    if "docProps" in data_name:
                                        break
                            endingpoint = f.tell() - 1
                            temp1 = endingpoint - temp1
                    elif tmp == b'':
                        break

                self.content = final_word
                #self.parse_media(filename, filetype, isDamaged, tmp_path)
                return final_word

                """if "docProps" not in data_name:
                    temp_size = lastpart[30 + data_name_length:]

                    f1 = open("./outputtest.zip", 'wb')
                    f1.write(b'\x78\x9C')
                    f1.write(temp_size)
                    f1.close()

                    fz = open("./outputtest.zip", 'rb')
                    d = fz.read()
                    fz.close()

                    zobj = zlib.decompressobj()
                    real_data = zobj.decompress(d)

                    f2 = open("./test.xml", 'wb')
                    f2.write(real_data)
                    f2.close()

                    f3 = open("./test.xml", 'r', encoding='utf-8')
                    a1 = f3.read()
                    f3.close()

                    i = 0
                    only_data = ""
                    while i < len(a1) - 1:
                        if a1[i] == '<':
                            i = i + 1
                            if a1[i] == 'v':
                                i = i + 1
                                if a1[i] == '>':
                                    i = i + 1
                                    while a1[i] != '<':
                                        intToString = a1[i]
                                        only_data = only_data + intToString
                                        self.content = self.content + intToString
                                        if i < len(a1) - 1:
                                            i = i + 1
                                            if a1[i] == '<':
                                                only_data = only_data + ''
                                                self.content = self.content + ''
                                        else:
                                            break
                        i = i + 1

                    return only_data"""

        if filetype == 'pptx':
           if isDamaged == False:
                #print("**********본문파싱**********")
                zfile = zipfile.ZipFile(filename)
                filelist_1 = []
                filelist_2 = []
                for a in zfile.filelist:
                    if 'ppt/slides/slide' in a.filename:
                        if len(a.filename) == 21:
                            filelist_1.append(a.filename)
                        else:
                            filelist_2.append(a.filename)
                    filelist_1.sort()
                    filelist_2.sort()
                filelist = filelist_1 + filelist_2

                for b in filelist:
                    form = zfile.read(b)
                    xmlroot = ET.fromstring(form)
                    for content in xmlroot.getiterator(TXBODY):
                        for a in content:
                            for b in a:
                                for c in b:
                                    if c.tag == P_TEXT and c.text is not None:
                                        normal_content_data = normal_content_data + c.text
                                        self.content = self.content + c.text

                #self.parse_media(filename, filetype, isDamaged, tmp_path)

                return normal_content_data
           else:
               #손상일때
               #슬라이드 갯수구하기
               f = open(self.filename, "rb")
               temp1 = 0
               fileSize = f.seek(0, 2)
               f.seek(0, 0)
               #print("**********본문파싱**********")
               while True:
                   read_onebyte = f.read(1)
                   if read_onebyte == b'\x50':
                       read_threebyte = f.read(3)
                       if read_threebyte == signature_three:
                           f.seek(0xE, 1)
                           data_length = int(hex(int.from_bytes(f.read(4), 'little')), 16)
                           f.seek(4, 1)
                           data_name_length = int(hex(int.from_bytes(f.read(2), 'little')), 16)
                           data_offset = int(hex(int.from_bytes(f.read(2), 'little')), 16)

                           data_name = f.read(data_name_length).decode("utf-8")
                           f.seek(data_offset, 1)
                           if data_name == "docProps/app.xml":
                               content_saved = f.read(data_length)

                               f1 = open(os.path.dirname(self.filename) + os.sep + "outputtest.zip", 'wb')
                               f1.write(b'\x78\x9C')
                               f1.write(content_saved)
                               f1.close()

                               fz = open(os.path.dirname(self.filename) + os.sep + "outputtest.zip", 'rb')
                               d = fz.read()
                               fz.close()

                               zobj = zlib.decompressobj()
                               real_data = zobj.decompress(d)

                               f2 = open(os.path.dirname(self.filename) + os.sep + "test.xml", 'wb')
                               f2.write(real_data)
                               f2.close()

                               f3 = open(os.path.dirname(self.filename) + os.sep + "test.xml", 'r', encoding='utf-8')
                               a1 = f3.read()
                               f3.close()

                               i = 0
                               slides_app = "<Slides>"
                               s_pos = a1.find(slides_app) + 1

                               if s_pos is not 0:
                                   tmp = 0
                                   while True:
                                       tmp += 1
                                       slides_value = slides_value + a1[s_pos + i + 7]
                                       i = i + 1
                                       if a1[s_pos + i + 7] == '<':
                                           break
                                       if tmp >= 1000000:
                                           break

                                   i = 0

                           if f.tell() + data_length > fileSize:
                               break

                       elif read_threebyte == stop_signature_three:
                           break
                   elif read_onebyte == b'':
                       break
               f.close()
               if slides_value is not "":
                   f = open(self.filename, "rb")
                   f.seek(0, 0)
                   for slides_i in range(1, int(slides_value)+1):
                       f.seek(0, 0)
                       while True:
                           tmp = f.read(1)
                           if tmp == b'\x50':
                               if f.read(3) == signature_three:
                                   f.seek(0xE, 1)
                                   data_length = int(hex(int.from_bytes(f.read(4), 'little')), 16)
                                   f.seek(4, 1)
                                   data_name_length = int(hex(int.from_bytes(f.read(2), 'little')), 16)
                                   data_offset = int(hex(int.from_bytes(f.read(2), 'little')), 16)

                                   data_name = f.read(data_name_length).decode("utf-8")
                                   f.seek(data_offset, 1)

                                   if f.tell() + data_length > fileSize:
                                       temp_rest = fileSize - endingpoint + 1
                                       f.seek(endingpoint + 1, 0)
                                       lastpart = f.read(temp_rest)  # 마지막까지 읽어라
                                       break
                                   else:
                                       if "ppt/slides/slide"+str(slides_i)+".xml" == data_name:
                                           # 순서대로 일단 넣어야할듯...
                                           # 엑셀은... 순서대로 나오게 해야한다.. 둘다 ㅠㅠ

                                           content_saved = f.read(data_length)
                                           pptx_ordering_table.append(content_saved)
                                           f1 = open(os.path.dirname(self.filename) + os.sep + "outputtest.zip", 'wb')
                                           f1.write(b'\x78\x9C')
                                           f1.write(content_saved)
                                           f1.close()

                                           fz = open(os.path.dirname(self.filename) + os.sep + "outputtest.zip", 'rb')
                                           d = fz.read()
                                           fz.close()

                                           zobj = zlib.decompressobj()
                                           real_data = zobj.decompress(d)

                                           f2 = open(os.path.dirname(self.filename) + os.sep + "test.xml", 'wb')
                                           f2.write(real_data)
                                           f2.close()

                                           f3 = open(os.path.dirname(self.filename) + os.sep + "test.xml", 'r', encoding='utf-8')
                                           a1 = f3.read()
                                           f3.close()

                                           i = 0

                                           while i < len(a1) - 1:
                                               if a1[i] == '<':
                                                   i = i + 1
                                                   if a1[i] == 'a':
                                                       i = i + 1
                                                       if a1[i] == ':':
                                                           i = i + 1
                                                           if a1[i] == 't':
                                                               i = i + 1
                                                               if a1[i] == '>':
                                                                   i = i + 1
                                                                   while a1[i] != '<':
                                                                       intToString = a1[i]
                                                                       self.content = self.content + intToString
                                                                       only_data = only_data + intToString
                                                                       if i < len(a1) - 1:
                                                                           i = i + 1
                                                                           if a1[i] == '<':
                                                                               only_data = only_data + ''
                                                                               self.content = self.content + ''
                                                                       else:
                                                                           break
                                               i = i + 1
                                           break
                                       else:
                                           f.seek(data_length, 1)
                                           if "ppt/slideL" in data_name:
                                               break
                                   endingpoint = f.tell() - 1
                                   temp1 = endingpoint - temp1
                           elif tmp == b'':
                               break
                   #self.parse_media(filename, filetype, isDamaged, tmp_path)
                   return only_data
               else:
                   # 손상일때
                   f = open(self.filename, "rb")
                   temp1 = 0
                   fileSize = f.seek(0, 2)
                   f.seek(0, 0)
                   # print("**********본문파싱**********")
                   while True:
                       tmp = f.read(1)
                       if tmp == b'\x50':
                           if f.read(3) == signature_last_three:
                               f.seek(0xE, 1)
                               data_length = int(hex(int.from_bytes(f.read(4), 'little')), 16)
                               f.seek(4, 1)
                               data_name_length = int(hex(int.from_bytes(f.read(2), 'little')), 16)
                               data_offset = int(hex(int.from_bytes(f.read(2), 'little')), 16)

                               data_name = f.read(data_name_length).decode("utf-8")

                               f.seek(data_offset, 1)

                               if f.tell() + data_length > fileSize:
                                   temp_rest = fileSize - endingpoint + 1
                                   f.seek(endingpoint + 1, 0)
                                   lastpart = f.read(temp_rest)  # 마지막까지 읽어라
                                   break
                               else:
                                   if "ppt/slides/s" in data_name:
                                       # 순서대로 일단 넣어야할듯...
                                       # 엑셀은... 순서대로 나오게 해야한다.. 둘다 ㅠㅠ

                                       content_saved = f.read(data_length)
                                       pptx_ordering_table.append(content_saved)
                                       f1 = open(os.path.dirname(self.filename) + os.sep + "outputtest.zip", 'wb')
                                       f1.write(b'\x78\x9C')
                                       f1.write(content_saved)
                                       f1.close()

                                       fz = open(os.path.dirname(self.filename) + os.sep + "outputtest.zip", 'rb')
                                       d = fz.read()
                                       fz.close()

                                       zobj = zlib.decompressobj()
                                       real_data = zobj.decompress(d)

                                       f2 = open(os.path.dirname(self.filename) + os.sep + "test.xml", 'wb')
                                       f2.write(real_data)
                                       f2.close()

                                       f3 = open(os.path.dirname(self.filename) + os.sep + "test.xml", 'r', encoding='utf-8')
                                       a1 = f3.read()
                                       f3.close()

                                       i = 0

                                       while i < len(a1) - 1:
                                           if a1[i] == '<':
                                               i = i + 1
                                               if a1[i] == 'a':
                                                   i = i + 1
                                                   if a1[i] == ':':
                                                       i = i + 1
                                                       if a1[i] == 't':
                                                           i = i + 1
                                                           if a1[i] == '>':
                                                               i = i + 1
                                                               while a1[i] != '<':
                                                                   intToString = a1[i]
                                                                   only_data = only_data + intToString
                                                                   self.content = self.content + intToString
                                                                   if i < len(a1) - 1:
                                                                       i = i + 1
                                                                       if a1[i] == '<':
                                                                           only_data = only_data + ''
                                                                           self.content = self.content + ''
                                                                   else:
                                                                       break
                                           i = i + 1
                                       # return only_data
                                   else:
                                       f.seek(data_length, 1)
                                       if "ppt/slideL" in data_name:
                                           break
                               endingpoint = f.tell() - 1
                               temp1 = endingpoint - temp1
                       elif tmp == b'':
                           break

                   if "ppt/slideL" not in data_name:
                       temp_size = lastpart[30 + data_name_length:]

                       f1 = open(os.path.dirname(self.filename) + os.sep + "outputtest.zip", 'wb')
                       f1.write(b'\x78\x9C')
                       f1.write(temp_size)
                       f1.close()

                       fz = open(os.path.dirname(self.filename) + os.sep + "outputtest.zip", 'rb')
                       d = fz.read()
                       fz.close()

                       zobj = zlib.decompressobj()
                       real_data = zobj.decompress(d)

                       f2 = open(os.path.dirname(self.filename) + os.sep + "test.xml", 'wb')
                       f2.write(real_data)
                       f2.close()

                       f3 = open(os.path.dirname(self.filename) + os.sep + "test.xml", 'r', encoding='utf-8')
                       a1 = f3.read()
                       f3.close()

                       i = 0
                       while i < len(a1) - 1:
                           if a1[i] == '<':
                               i = i + 1
                               if a1[i] == 'a':
                                   i = i + 1
                                   if a1[i] == ':':
                                       i = i + 1
                                       if a1[i] == 't':
                                           i = i + 1
                                           if a1[i] == '>':
                                               i = i + 1
                                               while a1[i] != '<':
                                                   intToString = a1[i]
                                                   only_data = only_data + intToString
                                                   self.content = self.content + intToString
                                                   if i < len(a1) - 1:
                                                       i = i + 1
                                                       if a1[i] == '<':
                                                           only_data = only_data + ''
                                                           self.content = self.content + ''
                                                   else:
                                                       break
                           i = i + 1
                       #self.parse_media(filename, filetype, isDamaged, tmp_path)
                       return only_data
                   else:
                       #self.parse_media(filename, filetype, isDamaged, tmp_path)
                       return only_data

    def parse_metadata(self, filename, isDamaged):

        metadata_value = []
        if isDamaged == False:
            zfile = zipfile.ZipFile(filename)
            for a in zfile.filelist:
                if 'docProps/core.xml' in a.filename:
                    form = zfile.read(a)
                    xmlroot = ET.fromstring(form)
                    self.metadata["Title"] = "None"
                    self.metadata["Author"] = "None"
                    self.metadata["LastSavedBy"] = "None"
                    self.metadata["CreatedTime"] = "None"
                    self.metadata["LastSavedTime"] = "None"
                    self.metadata["Subject"] = "None"
                    self.metadata["Tags"] = "None"
                    self.metadata["Comment"] = "None"
                    self.metadata["RevisionNumber"] = "None"
                    self.metadata["LastPrintedTime"] = "None"
                    self.metadata["Category"] = "None"
                    self.metadata["Explanation"] = "Unsupported"
                    self.metadata["Date"] = "Unsupported"
                    self.metadata["Creator"] = "Unsupported"
                    self.metadata["Trapped"] = "Unsupported"
                    for content in xmlroot:
                        location = content.tag.find('}')
                        metadata_type = content.tag[location + 1:]
                        if metadata_type == 'title' or metadata_type == 'creator' or metadata_type == 'lastModifiedBy' or metadata_type == 'created' or metadata_type == 'modified' or metadata_type == 'subject' or metadata_type == 'keywords' or metadata_type == 'description' or metadata_type == 'revision' or metadata_type == 'lastPrinted'  or metadata_type == 'category':
                            if (content.text == None):
                                if metadata_type == "title":
                                    metadata_type = 'Title'
                                elif metadata_type == 'creator':
                                    metadata_type = 'Author'
                                elif metadata_type == 'lastModifiedBy':
                                    metadata_type = 'LastSavedBy'
                                elif metadata_type == 'created':
                                    metadata_type = 'CreatedTime'
                                elif metadata_type == 'modified':
                                    metadata_type = 'LastSavedTime'
                                elif metadata_type == 'subject':
                                    metadata_type = 'Subject'
                                elif metadata_type == 'keywords':
                                    metadata_type == 'Tags'
                                elif metadata_type == 'description':
                                    metadata_type = 'Comment'
                                elif metadata_type == 'revision':
                                    metadata_type = 'RevisionNumber'
                                elif metadata_type == 'lastPrinted':
                                    metadata_type = 'LastPrintedTime'
                                elif metadata_type == 'category':
                                    metadata_type = 'Category'
                                metadata_value.append(metadata_type + " : None")
                                self.metadata[metadata_type] = content.text
                            else:
                                if metadata_type == "title":
                                    metadata_type = 'Title'
                                elif metadata_type == 'creator':
                                    metadata_type = 'Author'
                                elif metadata_type == 'lastModifiedBy':
                                    metadata_type = 'LastSavedBy'
                                elif metadata_type == 'created':
                                    metadata_type = 'CreatedTime'
                                elif metadata_type == 'modified':
                                    metadata_type = 'LastSavedTime'
                                elif metadata_type == 'subject':
                                    metadata_type = 'Subject'
                                elif metadata_type == 'keywords':
                                    metadata_type == 'Tags'
                                elif metadata_type == 'description':
                                    metadata_type = 'Comment'
                                elif metadata_type == 'revision':
                                    metadata_type = 'RevisionNumber'
                                elif metadata_type == 'lastPrinted':
                                    metadata_type = 'LastPrintedTime'
                                elif metadata_type == 'category':
                                    metadata_type = 'Category'
                                metadata_value.append(metadata_type + " : " + content.text)
                                self.metadata[metadata_type] = content.text

                elif 'docProps/app.xml' in a.filename:
                    form = zfile.read(a)
                    xmlroot = ET.fromstring(form)
                    self.metadata["Manager"] = "None"
                    self.metadata["Company"] = "None"
                    self.metadata["ProgramName"] = "None"
                    self.metadata["TotalTime"] = "None"
                    self.metadata["Version"] = "None"
                    for content in xmlroot:
                        location = content.tag.find('}')
                        metadata_type = content.tag[location + 1:]
                        if metadata_type == 'Manager' or metadata_type == 'Company' or metadata_type == 'Application' or metadata_type == 'TotalTime' or metadata_type == 'AppVersion':
                            if (content.text == None):
                                if metadata_type == 'Application':
                                    metadata_type = 'ProgramName'
                                elif metadata_type == 'AppVersion':
                                    metadata_type = 'Version'
                                metadata_value.append(metadata_type + " : None")
                                self.metadata[metadata_type] = content.text
                            else:
                                if metadata_type == 'Application':
                                    metadata_type = 'ProgramName'
                                elif metadata_type == 'AppVersion':
                                    metadata_type = 'Version'
                                metadata_value.append(metadata_type + " : " + content.text)
                                self.metadata[metadata_type] = content.text
            return metadata_value

        else:
            # 손상 시
            self.metadata["Title"] = "None"
            self.metadata["Author"] = "None"
            self.metadata["LastSavedBy"] = "None"
            self.metadata["CreatedTime"] = "None"
            self.metadata["LastSavedTime"] = "None"
            self.metadata["Subject"] = "None"
            self.metadata["Tags"] = "None"
            self.metadata["Comment"] = "None"
            self.metadata["RevisionNumber"] = "None"
            self.metadata["LastPrintedTime"] = "None"
            self.metadata["Category"] = "None"
            self.metadata["Explanation"] = "Unsupported"
            self.metadata["Date"] = "Unsupported"
            self.metadata["Creator"] = "Unsupported"
            self.metadata["Trapped"] = "Unsupported"
            self.metadata["Manager"] = "None"
            self.metadata["Company"] = "None"
            self.metadata["ProgramName"] = "None"
            self.metadata["TotalTime"] = "None"
            self.metadata["Version"] = "None"
            if isinstance(self.filename, str):
                f = open(self.filename, "rb")
            else:
                f = self.filename
            cal_recovable_count = 0
            f.seek(0, 0)
            signature_three = b'\x4b\x03\x04'
            while True:
                read_onebyte = f.read(1)
                if read_onebyte == b'\x50':
                    read_threebyte = f.read(3)
                    if read_threebyte == signature_three:
                        f.seek(0xE, 1)
                        data_length = int(hex(int.from_bytes(f.read(4), 'little')), 16)
                        f.seek(4, 1)
                        data_name_length = int(hex(int.from_bytes(f.read(2), 'little')), 16)
                        data_offset = int(hex(int.from_bytes(f.read(2), 'little')), 16)

                        data_name = f.read(data_name_length).decode("utf-8")
                        f.seek(data_offset, 1)

                        if data_name == "docProps/core.xml":
                            content_saved = f.read(data_length)

                            f1 = open(os.path.dirname(self.filename) + os.sep + "outputtest.zip", 'wb')
                            f1.write(b'\x78\x9C')
                            f1.write(content_saved)
                            f1.close()

                            fz = open(os.path.dirname(self.filename) + os.sep + "outputtest.zip", 'rb')
                            d = fz.read()
                            fz.close()

                            zobj = zlib.decompressobj()
                            real_data = zobj.decompress(d)

                            f2 = open(os.path.dirname(self.filename) + os.sep + "test.xml", 'wb')
                            f2.write(real_data)
                            f2.close()

                            f3 = open(os.path.dirname(self.filename) + os.sep + "test.xml", 'r', encoding='utf-8')
                            a1 = f3.read()
                            f3.close()

                            i = 0
                            self.metadata["Title"] = "None"
                            self.metadata["Author"] = "None"
                            self.metadata["LastSavedBy"] = "None"
                            self.metadata["CreatedTime"] = "None"
                            self.metadata["LastSavedTime"] = "None"
                            self.metadata["Subject"] = "None"
                            self.metadata["Tags"] = "None"
                            self.metadata["Comment"] = "None"
                            self.metadata["RevisionNumber"] = "None"
                            self.metadata["LastPrintedTime"] = "None"
                            self.metadata["Category"] = "None"
                            self.metadata["Explanation"] = "Unsupported"
                            self.metadata["Date"] = "Unsupported"
                            self.metadata["Creator"] = "Unsupported"
                            self.metadata["Trapped"] = "Unsupported"
                            self.metadata["Manager"] = "None"
                            self.metadata["Company"] = "None"
                            self.metadata["ProgramName"] = "None"
                            self.metadata["TotalTime"] = "None"
                            self.metadata["Version"] = "None"

                            title = "<dc:title>"
                            subject = "<dc:subject>"
                            creator = "<dc:creator>"
                            keywords = "<cp:keywords>"
                            description = "<dc:description>"
                            lastmodifiedBy = "<cp:lastModifiedBy>"
                            revision = "<cp:revision>"
                            c_time = "<dcterms:created"
                            m_time = "<dcterms:modified"
                            category = "<cp:category>"
                            lastprinted = "<cp:lastPrinted>"

                            t_pos = a1.find(title) + 1
                            c_pos = a1.find(creator) + 1
                            c_time_pos = a1.find(c_time) + 1
                            m_time_pos = a1.find(m_time) + 1
                            s_pos = a1.find(subject) + 1
                            k_pos = a1.find(keywords) + 1
                            d_pos = a1.find(description) + 1
                            l_pos = a1.find(lastmodifiedBy) + 1
                            r_pos = a1.find(revision) + 1
                            ca_pos = a1.find(category) + 1
                            la_pos = a1.find(lastprinted) + 1

                            # print('*******메타데이터파싱*******')
                            metadata_count = 0
                            if t_pos is not 0:
                                metadata_value.append("")
                                tmp = 0
                                while True:
                                    tmp += 1
                                    if a1[c_pos + i + 9] == '<':
                                        metadata_value[metadata_count] = metadata_value[metadata_count] + ''
                                        break
                                    metadata_value[metadata_count] = metadata_value[metadata_count] + a1[c_pos + i + 9]
                                    self.metadata['Title'] = metadata_value[metadata_count]
                                    i = i + 1
                                    if a1[c_pos + i + 9] == '<':
                                        break
                                    if tmp >= 1000000:
                                        break
                                metadata_count = metadata_count + 1
                                i = 0

                            if c_pos is not 0:
                                metadata_value.append("")
                                tmp = 0
                                while True:
                                    tmp +=1
                                    if a1[c_pos + i + 11] == '<':
                                        metadata_value[metadata_count] = metadata_value[metadata_count] + ''
                                        break
                                    metadata_value[metadata_count] = metadata_value[metadata_count] + a1[c_pos + i + 11]
                                    self.metadata['Author'] = metadata_value[metadata_count]
                                    i = i + 1
                                    if a1[c_pos + i + 11] == '<':
                                        break
                                    if tmp >= 1000000:
                                        break
                                metadata_count = metadata_count + 1
                                i = 0

                            if c_time_pos is not 0:
                                metadata_value.append("")
                                tmp = 0
                                while True:
                                    tmp += 1
                                    if a1[c_time_pos + i + 42] == '<':
                                        metadata_value[metadata_count] = metadata_value[metadata_count] + ''
                                        break
                                    metadata_value[metadata_count] = metadata_value[metadata_count] + a1[
                                        c_time_pos + i + 42]
                                    # self.metadata['created'] = metadata_value[1]
                                    self.metadata['CreatedTime'] = metadata_value[metadata_count]
                                    i = i + 1
                                    if a1[c_time_pos + i + 42] == '<':
                                        break
                                    if tmp >= 1000000:
                                        break
                                metadata_count = metadata_count + 1
                                i = 0

                            if m_time_pos is not 0:
                                metadata_value.append("")
                                tmp = 0
                                while True:
                                    tmp += 1
                                    if a1[m_time_pos + i + 43] == '<':
                                        metadata_value[metadata_count] = metadata_value[metadata_count] + ''
                                        break
                                    metadata_value[metadata_count] = metadata_value[metadata_count] + a1[
                                        m_time_pos + i + 43]
                                    self.metadata['LastSavedTime'] = metadata_value[metadata_count]
                                    i = i + 1
                                    if a1[m_time_pos + i + 43] == '<':
                                        break
                                    if tmp >= 1000000:
                                        break

                            if s_pos is not 0:
                                metadata_value.append("")
                                tmp = 0
                                while True:
                                    tmp += 1
                                    if a1[s_pos + i + 43] == '<':
                                        metadata_value[metadata_count] = metadata_value[metadata_count] + ''
                                        break
                                    metadata_value[metadata_count] = metadata_value[metadata_count] + a1[s_pos + i + 43]
                                    self.metadata['Subject'] = metadata_value[metadata_count]
                                    i = i + 1
                                    if a1[s_pos + i + 43] == '<':
                                        break
                                    if tmp >= 1000000:
                                        break
                            if k_pos is not 0:
                                metadata_value.append("")
                                tmp = 0
                                while True:
                                    tmp += 1
                                    if a1[s_pos + i + 43] == '<':
                                        metadata_value[metadata_count] = metadata_value[metadata_count] + ''
                                        break
                                    metadata_value[metadata_count] = metadata_value[metadata_count] + a1[k_pos + i + 43]
                                    self.metadata['Tags'] = metadata_value[metadata_count]
                                    i = i + 1
                                    if a1[k_pos + i + 43] == '<':
                                        break
                                    if tmp >= 1000000:
                                        break
                            if d_pos is not 0:
                                metadata_value.append("")
                                tmp = 0
                                while True:
                                    tmp += 1
                                    if a1[d_pos + i + 43] == '<':
                                        metadata_value[metadata_count] = metadata_value[metadata_count] + ''
                                        break
                                    metadata_value[metadata_count] = metadata_value[metadata_count] + a1[d_pos + i + 43]
                                    self.metadata['Comment'] = metadata_value[metadata_count]
                                    i = i + 1
                                    if a1[d_pos + i + 43] == '<':
                                        break
                                    if tmp >= 1000000:
                                        break
                            if l_pos is not 0:
                                metadata_value.append("")
                                tmp = 0
                                while True:
                                    tmp += 1
                                    if a1[l_pos + i + 43] == '<':
                                        metadata_value[metadata_count] = metadata_value[metadata_count] + ''
                                        break
                                    metadata_value[metadata_count] = metadata_value[metadata_count] + a1[l_pos + i + 43]
                                    self.metadata['LastSavedBy'] = metadata_value[metadata_count]
                                    i = i + 1
                                    if a1[l_pos + i + 43] == '<':
                                        break
                                    if tmp >= 1000000:
                                        break
                            if r_pos is not 0:
                                metadata_value.append("")
                                tmp = 0
                                while True:
                                    tmp += 1
                                    if a1[r_pos + i + 43] == '<':
                                        metadata_value[metadata_count] = metadata_value[metadata_count] + ''
                                        break
                                    metadata_value[metadata_count] = metadata_value[metadata_count] + a1[r_pos + i + 43]
                                    self.metadata['RevisionNumber'] = metadata_value[metadata_count]
                                    i = i + 1
                                    if a1[r_pos + i + 43] == '<':
                                        break
                                    if tmp >= 1000000:
                                        break
                            if ca_pos is not 0:
                                metadata_value.append("")
                                tmp = 0
                                while True:
                                    tmp += 1
                                    if a1[ca_pos + i + 43] == '<':
                                        metadata_value[metadata_count] = metadata_value[metadata_count] + ''
                                        break
                                    metadata_value[metadata_count] = metadata_value[metadata_count] + a1[ca_pos + i + 43]
                                    self.metadata['Category'] = metadata_value[metadata_count]
                                    i = i + 1
                                    if a1[ca_pos + i + 43] == '<':
                                        break
                                    if tmp >= 1000000:
                                        break
                            if la_pos is not 0:
                                metadata_value.append("")
                                tmp = 0
                                while True:
                                    tmp += 1
                                    if a1[la_pos + i + 43] == '<':
                                        metadata_value[metadata_count] = metadata_value[metadata_count] + ''
                                        break
                                    metadata_value[metadata_count] = metadata_value[metadata_count] + a1[la_pos + i + 43]
                                    self.metadata['LastPrintedTime'] = metadata_value[metadata_count]
                                    i = i + 1
                                    if a1[la_pos + i + 43] == '<':
                                        break
                                    if tmp >= 1000000:
                                        break
                            return metadata_value

                        elif data_name == "docProps/app.xml":
                            content_saved = f.read(data_length)

                            f1 = open(os.path.dirname(self.filename) + os.sep + "outputtest.zip", 'wb')
                            f1.write(b'\x78\x9C')
                            f1.write(content_saved)
                            f1.close()

                            fz = open(os.path.dirname(self.filename) + os.sep + "outputtest.zip", 'rb')
                            d = fz.read()
                            fz.close()

                            zobj = zlib.decompressobj()
                            real_data = zobj.decompress(d)

                            f2 = open(os.path.dirname(self.filename) + os.sep + "test.xml", 'wb')
                            f2.write(real_data)
                            f2.close()

                            f3 = open(os.path.dirname(self.filename) + os.sep + "test.xml", 'r', encoding='utf-8')
                            a1 = f3.read()
                            f3.close()

                            i = 0
                            self.metadata["Manager"] = "None"
                            self.metadata["Company"] = "None"
                            self.metadata["Application"] = "None"
                            self.metadata["TotalTime"] = "None"
                            self.metadata["AppVersion"] = "None"

                            manager = "<Manager>"
                            company = "<Company>"
                            application = "<Application>"
                            totaltime = "<TotalTime>"
                            appversion = "<AppVersion>"

                            m_pos = a1.find(manager) + 1
                            c_pos = a1.find(company) + 1
                            a_pos = a1.find(application) + 1
                            t_pos = a1.find(totaltime) + 1
                            ap_pos = a1.find(appversion) + 1

                            # print('*******메타데이터파싱*******')
                            try:
                                metadata_count = 0
                                if m_pos is not 0:
                                    metadata_value.append("")
                                    tmp = 0
                                    while True:
                                        tmp += 1
                                        if a1[m_pos + i + 9] == '<':
                                            metadata_value[metadata_count] = metadata_value[metadata_count] + ''
                                            break
                                        metadata_value[metadata_count] = metadata_value[metadata_count] + a1[m_pos + i + 9]
                                        self.metadata['Manager'] = metadata_value[metadata_count]
                                        i = i + 1
                                        if a1[m_pos + i + 9] == '<':
                                            break
                                        if tmp >= 1000000:
                                            break
                                    metadata_count = metadata_count + 1
                                    i = 0

                                if c_pos is not 0:
                                    metadata_value.append("")
                                    tmp = 0
                                    while True:
                                        tmp += 1
                                        if a1[c_pos + i + 11] == '<':
                                            metadata_value[metadata_count] = metadata_value[metadata_count] + ''
                                            break
                                        metadata_value[metadata_count] = metadata_value[metadata_count] + a1[c_pos + i + 11]
                                        self.metadata['Company'] = metadata_value[metadata_count]
                                        i = i + 1
                                        if a1[c_pos + i + 11] == '<':
                                            break
                                        if tmp >= 1000000:
                                            break
                                    metadata_count = metadata_count + 1
                                    i = 0

                                if a_pos is not 0:
                                    metadata_value.append("")
                                    tmp = 0
                                    while True:
                                        tmp += 1
                                        if a1[a_pos + i + 42] == '<':
                                            metadata_value[metadata_count] = metadata_value[metadata_count] + ''
                                            break
                                        metadata_value[metadata_count] = metadata_value[metadata_count] + a1[
                                            a_pos + i + 42]
                                        # self.metadata['created'] = metadata_value[1]
                                        self.metadata['ProgramName'] = metadata_value[metadata_count]
                                        i = i + 1
                                        if a1[a_pos + i + 42] == '<':
                                            break
                                        if tmp >= 1000000:
                                            break
                                    metadata_count = metadata_count + 1
                                    i = 0

                                if t_pos is not 0:
                                    metadata_value.append("")
                                    tmp = 0
                                    while True:
                                        tmp += 1
                                        if a1[t_pos + i + 43] == '<':
                                            metadata_value[metadata_count] = metadata_value[metadata_count] + ''
                                            break
                                        metadata_value[metadata_count] = metadata_value[metadata_count] + a1[
                                            t_pos + i + 43]
                                        self.metadata['TotalTime'] = metadata_value[metadata_count]
                                        i = i + 1
                                        if a1[t_pos + i + 43] == '<':
                                            break
                                        if tmp >= 1000000:
                                            break

                                if ap_pos is not 0:
                                    metadata_value.append("")
                                    tmp = 0
                                    while True:
                                        tmp += 1
                                        if a1[ap_pos + i + 43] == '<':
                                            metadata_value[metadata_count] = metadata_value[metadata_count] + ''
                                            break
                                        metadata_value[metadata_count] = metadata_value[metadata_count] + a1[ap_pos + i + 43]
                                        self.metadata['Version'] = metadata_value[metadata_count]
                                        i = i + 1
                                        if a1[ap_pos + i + 43] == '<':
                                            break
                                        if tmp >= 1000000:
                                            break

                                return metadata_value
                            except Exception as e:
                                print(f"Error : {str(e)}")
                elif read_onebyte == b'':
                    break

    def parse_media(self, filename, filetype, isDamaged, tmp_path):
        signature_last_three = b'\x4b\x03\x04'
        extracted_filename = tmp_path
        # 정상일 경우
        if isDamaged == False:
            if filetype == 'docx':
                #media file extraction
                fantasy_zip = zipfile.ZipFile(filename)
                fantasy_zip.extractall("./test/")
                fantasy_zip.close()
                for a in fantasy_zip.filelist:
                    if 'media' in a.filename:
                        self.has_ole = True
                        filelists = os.listdir('./test/word/media')
                        if (os.path.isdir(extracted_filename + '_extracted')):
                            shutil.rmtree(extracted_filename + '_extracted')
                            os.mkdir(extracted_filename + '_extracted')
                        else:
                            os.mkdir(extracted_filename + '_extracted')
                        for a in filelists:
                            full_filename = os.path.join('./test/word/media/', a)
                            copyfile(full_filename, extracted_filename + '_extracted'+"/"+a)
                        break

                #embedding file extraction
                for a in fantasy_zip.filelist:
                    if 'embeddings' in a.filename:
                        self.has_ole = True
                        filelists = os.listdir('./test/word/embeddings')
                        if not (os.path.isdir(extracted_filename + '_extracted')):
                            os.mkdir(extracted_filename + '_extracted')

                        for a in filelists:
                            full_filename = os.path.join('./test/word/embeddings/', a)
                            copyfile(full_filename, extracted_filename + '_extracted'+"/"+a)

                            # 엑셀인 경우에 hidden 없애줘야한다

                            if a[0] == 'o':
                                ole = olefile.OleFileIO(full_filename)
                                for ole_list in ole.listdir():
                                    if 'Ole10Native' in ole_list[0]:
                                        stream = ole.openstream('\x01Ole10Native')
                                        data = stream.read()
                                        count_data_name = 6
                                        for i in data[6:]:
                                            if i == 0:
                                                break
                                            count_data_name = count_data_name +1
                                        ole.close()
                                        fembedd = open(full_filename, 'rb')
                                        tmp = 0
                                        while True:
                                            tmp += 1
                                            em_data = fembedd.read(1)
                                            if em_data == b'\x52':
                                                em_data = fembedd.read(1)
                                                if em_data == b'\x49':
                                                    em_data = fembedd.read(1)
                                                    if em_data == b'\x46':
                                                        fembedd.seek(-3,1)
                                                        aaa = fembedd.read()
                                                        fembedd.close()
                                                        break
                                            if tmp >= 1000000:
                                                break
                                        fembedd2 = open(extracted_filename+ '_extracted' + '/' + data[6:count_data_name].decode(), 'wb')
                                        fembedd2.write(aaa)
                                        os.remove(extracted_filename + '_extracted' + '/' + a)
                                        fembedd2.close()
                                    elif 'Hwp' in ole_list[0]:
                                        filename_hwp = os.path.splitext(extracted_filename + '_extracted'+"/"+a)
                                        os.rename(extracted_filename + '_extracted'+"/"+a, filename_hwp[0] + '.hwp')
                                    elif ole_list[0] == 'CONTENTS':
                                        stream = ole.openstream('CONTENTS')
                                        data = stream.read()
                                        fembedd2 = open(extracted_filename + '_extracted' + '/' + a + '.pdf', 'wb')
                                        fembedd2.write(data)
                                        os.remove(extracted_filename + '_extracted' + '/' + a)
                                        fembedd2.close()
                        break

                for (path, dir, files) in os.walk(extracted_filename+'_extracted/'):
                    for fname in files:
                        self.ole_path.append(os.path.join(path, fname))

            if filetype == 'xlsx':
                # media file extraction
                fantasy_zip = zipfile.ZipFile(filename)
                fantasy_zip.extractall("./test/")
                fantasy_zip.close()
                for a in fantasy_zip.filelist:
                    if 'media' in a.filename:
                        self.has_ole = True
                        filelists = os.listdir('./test/xl/media')
                        if (os.path.isdir(extracted_filename + '_extracted')):
                            shutil.rmtree(extracted_filename + '_extracted')
                            os.mkdir(extracted_filename + '_extracted')
                        else:
                            os.mkdir(extracted_filename + '_extracted')
                        for a in filelists:
                            full_filename = os.path.join('./test/xl/media/', a)
                            copyfile(full_filename, extracted_filename + '_extracted'+"/"+a)
                        break
                #embedding file extraction
                for a in fantasy_zip.filelist:
                    if 'embeddings' in a.filename:
                        self.has_ole = True
                        filelists = os.listdir('./test/xl/embeddings')
                        if not (os.path.isdir(extracted_filename + '_extracted')):
                            os.mkdir(extracted_filename + '_extracted')
                        for a in filelists:
                            full_filename = os.path.join('./test/xl/embeddings/', a)
                            copyfile(full_filename, extracted_filename + '_extracted'+"/"+a)
                            if a[0] == 'o':
                                ole = olefile.OleFileIO(full_filename)
                                for ole_list in ole.listdir():
                                    if 'Ole10Native' in ole_list[0]:
                                        stream = ole.openstream('\x01Ole10Native')
                                        data = stream.read()
                                        count_data_name = 6
                                        for i in data[6:]:
                                            if i == 0:
                                                break
                                            count_data_name = count_data_name +1
                                        ole.close()
                                        fembedd = open(full_filename, 'rb')
                                        tmp = 0
                                        while True:
                                            tmp += 1
                                            em_data = fembedd.read(1)
                                            if em_data == b'\x52':
                                                em_data = fembedd.read(1)
                                                if em_data == b'\x49':
                                                    em_data = fembedd.read(1)
                                                    if em_data == b'\x46':
                                                        fembedd.seek(-3,1)
                                                        aaa = fembedd.read()
                                                        fembedd.close()
                                                        break
                                            if em_data == b'\xFF':
                                                em_data = fembedd.read(1)
                                                if em_data == b'\xD8':
                                                    em_data = fembedd.read(1)
                                                    if em_data == b'\xFF':
                                                        fembedd.seek(-3,1)
                                                        aaa = fembedd.read()
                                                        fembedd.close()
                                                        break
                                            if tmp >= 1000000:
                                                break
                                        fembedd2 = open(extracted_filename + '_extracted' + '/' + data[6:count_data_name].decode(), 'wb')
                                        fembedd2.write(aaa)
                                        os.remove(extracted_filename + '_extracted' + '/' + a)
                                        fembedd2.close()
                                    elif 'Hwp' in ole_list[0]:
                                        filename_hwp = os.path.splitext(extracted_filename + '_extracted' + "/" + a)
                                        os.rename(extracted_filename + '_extracted' + "/" + a, filename_hwp[0] + '.hwp')
                                    elif ole_list[0] == 'CONTENTS':
                                        stream = ole.openstream('CONTENTS')
                                        data = stream.read()
                                        fembedd2 = open(extracted_filename + '_extracted' + '/' + a + '.pdf', 'wb')
                                        fembedd2.write(data)
                                        os.remove(extracted_filename + '_extracted' + '/' + a)
                                        fembedd2.close()
                        break
                for (path, dir, files) in os.walk(extracted_filename+'_extracted/'):
                    for fname in files:
                        self.ole_path.append(os.path.join(path, fname))

            if filetype == 'pptx':
                # media file extraction
                fantasy_zip = zipfile.ZipFile(filename)
                fantasy_zip.extractall("./test/")
                fantasy_zip.close()

                for a in fantasy_zip.filelist:
                    if 'media' in a.filename:
                        self.has_ole = True
                        filelists = os.listdir('./test/ppt/media')
                        if (os.path.isdir(extracted_filename + '_extracted')):
                            shutil.rmtree(extracted_filename + '_extracted')
                            os.mkdir(extracted_filename + '_extracted')
                        else:
                            os.mkdir(extracted_filename + '_extracted')
                        for a in filelists:
                            full_filename = os.path.join('./test/ppt/media/', a)
                            copyfile(full_filename, extracted_filename + '_extracted'+"/"+a)
                        break

                # embedding file extraction
                for a in fantasy_zip.filelist:
                    if 'embeddings' in a.filename:
                        filelists = os.listdir('./test/ppt/embeddings')
                        if not (os.path.isdir(extracted_filename + '_extracted')):
                            os.mkdir(extracted_filename + '_extracted')

                        for a in filelists:
                            full_filename = os.path.join('./test/ppt/embeddings/', a)
                            copyfile(full_filename, extracted_filename + '_extracted' + "/" + a)
                            if a[0] == 'o':
                                self.has_ole = True
                                ole = olefile.OleFileIO(full_filename)
                                for temp_list in ole.listdir():
                                    if temp_list[0] == 'Package':
                                        stream = ole.openstream('Package')
                                        data = stream.read()
                                        if 'word' in str(data):
                                            fembedd2 = open(extracted_filename + '_extracted' + '/' + a + '.docx', 'wb')
                                            os.remove(extracted_filename + '_extracted' + '/' + a)
                                            fembedd2.write(data)
                                            fembedd2.close()
                                        elif 'ppt' in str(data):
                                            fembedd2 = open(extracted_filename + '_extracted' + '/' + a + '.pptx', 'wb')
                                            os.remove(extracted_filename + '_extracted' + '/' + a)
                                            fembedd2.write(data)
                                            fembedd2.close()
                                        elif 'workbook' in str(data):
                                            fembedd2 = open(extracted_filename + '_extracted' + '/' + a + '.xlsx', 'wb')
                                            os.remove(extracted_filename + '_extracted' + '/' + a)
                                            fembedd2.write(data)
                                            fembedd2.close()

                                    elif 'Hwp' in temp_list[0]:
                                        filename_hwp = os.path.splitext(extracted_filename + '_extracted' + "/" + a)
                                        os.rename(extracted_filename + '_extracted' + "/" + a, filename_hwp[0] + '.hwp')
                                        break

                                    elif '1Table' in temp_list[0]:
                                        filename_hwp = os.path.splitext(extracted_filename + '_extracted' + "/" + a)
                                        os.rename(extracted_filename + '_extracted' + "/" + a, filename_hwp[0] + '.doc')
                                        break

                                    elif 'Workbook' in temp_list[0]:
                                        filename_hwp = os.path.splitext(extracted_filename + '_extracted' + "/" + a)
                                        os.rename(extracted_filename + '_extracted' + "/" + a, filename_hwp[0] + '.xls')
                                        break

                                    elif 'Pictures' in temp_list[0]:
                                        filename_hwp = os.path.splitext(extracted_filename + '_extracted' + "/" + a)
                                        os.rename(extracted_filename + '_extracted' + "/" + a, filename_hwp[0] + '.ppt')
                                        break

                                    elif temp_list[0] == 'CONTENTS':
                                        stream = ole.openstream('CONTENTS')
                                        data = stream.read()
                                        fembedd2 = open(extracted_filename + '_extracted' + '/' + a + '.pdf', 'wb')
                                        fembedd2.write(data)
                                        os.remove(extracted_filename + '_extracted' + '/' + a)
                                        fembedd2.close()
                        ole.close()
                        break
                for (path, dir, files) in os.walk(extracted_filename+'_extracted/'):
                    for fname in files:
                        self.ole_path.append(os.path.join(path, fname))

        #손상일때
        else:
            if (os.path.isdir(extracted_filename + '_extracted')):
                shutil.rmtree(extracted_filename + '_extracted')
                os.mkdir(extracted_filename + '_extracted')
            else:
                os.mkdir(extracted_filename + '_extracted')
            with open(extracted_filename, 'rb') as f:
                notEnd = True
                while notEnd:
                    try:
                        hd = FileHeader(f)
                        comps = f.read(hd.compSize)
                        if 'image' in hd.name.decode('utf-8') or 'oleObject' in hd.name.decode('utf-8') or 'Microsoft_' in hd.name.decode('utf-8'):
                            self.has_ole = True
                            #print(os.path.basename(hd.name.decode('utf-8')))
                            image_file = os.path.basename(hd.name.decode('utf-8'))
                            if image_file[0] != 'o':
                                new_file = open(extracted_filename + '_extracted/' + image_file, 'wb')
                                new_file.write(comps)
                            else:
                                new_file = open(extracted_filename + '_extracted/' + image_file, 'wb')
                                hd.writeHeader(new_file)
                                new_file.write(comps)
                            new_file.flush()
                        if comps == b'':
                            break
                    except:
                        break


            for (path, dir, files) in os.walk(extracted_filename + '_extracted/'):
                for fname in files:
                    self.ole_path.append(os.path.join(path, fname))

    def parse_main(self, filename, filetype, tmp_path):

        content_data = ''
        metadata_data = ''

        # 손상 여부 확인 "isDamaged"
        #print("----------손상여부----------")
        damaged_flag = self.isDamaged(filename, filetype)
        #print(damaged_flag)

        # 복구 가능
            # 정상일때
        if damaged_flag == False:
            # 본문 파싱
            content_data = self.parse_content(filename, filetype, damaged_flag, tmp_path)
            # 메타데이터 파싱
            metadata_data = self.parse_metadata(filename, damaged_flag)

            content_recoverable_flag = True
            metadata_recoverable_flag = True

            # 손상일때
        elif damaged_flag == True:
            # 본문 복구 가능 여부 확인
            #print("------본문복구가능여부------")
            content_recoverable_flag = self.isRecoverable_content(filetype)
            #print(content_recoverable_flag)
            # 본문 복구 가능일 때
            if content_recoverable_flag == True:
                # 본문 파싱
                content_data = self.parse_content(filename, filetype, damaged_flag)
            # 메타데이터 복구 가능 여부 확인
            #print("---메타데이터복구가능여부---")
            metadata_recoverable_flag = self.isRecoverable_metadata(filetype)
            #print(metadata_recoverable_flag)
            # 메타데이터 복구 가능일 때
            if metadata_recoverable_flag == True:
                # 메타데이터 파싱
                metadata_data = self.parse_metadata(filename, damaged_flag)
            if metadata_recoverable_flag == False:
                self.metadata["Title"] = "None"
                self.metadata["Author"] = "None"
                self.metadata["LastSavedBy"] = "None"
                self.metadata["CreatedTime"] = "None"
                self.metadata["LastSavedTime"] = "None"
                self.metadata["Subject"] = "None"
                self.metadata["Tags"] = "None"
                self.metadata["Comment"] = "None"
                self.metadata["RevisionNumber"] = "None"
                self.metadata["LastPrintedTime"] = "None"
                self.metadata["Category"] = "None"
                self.metadata["Explanation"] = "Unsupported"
                self.metadata["Date"] = "Unsupported"
                self.metadata["Creator"] = "Unsupported"
                self.metadata["Trapped"] = "Unsupported"
                self.metadata["Manager"] = "None"
                self.metadata["Company"] = "None"
                self.metadata["ProgramName"] = "None"
                self.metadata["TotalTime"] = "None"
                self.metadata["Version"] = "None"
        # 복구 불가
        else:
            # 메타데이터 복구 가능 여부 확인
            #print("---메타데이터복구가능여부---")
            metadata_recoverable_flag = self.isRecoverable_metadata(filetype)
            self.metadata["Title"] = "None"
            self.metadata["Author"] = "None"
            self.metadata["LastSavedBy"] = "None"
            self.metadata["CreatedTime"] = "None"
            self.metadata["LastSavedTime"] = "None"
            self.metadata["Subject"] = "None"
            self.metadata["Tags"] = "None"
            self.metadata["Comment"] = "None"
            self.metadata["RevisionNumber"] = "None"
            self.metadata["LastPrintedTime"] = "None"
            self.metadata["Category"] = "None"
            self.metadata["Explanation"] = "Unsupported"
            self.metadata["Date"] = "Unsupported"
            self.metadata["Creator"] = "Unsupported"
            self.metadata["Trapped"] = "Unsupported"
            self.metadata["Manager"] = "None"
            self.metadata["Company"] = "None"
            self.metadata["ProgramName"] = "None"
            self.metadata["TotalTime"] = "None"
            self.metadata["Version"] = "None"
			#print(metadata_recoverable_flag)
            # 메타데이터 복구 가능일 때
            if metadata_recoverable_flag == True:
                
				# 메타데이터 파싱
                metadata_data = self.parse_metadata(filename, damaged_flag)
            #else:
                #print("***본문, 메타데이터복구불가***")

        #print(self.ole_path)
        #print(content_data)
        #self.parse_media(filename, filetype)