import zipfile, os, shutil
import xml.etree.ElementTree as ET
import xlrd
from shutil import copyfile
from zipfile import BadZipFile
import zlib

WORD_NAMESPACE = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
PARA = WORD_NAMESPACE + 'p'
TEXT = WORD_NAMESPACE + 't'
S_TEXT = WORD_NAMESPACE + 'r'

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

def isNumber(s):
  try:
    int(s)
    return True
  except ValueError:
    return False

class OOXML:

    def __init__(self, filename):
        # 초기화
        self.filename = filename
        self.is_damaged = False
        self.has_content = False
        self.has_metadata = False
        self.content = ""
        self.metadata = {}

    def parse_ooxml(self):
        filetype = ''
        # 확장자 체크
        # 설명: 1: docx, 2: xlsx, 3: pptx

        if self.checktype(self.filename) == 1:
            filetype = "docx"
        if self.checktype(self.filename) == 2:
            filetype = "xlsx"
        if self.checktype(self.filename) == 3:
            filetype = "pptx"

        self.parse_main(self.filename, filetype)

    def checktype(self, filename):
        # 확장자로 구분 (확장자 뒤에서 두번째 자리)
        # 설명: 1: docx, 2: xlsx, 3: pptx
        if filename[-2] == 'c':
            return 1 #docx
        if filename[-2] == 's':
            return 2 #xlsx
        if filename[-2] == 't':
            return 3

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

                f = open(self.filename, "rb")

                if f.read(4) == b'\x50\x4b\x03\x04':
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

                f = open(self.filename, "rb")

                if f.read(4) == b'\x50\x4b\x03\x04':
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
                    return isDamagedFlag
                else:
                    isDamagedFlag = True
                    return isDamagedFlag
                return isDamagedFlag

            # pptx 일때
            if filetype == "pptx":

                f = open(self.filename, "rb")

                if f.read(4) == b'\x50\x4b\x03\x04':

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
                    return isDamagedFlag
                else:
                    isDamagedFlag = True
                    return isDamagedFlag
                return isDamagedFlag

        except BadZipFile:
            isDamagedFlag = True
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
            f = open(self.filename, "rb")
            temp1 = 0
            fileSize = f.seek(0, 2)
            f.seek(0, 0)
            while True:
                if f.read(1) == b'\x50':
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

            return recovableFlag

        # xlsx 일때
        if filetype == "xlsx":
            f = open(self.filename, "rb")
            temp1 = 0
            fileSize = f.seek(0, 2)
            f.seek(0, 0)
            while True:
                if f.read(1) == b'\x50':
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

            return recovableFlag

        # pptx 일때
        if filetype == "pptx":
            f = open(self.filename, "rb")
            temp1 = 0
            fileSize = f.seek(0, 2)
            f.seek(0, 0)
            while True:
                if f.read(1) == b'\x50':
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
            f = open(self.filename, "rb")
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

            return recovableFlag

        # xlsx 일때
        if filetype == "xlsx":
            f = open(self.filename, "rb")
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

            return recovableFlag

        # pptx 일때
        if filetype == "pptx":
            f = open(self.filename, "rb")
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

            return recovableFlag

        return recovableFlag

    def parse_content(self, filename, filetype, isDamaged):
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
                    if 'word/document.xml' in a.filename:
                        form = zfile.read(a)
                        xmlroot = ET.fromstring(form)
                        for content in xmlroot.getiterator(PARA):
                            for a in content:
                                for b in a:
                                    if b.tag == TEXT:
                                        normal_content_data = normal_content_data + b.text
                                        self.content = self.content + b.text
                                    if b.tag == S_TEXT:
                                        for c in b:
                                            if c.tag == TEXT:
                                                normal_content_data = normal_content_data + c.text
                                                self.content = self.content + c.text
                return normal_content_data
            #손상일 때
            else:
                f = open(self.filename, "rb")
                temp1 = 0
                fileSize = f.seek(0, 2)
                f.seek(0, 0)
                #print("**********본문파싱**********")
                while True:
                    if f.read(1) == b'\x50':
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

                if content_saved == "":
                    temp_size = lastpart[30+data_name_length:]

                    f1 = open("./outputtest.zip", 'wb')
                    f1.write(b'\x78\x9C')
                    f1.write(temp_size)
                    f1.close()

                    fz = open("./outputtest.zip",'rb')
                    d = fz.read()
                    fz.close()

                    zobj = zlib.decompressobj()
                    real_data = zobj.decompress(d)

                    f2 = open("./test.xml",'wb')
                    f2.write(real_data)
                    f2.close()

                    f3 = open("./test.xml",'r',encoding='utf-8')
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

                    return only_data
                else:
                    f1 = open("./outputtest.zip", 'wb')
                    f1.write(b'\x78\x9C')
                    f1.write(content_saved)
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

                    return only_data

        if filetype == 'xlsx':
            if isDamaged == False:
                #print("**********본문파싱**********")
                wb = xlrd.open_workbook(filename)
                ws = wb.sheet_by_index(0)
                ncol = ws.ncols
                nlow = ws.nrows
                i = 0
                j = 0
                low = []
                list = []
                while i < nlow:
                    while j < ncol:
                        low.append(str(ws.row_values(i)[j]))
                        j += 1
                    list.append(low)
                    low = []
                    i += 1
                    j = 0
                i = 0
                while i < nlow:
                    xlsx_normal_content_data.append(list[i])
                    self.content = self.content + str(list[i])
                    i += 1
                return xlsx_normal_content_data

            else:
                # 손상일때
                f = open(self.filename, "rb")
                temp1 = 0
                fileSize = f.seek(0, 2)
                f.seek(0, 0)
                #print("**********본문파싱**********")
                while True:
                    if f.read(1) == b'\x50':
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
                                    f1 = open("./outputtest.zip", 'wb')
                                    f1.write(b'\x78\x9C')
                                    f1.write(content_saved)
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
                f.close()
                f = open(self.filename, "rb")
                temp1 = 0
                fileSize = f.seek(0, 2)
                f.seek(0, 0)
                # print("**********본문파싱**********")
                while True:
                    if f.read(1) == b'\x50':
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
                                    f1 = open("./outputtest.zip", 'wb')
                                    f1.write(b'\x78\x9C')
                                    f1.write(content_saved)
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
                '''
                for num_list in order_word:
                    if int(num_list) > len(list_word):
                        final_word = final_word + num_list + ' '
                    else:
                        final_word = final_word + list_word[int(num_list)] + ' '
                '''
                self.content = final_word
                return final_word

                if "docProps" not in data_name:
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

                    return only_data

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

                               f1 = open("./outputtest.zip", 'wb')
                               f1.write(b'\x78\x9C')
                               f1.write(content_saved)
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
                               slides_app = "<Slides>"
                               s_pos = a1.find(slides_app) + 1

                               if s_pos is not 0:
                                   while True:
                                       slides_value = slides_value + a1[s_pos + i + 7]
                                       i = i + 1
                                       if a1[s_pos + i + 7] == '<':
                                           break
                                   i = 0

                           if f.tell() + data_length > fileSize:
                               break

                       elif read_threebyte == stop_signature_three:
                           break
               f.close()
               if slides_value is not "":
                   f = open(self.filename, "rb")
                   f.seek(0, 0)
                   for slides_i in range(1, int(slides_value)+1):
                       f.seek(0, 0)
                       while True:

                           if f.read(1) == b'\x50':
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
                                           f1 = open("./outputtest.zip", 'wb')
                                           f1.write(b'\x78\x9C')
                                           f1.write(content_saved)
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
                   return only_data
               else:
                   # 손상일때
                   f = open(self.filename, "rb")
                   temp1 = 0
                   fileSize = f.seek(0, 2)
                   f.seek(0, 0)
                   # print("**********본문파싱**********")
                   while True:
                       if f.read(1) == b'\x50':
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
                                       f1 = open("./outputtest.zip", 'wb')
                                       f1.write(b'\x78\x9C')
                                       f1.write(content_saved)
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

                   if "ppt/slideL" not in data_name:
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

                       return only_data
                   else:
                       return only_data

    def parse_metadata(self, filename, isDamaged):

        metadata_value = []
        if isDamaged == False:
            zfile = zipfile.ZipFile(filename)
            for a in zfile.filelist:
                if 'docProps/core.xml' in a.filename:
                    form = zfile.read(a)
                    xmlroot = ET.fromstring(form)
                    self.metadata["title"] = "None"
                    self.metadata["creator"] = "None"
                    self.metadata["created"] = "None"
                    self.metadata["modified"] = "None"
                    for content in xmlroot:
                        location = content.tag.find('}')
                        metadata_type = content.tag[location + 1:]

                        if (content.text == None):
                            metadata_value.append(metadata_type + " : None")
                            self.metadata[metadata_type] = content.text
                        else:
                            metadata_value.append(metadata_type + " : " + content.text)
                            self.metadata[metadata_type] = content.text
                    return metadata_value

        else:
            # 손상 시
            self.metadata["title"] = "None"
            self.metadata["creator"] = "None"
            self.metadata["created"] = "None"
            self.metadata["modified"] = "None"
            f = open(self.filename, "rb")
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

                            f1 = open("./outputtest.zip", 'wb')
                            f1.write(b'\x78\x9C')
                            f1.write(content_saved)
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
                            title = "<dc:title>"
                            subject = "<dc:subject>"
                            creator = "<dc:creator>"
                            keywords = "<cp:keywords>"
                            description = "<dc:description>"
                            lastmodifiedBy = "<cp:lastModifiedBy>"
                            revision = "<cp:revision>"
                            c_time = "<dcterms:created"
                            m_time = "<dcterms:modified"

                            t_pos = a1.find(title)+1
                            c_pos = a1.find(creator)+1
                            c_time_pos = a1.find(c_time)+1
                            m_time_pos = a1.find(m_time)+1
                            #print('*******메타데이터파싱*******')
                            metadata_count = 0
                            if t_pos is not 0:
                                metadata_value.append("")
                                while True:
                                    if a1[c_pos + i + 9] == '<':
                                        metadata_value[metadata_count] = metadata_value[metadata_count] + ''
                                        break
                                    metadata_value[metadata_count] = metadata_value[metadata_count]+a1[c_pos+i+9]
                                    self.metadata['title'] = metadata_value[metadata_count]
                                    i = i + 1
                                    if a1[c_pos+i+9] == '<':
                                        break
                                metadata_count = metadata_count + 1
                                i=0

                            if c_pos is not 0:
                                metadata_value.append("")
                                while True:
                                    if a1[c_pos + i + 11] == '<':
                                        metadata_value[metadata_count] = metadata_value[metadata_count] + ''
                                        break
                                    metadata_value[metadata_count] = metadata_value[metadata_count]+a1[c_pos+i+11]
                                    self.metadata['creator'] = metadata_value[metadata_count]
                                    i = i + 1
                                    if a1[c_pos+i+11] == '<':
                                        break
                                metadata_count = metadata_count + 1
                                i=0

                            if c_time_pos is not 0:
                                metadata_value.append("")
                                while True:
                                    if a1[c_time_pos + i + 42] == '<':
                                        metadata_value[metadata_count] = metadata_value[metadata_count] + ''
                                        break
                                    metadata_value[metadata_count] = metadata_value[metadata_count]+a1[c_time_pos+i+42]
                                    #self.metadata['created'] = metadata_value[1]
                                    self.metadata['created'] = metadata_value[metadata_count]
                                    i = i + 1
                                    if a1[c_time_pos+i+42] == '<':
                                        break
                                metadata_count = metadata_count + 1
                                i=0

                            if m_time_pos is not 0:
                                metadata_value.append("")
                                while True:
                                    if a1[m_time_pos + i + 43] == '<':
                                        metadata_value[metadata_count] = metadata_value[metadata_count] + ''
                                        break
                                    metadata_value[metadata_count] = metadata_value[metadata_count]+a1[m_time_pos+i+43]
                                    self.metadata['modified'] = metadata_value[metadata_count]
                                    i = i + 1
                                    if a1[m_time_pos+i+43] == '<':
                                        break

                            return metadata_value

    def parse_media(self, filename, filetype):
        if filetype == 'docx':
            fantasy_zip = zipfile.ZipFile(filename)
            fantasy_zip.extractall("./test/")
            fantasy_zip.close()
            filelists = os.listdir('./test/word/media')
            if not(os.path.isdir('./'+filename)):
                os.mkdir('./'+filename)
            for a in filelists:
                full_filename = os.path.join('./test/word/media/', a)
                copyfile(full_filename, './'+filename+"/"+a)
                '''
                    # 바로 출력해주기
                    while True:
                        string = IN.read(16)
                        bufString = len(string)
                        if bufString == 0: break
                        else: print(string) # 일단 print로 해놓음
                '''
        if filetype == 'xlsx':
            fantasy_zip = zipfile.ZipFile(filename)
            fantasy_zip.extractall("./test/")
            fantasy_zip.close()
            filelists = os.listdir('./test/xl/media')
            if not(os.path.isdir('./'+filename)):
                os.mkdir('./'+filename)
            for a in filelists:
                full_filename = os.path.join('./test/xl/media/', a)
                copyfile(full_filename, './'+filename+"/"+a)

        if filetype == 'pptx':
            fantasy_zip = zipfile.ZipFile(filename)
            fantasy_zip.extractall("./test/")
            fantasy_zip.close()
            filelists = os.listdir('./test/ppt/media')
            if not(os.path.isdir('./'+filename)):
                os.mkdir('./'+filename)
            for a in filelists:
                full_filename = os.path.join('./test/ppt/media/', a)
                copyfile(full_filename, './'+filename+"/"+a)

    def parse_main(self, filename, filetype):

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
            content_data = self.parse_content(filename, filetype, damaged_flag)
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
                self.metadata["title"] = "None"
                self.metadata["creator"] = "None"
                self.metadata["created"] = "None"
                self.metadata["modified"] = "None"
        # 복구 불가
        else:
            # 메타데이터 복구 가능 여부 확인
            #print("---메타데이터복구가능여부---")
            metadata_recoverable_flag = self.isRecoverable_metadata(filetype)
            #print(metadata_recoverable_flag)
            # 메타데이터 복구 가능일 때
            if metadata_recoverable_flag == True:
                # 메타데이터 파싱
                metadata_data = self.parse_metadata(filename, damaged_flag)
            #else:
                #print("***본문, 메타데이터복구불가***")

        #print("")
        #print("********본문********")
        #print(content_data)

        '''
        #메모장 생성
        filenameonly = os.path.split(filename)
        memo_name = "./"+filenameonly[1]+'_content.txt'
        fmemo = open(memo_name, 'w', encoding='UTF8')
        fmemo.write(str(content_data))
        fmemo.close()

        #print("*****메타데이터*****")
        #print(metadata_data)

        #메모장 생성
        memo_name2 = "./"+filenameonly[1]+'_metadata.txt'
        fmemo2 = open(memo_name2, 'w', encoding='UTF8')
        fmemo2.write(str(metadata_data))
        fmemo2.close()
        '''
        #self.parse_media(filename, filetype)
        if os.path.isdir('./test'):
            shutil.rmtree('./test')



