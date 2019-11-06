# carpe_doc.py
import struct
import compoundfiles

class DOC:

    def __init__(self, compound):
        self.compound = compound

    def __enter__(self):
        raise NotImplementedError

    def __exit__(self):
        raise NotImplementedError

    def parse_doc(self):
        if self.compound.is_damaged == self.compound.CONST_DOCUMENT_NORMAL:
            self.__parse_doc_normal__()
        elif self.compound.is_damaged == self.compound.CONST_DOCUMENT_DAMAGED:
            self.__parse_doc_damaged__()

    def __doc_extra_filter__(self, string, uFilteredTextLen):
        i = 0
        j = 0
        k = 0
        textLen = uFilteredTextLen
        # 1. 첫 부분의        공백        문자        모두        제거
        # 2. 공백        문자가        2        개        이상인        경우에        1        개로        만들자
        # 3.        개행        문자가        2        개        이상인        경우에        1        개로        만들자
        # 4.        Filtering

        uBlank = b'\x20\x00'   # ASCII Blank
        uBlank2 = b'\xA0\x00'   # Unicode Blank
        uNewline = b'\x0A\x00'   # Line Feed
        uNewline2 = b'\x0D\x00'
        uNewline3 = b'\x04\x00'
        uNewline4 = b'\x03\x00'
        uSection = b'\x01\x00'
        uSection2 = b'\x02\x00'
        uSection3 = b'\x05\x00'
        uSection4 = b'\x07\x00'
        uSection5 = b'\x08\x00'
        uSection6 = b'\x15\x00'
        uSection7 = b'\x0C\x00'
        uSection8 = b'\x0B\x00'
        uSection9 = b'\x14\x00'
        uTrash = b'\x00\x00'
        uCaption = b'\x53\x00\x45\x00\x51\x00'
        uCaption2 = b'\x41\x00\x52\x00\x41\x00\x43\x00\x49\x00\x43\x00\x20\x00\x14\x00'
        uHyperlink = b'\x48\x00\x59\x00\x50\x00\x45\x00\x52\x00\x4C\x00\x49\x00\x4E\x00\x4B\x00'
        uToc = b'\x54\x00\x4F\x00'
        uPageref = b'\x50\x00\x41\x00\x47\x00\x45\x00\x52\x00\x45\x00\x46\x00'
        uIndex = b'\x49\x00\x4E\x00\x44\x00\x45\x00\x58\x00'
        uEnd = b'\x20\x00\x01\x00\x14\x00'
        uEnd2 = b'\x20\x00\x14\x00'
        uEnd3 = b'\x20\x00\x15\x00'
        uEnd4 = b'\x14\x00'
        uEnd5 = b'\x01\x00\x14\x00'
        uEnd6 = b'\x15\x00'
        uHeader = b'\x13\x00'
        uChart = b'\x45\x00\x4D\x00\x42\x00\x45\x00\x44\x00'
        uShape = b'\x53\x00\x48\x00\x41\x00\x50\x00\x45\x00'
        uPage = b'\x50\x00\x41\x00\x47\x00\x45\x00'
        uDoc = b'\x44\x00\x4F\x00\x43\x00'
        uStyleref = b'\x53\x00\x54\x00\x59\x00\x4C\x00\x45\x00\x52\x00\x45\x00\x46\x00'
        uTitle = b'\x54\x00\x49\x00\x54\x00\x4C\x00\x45\x00'
        uDate = b'\x49\x00\x46\x00\x20\x00\x44\x00\x41\x00\x54\x00\x45\x00'
        filteredText = string
        while i < textLen :
            if i == 0:
                k = 0
                while (filteredText[0:2] == uBlank or filteredText[0:2] == uBlank2 or filteredText
                                                                                      [0:2] == uNewline or filteredText
                                                                                                          [0:2] == uNewline2 or
                       filteredText[0:2] == uNewline3 or filteredText[0:2] == uNewline4) :
                    filteredText = filteredText[:k] + filteredText[k + 2:]
                    textLen -= 2

                    if (len(filteredText) == 0):
                        break

            if len(filteredText) == 0:
                break


            if (len(filteredText) >= 2 + i) and filteredText[i : i + 2] == uHeader:
                filteredText = filteredText[:i] + filteredText[i + 2:]
                textLen -= 2

                if (len(filteredText) >= 2 + i) and filteredText[i : i + 2] == uBlank:
                    filteredText = filteredText[:i] + filteredText[i + 2:]
                    textLen -= 2

                charSize = 0
                temp = True
                j = i

                if (len(filteredText) >= 16 + i) and \
                        (filteredText[i: i + 6] == uCaption or filteredText[i: i + 18] == uHyperlink or
                        filteredText[i: i + 4] == uToc or filteredText[i: i + 14] == uPageref or filteredText[
                                                                                                 i: i + 10] == uIndex or
                        filteredText[i: i + 10] == uChart or filteredText[i: i + 10] == uShape or filteredText[
                                                                                                  i: i + 8] == uPage or
                        filteredText[i: i + 6] == uDoc or filteredText[i: i + 16] == uStyleref or filteredText[
                                                                                                  i: i + 10] == uTitle or filteredText[
                                                                                                                          i: i + 14] == uDate):
                    pass
                else:
                    temp = False

                while temp == True:
                    if (len(filteredText) >= 6 + j) and (filteredText[j: j + 6] == uEnd):
                        charSize += 6
                        j += 6
                        break

                    elif (len(filteredText) >= 4 + j) and (
                            filteredText[j: j + 4] == uEnd2 or filteredText[j: j + 4] == uEnd3):
                        charSize += 4
                        j += 4
                        break
                    elif (len(filteredText) >= 2 + j) and (filteredText[j: j + 2] == uEnd4):
                        charSize += 2
                        j += 2
                        break

                    charSize += 2
                    j += 2

                    if (len(filteredText) < 6 + j):
                        temp = False
                        break

                if temp == True:
                    filteredText = filteredText[:i] + filteredText[i + charSize:]
                    textLen -= charSize

                i -= 2
                continue

            if (len(filteredText) >= 2 + i) and (
                    filteredText[i: i + 2] == uSection or filteredText[i: i + 2] == uSection6 or
                    filteredText[i: i + 2] == uSection9):
                filteredText = filteredText[:i] + filteredText[i + 2:]
                textLen -= 2

                i -= 2
                continue

            if (len(filteredText) >= 4 + i) and (filteredText[i: i + 4] == uHeader):
                filteredText = filteredText[:i] + filteredText[i + 4:]
                textLen -= 4

                i -= 4
                continue

            i += 2
        dict = {}
        dict['string'] = filteredText
        dict['length'] = textLen
        return dict

    def __parse_doc_normal__(self):
        word_document = bytearray(self.compound.fp.open('WordDocument').read())  # byteWD

        one_table = b''
        zero_table = b''
        try:
            one_table = bytearray(self.compound.fp.open('1Table').read())
        except compoundfiles.errors.CompoundFileNotFoundError:
            pass
            #print("1Table is not exist.")

        try:
            zero_table = bytearray(self.compound.fp.open('0Table').read())
        except compoundfiles.errors.CompoundFileNotFoundError:
            pass
            #print("0Table is not exist.")

        if len(one_table) == 0 and len(zero_table) == 0:
            return self.compound.CONST_ERROR

        # Extract doc Text
        ccpText = b''
        fcClx = b''
        lcbClx = b''
        aCP = b''
        aPcd = b''
        fcCompressed = b''
        Clx = b''
        byteTable = b''
        ccpTextSize = 0
        fcClxSize = 0
        lcbClxSize = 0
        ClxSize = 0
        string = b''
        CONST_FCFLAG = 1073741824  # 0x40000000
        CONST_FCINDEXFLAG = 1073741823  # 0x3FFFFFFF
        i = 0
        j = 0
        k = 0

        # Check Encrypted
        uc_temp = word_document[11]
        uc_temp = uc_temp & 1

        if uc_temp == 1:
            return self.compound.CONST_ERROR

        # 0Table 1Table
        is0Table = word_document[11] & 2

        if is0Table == 0:
            byteTable = zero_table
        else:
            byteTable = one_table

        # Get cppText in FibRgLw
        ccpText = word_document[0x4C:0x50]
        ccpTextSize = struct.unpack('<I', ccpText)[0]

        if (ccpTextSize == 0):
            return self.compound.CONST_ERROR

        # Get fcClx in FibRgFcLcbBlob
        fcClx = word_document[0x1A2:0x1A6]
        fcClxSize = struct.unpack('<I', fcClx)[0]

        if (fcClxSize == 0):
            return self.compound.CONST_ERROR

        # Get lcbClx in FibRgFcLcbBlob
        lcbClx = word_document[0x1A6:0x1AA]
        lcbClxSize = struct.unpack('<I', lcbClx)[0]

        if (lcbClxSize == 0):
            return self.compound.CONST_ERROR

        # Get Clx
        Clx = byteTable[fcClxSize: fcClxSize + lcbClxSize]

        if Clx[0] == 0x01:
            cbGrpprl = struct.unpack("<H", Clx[1:3])[0]
            Clx = byteTable[fcClxSize + cbGrpprl + 3: (fcClxSize + cbGrpprl + 3) + lcbClxSize - cbGrpprl + 3]
        if Clx[0] != 0x02:
            return self.compound.CONST_ERROR

        ClxSize = struct.unpack('<I', Clx[1:5])[0]

        ClxIndex = 5
        PcdCount = 0
        aCPSize = []
        fcFlag = 0
        fcIndex = 0
        fcSize = 0
        encodingFlag = False

        PcdCount = int(((ClxSize / 4) / 3)) + 1

        for i in range(0, PcdCount):
            aCp = Clx[ClxIndex:ClxIndex + 4]
            aCPSize.append(struct.unpack('<I', aCp[0:4])[0])
            ClxIndex += 4

        PcdCount -= 1

        ### Filtering

        uBlank = b'\x20\x00'  # ASCII Blank
        uBlank2 = b'\xA0\x00'  # Unicode Blank
        uNewline = b'\x0A\x00'  # Line Feed
        uNewline2 = b'\x0D\x00'
        uNewline3 = b'\x04\x00'
        uNewline4 = b'\x03\x00'
        uSection = b'\x01\x00'
        uSection2 = b'\x02\x00'
        uSection3 = b'\x05\x00'
        uSection4 = b'\x07\x00'
        uSection5 = b'\x08\x00'
        uSection6 = b'\x15\x00'
        uSection7 = b'\x0C\x00'
        uSection8 = b'\x0B\x00'
        uSection9 = b'\x14\x00'
        uTrash = b'\x00\x00'
        uCaption = b'\x53\x00\x45\x00\x51\x00'
        uCaption2 = b'\x41\x00\x52\x00\x41\x00\x43\x00\x49\x00\x43\x00\x20\x00\x14\x00'
        uHyperlink = b'\x48\x00\x59\x00\x50\x00\x45\x00\x52\x00\x4C\x00\x49\x00\x4E\x00\x4B\x00'
        uToc = b'\x54\x00\x4F\x00'
        uPageref = b'\x50\x00\x41\x00\x47\x00\x45\x00\x52\x00\x45\x00\x46\x00'
        uIndex = b'\x49\x00\x4E\x00\x44\x00\x45\x00\x58\x00'
        uEnd = b'\x20\x00\x01\x00\x14\x00'
        uEnd2 = b'\x20\x00\x14\x00'
        uEnd3 = b'\x20\x00\x15\x00'
        uEnd4 = b'\x14\x00'
        uEnd5 = b'\x01\x00\x14\x00'
        uEnd6 = b'\x15\x00'
        uHeader = b'\x13\x00'
        uChart = b'\x45\x00\x4D\x00\x42\x00\x45\x00\x44\x00'
        uShape = b'\x53\x00\x48\x00\x41\x00\x50\x00\x45\x00'
        uPage = b'\x50\x00\x41\x00\x47\x00\x45\x00'
        uDoc = b'\x44\x00\x4F\x00\x43\x00'
        uStyleref = b'\x53\x00\x54\x00\x59\x00\x4C\x00\x45\x00\x52\x00\x45\x00\x46\x00'
        uTitle = b'\x54\x00\x49\x00\x54\x00\x4C\x00\x45\x00'
        uDate = b'\x49\x00\x46\x00\x20\x00\x44\x00\x41\x00\x54\x00\x45\x00'

        ### Filtering targets: 0x0001 ~ 0x0017(0x000A Line Feed skipped)
        uTab = b'\x09\x00'  # Horizontal Tab
        uSpecial = b'\xF0'
        bFullScanA = False
        bFullScanU = False  # if the size info is invalid, then the entire range will be scanned.
        tempPlus = 0

        for i in range(0, PcdCount):
            aPcd = Clx[ClxIndex:ClxIndex + 8]
            fcCompressed = aPcd[2:6]

            fcFlag = struct.unpack('<I', fcCompressed[0:4])[0]

            if CONST_FCFLAG == (fcFlag & CONST_FCFLAG):
                encodingFlag = True  # 8-bit ANSI
            else:
                encodingFlag = False  # 16-bit Unicode

            fcIndex = fcFlag & CONST_FCINDEXFLAG

            k = 0
            if encodingFlag == True:  # 8-bit ANSI
                fcIndex = int(fcIndex / 2)
                fcSize = aCPSize[i + 1] - aCPSize[i]

                if len(word_document) < fcIndex + fcSize + 1:
                    if bFullScanA == False and len(word_document) > fcIndex:
                        fcSize = len(word_document) - fcIndex - 1
                        bFullScanA = True
                    else:
                        ClxIndex += 8
                        continue

                ASCIIText = word_document[fcIndex:fcIndex + fcSize]
                UNICODEText = b''

                for i in range(0, len(ASCIIText)):
                    UNICODEText += bytes([ASCIIText[i]])
                    UNICODEText += b'\x00'

                while k < len(UNICODEText):

                    if (UNICODEText[k: k + 2] == uSection2 or UNICODEText[k: k + 2] == uSection3 or UNICODEText[
                                                                                                    k: k + 2] == uSection4 or
                            UNICODEText[k: k + 2] == uSection5 or UNICODEText[k: k + 2] == uSection7 or UNICODEText[
                                                                                                        k: k + 2] == uSection8 or
                            UNICODEText[k + 1] == uSpecial or UNICODEText[k: k + 2] == uTrash):
                        k += 2  ### while
                        continue

                    if (UNICODEText[k: k + 2] == uNewline or UNICODEText[k: k + 2] == uNewline2 or UNICODEText[
                                                                                                   k: k + 2] == uNewline3 or UNICODEText[
                                                                                                                             k: k + 2] == uNewline4):
                        string += bytes([UNICODEText[k]])
                        string += bytes([UNICODEText[k + 1]])

                        j = k + 2
                        while j < len(UNICODEText):
                            if (UNICODEText[j:j + 2] == uSection2 or UNICODEText[j:j + 2] == uSection3 or UNICODEText[
                                                                                                          j:j + 2] == uSection4 or
                                    UNICODEText[j:j + 2] == uSection5 or UNICODEText[j:j + 2] == uSection7 or UNICODEText[
                                                                                                              j:j + 2] == uSection8 or
                                    UNICODEText[j:j + 2] == uBlank or UNICODEText[j:j + 2] == uBlank2 or UNICODEText[
                                                                                                         j:j + 2] == uNewline or
                                    UNICODEText[j:j + 2] == uNewline2 or UNICODEText[j:j + 2] == uNewline3 or UNICODEText[
                                                                                                              j:j + 2] == uNewline4 or
                                    UNICODEText[j:j + 2] == uTab or UNICODEText[j + 1] == uSpecial):
                                j += 2
                                continue
                            else:
                                k = j
                                break

                        if j >= len(UNICODEText):
                            break

                    elif (UNICODEText[k:k + 2] == uBlank or UNICODEText[k:k + 2] == uBlank2 or UNICODEText[
                                                                                               k:k + 2] == uTab):

                        string += bytes([UNICODEText[k]])
                        string += bytes([UNICODEText[k + 1]])

                        j = k + 2
                        while j < len(UNICODEText):
                            if (UNICODEText[j:j + 2] == uSection2 or UNICODEText[j:j + 2] == uSection3 or UNICODEText[
                                                                                                          j:j + 2] == uSection4 or
                                    UNICODEText[j:j + 2] == uSection5 or UNICODEText[j:j + 2] == uSection7 or UNICODEText[
                                                                                                              j:j + 2] == uSection8 or
                                    UNICODEText[j:j + 2] == uBlank or UNICODEText[j:j + 2] == uBlank2 or UNICODEText[
                                                                                                         j:j + 2] == uTab or
                                    UNICODEText[j + 1] == uSpecial):
                                j += 2
                                continue
                            else:
                                k = j
                                break

                        if (j >= len(UNICODEText)):
                            break

                    string += bytes([UNICODEText[k]])
                    string += bytes([UNICODEText[k + 1]])
                    k += 2




            elif encodingFlag == False:  ### 16-bit Unicode
                fcSize = 2 * (aCPSize[i + 1] - aCPSize[i])

                if (len(
                        word_document) < fcIndex + fcSize + 1):  # Invalid structure - size info is invalid (large) => scan from fcIndex to last
                    if (bFullScanU == False and len(word_document) > fcIndex):
                        fcSize = len(word_document) - fcIndex - 1
                        bFullScanU = True
                    else:
                        ClxIndex = ClxIndex + 8
                        continue

                while k < fcSize:
                    if (word_document[fcIndex + k: fcIndex + k + 2] == uSection2 or word_document[
                                                                                    fcIndex + k: fcIndex + k + 2] == uSection3 or
                            word_document[fcIndex + k: fcIndex + k + 2] == uSection4 or word_document[
                                                                                        fcIndex + k: fcIndex + k + 2] == uSection5 or
                            word_document[fcIndex + k: fcIndex + k + 2] == uSection7 or word_document[
                                                                                        fcIndex + k: fcIndex + k + 2] == uSection8 or
                            word_document[fcIndex + k + 1] == uSpecial or word_document[
                                                                          fcIndex + k: fcIndex + k + 2] == uTrash):
                        k += 2
                        continue

                    if (word_document[fcIndex + k: fcIndex + k + 2] == uNewline or word_document[
                                                                                   fcIndex + k: fcIndex + k + 2] == uNewline2 or
                            word_document[fcIndex + k: fcIndex + k + 2] == uNewline3 or word_document[
                                                                                        fcIndex + k: fcIndex + k + 2] == uNewline4):

                        if (word_document[fcIndex + k] == 0x0d):
                            string += b'\x0a'
                            string += bytes([word_document[fcIndex + k + 1]])
                        else:
                            string += bytes([word_document[fcIndex + k]])
                            string += bytes([word_document[fcIndex + k + 1]])

                        j = k + 2
                        while j < fcSize:
                            if (word_document[fcIndex + j: fcIndex + j + 2] == uSection2 or word_document[
                                                                                            fcIndex + j: fcIndex + j + 2] == uSection3 or word_document[
                                                                                                                                          fcIndex + j: fcIndex + j + 2] == uSection4 or
                                    word_document[fcIndex + j: fcIndex + j + 2] == uSection5 or word_document[
                                                                                                fcIndex + j: fcIndex + j + 2] == uSection7 or word_document[
                                                                                                                                              fcIndex + j: fcIndex + j + 2] == uSection8 or
                                    word_document[fcIndex + j: fcIndex + j + 2] == uBlank or word_document[
                                                                                             fcIndex + j: fcIndex + j + 2] == uBlank2 or word_document[
                                                                                                                                         fcIndex + j: fcIndex + j + 2] == uNewline or word_document[
                                                                                                                                                                                      fcIndex + j: fcIndex + j + 2] == uNewline2 or
                                    word_document[fcIndex + j: fcIndex + j + 2] == uNewline3 or word_document[
                                                                                                fcIndex + j: fcIndex + j + 2] == uNewline4 or word_document[
                                                                                                                                              fcIndex + j: fcIndex + j + 2] == uTab or
                                    word_document[
                                        fcIndex + j + 1] == uSpecial):
                                j += 2
                                continue
                            else:
                                k = j
                                break

                        if j >= fcSize:
                            break

                    elif word_document[fcIndex + k: fcIndex + k + 2] == uBlank or word_document[
                                                                                  fcIndex + k: fcIndex + k + 2] == uBlank2 or word_document[
                                                                                                                              fcIndex + k: fcIndex + k + 2] == uTab:
                        string += bytes([word_document[fcIndex + k]])
                        string += bytes([word_document[fcIndex + k + 1]])

                        j = k + 2
                        while j < fcSize:
                            if (word_document[fcIndex + j: fcIndex + j + 2] == uSection2 or word_document[
                                                                                            fcIndex + j: fcIndex + j + 2] == uSection3 or word_document[
                                                                                                                                          fcIndex + j: fcIndex + j + 2] == uSection4 or
                                    word_document[fcIndex + j: fcIndex + j + 2] == uSection5 or word_document[
                                                                                                fcIndex + j: fcIndex + j + 2] == uSection7 or word_document[
                                                                                                                                              fcIndex + j: fcIndex + j + 2] == uSection8 or
                                    word_document[fcIndex + j: fcIndex + j + 2] == uBlank or word_document[
                                                                                             fcIndex + j: fcIndex + j + 2] == uBlank2 or word_document[
                                                                                                                                         fcIndex + j: fcIndex + j + 2] == uTab or
                                    word_document[fcIndex + j + 1] == uSpecial):
                                j += 2
                                continue
                            else:
                                k = j
                                break

                        if j >= fcSize:
                            break

                    string += bytes([word_document[fcIndex + k]])
                    string += bytes([word_document[fcIndex + k + 1]])
                    k += 2

            ClxIndex += 8

        dictionary = self.__doc_extra_filter__(string, len(string))

        filteredText = dictionary['string']
        filteredLen = dictionary['length']
        #self.compound.content = filteredText.decode("utf-16")

        ###### DOC 추가

        if len(filteredText) != 0:
            nPos = filteredLen
            usTmp1 = 0
            usTmp2 = 0

            if nPos >= 4:
                usTmp1 = struct.unpack('<H', filteredText[0 + nPos - 4 : 0 + nPos - 4 + 2])[0]
            usTmp2 = struct.unpack('<H', filteredText[0 + nPos - 2: 0 + nPos - 2 + 2])[0]

            if usTmp1 == uNewline:
                if usTmp2 != uNewline:
                    filteredText += b'\x0A\x00\x00\x00'
            else:
                if usTmp2 == uNewline:
                    filteredText += b'\x0A\x00\x00\x00'
                else:
                    filteredText += b'\x0A\x00\x0A\x00\x00\x00'

        #######
        for i in range(0, len(filteredText), 2):
            try:
                self.compound.content += filteredText[i:i+2].decode('utf-16')
            except UnicodeDecodeError:
                continue



    def __parse_doc_damaged__(self):
        file = bytearray(self.compound.fp.read())
        m_word = b''
        m_table = b''
        wordFlag = False
        tableFlag = False
        word_document = b''
        one_table = b''
        zero_table = b''
    
        string = b''
        CONST_FCFLAG = 1073741824		# 0x40000000
        CONST_FCINDEXFLAG = 1073741823	# 0x3FFFFFFF
    
        CONST_TABLE1_WORD = b'\x57\x00\x6F\x00\x72\x00\x64\x00\x44\x00\x6F\x00'
        CONST_TABLE2_1TABLE = b'\x31\x00\x54\x00\x61\x00\x62\x00\x6C\x00\x65\x00'
        CONST_DATA_SIGNATURE = b'\xEC\xA5'
        nCurPos = 0
    
        while(nCurPos < len(file)):
            if(file[nCurPos : nCurPos + 12] == CONST_TABLE1_WORD):
                m_word = file[nCurPos : nCurPos + 0x80]
                wordFlag = True
    
            if (file[nCurPos: nCurPos + 12] == CONST_TABLE2_1TABLE):
                m_table = file[nCurPos: nCurPos + 0x80]
                tableFlag = True
    
            if (tableFlag == True and wordFlag == True):
                break
    
            nCurPos += 0x80
    
        if tableFlag == False or wordFlag == False:
            return


        # word
        if (file[0x200:0x202] == CONST_DATA_SIGNATURE):
            if wordFlag == True:
                wordStartIndex = struct.unpack('<I', m_word[0x74:0x78])[0]
                wordSize = struct.unpack('<I', m_word[0x78:0x7C])[0]
    
                if wordSize < len(file) - 0x202:
                    word_document = file[(wordStartIndex + 1) * 0x200 : (wordStartIndex + 1) * 0x200 + wordSize]
    
            else:
                word_document = file[0x200:]
    
        #table
        if tableFlag == True:
            tableStartIndex = struct.unpack('<I', m_table[0x74:0x78])[0]
            tableSize = struct.unpack('<I', m_table[0x78:0x7C])[0]
            byteTable = file[(tableStartIndex + 1) * 0x200 : (tableStartIndex + 1) * 0x200 + tableSize]
    
        if len(word_document) <= 0x200:     ### No Data
            return False

        # Get cppText in FibRgLw
        ccpText = word_document[0x4C:0x50]
        ccpTextSize = struct.unpack('<I', ccpText)[0]
    
        if (ccpTextSize == 0):
            return self.compound.CONST_ERROR
    
        # Get fcClx in FibRgFcLcbBlob
        fcClx = word_document[0x1A2:0x1A6]
        fcClxSize = struct.unpack('<I', fcClx)[0]
    
        if (fcClxSize == 0):
            return self.compound.CONST_ERROR
    
        # Get lcbClx in FibRgFcLcbBlob
        lcbClx = word_document[0x1A6:0x1AA]
        lcbClxSize = struct.unpack('<I', lcbClx)[0]
    
        if (lcbClxSize == 0):
            return self.compound.CONST_ERROR
    
        # Get Clx
        Clx = byteTable[fcClxSize: fcClxSize + lcbClxSize]
    
        if Clx[0] == 0x01:
            cbGrpprl = struct.unpack("<H", Clx[1:3])[0]
            Clx = byteTable[fcClxSize + cbGrpprl + 3: (fcClxSize + cbGrpprl + 3) + lcbClxSize - cbGrpprl + 3]
        if Clx[0] != 0x02:
            return self.compound.CONST_ERROR
    
        ClxSize = struct.unpack('<I', Clx[1:5])[0]
    
        ClxIndex = 5
        PcdCount = 0
        aCPSize = []
        fcFlag = 0
        fcIndex = 0
        fcSize = 0
        encodingFlag = False
    
        PcdCount = int(((ClxSize / 4) / 3)) + 1
    
        for i in range(0, PcdCount):
            aCp = Clx[ClxIndex:ClxIndex + 4]
            aCPSize.append(struct.unpack('<I', aCp[0:4])[0])
            ClxIndex += 4
    
        PcdCount -= 1
    
        ### Filtering
    
        uBlank = b'\x20\x00'  # ASCII Blank
        uBlank2 = b'\xA0\x00'  # Unicode Blank
        uNewline = b'\x0A\x00'  # Line Feed
        uNewline2 = b'\x0D\x00'
        uNewline3 = b'\x04\x00'
        uNewline4 = b'\x03\x00'
        uSection = b'\x01\x00'
        uSection2 = b'\x02\x00'
        uSection3 = b'\x05\x00'
        uSection4 = b'\x07\x00'
        uSection5 = b'\x08\x00'
        uSection6 = b'\x15\x00'
        uSection7 = b'\x0C\x00'
        uSection8 = b'\x0B\x00'
        uSection9 = b'\x14\x00'
        uTrash = b'\x00\x00'
        uCaption = b'\x53\x00\x45\x00\x51\x00'
        uCaption2 = b'\x41\x00\x52\x00\x41\x00\x43\x00\x49\x00\x43\x00\x20\x00\x14\x00'
        uHyperlink = b'\x48\x00\x59\x00\x50\x00\x45\x00\x52\x00\x4C\x00\x49\x00\x4E\x00\x4B\x00'
        uToc = b'\x54\x00\x4F\x00'
        uPageref = b'\x50\x00\x41\x00\x47\x00\x45\x00\x52\x00\x45\x00\x46\x00'
        uIndex = b'\x49\x00\x4E\x00\x44\x00\x45\x00\x58\x00'
        uEnd = b'\x20\x00\x01\x00\x14\x00'
        uEnd2 = b'\x20\x00\x14\x00'
        uEnd3 = b'\x20\x00\x15\x00'
        uEnd4 = b'\x14\x00'
        uEnd5 = b'\x01\x00\x14\x00'
        uEnd6 = b'\x15\x00'
        uHeader = b'\x13\x00'
        uChart = b'\x45\x00\x4D\x00\x42\x00\x45\x00\x44\x00'
        uShape = b'\x53\x00\x48\x00\x41\x00\x50\x00\x45\x00'
        uPage = b'\x50\x00\x41\x00\x47\x00\x45\x00'
        uDoc = b'\x44\x00\x4F\x00\x43\x00'
        uStyleref = b'\x53\x00\x54\x00\x59\x00\x4C\x00\x45\x00\x52\x00\x45\x00\x46\x00'
        uTitle = b'\x54\x00\x49\x00\x54\x00\x4C\x00\x45\x00'
        uDate = b'\x49\x00\x46\x00\x20\x00\x44\x00\x41\x00\x54\x00\x45\x00'
    
        ### Filtering targets: 0x0001 ~ 0x0017(0x000A Line Feed skipped)
        uTab = b'\x09\x00'  # Horizontal Tab
        uSpecial = b'\xF0'
        bFullScanA = False
        bFullScanU = False  # if the size info is invalid, then the entire range will be scanned.
        tempPlus = 0
    
        for i in range(0, PcdCount):
            aPcd = Clx[ClxIndex:ClxIndex + 8]
            fcCompressed = aPcd[2:6]
    
            fcFlag = struct.unpack('<I', fcCompressed[0:4])[0]
    
            if CONST_FCFLAG == (fcFlag & CONST_FCFLAG):
                encodingFlag = True  # 8-bit ANSI
            else:
                encodingFlag = False  # 16-bit Unicode
    
            fcIndex = fcFlag & CONST_FCINDEXFLAG
    
            k = 0
            if encodingFlag == True:  # 8-bit ANSI
                fcIndex = int(fcIndex / 2)
                fcSize = aCPSize[i + 1] - aCPSize[i]
    
                if len(word_document) < fcIndex + fcSize + 1:
                    if bFullScanA == False and len(word_document) > fcIndex:
                        fcSize = len(word_document) - fcIndex - 1
                        bFullScanA = True
                    else:
                        ClxIndex += 8
                        continue
    
                ASCIIText = word_document[fcIndex:fcIndex + fcSize]
                UNICODEText = b''
    
                for i in range(0, len(ASCIIText)):
                    UNICODEText += bytes([ASCIIText[i]])
                    UNICODEText += b'\x00'
    
                while k < len(UNICODEText):
    
                    if (UNICODEText[k: k + 2] == uSection2 or UNICODEText[k: k + 2] == uSection3 or UNICODEText[: k + 2] == uSection4 or
                            UNICODEText[k: k + 2] == uSection5 or UNICODEText[k: k + 2] == uSection7 or UNICODEText[k: k + 2] == uSection8 or
                            UNICODEText[k + 1] == uSpecial or UNICODEText[k: k + 2] == uTrash):
                        k += 2  ### while
                        continue
    
                    if (UNICODEText[k: k + 2] == uNewline or UNICODEText[k: k + 2] == uNewline2 or UNICODEText[k: k + 2] == uNewline3 or UNICODEText[k: k + 2] == uNewline4):
                        string += bytes([UNICODEText[k]])
                        string += bytes([UNICODEText[k + 1]])
    
                        j = k + 2
                        while j < len(UNICODEText):
                            if (UNICODEText[j:j + 2] == uSection2 or UNICODEText[j:j + 2] == uSection3 or UNICODEText[j:j + 2] == uSection4 or
                                    UNICODEText[j:j + 2] == uSection5 or UNICODEText[j:j + 2] == uSection7 or UNICODEText[j:j + 2] == uSection8 or
                                    UNICODEText[j:j + 2] == uBlank or UNICODEText[j:j + 2] == uBlank2 or UNICODEText[j:j + 2] == uNewline or
                                    UNICODEText[j:j + 2] == uNewline2 or UNICODEText[j:j + 2] == uNewline3 or UNICODEText[j:j + 2] == uNewline4 or
                                    UNICODEText[j:j + 2] == uTab or UNICODEText[j + 1] == uSpecial):
                                j += 2
                                continue
                            else:
                                k = j
                                break
    
                        if j >= len(UNICODEText):
                            break
    
                    elif (UNICODEText[k:k + 2] == uBlank or UNICODEText[k:k + 2] == uBlank2 or UNICODEText[k:k + 2] == uTab):
    
                        string += bytes([UNICODEText[k]])
                        string += bytes([UNICODEText[k + 1]])
    
                        j = k + 2
                        while j < len(UNICODEText):
                            if (UNICODEText[j:j + 2] == uSection2 or UNICODEText[j:j + 2] == uSection3 or UNICODEText[j:j + 2] == uSection4 or
                                    UNICODEText[j:j + 2] == uSection5 or UNICODEText[j:j + 2] == uSection7 or UNICODEText[j:j + 2] == uSection8 or
                                    UNICODEText[j:j + 2] == uBlank or UNICODEText[j:j + 2] == uBlank2 or UNICODEText[j:j + 2] == uTab or
                                    UNICODEText[j + 1] == uSpecial):
                                j += 2
                                continue
                            else:
                                k = j
                                break
    
                        if (j >= len(UNICODEText)):
                            break
    
                    string += bytes([UNICODEText[k]])
                    string += bytes([UNICODEText[k + 1]])
                    k += 2
    
    
    
    
            elif encodingFlag == False:  ### 16-bit Unicode
                fcSize = 2 * (aCPSize[i + 1] - aCPSize[i])
    
                if (len(
                        word_document) < fcIndex + fcSize + 1):  # Invalid structure - size info is invalid (large) => scan from fcIndex to last
                    if (bFullScanU == False and len(word_document) > fcIndex):
                        fcSize = len(word_document) - fcIndex - 1
                        bFullScanU = True
                    else:
                        ClxIndex = ClxIndex + 8
                        continue
    
                while k < fcSize:
                    if (word_document[fcIndex + k: fcIndex + k + 2] == uSection2 or word_document[fcIndex + k: fcIndex + k + 2] == uSection3 or
                            word_document[fcIndex + k: fcIndex + k + 2] == uSection4 or word_document[fcIndex + k: fcIndex + k + 2] == uSection5 or
                            word_document[fcIndex + k: fcIndex + k + 2] == uSection7 or word_document[fcIndex + k: fcIndex + k + 2] == uSection8 or
                            word_document[fcIndex + k + 1] == uSpecial or word_document[fcIndex + k: fcIndex + k + 2] == uTrash):
                        k += 2
                        continue
    
                    if (word_document[fcIndex + k: fcIndex + k + 2] == uNewline or word_document[fcIndex + k: fcIndex + k + 2] == uNewline2 or
                            word_document[fcIndex + k: fcIndex + k + 2] == uNewline3 or word_document[fcIndex + k: fcIndex + k + 2] == uNewline4):
    
                        if (word_document[fcIndex + k] == 0x0d):
                            string += b'\x0a'
                            string += bytes([word_document[fcIndex + k + 1]])
                        else:
                            string += bytes([word_document[fcIndex + k]])
                            string += bytes([word_document[fcIndex + k + 1]])
    
                        j = k + 2
                        while j < fcSize:
                            if (word_document[fcIndex + j: fcIndex + j + 2] == uSection2 or word_document[fcIndex + j: fcIndex + j + 2] == uSection3 or word_document[fcIndex + j: fcIndex + j + 2] == uSection4 or
                                    word_document[fcIndex + j: fcIndex + j + 2] == uSection5 or word_document[fcIndex + j: fcIndex + j + 2] == uSection7 or word_document[fcIndex + j: fcIndex + j + 2] == uSection8 or
                                    word_document[fcIndex + j: fcIndex + j + 2] == uBlank or word_document[fcIndex + j: fcIndex + j + 2] == uBlank2 or word_document[fcIndex + j: fcIndex + j + 2] == uNewline or
                                    word_document[fcIndex + j: fcIndex + j + 2] == uNewline2 or word_document[fcIndex + j: fcIndex + j + 2] == uNewline3 or word_document[fcIndex + j: fcIndex + j + 2] == uNewline4 or
                                    word_document[fcIndex + j: fcIndex + j + 2] == uTab or word_document[fcIndex + j + 1] == uSpecial):
                                j += 2
                                continue
                            else:
                                k = j
                                break
    
                        if j >= fcSize:
                            break
    
                    elif word_document[fcIndex + k: fcIndex + k + 2] == uBlank or word_document[fcIndex + k: fcIndex + k + 2] == uBlank2 or word_document[fcIndex + k: fcIndex + k + 2] == uTab:
                        string += bytes([word_document[fcIndex + k]])
                        string += bytes([word_document[fcIndex + k + 1]])
    
                        j = k + 2
                        while j < fcSize:
                            if (word_document[fcIndex + j: fcIndex + j + 2] == uSection2 or word_document[fcIndex + j: fcIndex + j + 2] == uSection3 or word_document[fcIndex + j: fcIndex + j + 2] == uSection4 or
                                    word_document[fcIndex + j: fcIndex + j + 2] == uSection5 or word_document[fcIndex + j: fcIndex + j + 2] == uSection7 or word_document[fcIndex + j: fcIndex + j + 2] == uSection8 or
                                    word_document[fcIndex + j: fcIndex + j + 2] == uBlank or word_document[fcIndex + j: fcIndex + j + 2] == uBlank2 or word_document[fcIndex + j: fcIndex + j + 2] == uTab or
                                    word_document[fcIndex + j + 1] == uSpecial):
                                j += 2
                                continue
                            else:
                                k = j
                                break
    
                        if j >= fcSize:
                            break
    
                    string += bytes([word_document[fcIndex + k]])
                    string += bytes([word_document[fcIndex + k + 1]])
                    k += 2
    
            ClxIndex += 8
    
        dictionary = self.__doc_extra_filter__(string, len(string))
    
        filteredText = dictionary['string']
        filteredLen = dictionary['length']

        #self.compound.content = filteredText.decode("utf-16")
        for i in range(0, len(filteredText), 2):
            try:
                self.compound.content += filteredText[i:i+2].decode('utf-16')
            except UnicodeDecodeError:
                continue



    """
    def __parse_doc_damaged__(self):
        pass
        
        file = bytearray(self.fp.read())
        offset = 0
        wordStartOffset = 0
        bWord = False
        while len(file) > offset:
            if file[offset:offset + 2] == b'\xEC\xA5':
                wordStartOffset = offset
                bWord = True
                break
            offset += 0x80
    
        bFinish = False
        string = ""
        offset = wordStartOffset + 0x200
        while len(file) > offset:
            if file[offset : offset + 2] == b'\x00\x00' or file[offset + 2: offset + 4] == b'\x00\x00':
                offset += 0x200
                continue
    
    
            encoding = chardet.detect(file[offset : offset + 0x100])
            if encoding['encoding'] != None :
                if encoding['encoding'] == 'ascii' or encoding['encoding'] == 'Windows-1252':
                    string += file[offset: offset + 0x200].decode('windows-1252')
                else:
                    for i in range(0, 0x200, 2):
                        string += file[offset + i : offset + i + 2].decode('utf-16')
    
    
            offset += 0x200
    
        test = open('/home/horensic/Desktop/extract.txt', 'w')
        test.write(string)
        test.close()
    """