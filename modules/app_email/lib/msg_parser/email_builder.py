# -*- coding: utf-8 -*-
import codecs
import os
import unicodedata
from email import encoders
from email.header import Header
from email.mime.audio import MIMEAudio
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


class EmailFormatter(object):
    def __init__(self, msg_object):
        self.msg_obj = msg_object
        self.message = MIMEMultipart()
        self.message.set_charset("utf-8")

    def build_email(self):

        # Setting Message ID
        self.message.set_param("Message-ID", self.msg_obj.message_id)

        # Encoding for unicode subject
        self.message["Subject"] = Header(self.msg_obj.subject, charset="UTF-8")

        # Setting Date Time
        # Returns a date string as specified by RFC 2822, e.g.: Fri, 09 Nov 2001 01:08:47 -0000
        self.message["Date"] = str(self.msg_obj.sent_date)

        # At least one recipient is required
        # Required fromAddress
        from_address = flatten_list(self.msg_obj.sender)
        if from_address:
            self.message["From"] = from_address

        to_address = flatten_list(self.msg_obj.header_dict.get("To"))
        if to_address:
            self.message["To"] = to_address

        cc_address = flatten_list(self.msg_obj.header_dict.get("CC"))
        if cc_address:
            self.message["CC"] = cc_address

        bcc_address = flatten_list(self.msg_obj.header_dict.get("BCC"))
        if bcc_address:
            self.message["BCC"] = bcc_address

        # Add reply-to
        reply_to = flatten_list(self.msg_obj.reply_to)
        if reply_to:
            self.message.add_header("reply-to", reply_to)
        else:
            self.message.add_header("reply-to", from_address)

        # Required Email body content
        body_content = self.msg_obj.body
        if body_content:
            if "<html>" in body_content:
                body_type = "html"
            else:
                body_type = "plain"

            body = MIMEText(_text=body_content, _subtype=body_type, _charset="UTF-8")
            self.message.attach(body)
        else:
            raise KeyError("Missing email body")

        # Add message preamble
        self.message.preamble = "You will not see this in a MIME-aware mail reader.\n"

        # Optional attachments
        attachments = self.msg_obj.attachments
        if len(attachments) > 0:
            # Some issues here, where data is None or is bytes-like object.
            self._process_attachments(self.msg_obj.attachments)

        # composed email
        composed = self.message.as_string()

        return composed

    def save_file(self, file_path, file_name):
        eml_content = self.build_email()
        #file_name = str(self.message["Subject"]) + ".eml"
        eml_file_path = os.path.join(file_path, file_name)
        with codecs.open(eml_file_path, mode="wb+", encoding="utf-8") as eml_file:
            eml_file.write(eml_content)

        return eml_file_path

    def _process_attachments(self, attachments):
        for attachment in attachments:
            ctype = attachment.AttachMimeTag
            data = attachment.data
            filename = attachment.Filename
            maintype, subtype = ctype.split("/", 1)

            if data is None:
                continue

            if isinstance(data, bytes):
                data = data.decode("utf-8", "ignore")

            if maintype == "text" or "message" in maintype:
                attach = MIMEText(data, _subtype=subtype)
            elif maintype == "image":
                attach = MIMEImage(data, _subtype=subtype)
            elif maintype == "audio":
                attach = MIMEAudio(data, _subtype=subtype)
            else:
                attach = MIMEBase(maintype, subtype)
                attach.set_payload(data)

                # Encode the payload using Base64
                encoders.encode_base64(attach)
            # Set the filename parameter
            base_filename = os.path.basename(filename)
            attach.add_header("Content-ID", "<{}>".format(base_filename))
            attach.add_header(
                "Content-Disposition", "attachment", filename=base_filename
            )
            self.message.attach(attach)


def flatten_list(string_list):
    if string_list and isinstance(string_list, list):
        string = ",".join(string_list)
        return string
    return None


def normalize(input_str):
    if not input_str:
        return input_str
    try:
        if isinstance(input_str, list):
            input_str = [s.decode("ascii") for s in input_str]
        else:
            input_str.decode("ascii")
        return input_str
    except UnicodeError:
        if isinstance(input_str, bytes):
            input_str = input_str.decode("utf-8", "ignore")
        normalized = unicodedata.normalize("NFKD", input_str)
        if not normalized.strip():
            normalized = input_str.encode("unicode-escape").decode("utf-8")

        return normalized
