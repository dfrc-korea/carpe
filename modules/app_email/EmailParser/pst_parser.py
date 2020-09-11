"""
if __name__ == "__main__":
    import sys, os
    _root_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    sys.path.append(_root_dir)
"""
import pypff
from modules.app_email.lib.yjSysUtils import *
from modules.app_email.EmailBoxClass import parseReceivedLine, makeEmailHeaderType, parseEmailHeader, get_content_type, decode_body


class TPST_Parser:
    def __init__(self, fileName):
        self.fileName = fileName
        self.messageCount = 0
        self.__file = None
        self.root = None
        self.EmailBox = None

    def __del__(self):
        if self.__file: self.__file.close()
        pass

    def open(self):
        self.__file = pypff.file()
        f = self.__file
        f.open(self.fileName)
        self.root = f.get_root_folder()

    def close(self):
        self.__file.close()
        self.__file = None

    def traverseFolder(self, messageProc, base=None, _dir=''):
        result = 0
        if not base: base = self.root
        for folder in base.sub_folders:
            if folder.number_of_sub_folders:
                result += self.traverseFolder(messageProc, folder, os.path.join(_dir, folder.name))
            cnt = len(folder.sub_messages)
            result += cnt
            if messageProc and cnt:
                i = 0
                d = '%s/%s' % (_dir, folder.name)
                for message in folder.sub_messages:
                    i += 1
                    if not messageProc(self, i, message, d, cnt): break
        return result

_folder_no = 0

value_Null_terminated_String = 0x001E
value_Unicode_string = 0x001F
entry_Attachment_Filename = 0x3704
entry_Attachement_method = 0x3705
entry_Attachment_Filename_long = 0x3707


def msgProc(self, no, message, _dir, cnt):

    def getBody(message, charset):
        data = message.get_html_body()
        if data == None:
            data = message.get_plain_text_body()
            if data == None: return ''
        if __debug__: type(data) is bytes
        return decode_body(data, charset)

    global _folder_no
    if no == 1: _folder_no += 1
    if __debug__: assert ExtractFilePath(self.fileName) != ''

    msg_info = {}
    msg_info['file'] = ExtractFileName(self.fileName)
    msg_info['dir'] = _dir

    headers = message.get_transport_headers()
    if headers == None: return True

    headers = parseEmailHeader(headers)
    content_type = get_content_type(headers)
    if len(content_type) >= 2:
        charset = content_type[1]
    else:
        charset = 'utf-8'

    clsEmailMessageObject = {}
    msg_info['EmailMessageObject'] = clsEmailMessageObject
    clsEmailMessageObject['Header'] = makeEmailHeaderType(headers)
    clsEmailMessageObject['Body'] = getBody(message, charset)

    # 첨부 처리
    if ('attachments' in dir(message)) and (message.number_of_attachments > 0):

        def attachment_name(attachment):
            try:
                if attachment.number_of_record_sets > 0:
                    for entry in attachment.get_record_set(0).entries:
                        if (entry.entry_type == entry_Attachment_Filename_long) and (
                                entry.value_type in [value_Null_terminated_String, value_Unicode_string]):  # 첨부파일명
                            return entry.data_as_string
            except:
                pass
            return None

        attachments = []
        for i in range(message.number_of_attachments):
            attachment = message.get_attachment(i)
            if __debug__: assert type(attachment) is pypff.attachment
            name = attachment_name(attachment)
            if name == None: continue
            file_info = {}
            file_info['name'] = name  # 파일명
            file_info['size'] = attachment.get_size()  # 파일크기
            attachments.append(file_info)

            # 첨부 파일 생성
            try:
                f = open(os.path.join(self.EmailBox.createAttachmentDir(_folder_no, no), name), 'wb')
                f.write(attachment.read_buffer(attachment.get_size()))
                f.close()
            except Exception as e:
                continue
                #print(e)
        if len(attachments) > 0:
            clsEmailMessageObject['Attachments'] = attachments
            #print(attachments)

    # self.EmailBox.makeMessageFile(_folder_no, no, msg_info)  # make json
    self.EmailBox.result.append(msg_info)
    return True

def main(self):
    fileName = self.fileName
    pstParser = TPST_Parser(fileName)
    pstParser.EmailBox = self
    pstParser.open()

    pstParser.traverseFolder(msgProc)
    pstParser.close()

    return self.result

"""

if __name__ == "__main__":
    print('libpff version :', pypff.get_version())
else:
    from modules.app_email.EmailBoxClass import EmailBox
    EmailBox.main = main
"""
