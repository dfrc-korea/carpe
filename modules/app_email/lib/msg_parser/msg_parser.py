# -*- coding: utf-8 -*-
# !/usr/bin/env python
# Based on MS-OXMSG protocol specification
# ref: https://blogs.msdn.microsoft.com/openspecification/2010/06/20/msg-file-format-rights-managed-email-message-part-2/
# ref: https://msdn.microsoft.com/en-us/library/cc463912(v=EXCHG.80).aspx
import email
import os
import re
from pickle import dumps
from struct import unpack

from modules.app_email.lib.olefile import OleFileIO
from modules.app_email.lib.olefile import isOleFile

from .data_models import DataModel
from .email_builder import EmailFormatter
from .properties.ms_props_id_map import PROPS_ID_MAP

TOP_LEVEL_HEADER_SIZE = 32
RECIPIENT_HEADER_SIZE = 8
ATTACHMENT_HEADER_SIZE = 8
EMBEDDED_MSG_HEADER_SIZE = 24
CONTROL_CHARS = re.compile(r"[\n\r\t]")


class Message(object):
    """
     Class to store Message properties
    """

    def __init__(self, directory_entries):

        self._streams = self._process_directory_entries(directory_entries)
        self._data_model = DataModel()
        self._nested_attachments_depth = 0
        self.properties = self._get_properties()
        self.attachments = self._get_attachments()
        self.recipients = self._get_recipients()

    def as_dict(self):
        """
        returns message attributes as a python dictionary.
        :return: dict
        """
        message_dict = {"attachments": self.attachments, "recipients": self.recipients}
        message_dict.update(self.properties)
        return message_dict

    def _set_property_stream_info(self, ole_file, header_size):
        property_dir_entry = ole_file.openstream("__properties_version1.0")
        version_stream_data = property_dir_entry.read()

        if not version_stream_data:
            raise Exception(
                "Invalid MSG file provided, 'properties_version1.0' stream data is empty."
            )

        if version_stream_data:

            if header_size >= EMBEDDED_MSG_HEADER_SIZE:

                properties_metadata = unpack("8sIIII", version_stream_data[:24])
                if not properties_metadata or not len(properties_metadata) >= 5:
                    raise Exception("'properties_version1.0' stream data is corrupted.")
                self.next_recipient_id = properties_metadata[1]
                self.next_attachment_id = properties_metadata[2]
                self.recipient_count = properties_metadata[3]
                self.attachment_count = properties_metadata[4]

            if (len(version_stream_data) - header_size) % 16 != 0:
                raise Exception(
                    "Property Stream size less header is not exactly divisible by 16"
                )

            self.property_entries_count = (len(version_stream_data) - header_size) / 16

    @staticmethod
    def _process_directory_entries(directory_entries):

        streams = {"properties": {}, "recipients": {}, "attachments": {}}
        for name, stream in directory_entries.items():
            # collect properties
            if "__substg1.0_" in name:
                streams["properties"][name] = stream

            # collect attachments
            elif "__attach_" in name:
                streams["attachments"][name] = stream.kids

            # collect recipients
            elif "__recip_" in name:
                streams["recipients"][name] = stream.kids

            # unknown stream name
            else:
                continue

        return streams

    def _get_properties(self):

        directory_entries = self._streams.get("properties")
        directory_name_filter = "__substg1.0_"
        property_entries = {}
        for directory_name, directory_entry in directory_entries.items():

            if directory_name_filter not in directory_name:
                continue

            if not directory_entry:
                continue

            if isinstance(directory_entry, list):
                directory_values = {}
                for property_entry in directory_entry:
                    property_data = self._get_property_data(
                        directory_name, property_entry, is_list=True
                    )
                    if property_data:
                        directory_values.update(property_data)

                property_entries[directory_name] = directory_values
            else:
                property_data = self._get_property_data(directory_name, directory_entry)
                if property_data:
                    property_entries.update(property_data)
        return property_entries

    def _get_recipients(self):

        directory_entries = self._streams.get("recipients")
        directory_name_filter = "__recip_version1.0_"
        recipient_entries = {}
        for directory_name, directory_entry in directory_entries.items():

            if directory_name_filter not in directory_name:
                continue

            if not directory_entry:
                continue

            if isinstance(directory_entry, list):
                directory_values = {}
                for property_entry in directory_entry:
                    property_data = self._get_property_data(
                        directory_name, property_entry, is_list=True
                    )
                    if property_data:
                        directory_values.update(property_data)

                recipient_address = directory_values.get(
                    "EmailAddress", directory_values.get("SmtpAddress", directory_name)
                )
                recipient_entries[recipient_address] = directory_values
            else:
                property_data = self._get_property_data(directory_name, directory_entry)
                if property_data:
                    recipient_entries.update(property_data)
        return recipient_entries

    def _get_attachments(self):
        directory_entries = self._streams.get("attachments")
        directory_name_filter = "__attach_version1.0_"
        attachment_entries = {}
        for directory_name, directory_entry in directory_entries.items():

            if directory_name_filter not in directory_name:
                continue

            if not directory_entry:
                continue

            if isinstance(directory_entry, list):
                directory_values = {}
                for property_entry in directory_entry:

                    kids = property_entry.kids
                    if kids:
                        embedded_message = Message(property_entry.kids_dict)
                        directory_values["EmbeddedMessage"] = {
                            "properties": embedded_message.properties,
                            "recipients": embedded_message.recipients,
                            "attachments": embedded_message.attachments,
                        }

                    property_data = self._get_property_data(
                        directory_name, property_entry, is_list=True
                    )
                    if property_data:
                        directory_values.update(property_data)

                attachment_entries[directory_name] = directory_values

            else:
                property_data = self._get_property_data(directory_name, directory_entry)
                if property_data:
                    attachment_entries.update(property_data)
        return attachment_entries

    def _get_property_data(self, directory_name, directory_entry, is_list=False):
        directory_entry_name = directory_entry.name
        if is_list:
            stream_name = [directory_name, directory_entry_name]
        else:
            stream_name = [directory_entry_name]

        ole_file = directory_entry.olefile
        property_details = self._get_canonical_property_name(directory_entry_name)
        if not property_details:
            return None

        property_name = property_details.get("name")
        property_type = property_details.get("data_type")
        if not property_type:
            return None

        try:
            raw_content = ole_file.openstream(stream_name).read()
        except IOError:
            raw_content = None
        property_value = self._data_model.get_value(
            raw_content, data_type=property_type
        )

        if property_value:
            property_detail = {property_name: property_value}
        else:
            property_detail = None

        return property_detail

    @staticmethod
    def _get_canonical_property_name(dir_entry_name):
        if not dir_entry_name:
            return None

        if "__substg1.0_" in dir_entry_name:
            name = dir_entry_name.replace("__substg1.0_", "")
            prop_name_id = "0x" + name[0:4]
            prop_details = PROPS_ID_MAP.get(prop_name_id)
            return prop_details

        return None

    def __repr__(self):
        return "Message [%s]" % self.properties.get(
            "InternetMessageId", self.properties.get("Subject")
        )


class Recipient(object):
    """
     class to store recipient attributes
    """

    def __init__(self, recipients_properties):
        self.AddressType = recipients_properties.get("AddressType")
        self.Account = recipients_properties.get("Account")
        self.EmailAddress = recipients_properties.get("SmtpAddress")
        self.DisplayName = recipients_properties.get("DisplayName")
        self.ObjectType = recipients_properties.get("ObjectType")
        self.RecipientType = recipients_properties.get("RecipientType")

    def __repr__(self):
        return "%s (%s)" % (self.DisplayName, self.EmailAddress)


class Attachment(object):
    """
     class to store attachment attributes
    """

    def __init__(self, attachment_properties):

        self.DisplayName = attachment_properties.get("DisplayName")
        self.AttachEncoding = attachment_properties.get("AttachEncoding")
        self.AttachContentId = attachment_properties.get("AttachContentId")
        self.AttachMethod = attachment_properties.get("AttachMethod")
        self.AttachmentSize = format_size(attachment_properties.get("AttachmentSize"))
        self.AttachFilename = attachment_properties.get("AttachFilename")
        self.AttachLongFilename = attachment_properties.get("AttachLongFilename")
        if self.AttachLongFilename:
            self.Filename = self.AttachLongFilename
        else:
            self.Filename = self.AttachFilename
        if self.Filename:
            self.Filename = os.path.basename(self.Filename)
        else:
            self.Filename = "[NoFilename_Method%s]" % self.AttachMethod
        self.data = attachment_properties.get("AttachDataObject")
        self.AttachMimeTag = attachment_properties.get(
            "AttachMimeTag", "application/octet-stream"
        )
        self.AttachExtension = attachment_properties.get("AttachExtension")

    def __repr__(self):
        return "%s (%s / %s)" % (
            self.Filename,
            self.AttachmentSize,
            len(self.data or []),
        )


class MsOxMessage(object):
    """
     Base class for Microsoft Message Object
    """

    def __init__(self, msg_file_path):
        self.msg_file_path = msg_file_path
        self.include_attachment_data = False

        if not self.is_valid_msg_file():
            raise Exception(
                "Invalid file provided, please provide valid Microsoft’s Outlook MSG file."
            )

        with OleFileIO(msg_file_path) as ole_file:
            # process directory entries
            ole_root = ole_file.root
            kids_dict = ole_root.kids_dict

            self._message = Message(kids_dict)
            self._message_dict = self._message.as_dict()

            # process msg properties
            self._set_properties()

            # process msg recipients
            self._set_recipients()

            # process attachments
            self._set_attachments()

    def get_properties(self):

        properties = {}

        for key, value in self._message_dict.items():

            if key == "attachments" and value:
                properties["attachments"] = self.attachments

            elif key == "recipients" and value:
                properties["recipients"] = self.recipients

            else:
                properties[key] = value

        return properties

    def get_properties_as_dict(self):
        return self._message

    def get_message_as_json(self):
        try:
            if not self.include_attachment_data:
                for _, attachment in self._message_dict.get("attachments", []).items():
                    if not isinstance(attachment, dict):
                        continue
                    attachment["AttachDataObject"] = {}
            # Using Pickle to encode message. There is bytes-like objects in it. Therefore cannot be treated by embed json.dumps method
            json_string = dumps(self._message_dict)
            return json_string
        except ValueError:
            return None

    def get_email_mime_content(self):
        email_obj = EmailFormatter(self)
        return email_obj.build_email()

    def save_email_file(self, file_path, file_name):
        email_obj = EmailFormatter(self)
        email_obj.save_file(file_path, file_name)
        return True

    def _set_properties(self):
        property_values = self._message.properties

        # setting generally required properties to easily access using MsOxMessage instance.
        self.subject = property_values.get("Subject")

        header = property_values.get("TransportMessageHeaders")
        self.header = parse_email_headers(header, True)
        self.header_dict = parse_email_headers(header) or {}

        self.created_date = property_values.get("CreationTime")
        self.received_date = property_values.get("ReceiptTime")

        sent_date = property_values.get("DeliverTime")
        if not sent_date:
            sent_date = self.header_dict.get("Date")
        self.sent_date = sent_date

        sender_address = self.header_dict.get("From")
        if not sender_address:
            sender_address = property_values.get("SenderRepresentingSmtpAddress")
        self.sender = sender_address

        reply_to_address = self.header_dict.get("Reply-To")
        if not reply_to_address:
            reply_to_address = property_values.get("ReplyRecipientNames")
        self.reply_to = reply_to_address

        self.message_id = property_values.get("InternetMessageId")

        to_address = self.header_dict.get("TO")
        if not to_address:
            to_address = property_values.get("DisplayTo")
            if not to_address:
                to_address = property_values.get("ReceivedRepresentingSmtpAddress")
        self.to = to_address

        cc_address = self.header_dict.get("CC")
        # if cc_address:
        #     cc_address = [CONTROL_CHARS.sub(" ", cc_add) for cc_add in cc_address.split(",")]
        self.cc = cc_address

        bcc_address = self.header_dict.get("BCC")
        self.bcc = bcc_address

        # prefer HTMl over plain text
        if "Html" in property_values:
            self.body = property_values.get("Html")
        else:
            self.body = property_values.get("Body")

        # Trying to decode body if is bytes obj. This is not the way to go. Quick-fix only.
        # See IMAP specs. Use charset-normalizer, cchardet or chardet as last resort.
        if isinstance(self.body, bytes):
            self.body = self.body.decode("utf-8", "ignore")

        if not self.body and "RtfCompressed" in property_values:
            try:
                import compressed_rtf
            except ImportError:
                compressed_rtf = None
            if compressed_rtf:
                compressed_rtf_body = property_values["RtfCompressed"]
                self.body = compressed_rtf.decompress(compressed_rtf_body)

    def _set_recipients(self):
        recipients = self._message.recipients
        self.recipients = []
        for recipient_name, recipient in recipients.items():

            if self.to and recipient_name in self.to:
                recipient["RecipientType"] = "TO"

            if self.cc and recipient_name in self.cc:
                recipient["RecipientType"] = "CC"

            if self.bcc and recipient_name in self.bcc:
                recipient["RecipientType"] = "BCC"

            if self.reply_to and recipient_name in self.reply_to:
                recipient["RecipientType"] = "ReplyTo"

            self.recipients.append(Recipient(recipient))

    def _set_attachments(self):
        attachments = self._message.attachments
        self.attachments = [Attachment(attach) for attach in attachments.values()]

    def is_valid_msg_file(self):
        if not isOleFile(self.msg_file_path) and not os.path.exists(self.msg_file_path):
            return False

        return True


def format_size(num, suffix="B"):
    if not num:
        return "unknown"
    for unit in ["", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei", "Zi"]:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, "Yi", suffix)


def parse_email_headers(header, raw=False):
    if not header:
        return None

    headers = email.message_from_string(header)
    if raw:
        return headers

    email_address_headers = {
        "To": [],
        "From": [],
        "CC": [],
        "BCC": [],
        "Reply-To": [],
    }

    for addr in email_address_headers.keys():
        for (name, email_address) in email.utils.getaddresses(
            headers.get_all(addr, [])
        ):
            email_address_headers[addr].append("{} <{}>".format(name, email_address))

    parsed_headers = dict(headers)
    parsed_headers.update(email_address_headers)

    return parsed_headers
