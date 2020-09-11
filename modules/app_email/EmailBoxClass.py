import sys, os
from modules.app_email.lib.yjSysUtils import *
from modules.app_email.lib.delphi import *


import email, mailbox
from email.header import Header as TEmailHeader, decode_header, make_header
from email.parser import HeaderParser as TEmailHeaderParser
import re
import json

def parseReceivedLine(received):
    """  메일 헤더의 'Received' 헤더들을 분석한다.  """
    received = ' '.join(received.split())
    received = re.split('(\(|\)|;|from |by |via |with |for |id | )', received)
    received = [v for v in received if v not in ['']]

    result = {}
    key = ''
    val = ''
    inParenthesis = 0
    n = 0
    for v in received:
        if v == '(': 
            if inParenthesis < 0: inParenthesis = 0
            inParenthesis += 1
        elif v == ')': 
            inParenthesis -= 1
        elif (inParenthesis <= 0) and (len(v) > 2) and v.endswith(' '):
            if key: 
                n += 1
                result[key] = val
            if debug_mode: assert v != ';'
            key = v
            val = ''
            result[key] = val
            continue
        if key and (v == ';'):
            n += 1
            result[key] = val
            key = ''
            val = ''
            continue
        val += v

    if key == '':
        cRe = re.compile('(Sun, |Mon, |Tue, |Wed, |Thu, |Fri, |Sat, )', re.I)  # 대소문자 구분 안함 (re.I)
        l = cRe.split(val)   # re.split('(Sun, |Mon, |Tue, |Wed, |Thu, |Fri, |Sat, )', val)
        result['timestamp'] = ''.join(l)
    else:
        result[key] = val

    d = ('from ', 'by ', 'via ', 'with ', 'for ', 'id ', 'timestamp')
    t = ('From', 'By', 'Via', 'With', 'For', 'ID', 'Timestamp')
    receivedLine = {'From': '', 'By': '', 'Via': '', 'With': '', 'For': '', 'ID': '', 'Timestamp': ''}
    for i in range(0, len(d)):
        v = result.get(d[i])
        if v: receivedLine[t[i]] = v.strip()
    if n == 0: receivedLine = {}
    return receivedLine

def decode_text(v):
    h = make_header(decode_header(v))
    if type(h) is TEmailHeader:
        v = [_[0] for _ in h._chunks if True]
        return ' '.join(v)
    else: return h

def decode_body(body, charset):

    def _decode_body(body):
        v = None
        try:
            v = body.decode('cp949')
        except UnicodeDecodeError:
            v = body.decode('utf-8')
        finally:
            if v == None: v = body.decode('ascii', errors="ignore")
            return v

    if type(body) is str: v = body
    else:
        try:
            if charset == 'euc-kr':  v = body.decode('cp949')
            elif charset == 'utf-8': v = body.decode('utf-8')
            else: v = _decode_body(body)
        except Exception as e:
            v = _decode_body(body)
    return v

def get_content_type(msg):
    """
    Content-Type: text/html; charset=euc-kr
    Content-Type: text/plain; charset="UTF-8"
    Content-Transfer-Encoding: 8bit
    Content-Transfer-Encoding: base64
    """
    if debug_mode: assert type(msg) in (email.message.Message, mailbox.mboxMessage)
    v = msg['content-type']
    r = []
    if v == None: return r
    p = v.find(';')
    if p != -1: r.append(v[0: p])
    else: r.append('')
    sub = 'charset='
    p = v.rfind(sub)
    if p != -1: v = v[p + len(sub):].strip('\'"').lower()
    else: v = ''
    r.append(v)
    return r

def parseEmailHeader(headers):
    if debug_mode: assert type(headers) is str
    headerParser = TEmailHeaderParser()
    return headerParser.parsestr(headers)

def makeEmailHeaderType(headers):
    """ 메일 헤더를 분석한다. """

    def parseEmailRecipients(v):
        """ EmailRecipients 를 분석한다. """
        if v == None: v = []
        if type(v) is str:
            v = v.split(',')
            for i in range(0, len(v)):
                try:
                    v[i] = decode_text(v[i].strip())
                except:
                    v[i] = ''
        return v

    def parseEmailReceivedLines(receivedLines):
        """ receivedLines를 분석한다. """
        v = []
        if type(receivedLines) is list:
            for receivedLine in receivedLines:
                t = parseReceivedLine(receivedLine)
                if t: v.append(t)
        return v

    if debug_mode: type(headers) is email.message.Message
    h = headers

    if debug_mode:
        assert type(h) in (email.message.Message, mailbox.mboxMessage)
    receivedLines = []
    for _, (k, v) in enumerate(h.items()):
        if k.lower() == 'received':
            receivedLines.append(v)

    clsEmailHeaderType = {}
    clsEmailHeaderType['Received_Lines'] = parseEmailReceivedLines(receivedLines)
    clsEmailHeaderType['To'] = parseEmailRecipients(h['to'])
    clsEmailHeaderType['CC'] = parseEmailRecipients(h['cc'])
    clsEmailHeaderType['BCC'] = parseEmailRecipients(h['bcc'])
    clsEmailHeaderType['From'] = h['from']
    clsEmailHeaderType['Subject'] = h['subject']
    clsEmailHeaderType['In_Reply_to'] = h['in-reply-to']
    clsEmailHeaderType['Date'] = h['date']
    clsEmailHeaderType['Message_ID'] = h['message-id']
    clsEmailHeaderType['Sender'] = h['sender']
    clsEmailHeaderType['Reply_To'] = h['reply-to']
    clsEmailHeaderType['Errors_To'] = h['error-to']
    clsEmailHeaderType['Boundary'] = h['boundary']
    clsEmailHeaderType['Content_Type'] = h['content-type']
    clsEmailHeaderType['MIME_Version'] = h['mime-version']
    clsEmailHeaderType['Precedence'] = h['precedence']
    clsEmailHeaderType['User_Agent'] = h['user-agent']
    clsEmailHeaderType['X_Mailer'] = h['x-mailer']
    clsEmailHeaderType['X_Originating_IP'] = h['x-originating-ip']
    clsEmailHeaderType['X_Priority'] = h['x-priority']
    for i, (k, v) in enumerate(clsEmailHeaderType.items()):
        if v == None: clsEmailHeaderType[k] = ''
        elif type(v) is str:
            clsEmailHeaderType[k] = decode_text(v)
    return clsEmailHeaderType


class TEmailBox:
    def __init__(self):
        self.main = None
        self.fileName = ''
        self.appDir = ''
        self.exportDir = ''
        self.result = list()

    def __del__(self):
        pass

    def createDir(self, dir):
        if not os.path.isdir(dir): os.makedirs(os.path.join(dir))
        return True

    """
      sam.pst :
        sam.pst.cls\
            msg_001_000001.json
            msg_001_000001.attachments\
                a.doc
                b.xls
            msg_001_000002.json
                ...
    """
    def makeMessageFile(self, folder_no, msg_no, msg_obj, file_ext = '.json'):
        """ msg_obj 데이터를 json 포맷으로 파일에 저장한다. """
        if debug_mode: assert type(msg_obj) is dict
        export_dir = self.exportDir
        fn = '%s%smsg_%.3d_%.6d%s' % (export_dir, PathDelimiter, folder_no, msg_no, file_ext)   # fn = '<export_dir>\msg_001_000001.json'
        if debug_mode: assert DirectoryExists(export_dir)
        f = open(fn, 'w', encoding='utf-8')
        f.write(json.dumps(msg_obj, indent = 3, ensure_ascii = False))
        f.close()
        #print(fn)
        return fn

    def getAttachmentDir(self, folder_no, msg_no):
        export_dir = self.exportDir
        return '%s%smsg_%.3d_%.6d.attachments' % (export_dir, PathDelimiter, folder_no, msg_no)   # fn = '<export_dir>\msg_001_000001.attachments'

    def createAttachmentDir(self, folder_no, msg_no):
        dir = self.getAttachmentDir(folder_no, msg_no)
        if not os.path.isdir(dir): os.makedirs(os.path.join(dir))
        return dir

    def parseEML(self, folder_no, msg_no, msg):
        if debug_mode: assert type(msg) in (email.message.Message, mailbox.mboxMessage)
        msg_info = {}
        msg_info['file'] = ExtractFileName(self.fileName)

        clsEmailMessageObject = {}
        msg_info['EmailMessageObject'] = clsEmailMessageObject
        h = makeEmailHeaderType(msg)
        clsEmailMessageObject['Header'] = h
        clsEmailMessageObject['Body'] = ''
        if (h['To'] == h['CC'] == h['BCC'] == h['Received_Lines'] == []) and (h['From'] == h['Subject'] == h['Sender'] == ''):
            print('\nWarning: Unnormal format.\n')

        i = 0
        parts = []
        for part in msg.walk():
            content_maintype = part.get_content_maintype()
            if not content_maintype in ['text', 'application', 'message']:
                continue
            parts.append(part)

        # 메일 내용 (Body)
        plain_text_body = None
        html_body = None
        i = 0
        body = ''
        for part in parts:
            if part.get_content_maintype() in ['application', 'message']: break
            content_type = get_content_type(part)
            charset = part.get_content_charset()
            body = part.get_payload(decode=1)
            body = decode_body(body, charset)
            if part.get_content_type() == 'text/html': html_body = body
            else: plain_text_body = body
            i += 1

        if html_body != None: body = html_body
        else: body = plain_text_body
        clsEmailMessageObject['Body'] = body

        # 첨부 처리
        attachments = []
        attach_dir = self.getAttachmentDir(folder_no, msg_no)
        for i in range(i, len(parts)):
            part = parts[i]
            if not part.get_content_maintype() in ['application', 'message']: continue
            fname = part.get_filename()
            if not type(fname) is str: continue
            fname = decode_text(fname)
            content_type = part.get_content_maintype()
            if content_type == 'message':
                if debug_mode: assert type(part.get_payload()[0]) is email.message.Message
                continue
            else:
                assert content_type == 'application', content_type
                fdata = part.get_payload(decode=True,)

            file_info = {}
            file_info['name'] = os.path.join(os.path.basename(attach_dir), fname)
            file_info['size'] = len(fdata)
            attachments.append(file_info)

            # 첨부 파일 생성
            if self.createDir(attach_dir):
                f = open(os.path.join(attach_dir, fname), 'wb')
                f.write(fdata)
                f.close()

        if len(attachments) > 0:
            clsEmailMessageObject['Attachments'] = attachments
            #print(attachments)
        return msg_info

    def parse(self, file_ext = None):
        EmailParserDir = 'EmailParser'
        module = '%s.%s_parser' % (EmailParserDir, file_ext)
        if __debug__: 
            v = '%s/%s/%s_parser.py' % (self.appDir, EmailParserDir, file_ext.strip('.'))
            assert FileExists(v), '[Error] %s 모듈이 없습니다.' % os.path.basename(v)

        #import importlib
        #importlib.import_module("modules.app_email." + module)
        #loadModule(module)   # msg_file, pst_file, ost_file, eml_file, ...
        export_dir = self.exportDir + '%s.cls' % self.fileName[self.fileName.rfind(os.path.sep):]
        #self.exportDir = export_dir
        if not DirectoryExists(export_dir):
            CreateDir(export_dir)

        """try:
            if file_ext == "eml":
                from modules.app_email.EmailParser.eml_parser import main
                result = main(self)
            elif file_ext == "mbox":
                from modules.app_email.EmailParser.mbox_parser import main
                result = main(self)
            elif file_ext == "msg":
                from modules.app_email.EmailParser.msg_parser import main
                result = main(self)
            elif file_ext == "ost" or file_ext == "pst":
                from modules.app_email.EmailParser.pst_parser import main
                result = main(self)
            #result = self.main(self)
            return result
        except Exception as e:
            print("[EmailBoxClass.py parse(), " + self.fileName[self.fileName.rfind(os.path.sep):] + " Error: " + str(e))
            #raise NotImplemented
        """
        if file_ext == "eml":
            from modules.app_email.EmailParser.eml_parser import main
            result = main(self)
        elif file_ext == "mbox":
            from modules.app_email.EmailParser.mbox_parser import main
            result = main(self)
        elif file_ext == "msg":
            from modules.app_email.EmailParser.msg_parser import main
            result = main(self)
        elif file_ext == "ost" or file_ext == "pst":
            from modules.app_email.EmailParser.pst_parser import main
            result = main(self)

        return result


        #return False

            
EmailBox = TEmailBox()
