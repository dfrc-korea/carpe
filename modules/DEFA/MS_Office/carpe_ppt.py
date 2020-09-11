# carpe_ppt.py
import struct
import zipfile
import zlib
import os
import shutil
from compoundfiles import *

class PPT :
    RT_CurrentUserAtom = b'\xF6\x0F'
    RT_UserEditAtom = b'\xF5\x0F'
    RT_PersistPtrIncrementalAtom = b'\x72\x17'

    RT_Document = b'\xE8\x03'
    RT_MainMaster = b'\xF8\x03'
    RT_Slide = b'\xEE\x03'
    RT_Notes = b'\xF0\x03'
    RT_NotesAtom = b'\xF1\x03'

    RT_SlideListWithText = b'\xF0\x0F'
    RT_SlidePersistAtom = b'\xF3\x03'
    RT_TextHeader = b'\x9F\x0F'
    RT_TextBytesAtom = b'\xA8\x0F'
    RT_TextCharsAtom = b'\xA0\x0F'
    RT_StyleTextPropAtom = b'\xA1\x0F'
    RT_TextSpecInfoAtom = b'\xAA\x0F'

    RT_SlideAtom = b'\xEF\x03'
    RT_PPDrawing = b'\x0C\x04'
    RT_EscherClientTextbox = b'\x0D\xF0'

    # define RT_Slide							0x03EE	// 1006	 [C]
    RT_ProgTags = b'\x88\x13'
    RT_BinaryTagDataBlob = b'\x8B\x13'
    RT_Comment10 = b'\xE0\x2E'
    RT_CString = b'\xBA\x0F'

    # define RT_CString		0x0FBA	// 4026	 [A]	// UNICODE
    # define RT_Comment10			0x2EE0	// 12000 [C]
    # define RT_CString		0x0FBA	// 4026	 [A]	// UNICODE

    RT_EndDocument = b'\xEA\x03'



    def __init__(self, compound):
        self.compound = compound
        self.powerpoint_document = b''
        self.current_user = b''
        self.current_offset = 0
        self.arr_user_edit_block = []
        self.arr_persist_ptr_incremental_block = []
        self.arr_edit_block_text = []
        self.text = b''              # tempText
        self.text_bytes = b''
        self.text_chars = b''
        self.filteredText = bytearray(b'')

    def __enter__(self):
        raise NotImplementedError

    def __exit__(self):
        raise NotImplementedError

    def parse_ppt(self):
        if self.compound.is_damaged == self.compound.CONST_DOCUMENT_NORMAL:
            self.__parse_ppt_normal__()
        elif self.compound.is_damaged == self.compound.CONST_DOCUMENT_DAMAGED:
            self.__parse_ppt_damaged__()

    def __get_user_edit_offset__(self):
        raise NotImplementedError

    def __set_chain__(self):
        raise NotImplementedError

    def __extract_text__(self):
        raise NotImplementedError

    def __extract_text_in_slide__(self, block_number, sheet_number, slide_id):
        slide_total_length = 0
        length = 0

        tmpHeader = {}
        tmpHeader['option'] = 0
        tmpHeader['type'] = b''
        tmpHeader['length'] = 0


        # set the current offset
        self.current_offset = 0

        for i in range(block_number, len(self.arr_persist_ptr_incremental_block)):
            for j in range(0, len(self.arr_persist_ptr_incremental_block[i])):
                for k in range(0, self.arr_persist_ptr_incremental_block[i][j]['count']):
                    if self.arr_persist_ptr_incremental_block[i][j]['startnum'] + k == sheet_number:
                        self.current_offset = struct.unpack('<I', self.arr_persist_ptr_incremental_block[i][j]['object'][4 * k : 4 * (k + 1)])[0]
                if self.current_offset != 0:
                    break
            if self.current_offset != 0:
                break

        # traverse records in a slide record
        if self.__get_header_info__(tmpHeader) == False:
            return

        if tmpHeader['type'] != self.RT_Slide and tmpHeader['type'] != self.RT_Notes:
            return

        slide_total_length = tmpHeader['length']

        while True:
            if length >= slide_total_length:
                return

            if self.__get_header_info__(tmpHeader) == False:
                return

            if tmpHeader['type'] == self.RT_PPDrawing:
                self.__extract_text_in_slide_ppt_drawing__(tmpHeader)
                length += tmpHeader['length']
                continue
            elif tmpHeader['type'] == self.RT_ProgTags:
                self.__extract_text_in_slide_ppt_comment__(tmpHeader)
                length += tmpHeader['length']
                continue

            self.current_offset += tmpHeader['length']
            length += tmpHeader['length']

    def __extract_text_in_slide_ppt_comment__(self, header):
        j = 0
        preSize = 0
        totalLength_tmp = header['length']
        totalLength = 0
        tmpLength = 0
        readLength = 0

        tmpHeader = {}
        tmpHeader['option'] = 0
        tmpHeader['type'] = b''
        tmpHeader['length'] = 0

        while True :
            if totalLength_tmp <= totalLength:
                break

            if ((tmpHeader['option'] & 0x000F) == 0x000F):  # Container
                pass
            else:  # Atom
                self.current_offset += tmpHeader['length']
                totalLength += tmpHeader['length']

            if totalLength_tmp <= totalLength:
                break

            if self.__get_header_info__(tmpHeader) == self.compound.CONST_ERROR:
                break

            totalLength += 8

            if tmpHeader['type'] == self.RT_BinaryTagDataBlob:
                tmpLength = tmpHeader['length']
                readLength = 0

                while True:
                    if tmpLength <= readLength:
                        break

                    if self.__get_header_info__(tmpHeader) == self.compound.CONST_ERROR:
                        break

                    readLength += 8

                    if tmpHeader['type'] == self.RT_CString:
                        if tmpHeader['length'] == 2 and self.powerpoint_document[self.current_offset] == 0x6A and self.powerpoint_document[self.current_offset + 1] == 0x00:
                            self.current_offset += tmpHeader['length']
                            readLength += tmpHeader['length']

                        self.text_chars = b''
                        self.text_chars = self.powerpoint_document[self.current_offset : self.current_offset + tmpHeader['length']]

                        preSize = len(self.text)
                        self.text += self.text_chars
                        self.text += b'\x0A'

                        self.current_offset += tmpHeader['length']
                        readLength += tmpHeader['length']
                    else:
                        if((tmpHeader['option'] & 0x000F) == 0x000F):       # Container
                            pass
                        else:                                               # Atom
                            self.current_offset += tmpHeader['length']
                            readLength += tmpHeader['length']

                totalLength += readLength

                if totalLength_tmp != totalLength :
                    if self.__get_header_info__(tmpHeader) == self.compound.CONST_ERROR:
                        break
                    totalLength += 8

    def __extract_text_in_slide_ppt_drawing__(self, header):

        preSize = 0
        tmpPPDrawingLength = header['length']
        PPDrawingReadLength = 0

        tmpLength = 0
        readLength = 0
        textOK = False

        tmpHeader = {}
        tmpHeader['option'] = 0
        tmpHeader['type'] = b''
        tmpHeader['length'] = 0

        while True:
            if tmpPPDrawingLength <= PPDrawingReadLength:
                break
            if tmpHeader['option'] & 0x000F == 0x000F:
                pass            # Container
            else:               # Atom
                self.current_offset += tmpHeader['length']
                PPDrawingReadLength += tmpHeader['length']


            if tmpPPDrawingLength <= PPDrawingReadLength:
                break

            if self.__get_header_info__(tmpHeader) == self.compound.CONST_ERROR:
                break

            PPDrawingReadLength += 8

            if tmpHeader['type'] == self.RT_EscherClientTextbox:
                tmpLength = tmpHeader['length']
                readLength = 0
                textOK = False

                while True:
                    if tmpLength <= readLength:
                        break

                    if self.__get_header_info__(tmpHeader) == self.compound.CONST_ERROR:
                        break

                    readLength += 8

                    if tmpHeader['type'] == self.RT_SlidePersistAtom:
                        pass
                    elif tmpHeader['type'] == self.RT_TextHeader:
                        self.current_offset += tmpHeader['length']
                        readLength += tmpHeader['length']
                    elif tmpHeader['type'] == self.RT_TextBytesAtom:
                        self.text_bytes = b''
                        self.text_chars = b''
                        self.text_bytes = self.powerpoint_document[self.current_offset : self.current_offset + tmpHeader['length']]
                        for i in range(0, len(self.text_bytes)):
                            self.text_chars += bytes([self.text_bytes[i]])
                            self.text_chars += b'\x00'

                        preSize = len(self.text)
                        self.text += self.text_chars
                        self.text += b'\x0A\x00'

                        self.current_offset += tmpHeader['length']
                        readLength += tmpHeader['length']
                        textOK = True
                    elif tmpHeader['type'] == self.RT_TextCharsAtom:
                        self.text_chars = b''
                        self.text_chars = self.powerpoint_document[self.current_offset : self.current_offset + tmpHeader['length']]

                        self.text += self.text_chars
                        self.text += b'\x0A\x00'

                        self.current_offset += tmpHeader['length']
                        readLength += tmpHeader['length']
                        textOK = True
                    else:
                        if((tmpHeader['option'] & 0x000F) == 0x000F):       # Container
                            pass
                        else:                                               # Atom
                            self.current_offset += tmpHeader['length']
                            readLength += tmpHeader['length']

                PPDrawingReadLength += readLength

                if tmpPPDrawingLength != PPDrawingReadLength:
                    if self.__get_header_info__(tmpHeader) == self.compound.CONST_ERROR:
                        break
                    PPDrawingReadLength += 8

    def __get_header_info__(self, header):
        if self.current_offset + 8 > len(self.powerpoint_document):
            return self.compound.CONST_ERROR

        header['option'] = struct.unpack('<H', self.powerpoint_document[self.current_offset: self.current_offset + 2])[0]
        header['type'] = self.powerpoint_document[self.current_offset + 2: self.current_offset + 4]
        header['length'] = struct.unpack('<I', self.powerpoint_document[self.current_offset + 4: self.current_offset + 8])[0]
        self.current_offset += 8
        return self.compound.CONST_SUCCESS

    def __ppt_extra_filter__(self, tempLen):
        i = 0
        j = 0
        k = 0

        uBlank = b'\x20\x00'    # ASCII Blank
        uBlank2 = b'\xA0\x00'   # Unicode Blank
        uBlank3 = b'\x0B\x00'
        uNewline = b'\x0A\x00'  # Line Feed
        uTab = b'\x09\x00'      # Horizontal Tab
        uCR = b'\x0D\x00'       # Carriage Return
        uFilteredTextLen = tempLen
        while i < len(self.filteredText):
            if i == 0:
                k = 0
                while self.filteredText[0 : 2] == uBlank or self.filteredText[0 : 2] == uBlank2 or self.filteredText[0 : 2] == uNewline :
                    self.filteredText = self.filteredText[: k] + self.filteredText[k + 2 :]
                    uFilteredTextLen -= 1

                    if len(self.filteredText) <= 0:
                        break

            if len(self.filteredText) <= 0:
                break

            if self.filteredText[i : i + 2] == uNewline:
                j = i
                while True :
                    j += 2
                    if j >= len(self.filteredText):
                        break

                    if self.filteredText[j : j + 2] == uNewline or self.filteredText[j : j + 2] == uBlank or self.filteredText[j : j + 2] == uBlank2:
                        self.filteredText = self.filteredText[: j] + self.filteredText[j + 2:]
                        uFilteredTextLen -= 1
                        j -= 2
                    elif self.filteredText[j : j + 2] == uTab or self.filteredText[j : j + 2] == uBlank3 or self.filteredText[j : j + 2] == uCR :
                        self.filteredText = self.filteredText[: j] + self.filteredText[j + 2:]
                        uFilteredTextLen -= 1
                        j -= 2
                    else :
                        break


            elif self.filteredText[i : i + 2] == uBlank or self.filteredText[i : i + 2] == uBlank2:
                j = i
                while True :
                    j += 2
                    if j >= len(self.filteredText):
                        break

                    if self.filteredText[j: j + 2] == uBlank or self.filteredText[j : j + 2] == uBlank2:
                        self.filteredText = self.filteredText[: j] + self.filteredText[j + 2:]
                        uFilteredTextLen -= 1
                        j -= 2
                    elif self.filteredText[j: j + 2] == uTab:
                        self.filteredText = self.filteredText[: j] + self.filteredText[j + 2:]
                        uFilteredTextLen -= 1
                        j -= 2
                    elif self.filteredText[j: j + 2] == uBlank3:
                        self.filteredText = self.filteredText[: j] + self.filteredText[j + 2:]
                        uFilteredTextLen -= 1
                        j -= 2
                    else:
                        break

            elif self.filteredText[i : i + 2] == uBlank3:
                self.filteredText[i] = 0x20
                i -= 2
            elif self.filteredText[i : i + 2] == uCR:
                self.filteredText[i] = 0x0A
                i -= 2
            elif self.filteredText[i : i + 2] == uTab:
                self.filteredText[i] = 0x20
                i -= 2

            i += 2

        return uFilteredTextLen

    def __parse_ppt_normal__(self):
        # ppt 97????????????????

        self.powerpoint_document = bytearray(self.compound.fp.open('PowerPoint Document').read())
        self.current_user = bytearray(self.compound.fp.open('Current User').read())

        # Get User Edit Offset
        self.current_offset = struct.unpack('<I', self.current_user[16 : 20])[0]

        # Set Chain
        # Set User Edit Chain
        tmpHeader = {}
        tmpHeader['option'] = struct.unpack('<H', self.powerpoint_document[self.current_offset: self.current_offset + 2])[0]
        tmpHeader['type'] = self.powerpoint_document[self.current_offset + 2 : self.current_offset + 4]
        tmpHeader['length'] = struct.unpack('<I', self.powerpoint_document[self.current_offset + 4: self.current_offset + 8])[0]

        editblock = {}
        editblock['last_user_edit_atom_offset'] = 0
        editblock['persist_ptr_incremental_block_offset'] = 0

        if tmpHeader['type'] == self.RT_UserEditAtom:
            self.current_offset += 8
            self.current_offset += 8

            editblock['last_user_edit_atom_offset'] = struct.unpack('<I', self.powerpoint_document[self.current_offset : self.current_offset + 4])[0]
            self.current_offset += 4
            editblock['persist_ptr_incremental_block_offset']  = struct.unpack('<I', self.powerpoint_document[self.current_offset : self.current_offset + 4])[0]
            self.current_offset += 4
            self.arr_user_edit_block.append(editblock)

        while editblock['last_user_edit_atom_offset'] != 0:
            self.current_offset = editblock['last_user_edit_atom_offset']

            tmpHeader.fromkeys(tmpHeader.keys(), 0)
            editblock.fromkeys(editblock.keys(), 0)

            tmpHeader['option'] = struct.unpack('<H', self.powerpoint_document[self.current_offset: self.current_offset + 2])[0]
            tmpHeader['type'] = self.powerpoint_document[self.current_offset + 2: self.current_offset + 4]
            tmpHeader['length'] = struct.unpack('<I', self.powerpoint_document[self.current_offset + 4: self.current_offset + 8])[0]

            if tmpHeader['type'] == self.RT_UserEditAtom:
                self.current_offset += 8
                self.current_offset += 8

                editblock['last_user_edit_atom_offset'] = struct.unpack('<I', self.powerpoint_document[self.current_offset : self.current_offset + 4])[0]
                self.current_offset += 4
                editblock['persist_ptr_incremental_block_offset'] = struct.unpack('<I', self.powerpoint_document[self.current_offset : self.current_offset + 4])[0]
                self.current_offset += 4
                self.arr_user_edit_block.append(editblock)




        # SetPersistPtrIncrementalBlockChain
        tmpSheet = 0
        tmpLength = 0
        ppl_block = []

        for i in range(0, len(self.arr_user_edit_block)):
            self.current_offset = self.arr_user_edit_block[i]['persist_ptr_incremental_block_offset']

            tmpHeader.fromkeys(tmpHeader.keys(), 0)
            ppl_block.clear()


            tmpLength = 0

            tmpHeader['option'] = struct.unpack('<H', self.powerpoint_document[self.current_offset: self.current_offset + 2])[0]
            tmpHeader['type'] = self.powerpoint_document[self.current_offset + 2: self.current_offset + 4]
            tmpHeader['length'] = struct.unpack('<I', self.powerpoint_document[self.current_offset + 4: self.current_offset + 8])[0]

            if tmpHeader['type'] == self.RT_PersistPtrIncrementalAtom:
                self.current_offset += 8

                while True:
                    sheet_offset = {}
                    sheet_offset['count'] = 0
                    sheet_offset['startnum'] = 0
                    sheet_offset['object'] = b''
                    sheet_offset['slidenum'] = []
                    sheet_offset['slideid'] = []

                    sheet_offset.fromkeys(sheet_offset.keys(), 0)
                    tmpSheet = 0

                    tmpSheet = struct.unpack('<I', self.powerpoint_document[self.current_offset : self.current_offset + 4])[0]
                    self.current_offset += 4

                    sheet_offset['count'] = tmpSheet >> 20
                    sheet_offset['startnum'] = tmpSheet & 0x000FFFFF
                    sheet_offset['object'] = self.powerpoint_document[self.current_offset : self.current_offset + sheet_offset['count'] * 4]
                    self.current_offset += sheet_offset['count'] * 4

                    ppl_block.append(sheet_offset)

                    tmpLength += (sheet_offset['count'] + 1) * 4
                    if tmpHeader['length'] == tmpLength:
                        break

                self.arr_persist_ptr_incremental_block.append(ppl_block)

        ### Extract Body Text
        # arrSlideText에 각 slide의 text 저장
        arrSlideText = []
        for i in range(0, len(self.arr_persist_ptr_incremental_block)):
            self.current_offset = struct.unpack('<I', self.arr_persist_ptr_incremental_block[i][0]['object'][0:4])[0]

            tmpHeader.fromkeys(tmpHeader.keys(), 0)
            tmpHeader['option'] = struct.unpack('<H', self.powerpoint_document[self.current_offset: self.current_offset + 2])[0]
            tmpHeader['type'] = self.powerpoint_document[self.current_offset + 2: self.current_offset + 4]
            tmpHeader['length'] = struct.unpack('<I', self.powerpoint_document[self.current_offset + 4: self.current_offset + 8])[0]
            self.current_offset += 8

            if tmpHeader['type'] != self.RT_Document:
                #print("Not RT_Document.")
                return

            tmpHeader.fromkeys(tmpHeader.keys(), 0)
            tmpHeader['option'] = struct.unpack('<H', self.powerpoint_document[self.current_offset: self.current_offset + 2])[0]
            tmpHeader['type'] = self.powerpoint_document[self.current_offset + 2: self.current_offset + 4]
            tmpHeader['length'] = struct.unpack('<I', self.powerpoint_document[self.current_offset + 4: self.current_offset + 8])[0]
            self.current_offset += 8

            if tmpHeader['type'] != self.RT_SlideListWithText:
                while True:
                    self.current_offset += tmpHeader['length']

                    if self.current_offset > len(self.powerpoint_document):
                        #print("Error!")
                        return

                    tmpHeader.fromkeys(tmpHeader.keys(), 0)
                    tmpHeader['option'] = struct.unpack('<H', self.powerpoint_document[self.current_offset: self.current_offset + 2])[0]
                    tmpHeader['type'] = self.powerpoint_document[self.current_offset + 2: self.current_offset + 4]
                    tmpHeader['length'] = struct.unpack('<I', self.powerpoint_document[self.current_offset + 4: self.current_offset + 8])[0]
                    self.current_offset += 8

                    if tmpHeader['type'] == self.RT_SlideListWithText:
                        break

            slide_text = ""
            in_text = False
            sheet_number = 0
            slide_id = 0
            current_offset_backup = 0
            presize = 0
            editblock_text = []

            while tmpHeader['type'] != self.RT_EndDocument:
                if len(self.powerpoint_document) < self.current_offset + 8:
                    if len(self.text) > 0 :
                        editblock_text.append(self.text)
                        self.text = b''
                    else :
                        slide_text = ""
                    break

                tmpHeader.fromkeys(tmpHeader.keys(), 0)
                tmpHeader['option'] = struct.unpack('<H', self.powerpoint_document[self.current_offset: self.current_offset + 2])[0]
                tmpHeader['type'] = self.powerpoint_document[self.current_offset + 2: self.current_offset + 4]
                tmpHeader['length'] = struct.unpack('<I', self.powerpoint_document[self.current_offset + 4: self.current_offset + 8])[0]
                self.current_offset += 8

                if tmpHeader['type'] == self.RT_SlideListWithText:
                    pass
                elif tmpHeader['type'] == self.RT_SlidePersistAtom:
                    if in_text == True:
                        editblock_text.append(self.text)
                        self.text = b''

                        in_text = False

                        if len(self.powerpoint_document) >= self.current_offset + 16 :
                            sheet_number = struct.unpack('<I', self.powerpoint_document[self.current_offset : self.current_offset + 4])[0]
                            slide_id = struct.unpack('<I', self.powerpoint_document[self.current_offset + 12: self.current_offset + 16])[0]
                            current_offset_backup = self.current_offset
                            self.__extract_text_in_slide__(i, sheet_number, slide_id)
                            self.current_offset = current_offset_backup
                        if self.text == None :
                            pass
                        elif len(self.text) > 0:
                            in_text = True

                    else :
                        # 각 슬라이드 text 추출
                        if len(self.powerpoint_document) >= self.current_offset + 16 :
                            sheet_number = struct.unpack('<I', self.powerpoint_document[self.current_offset : self.current_offset + 4])[0]
                            slide_id = struct.unpack('<I', self.powerpoint_document[self.current_offset + 12: self.current_offset + 16])[0]
                            current_offset_backup = self.current_offset
                            self.__extract_text_in_slide__(i, sheet_number, slide_id)
                            self.current_offset = current_offset_backup
                        if self.text == None :
                            pass
                        elif len(self.text) > 0:
                            in_text = True

                    self.current_offset += tmpHeader['length']

                elif tmpHeader['type'] == self.RT_TextHeader:
                    self.current_offset += tmpHeader['length']

                elif tmpHeader['type'] == self.RT_TextBytesAtom:
                    self.text_bytes = b''
                    self.text_chars = b''
                    self.text_bytes = self.powerpoint_document[self.current_offset: self.current_offset + tmpHeader['length']]
                    for i in range(0, len(self.text_bytes)):
                        self.text_chars += bytes([self.text_bytes[i]])
                        self.text_chars += b'\x00'

                    if self.text == None:
                        self.text = b''

                    presize = len(self.text)
                    self.text += self.text_chars
                    self.text += b'\x0A\x00'

                    self.current_offset += tmpHeader['length']
                    in_text = True

                elif tmpHeader['type'] == self.RT_TextCharsAtom:
                    self.text_chars = b''
                    self.text_chars = self.powerpoint_document[self.current_offset : self.current_offset + tmpHeader['length']]

                    if self.text == None:
                        self.text = b''

                    self.text += self.text_chars
                    self.text += b'\x0A\x00'

                    self.current_offset += tmpHeader['length']
                    in_text = True

                elif tmpHeader['type'] == self.RT_EndDocument:
                    if in_text == True:
                        editblock_text.append(self.text)
                        in_text = False
                else :
                    self.current_offset += tmpHeader['length']

            if len(editblock_text) > 0:
                self.arr_edit_block_text.append(editblock_text)

        j = 0
        uFilteredTextLen = 0

        for i in range(0, 1):
            if len(self.arr_edit_block_text) > 0:
                for j in range(0, len(self.arr_edit_block_text[i])):
                    uTempLen = int(len(self.arr_edit_block_text[i][j]) / 2)
                    self.filteredText += self.arr_edit_block_text[i][j]
                    uFilteredTextLen += uTempLen

        uFilteredTextLen = self.__ppt_extra_filter__(uFilteredTextLen)
        """
        for i in range(0, len(self.filteredText), 2):
            try:
                self.compound.content += self.filteredText[i:i+2].decode('utf-16')
            except UnicodeDecodeError:
                continue
       """
        for i in range(0, len(self.filteredText), 2):
            try:
                self.compound.content += self.filteredText[i:i+2].decode('utf-16')
            except UnicodeDecodeError:
                continue
        #self.compound.content = self.filteredText.decode('utf-16')



        """
        #### Drawing
        try:
            drawing_data = bytearray(self.compound.fp.open('Pictures').read())
        except Exception:
            # not exist pictures
            return False

        drawing_offset = 0
        img_num = 0

        while drawing_offset < len(drawing_data):
            embedded_blip_rh_ver_instance = struct.unpack('<H', drawing_data[drawing_offset: drawing_offset + 2])[0]
            embedded_blip_rh_Type = struct.unpack('<H', drawing_data[drawing_offset + 2: drawing_offset + 4])[0]
            embedded_blip_rh_recLen = struct.unpack('<I', drawing_data[drawing_offset + 4: drawing_offset + 8])[0]
            drawing_offset += 0x08
            embedded_size = embedded_blip_rh_recLen


            embedded_blip_rgbUid1 = drawing_data[drawing_offset : drawing_offset + 0x10]
            drawing_offset += 0x10
            embedded_size -= 0x10
            embedded_blip_rgbUid2 = None
            if int(embedded_blip_rh_ver_instance / 0x10) == 0x46B or int(embedded_blip_rh_ver_instance / 0x10) == 0x6E3:
                embedded_blip_rgbUid2 = drawing_data[drawing_offset: drawing_offset + 0x10]
                drawing_offset += 0x10
                embedded_size -= 0x10

            if embedded_blip_rh_Type != 0xF01A and embedded_blip_rh_Type != 0xF01B and embedded_blip_rh_Type != 0xF01C and \
                    embedded_blip_rh_Type != 0xF01D and embedded_blip_rh_Type != 0xF01E and embedded_blip_rh_Type != 0xF01F and \
                    embedded_blip_rh_Type != 0xF029:
                break

            extension = ""
            if embedded_blip_rh_Type == 0xF01A:
                extension = ".emf"
                embedded_blip_metafileheader = drawing_data[drawing_offset: drawing_offset + 0x22]
                drawing_offset += 0x22
                embedded_size -= 0x22
            elif embedded_blip_rh_Type == 0xF01B:
                extension = ".wmf"
                embedded_blip_metafileheader = drawing_data[drawing_offset: drawing_offset + 0x22]
                drawing_offset += 0x22
                embedded_size -= 0x22
            elif embedded_blip_rh_Type == 0xF01C:
                extension = ".pict"
                embedded_blip_metafileheader = drawing_data[drawing_offset: drawing_offset + 0x22]
                drawing_offset += 0x22
                embedded_size -= 0x22
            elif embedded_blip_rh_Type == 0xF01D:
                extension = ".jpg"
                embedded_blip_tag = drawing_data[drawing_offset: drawing_offset + 0x01]
                drawing_offset += 0x01
                embedded_size -= 0x01
            elif embedded_blip_rh_Type == 0xF01E:
                extension = ".png"
                embedded_blip_tag = drawing_data[drawing_offset: drawing_offset + 0x01]
                drawing_offset += 0x01
                embedded_size -= 0x01
            elif embedded_blip_rh_Type == 0xF01F:
                extension = ".dib"
                embedded_blip_tag = drawing_data[drawing_offset: drawing_offset + 0x01]
                drawing_offset += 0x01
                embedded_size -= 0x01
            elif embedded_blip_rh_Type == 0xF029:
                extension = ".tiff"
                embedded_blip_tag = drawing_data[drawing_offset: drawing_offset + 0x01]
                drawing_offset += 0x01
                embedded_size -= 0x01

            embedded_data = drawing_data[drawing_offset : drawing_offset + embedded_size]
            drawing_offset += embedded_size

            if not (os.path.isdir(self.compound.tmp_path + self.compound.fileName + "_extracted")):
                os.makedirs(os.path.join(self.compound.tmp_path + self.compound.fileName + "_extracted"))

            self.compound.ole_path.append(
                self.compound.tmp_path + self.compound.fileName + "_extracted\\" + self.compound.fileName + "_" + str(img_num) + extension)

            embedded_fp = open(self.compound.tmp_path + self.compound.fileName + "_extracted\\" + self.compound.fileName + "_" + str(img_num) + extension, 'wb')
            img_num += 1
            embedded_fp.write(embedded_data)
            embedded_fp.close()

        ##### OLE Object
        counter = 0
        self.current_offset = 0
        file_list = []
        while(self.current_offset < len(self.powerpoint_document)):
            rh_ver_instance = struct.unpack('<H', self.powerpoint_document[self.current_offset: self.current_offset + 2])[0]
            rh_Type = struct.unpack('<H', self.powerpoint_document[self.current_offset + 2: self.current_offset + 4])[0]
            rh_recLen = struct.unpack('<I', self.powerpoint_document[self.current_offset + 4: self.current_offset + 8])[0]
            self.current_offset += 8

            if rh_Type == 0x1011:
                if not (os.path.isdir(self.compound.tmp_path + self.compound.fileName + "_extracted")):
                    os.makedirs(os.path.join(self.compound.tmp_path + self.compound.fileName + "_extracted"))

                path = self.compound.tmp_path + self.compound.fileName + "_extracted\\OLE_Object" + str(counter) + ".bin"
                self.compound.ole_path.append(path)
                outfile = open(path, "wb")
                counter += 1

                bindata: bytearray = bytearray(self.powerpoint_document[self.current_offset + 6 : self.current_offset + rh_recLen - 8])
                decompress = zlib.decompressobj(-zlib.MAX_WBITS)
                stream = bytearray()

                try:
                    stream = decompress.decompress(bindata)
                    stream += decompress.flush()
                except Exception:
                    pass
                file_list.append(path)
                outfile.write(stream)
                outfile.close()

            self.current_offset += (rh_recLen)  # - Header Size

        self.__getOLEFile__(file_list)
        """

    def __getOLEFile__(self, files):
        for file in files:
            try:
                ole = CompoundFileReader(file)
                ole_filename = file[file.rfind('\\') + 1:]
                for entry in ole.root:
                    if entry.name == 'Package':  # ooxml
                        bindata: bytearray = bytearray(ole.open('Package').read())
                        f = open(ole_filename + '.zip', mode='wb')
                        f.write(bindata)
                        f.close()
                        with zipfile.ZipFile(ole_filename + '.zip') as z:
                            for filename in z.namelist():
                                if filename == 'word/document.xml':
                                    savefilename = ole_filename + '.docx'
                                    break
                                elif filename == 'ppt/presentation.xml':
                                    savefilename = ole_filename + '.pptx'
                                    break
                                elif filename == 'xl/workbook.xml':
                                    savefilename = ole_filename + '.xlsx'
                                    break

                        if not (os.path.isdir(self.compound.tmp_path + self.compound.fileName + "_extracted")):
                            os.makedirs(os.path.join(self.compound.tmp_path + self.compound.fileName + "_extracted"))

                        self.compound.ole_path.append(
                            self.compound.tmp_path + self.compound.fileName + "_extracted\\" + savefilename)
                        f = open(self.compound.tmp_path + self.compound.fileName + "_extracted\\" + savefilename, mode='wb')
                        f.write(bindata)
                        f.close()
                        os.remove(ole_filename + '.zip')

                    elif entry.name == 'WordDocument':
                        if not (os.path.isdir(self.compound.tmp_path + self.compound.fileName + "_extracted")):
                            os.makedirs(os.path.join(self.compound.tmp_path + self.compound.fileName + "_extracted"))

                        self.compound.ole_path.append(file + '.doc')

                        shutil.copy(file, file + '.doc')
                    elif entry.name == 'PowerPoint Document':
                        if not (os.path.isdir(self.compound.tmp_path + self.compound.fileName + "_extracted")):
                            os.makedirs(os.path.join(self.compound.tmp_path + self.compound.fileName + "_extracted"))

                        self.compound.ole_path.append(file + '.ppt')

                        shutil.copy(file, file + '.ppt')
                    elif entry.name == 'Workbook':
                        if not (os.path.isdir(self.compound.tmp_path + self.compound.fileName + "_extracted")):
                            os.makedirs(os.path.join(self.compound.tmp_path + self.compound.fileName + "_extracted"))

                        self.compound.ole_path.append(file + '.xls')

                        shutil.copy(file, file + '.xls')
                    elif entry.name == 'CONTENTS':
                        bindata: bytearray = bytearray(ole.open('CONTENTS').read())
                        if not (os.path.isdir(self.compound.tmp_path + self.compound.fileName + "_extracted")):
                            os.makedirs(os.path.join(self.compound.tmp_path + self.compound.fileName + "_extracted"))

                        self.compound.ole_path.append(
                            self.compound.tmp_path + self.compound.fileName + "_extracted\\" + ole_filename + '.pdf')

                        f = open(self.compound.tmp_path + self.compound.fileName + "_extracted\\" + ole_filename + '.pdf', mode='wb')
                        f.write(bindata)
                        f.close()
                    elif entry.name == 'Ole10Native':
                        if not (os.path.isdir(self.compound.tmp_path + self.compound.fileName + "_extracted")):
                            os.makedirs(os.path.join(self.compound.tmp_path + self.compound.fileName + "_extracted"))

                        bindata: bytearray = bytearray(ole.open('Ole10Native').read())
                        name_len = 6
                        for i in bindata[name_len:]:
                            if i == 0:
                                break
                            name_len += 1
                        cnt = 0
                        while cnt < 1000:
                            if bindata[cnt:cnt + 4] == b'RIFF' and bindata[cnt + 8: cnt + 16] == b'AVI\x20LIST':
                                self.compound.ole_path.append(self.compound.tmp_path + self.compound.fileName + "_extracted\\" + ole_filename + '.avi')
                                f = open(self.compound.tmp_path + self.compound.fileName + "_extracted\\" + ole_filename + '.avi', mode='wb')
                                f.write(bindata[cnt:])
                                f.close()
                                break
                            if bindata[cnt:cnt + 4] == b'RIFF' and bindata[cnt + 8 : cnt + 16] == b'WAVEfmt\x20':
                                self.compound.ole_path.append(self.compound.tmp_path + self.compound.fileName + "_extracted\\" + ole_filename + '.wav')
                                f = open(self.compound.tmp_path + self.compound.fileName + "_extracted\\" + ole_filename + '.wav', mode='wb')
                                f.write(bindata[cnt:])
                                f.close()
                                break
                            if bindata[cnt:cnt + 2] == b'\x00\x00' and bindata[cnt + 4: cnt + 8] == b'ftyp':
                                self.compound.ole_path.append(self.compound.tmp_path + self.compound.fileName + "_extracted\\" + ole_filename + '.mp4')
                                f = open(self.compound.tmp_path + self.compound.fileName + "_extracted\\" + ole_filename + '.mp4', mode='wb')
                                f.write(bindata[cnt:])
                                f.close()
                                break
                            cnt += 1
                    elif entry.name == 'BodyText':
                        if not (os.path.isdir(self.compound.tmp_path + self.compound.fileName + "_extracted")):
                            os.makedirs(os.path.join(self.compound.tmp_path + self.compound.fileName + "_extracted"))

                        self.compound.ole_path.append(file + '.hwp')

                        shutil.copy(file, file + '.hwp')

                    else:
                        continue
            except:
                return False


    def __parse_ppt_normal_for_ole__(self, powerpoint_document, current_user):
        # ppt 97????????????????

        self.powerpoint_document = powerpoint_document
        self.current_user = current_user

        # Get User Edit Offset
        self.current_offset = struct.unpack('<I', self.current_user[16 : 20])[0]

        # Set Chain
        # Set User Edit Chain
        tmpHeader = {}
        tmpHeader['option'] = struct.unpack('<H', self.powerpoint_document[self.current_offset: self.current_offset + 2])[0]
        tmpHeader['type'] = self.powerpoint_document[self.current_offset + 2 : self.current_offset + 4]
        tmpHeader['length'] = struct.unpack('<I', self.powerpoint_document[self.current_offset + 4: self.current_offset + 8])[0]

        editblock = {}
        editblock['last_user_edit_atom_offset'] = 0
        editblock['persist_ptr_incremental_block_offset'] = 0

        if tmpHeader['type'] == self.RT_UserEditAtom:
            self.current_offset += 8
            self.current_offset += 8

            editblock['last_user_edit_atom_offset'] = struct.unpack('<I', self.powerpoint_document[self.current_offset : self.current_offset + 4])[0]
            self.current_offset += 4
            editblock['persist_ptr_incremental_block_offset']  = struct.unpack('<I', self.powerpoint_document[self.current_offset : self.current_offset + 4])[0]
            self.current_offset += 4
            self.arr_user_edit_block.append(editblock)

        while editblock['last_user_edit_atom_offset'] != 0:
            self.current_offset = editblock['last_user_edit_atom_offset']

            tmpHeader.fromkeys(tmpHeader.keys(), 0)
            editblock.fromkeys(editblock.keys(), 0)

            tmpHeader['option'] = struct.unpack('<H', self.powerpoint_document[self.current_offset: self.current_offset + 2])[0]
            tmpHeader['type'] = self.powerpoint_document[self.current_offset + 2: self.current_offset + 4]
            tmpHeader['length'] = struct.unpack('<I', self.powerpoint_document[self.current_offset + 4: self.current_offset + 8])[0]

            if tmpHeader['type'] == self.RT_UserEditAtom:
                self.current_offset += 8
                self.current_offset += 8

                editblock['last_user_edit_atom_offset'] = struct.unpack('<I', self.powerpoint_document[self.current_offset : self.current_offset + 4])[0]
                self.current_offset += 4
                editblock['persist_ptr_incremental_block_offset'] = struct.unpack('<I', self.powerpoint_document[self.current_offset : self.current_offset + 4])[0]
                self.current_offset += 4
                self.arr_user_edit_block.append(editblock)




        # SetPersistPtrIncrementalBlockChain
        tmpSheet = 0
        tmpLength = 0
        ppl_block = []

        for i in range(0, len(self.arr_user_edit_block)):
            self.current_offset = self.arr_user_edit_block[i]['persist_ptr_incremental_block_offset']

            tmpHeader.fromkeys(tmpHeader.keys(), 0)
            ppl_block.clear()


            tmpLength = 0

            tmpHeader['option'] = struct.unpack('<H', self.powerpoint_document[self.current_offset: self.current_offset + 2])[0]
            tmpHeader['type'] = self.powerpoint_document[self.current_offset + 2: self.current_offset + 4]
            tmpHeader['length'] = struct.unpack('<I', self.powerpoint_document[self.current_offset + 4: self.current_offset + 8])[0]

            if tmpHeader['type'] == self.RT_PersistPtrIncrementalAtom:
                self.current_offset += 8

                while True:
                    sheet_offset = {}
                    sheet_offset['count'] = 0
                    sheet_offset['startnum'] = 0
                    sheet_offset['object'] = b''
                    sheet_offset['slidenum'] = []
                    sheet_offset['slideid'] = []

                    sheet_offset.fromkeys(sheet_offset.keys(), 0)
                    tmpSheet = 0

                    tmpSheet = struct.unpack('<I', self.powerpoint_document[self.current_offset : self.current_offset + 4])[0]
                    self.current_offset += 4

                    sheet_offset['count'] = tmpSheet >> 20
                    sheet_offset['startnum'] = tmpSheet & 0x000FFFFF
                    sheet_offset['object'] = self.powerpoint_document[self.current_offset : self.current_offset + sheet_offset['count'] * 4]
                    self.current_offset += sheet_offset['count'] * 4

                    ppl_block.append(sheet_offset)

                    tmpLength += (sheet_offset['count'] + 1) * 4
                    if tmpHeader['length'] == tmpLength:
                        break

                self.arr_persist_ptr_incremental_block.append(ppl_block)

        ### Extract Body Text
        # arrSlideText에 각 slide의 text 저장
        arrSlideText = []
        for i in range(0, len(self.arr_persist_ptr_incremental_block)):
            self.current_offset = struct.unpack('<I', self.arr_persist_ptr_incremental_block[i][0]['object'][0:4])[0]

            tmpHeader.fromkeys(tmpHeader.keys(), 0)
            tmpHeader['option'] = struct.unpack('<H', self.powerpoint_document[self.current_offset: self.current_offset + 2])[0]
            tmpHeader['type'] = self.powerpoint_document[self.current_offset + 2: self.current_offset + 4]
            tmpHeader['length'] = struct.unpack('<I', self.powerpoint_document[self.current_offset + 4: self.current_offset + 8])[0]
            self.current_offset += 8

            if tmpHeader['type'] != self.RT_Document:
                #print("Not RT_Document.")
                return

            tmpHeader.fromkeys(tmpHeader.keys(), 0)
            tmpHeader['option'] = struct.unpack('<H', self.powerpoint_document[self.current_offset: self.current_offset + 2])[0]
            tmpHeader['type'] = self.powerpoint_document[self.current_offset + 2: self.current_offset + 4]
            tmpHeader['length'] = struct.unpack('<I', self.powerpoint_document[self.current_offset + 4: self.current_offset + 8])[0]
            self.current_offset += 8

            if tmpHeader['type'] != self.RT_SlideListWithText:
                while True:
                    self.current_offset += tmpHeader['length']

                    if self.current_offset > len(self.powerpoint_document):
                        #print("Error!")
                        return

                    tmpHeader.fromkeys(tmpHeader.keys(), 0)
                    tmpHeader['option'] = struct.unpack('<H', self.powerpoint_document[self.current_offset: self.current_offset + 2])[0]
                    tmpHeader['type'] = self.powerpoint_document[self.current_offset + 2: self.current_offset + 4]
                    tmpHeader['length'] = struct.unpack('<I', self.powerpoint_document[self.current_offset + 4: self.current_offset + 8])[0]
                    self.current_offset += 8

                    if tmpHeader['type'] == self.RT_SlideListWithText:
                        break

            slide_text = ""
            in_text = False
            sheet_number = 0
            slide_id = 0
            current_offset_backup = 0
            presize = 0
            editblock_text = []

            while tmpHeader['type'] != self.RT_EndDocument:
                if len(self.powerpoint_document) < self.current_offset + 8:
                    if len(self.text) > 0 :
                        editblock_text.append(self.text)
                        self.text = b''
                    else :
                        slide_text = ""
                    break

                tmpHeader.fromkeys(tmpHeader.keys(), 0)
                tmpHeader['option'] = struct.unpack('<H', self.powerpoint_document[self.current_offset: self.current_offset + 2])[0]
                tmpHeader['type'] = self.powerpoint_document[self.current_offset + 2: self.current_offset + 4]
                tmpHeader['length'] = struct.unpack('<I', self.powerpoint_document[self.current_offset + 4: self.current_offset + 8])[0]
                self.current_offset += 8

                if tmpHeader['type'] == self.RT_SlideListWithText:
                    pass
                elif tmpHeader['type'] == self.RT_SlidePersistAtom:
                    if in_text == True:
                        editblock_text.append(self.text)
                        self.text = b''

                        in_text = False

                        if len(self.powerpoint_document) >= self.current_offset + 16 :
                            sheet_number = struct.unpack('<I', self.powerpoint_document[self.current_offset : self.current_offset + 4])[0]
                            slide_id = struct.unpack('<I', self.powerpoint_document[self.current_offset + 12: self.current_offset + 16])[0]
                            current_offset_backup = self.current_offset
                            self.__extract_text_in_slide__(i, sheet_number, slide_id)
                            self.current_offset = current_offset_backup
                        if self.text == None :
                            pass
                        elif len(self.text) > 0:
                            in_text = True

                    else :
                        # 각 슬라이드 text 추출
                        if len(self.powerpoint_document) >= self.current_offset + 16 :
                            sheet_number = struct.unpack('<I', self.powerpoint_document[self.current_offset : self.current_offset + 4])[0]
                            slide_id = struct.unpack('<I', self.powerpoint_document[self.current_offset + 12: self.current_offset + 16])[0]
                            current_offset_backup = self.current_offset
                            self.__extract_text_in_slide__(i, sheet_number, slide_id)
                            self.current_offset = current_offset_backup
                        if self.text == None :
                            pass
                        elif len(self.text) > 0:
                            in_text = True

                    self.current_offset += tmpHeader['length']

                elif tmpHeader['type'] == self.RT_TextHeader:
                    self.current_offset += tmpHeader['length']

                elif tmpHeader['type'] == self.RT_TextBytesAtom:
                    self.text_bytes = b''
                    self.text_chars = b''
                    self.text_bytes = self.powerpoint_document[self.current_offset: self.current_offset + tmpHeader['length']]
                    for i in range(0, len(self.text_bytes)):
                        self.text_chars += bytes([self.text_bytes[i]])
                        self.text_chars += b'\x00'

                    if self.text == None:
                        self.text = b''

                    presize = len(self.text)
                    self.text += self.text_chars
                    self.text += b'\x0A\x00'

                    self.current_offset += tmpHeader['length']
                    in_text = True

                elif tmpHeader['type'] == self.RT_TextCharsAtom:
                    self.text_chars = b''
                    self.text_chars = self.powerpoint_document[self.current_offset : self.current_offset + tmpHeader['length']]

                    if self.text == None:
                        self.text = b''

                    self.text += self.text_chars
                    self.text += b'\x0A\x00'

                    self.current_offset += tmpHeader['length']
                    in_text = True

                elif tmpHeader['type'] == self.RT_EndDocument:
                    if in_text == True:
                        editblock_text.append(self.text)
                        in_text = False
                else :
                    self.current_offset += tmpHeader['length']

            if len(editblock_text) > 0:
                self.arr_edit_block_text.append(editblock_text)

        j = 0
        uFilteredTextLen = 0

        for i in range(0, 1):
            if len(self.arr_edit_block_text) > 0:
                for j in range(0, len(self.arr_edit_block_text[i])):
                    uTempLen = int(len(self.arr_edit_block_text[i][j]) / 2)
                    self.filteredText += self.arr_edit_block_text[i][j]
                    uFilteredTextLen += uTempLen

        uFilteredTextLen = self.__ppt_extra_filter__(uFilteredTextLen)
        """
        for i in range(0, len(self.filteredText), 2):
            try:
                self.compound.content += self.filteredText[i:i+2].decode('utf-16')
            except UnicodeDecodeError:
                continue
        """
        result = ""
        for i in range(0, len(self.filteredText), 2):
            try:
                result += self.filteredText[i:i+2].decode('utf-16')
            except UnicodeDecodeError:
                continue
        #self.compound.content = self.filteredText.decode('utf-16')

        return result


    def __parse_ppt_damaged__(self):
        file = bytearray(self.compound.fp.read())
        m_root = b''
        m_pictures = b''
        m_currentuser = b''
        m_powerpointdocumentation = b''
        isRootDir = False
        isPictures = False
        isCurrentUser = False
        isPowerPointDocumentation = False



        CONST_DIR_ENTRY_NAME_ROOT = b'\x52\x00\x6F\x00\x6F\x00\x74\x00\x20\x00\x45\x00\x6E\x00\x74\x00\x72\x00\x79\x00\x00\x00'
        CONST_DIR_ENTRY_NAME_POWER_POINT_DOCUMENT = b'\x50\x00\x6F\x00\x77\x00\x65\x00\x72\x00\x50\x00\x6F\x00\x69\x00\x6E\x00\x74\x00\x20\x00\x44\x00\x6F\x00\x63\x00\x75\x00\x6D\x00\x65\x00\x6E\x00\x74\x00\x00\x00'
        CONST_DIR_ENTRY_NAME_PICTURES = b'\x50\x00\x69\x00\x63\x00\x74\x00\x75\x00\x72\x00\x65\x00\x73\x00\x00\x00'
        CONST_CURRENT_USER = b'\x00\x00\xF6\x0F'

        self.current_offset = 0

        while (self.current_offset < len(file)):
            if (file[self.current_offset : self.current_offset + len(CONST_DIR_ENTRY_NAME_ROOT)] == CONST_DIR_ENTRY_NAME_ROOT):
                m_root = file[self.current_offset: self.current_offset + 0x80]
                isRootDir = True

            if (file[self.current_offset : self.current_offset + len(CONST_DIR_ENTRY_NAME_POWER_POINT_DOCUMENT)] == CONST_DIR_ENTRY_NAME_POWER_POINT_DOCUMENT):
                m_powerpointdocumentation = file[self.current_offset: self.current_offset + 0x80]
                isPowerPointDocumentation = True

            if (file[self.current_offset : self.current_offset + len(CONST_DIR_ENTRY_NAME_PICTURES)] == CONST_DIR_ENTRY_NAME_PICTURES):
                m_pictures = file[self.current_offset: self.current_offset + 0x80]
                isPictures = True

            self.current_offset += 0x80

        self.current_offset = 0

        while (self.current_offset < len(file)):
            if (file[self.current_offset : self.current_offset + 4] == CONST_CURRENT_USER):
                isCurrentUser = True
                break
            self.current_offset += 0x40

        if isCurrentUser == False or isPowerPointDocumentation == False:
            return self.compound.CONST_ERROR

        self.current_user = file[self.current_offset : self.current_offset + 64]
        powerpoint_document_start = (struct.unpack('<I', m_powerpointdocumentation[0x74 : 0x78])[0] + 1) * 0x200
        powerpoint_document_size = struct.unpack('<I', m_powerpointdocumentation[0x78 : 0x7C])[0]
        self.powerpoint_document = file[powerpoint_document_start : powerpoint_document_start + powerpoint_document_size]

        try:  # 임시 처리
            pictures_start = (struct.unpack('<I', m_pictures[0x74 : 0x78])[0] + 1) * 0x200
            pictures_size = struct.unpack('<I', m_pictures[0x78 : 0x7C])[0]
            drawing_data = file[pictures_start: pictures_start + pictures_size]
        except struct.error:
            return self.compound.CONST_ERROR



        # Get User Edit Offset
        self.current_offset = struct.unpack('<I', self.current_user[16 : 20])[0]

        # Set Chain
        # Set User Edit Chain
        tmpHeader = {}
        tmpHeader['option'] = struct.unpack('<H', self.powerpoint_document[self.current_offset: self.current_offset + 2])[0]
        tmpHeader['type'] = self.powerpoint_document[self.current_offset + 2 : self.current_offset + 4]
        tmpHeader['length'] = struct.unpack('<I', self.powerpoint_document[self.current_offset + 4: self.current_offset + 8])[0]

        editblock = {}
        editblock['last_user_edit_atom_offset'] = 0
        editblock['persist_ptr_incremental_block_offset'] = 0

        if tmpHeader['type'] == self.RT_UserEditAtom:
            self.current_offset += 8
            self.current_offset += 8

            editblock['last_user_edit_atom_offset'] = struct.unpack('<I', self.powerpoint_document[self.current_offset : self.current_offset + 4])[0]
            self.current_offset += 4
            editblock['persist_ptr_incremental_block_offset']  = struct.unpack('<I', self.powerpoint_document[self.current_offset : self.current_offset + 4])[0]
            self.current_offset += 4
            self.arr_user_edit_block.append(editblock)

        while editblock['last_user_edit_atom_offset'] != 0:
            self.current_offset = editblock['last_user_edit_atom_offset']

            tmpHeader.fromkeys(tmpHeader.keys(), 0)
            editblock.fromkeys(editblock.keys(), 0)

            tmpHeader['option'] = struct.unpack('<H', self.powerpoint_document[self.current_offset: self.current_offset + 2])[0]
            tmpHeader['type'] = self.powerpoint_document[self.current_offset + 2: self.current_offset + 4]
            tmpHeader['length'] = struct.unpack('<I', self.powerpoint_document[self.current_offset + 4: self.current_offset + 8])[0]

            if tmpHeader['type'] == self.RT_UserEditAtom:
                self.current_offset += 8
                self.current_offset += 8

                editblock['last_user_edit_atom_offset'] = struct.unpack('<I', self.powerpoint_document[self.current_offset : self.current_offset + 4])[0]
                self.current_offset += 4
                editblock['persist_ptr_incremental_block_offset'] = struct.unpack('<I', self.powerpoint_document[self.current_offset : self.current_offset + 4])[0]
                self.current_offset += 4
                self.arr_user_edit_block.append(editblock)

        # SetPersistPtrIncrementalBlockChain
        tmpSheet = 0
        tmpLength = 0
        ppl_block = []

        for i in range(0, len(self.arr_user_edit_block)):
            self.current_offset = self.arr_user_edit_block[i]['persist_ptr_incremental_block_offset']

            tmpHeader.fromkeys(tmpHeader.keys(), 0)
            ppl_block.clear()

            tmpLength = 0

            tmpHeader['option'] = \
            struct.unpack('<H', self.powerpoint_document[self.current_offset: self.current_offset + 2])[0]
            tmpHeader['type'] = self.powerpoint_document[self.current_offset + 2: self.current_offset + 4]
            tmpHeader['length'] = \
            struct.unpack('<I', self.powerpoint_document[self.current_offset + 4: self.current_offset + 8])[0]

            if tmpHeader['type'] == self.RT_PersistPtrIncrementalAtom:
                self.current_offset += 8

                while True:
                    sheet_offset = {}
                    sheet_offset['count'] = 0
                    sheet_offset['startnum'] = 0
                    sheet_offset['object'] = b''
                    sheet_offset['slidenum'] = []
                    sheet_offset['slideid'] = []

                    sheet_offset.fromkeys(sheet_offset.keys(), 0)
                    tmpSheet = 0

                    tmpSheet = \
                    struct.unpack('<I', self.powerpoint_document[self.current_offset: self.current_offset + 4])[0]
                    self.current_offset += 4

                    sheet_offset['count'] = tmpSheet >> 20
                    sheet_offset['startnum'] = tmpSheet & 0x000FFFFF
                    sheet_offset['object'] = self.powerpoint_document[
                                             self.current_offset: self.current_offset + sheet_offset['count'] * 4]
                    self.current_offset += sheet_offset['count'] * 4

                    ppl_block.append(sheet_offset)

                    tmpLength += (sheet_offset['count'] + 1) * 4
                    if tmpHeader['length'] == tmpLength:
                        break

                self.arr_persist_ptr_incremental_block.append(ppl_block)

        ### Extract Body Text
        # arrSlideText에 각 slide의 text 저장
        arrSlideText = []
        for i in range(0, len(self.arr_persist_ptr_incremental_block)):
            self.current_offset = struct.unpack('<I', self.arr_persist_ptr_incremental_block[i][0]['object'][0:4])[0]

            tmpHeader.fromkeys(tmpHeader.keys(), 0)
            tmpHeader['option'] = struct.unpack('<H', self.powerpoint_document[self.current_offset: self.current_offset + 2])[0]
            tmpHeader['type'] = self.powerpoint_document[self.current_offset + 2: self.current_offset + 4]
            tmpHeader['length'] = struct.unpack('<I', self.powerpoint_document[self.current_offset + 4: self.current_offset + 8])[0]
            self.current_offset += 8

            if tmpHeader['type'] != self.RT_Document:
                #print("Not RT_Document.")
                return

            tmpHeader.fromkeys(tmpHeader.keys(), 0)
            tmpHeader['option'] = struct.unpack('<H', self.powerpoint_document[self.current_offset: self.current_offset + 2])[0]
            tmpHeader['type'] = self.powerpoint_document[self.current_offset + 2: self.current_offset + 4]
            tmpHeader['length'] = struct.unpack('<I', self.powerpoint_document[self.current_offset + 4: self.current_offset + 8])[0]
            self.current_offset += 8

            if tmpHeader['type'] != self.RT_SlideListWithText:
                while True:
                    self.current_offset += tmpHeader['length']

                    if self.current_offset > len(self.powerpoint_document):
                        #print("Error!")
                        return

                    tmpHeader.fromkeys(tmpHeader.keys(), 0)
                    tmpHeader['option'] = struct.unpack('<H', self.powerpoint_document[self.current_offset: self.current_offset + 2])[0]
                    tmpHeader['type'] = self.powerpoint_document[self.current_offset + 2: self.current_offset + 4]
                    tmpHeader['length'] = struct.unpack('<I', self.powerpoint_document[self.current_offset + 4: self.current_offset + 8])[0]
                    self.current_offset += 8

                    if tmpHeader['type'] == self.RT_SlideListWithText:
                        break

            slide_text = ""
            in_text = False
            sheet_number = 0
            slide_id = 0
            current_offset_backup = 0
            presize = 0
            editblock_text = []

            while tmpHeader['type'] != self.RT_EndDocument:
                if len(self.powerpoint_document) < self.current_offset + 8:
                    if len(self.text) > 0 :
                        editblock_text.append(self.text)
                        self.text = b''
                    else :
                        slide_text = ""
                    break

                tmpHeader.fromkeys(tmpHeader.keys(), 0)
                tmpHeader['option'] = struct.unpack('<H', self.powerpoint_document[self.current_offset: self.current_offset + 2])[0]
                tmpHeader['type'] = self.powerpoint_document[self.current_offset + 2: self.current_offset + 4]
                tmpHeader['length'] = struct.unpack('<I', self.powerpoint_document[self.current_offset + 4: self.current_offset + 8])[0]
                self.current_offset += 8

                if tmpHeader['type'] == self.RT_SlideListWithText:
                    pass
                elif tmpHeader['type'] == self.RT_SlidePersistAtom:
                    if in_text == True:
                        editblock_text.append(self.text)
                        self.text = b''

                        in_text = False

                        if len(self.powerpoint_document) >= self.current_offset + 16 :
                            sheet_number = struct.unpack('<I', self.powerpoint_document[self.current_offset : self.current_offset + 4])[0]
                            slide_id = struct.unpack('<I', self.powerpoint_document[self.current_offset + 12: self.current_offset + 16])[0]
                            current_offset_backup = self.current_offset
                            self.__extract_text_in_slide__(i, sheet_number, slide_id)
                            self.current_offset = current_offset_backup
                        if self.text == None :
                            pass
                        elif len(self.text) > 0:
                            in_text = True

                    else :
                        # 각 슬라이드 text 추출
                        if len(self.powerpoint_document) >= self.current_offset + 16 :
                            sheet_number = struct.unpack('<I', self.powerpoint_document[self.current_offset : self.current_offset + 4])[0]
                            slide_id = struct.unpack('<I', self.powerpoint_document[self.current_offset + 12: self.current_offset + 16])[0]
                            current_offset_backup = self.current_offset
                            self.__extract_text_in_slide__(i, sheet_number, slide_id)
                            self.current_offset = current_offset_backup
                        if self.text == None :
                            pass
                        elif len(self.text) > 0:
                            in_text = True

                    self.current_offset += tmpHeader['length']

                elif tmpHeader['type'] == self.RT_TextHeader:
                    self.current_offset += tmpHeader['length']

                elif tmpHeader['type'] == self.RT_TextBytesAtom:
                    self.text_bytes = b''
                    self.text_chars = b''
                    self.text_bytes = self.powerpoint_document[self.current_offset: self.current_offset + tmpHeader['length']]
                    for i in range(0, len(self.text_bytes)):
                        self.text_chars += bytes([self.text_bytes[i]])
                        self.text_chars += b'\x00'

                    if self.text == None:
                        self.text = b''

                    presize = len(self.text)
                    self.text += self.text_chars
                    self.text += b'\x0A\x00'

                    self.current_offset += tmpHeader['length']
                    in_text = True

                elif tmpHeader['type'] == self.RT_TextCharsAtom:
                    self.text_chars = b''
                    self.text_chars = self.powerpoint_document[self.current_offset : self.current_offset + tmpHeader['length']]

                    if self.text == None:
                        self.text = b''

                    self.text += self.text_chars
                    self.text += b'\x0A\x00'

                    self.current_offset += tmpHeader['length']
                    in_text = True

                elif tmpHeader['type'] == self.RT_EndDocument:
                    if in_text == True:
                        editblock_text.append(self.text)
                        in_text = False
                else :
                    self.current_offset += tmpHeader['length']

            if len(editblock_text) > 0:
                self.arr_edit_block_text.append(editblock_text)

        j = 0
        uFilteredTextLen = 0

        for i in range(0, 1):
            if len(self.arr_edit_block_text) > 0:
                for j in range(0, len(self.arr_edit_block_text[i])):
                    uTempLen = int(len(self.arr_edit_block_text[i][j]) / 2)
                    self.filteredText += self.arr_edit_block_text[i][j]
                    uFilteredTextLen += uTempLen

        uFilteredTextLen = self.__ppt_extra_filter__(uFilteredTextLen)

        for i in range(0, len(self.filteredText), 2):
            try:
                self.compound.content += self.filteredText[i:i+2].decode('utf-16')
            except UnicodeDecodeError:
                continue

        #self.compound.content = self.filteredText.decode('utf-16')

        """
        #### Drawing

        drawing_offset = 0
        img_num = 0

        while drawing_offset < len(drawing_data):
            embedded_blip_rh_ver_instance = \
            struct.unpack('<H', drawing_data[drawing_offset: drawing_offset + 2])[0]
            embedded_blip_rh_Type = struct.unpack('<H', drawing_data[drawing_offset + 2: drawing_offset + 4])[0]
            embedded_blip_rh_recLen = struct.unpack('<I', drawing_data[drawing_offset + 4: drawing_offset + 8])[
                0]
            drawing_offset += 0x08
            embedded_size = embedded_blip_rh_recLen

            embedded_blip_rgbUid1 = drawing_data[drawing_offset: drawing_offset + 0x10]
            drawing_offset += 0x10
            embedded_size -= 0x10
            embedded_blip_rgbUid2 = None
            if int(embedded_blip_rh_ver_instance / 0x10) == 0x46B or int(
                    embedded_blip_rh_ver_instance / 0x10) == 0x6E3:
                embedded_blip_rgbUid2 = drawing_data[drawing_offset: drawing_offset + 0x10]
                drawing_offset += 0x10
                embedded_size -= 0x10

            if embedded_blip_rh_Type != 0xF01A and embedded_blip_rh_Type != 0xF01B and embedded_blip_rh_Type != 0xF01C and \
                    embedded_blip_rh_Type != 0xF01D and embedded_blip_rh_Type != 0xF01E and embedded_blip_rh_Type != 0xF01F and \
                    embedded_blip_rh_Type != 0xF029:
                break

            extension = ""
            if embedded_blip_rh_Type == 0xF01A:
                extension = ".emf"
                embedded_blip_metafileheader = drawing_data[drawing_offset: drawing_offset + 0x22]
                drawing_offset += 0x22
                embedded_size -= 0x22
            elif embedded_blip_rh_Type == 0xF01B:
                extension = ".wmf"
                embedded_blip_metafileheader = drawing_data[drawing_offset: drawing_offset + 0x22]
                drawing_offset += 0x22
                embedded_size -= 0x22
            elif embedded_blip_rh_Type == 0xF01C:
                extension = ".pict"
                embedded_blip_metafileheader = drawing_data[drawing_offset: drawing_offset + 0x22]
                drawing_offset += 0x22
                embedded_size -= 0x22
            elif embedded_blip_rh_Type == 0xF01D:
                extension = ".jpg"
                embedded_blip_tag = drawing_data[drawing_offset: drawing_offset + 0x01]
                drawing_offset += 0x01
                embedded_size -= 0x01
            elif embedded_blip_rh_Type == 0xF01E:
                extension = ".png"
                embedded_blip_tag = drawing_data[drawing_offset: drawing_offset + 0x01]
                drawing_offset += 0x01
                embedded_size -= 0x01
            elif embedded_blip_rh_Type == 0xF01F:
                extension = ".dib"
                embedded_blip_tag = drawing_data[drawing_offset: drawing_offset + 0x01]
                drawing_offset += 0x01
                embedded_size -= 0x01
            elif embedded_blip_rh_Type == 0xF029:
                extension = ".tiff"
                embedded_blip_tag = drawing_data[drawing_offset: drawing_offset + 0x01]
                drawing_offset += 0x01
                embedded_size -= 0x01

            embedded_data = drawing_data[drawing_offset: drawing_offset + embedded_size]
            drawing_offset += embedded_size

            if not (os.path.isdir(self.compound.tmp_path + self.compound.fileName + "_extracted")):
                os.makedirs(os.path.join(self.compound.tmp_path + self.compound.fileName + "_extracted"))

            self.compound.ole_path.append(
                self.compound.tmp_path + self.compound.fileName + "_extracted\\" + self.compound.fileName + "_" + str(
                    img_num) + extension)

            embedded_fp = open(self.compound.tmp_path + self.compound.fileName + "_extracted\\" + self.compound.fileName + "_" + str(
                img_num) + extension, 'wb')
            img_num += 1
            embedded_fp.write(embedded_data)
            embedded_fp.close()

        ##### OLE Object
        counter = 0
        self.current_offset = 0
        file_list = []
        while (self.current_offset < len(self.powerpoint_document)):
            rh_ver_instance = \
            struct.unpack('<H', self.powerpoint_document[self.current_offset: self.current_offset + 2])[0]
            rh_Type = \
            struct.unpack('<H', self.powerpoint_document[self.current_offset + 2: self.current_offset + 4])[0]
            rh_recLen = \
            struct.unpack('<I', self.powerpoint_document[self.current_offset + 4: self.current_offset + 8])[0]
            self.current_offset += 8

            if rh_Type == 0x1011:
                if not (os.path.isdir(self.compound.tmp_path + self.compound.fileName + "_extracted")):
                    os.makedirs(os.path.join(self.compound.tmp_path + self.compound.fileName + "_extracted"))

                path = self.compound.tmp_path + self.compound.fileName + "_extracted\\OLE_Object" + str(counter) + ".bin"
                self.compound.ole_path.append(path)
                outfile = open(path, "wb")
                counter += 1

                bindata: bytearray = bytearray(
                    self.powerpoint_document[self.current_offset + 6: self.current_offset + rh_recLen - 8])
                decompress = zlib.decompressobj(-zlib.MAX_WBITS)
                stream = bytearray()

                try:
                    stream = decompress.decompress(bindata)
                    stream += decompress.flush()
                except Exception:
                    pass
                file_list.append(path)
                outfile.write(stream)
                outfile.close()

            self.current_offset += (rh_recLen)  # - Header Size

        self.__getOLEFile__(file_list)
        
        """


