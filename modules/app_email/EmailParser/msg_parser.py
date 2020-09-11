import json
import sys, os
_root_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
if os.path.isdir(os.path.join(_root_dir, 'lib', 'msg_parser')): from modules.app_email.lib.msg_parser import MsOxMessage
else: from modules.app_email.EmailParser.msg_parser import MsOxMessage
from modules.app_email.lib.delphi import *
from modules.app_email.EmailBoxClass import makeEmailHeaderType
import email

def main(self):
    fileName = self.fileName
    msg_obj = MsOxMessage(fileName)
    #msg_obj = MsOxMessage(self.fp)

    msg_info = {}
    msg_info['file'] = ExtractFileName(self.fileName)

    clsEmailMessageObject = {}
    msg_info['EmailMessageObject'] = clsEmailMessageObject
    if msg_obj.header == None: 
        clsEmailHeaderType = {}
        msg_dict = msg_obj._message_dict
        clsEmailHeaderType['To'] = list(msg_dict['recipients'].keys())
        clsEmailHeaderType['Subject'] = msg_dict['Subject']
        clsEmailHeaderType['Sender'] = '%s <%s>' % (msg_dict['SenderName'], msg_dict['SenderEmailAddress'])
        clsEmailMessageObject['Header'] = clsEmailHeaderType
    else: clsEmailMessageObject['Header'] = makeEmailHeaderType(msg_obj.header)
    clsEmailMessageObject['Body'] = msg_obj.body

    # 첨부 처리
    attachments = []
    for attachment in msg_obj.attachments:
        fn = attachment.Filename
        file_info = {}
        if attachment.data == None: sz = 0
        else: sz = len(attachment.data)
        # 첨부 파일 생성
        if sz > 0:
            file_info['name'] = fn
            file_info['size'] = len(attachment.data)
            attachments.append(file_info)
            f = open(os.path.join(self.createAttachmentDir(1, 1), fn), 'wb')
            f.write(attachment.data)
            f.close()

    if len(attachments) > 0:
        clsEmailMessageObject['Attachments'] = attachments
        #print(attachments)

    # self.makeMessageFile(1, 1, msg_info)  # export json

    return msg_info

    pass

"""

if __name__ == "__main__":
    print(dir(MsOxMessage))
else:
    from modules.app_email.EmailBoxClass import EmailBox
    EmailBox.main = main
"""
