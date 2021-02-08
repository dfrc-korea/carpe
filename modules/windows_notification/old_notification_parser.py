# Parse the Windows 10 ( & 8 ) notifications database
# Copyright (C) 2016  Yogesh Khatri <yogesh@swiftforensics.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You can get a copy of the complete license here:
#  <http://www.gnu.org/licenses/>.
#
# Author       : Yogesh Khatri <yogesh@swiftforensics.com>
# Last Updated : May 2016
# Version      : 0.3
# Required     : Python 3
#
# Notes -
# Parse the Windows 10 notifications database stored at:
# \Users\<user>\Appdata\Local\Microsoft\Windows\Notifications\appdb.dat
# This currently only works on appdb.dat version 3 (Windows 10)
#


import sys
import traceback
import struct
import re
import codecs
import xml.etree.ElementTree as ET
from datetime import datetime


# Decode the 64 bit windows FILETIME timestamp to python datetime
# Highest value is 3001-01-01 20:59:59.999992    441797651999999961 0x0621949FAE0FC7D9
# Lowest  value is 1969-12-31 12:00:00           116444303999999991 0x019DB17A40099FF7
# Limitation is due to function utcfromtimestamp()
def decode_time_stamp(filetimeQword):
    try:
        if filetimeQword != 0:
            return datetime.utcfromtimestamp(filetimeQword / 10000000 - 11644473600).strftime('%Y-%m-%d %H:%M:%S')
    except:
        msg = ""
        if filetimeQword > 441797651999999961:
            msg = "(Date is greater than 3001-01-01)"
        elif filetimeQword < 116444303999999991:
            msg = "(Date is older than 1970-01-01)"
        # print("Error converting timestamp, original value was : 0x%X %s" % (filetimeQword, msg))
    return None


def read_null_terminated_ascii_string(buffer, maxStringSize):
    str = ""
    pos = 0
    while pos < maxStringSize:
        byte = struct.unpack_from("<b", buffer, pos)[0]
        if byte == 0:
            break
        str += "%c" % byte
        pos += 1
    return str


# Check whether the database has a valid signature and version number
def is_valid_app_db(file):
    data = file.read(8)
    signature, version = struct.unpack_from("<2I", data)

    if (signature != 0x57504E44) or (version != 3):  # 'DNPW'
        return False
    return True


# Parses badge and push URI
class Badge:
    def __init__(self):
        self.Xml = ""  # from badge
        self.URI = ""
        self.TimeStamp1 = None
        self.TimeStamp2 = None
        self.NotificationId = ""  # from badge
        self.TimeStamp3 = None  # from badge
        self.Unknown = None  # from badge

    def ParseBadge(self, badgeData):
        self.TimeStamp1 = decode_time_stamp(struct.unpack_from("<Q", badgeData[0:8])[0])
        self.TimeStamp2 = decode_time_stamp(struct.unpack_from("<Q", badgeData[8:16])[0])
        self.URI = read_null_terminated_ascii_string(badgeData[16:1024 + 16], 1024)

        self.NotificationId = struct.unpack_from("<I", badgeData[0x818:0x81C])[0]
        self.TimeStamp3 = decode_time_stamp(struct.unpack_from("<Q", badgeData[0x820:0x828])[0])
        self.Unknown = struct.unpack_from("<H", badgeData[0x828:0x82A])[0]
        contentLength = struct.unpack_from("<H", badgeData[0x82A:0x82C])[0]
        s = badgeData[0x82C: 0x82C + contentLength]
        self.Xml = s.decode('utf-8')


class Toast:
    def __init__(self):
        self.Xml = ""
        self.NotificationId = ""
        self.TimeStamp1 = None
        self.TimeStamp2 = None
        self.Type = 0
        self.Index = 0
        self.Name1 = ""
        self.Name2 = ""

    def ParseToast(self, toastData, toastXmlData):
        self.NotificationId = struct.unpack_from("<I", toastData[0:4])[0]
        self.TimeStamp1 = decode_time_stamp(struct.unpack_from("<Q", toastData[8:16])[0])
        self.TimeStamp2 = decode_time_stamp(struct.unpack_from("<Q", toastData[16:24])[0])
        self.Type, self.Index = struct.unpack_from("<2B", toastData[24:26])
        contentLength = struct.unpack_from("<H", toastData[26:28])[0]
        s1 = toastData[28:62]
        s2 = toastData[62:96]
        self.Name1 = (s1.decode('utf-16')).rstrip("\x00")
        self.Name2 = (s2.decode('utf-16')).rstrip("\x00")
        if (contentLength > 0):
            xml = toastXmlData[(self.Index * 0x1400):(self.Index * 0x1400) + contentLength]
            self.Xml = xml.decode('utf-8')


class Tile(object):
    def __init__(self):
        self.Xml = ""
        self.NotificationId = 0
        self.TimeStamp1 = None
        self.TimeStamp2 = None
        self.Type = 0
        self.Index = 0
        self.Name = ""

    # tileData = Tile Descriptor structure
    # tileXmlData = All 5 Xml fields, choose one depending on index in tile descriptor
    def ParseTile(self, tileData, tileXmlData):
        self.NotificationId = struct.unpack_from("<I", tileData[0:4])[0]
        self.TimeStamp1 = decode_time_stamp(struct.unpack_from("<Q", tileData[8:16])[0])
        self.TimeStamp2 = decode_time_stamp(struct.unpack_from("<Q", tileData[16:24])[0])
        self.Type, self.Index = struct.unpack_from("<2B", tileData[24:26])
        contentLength = struct.unpack_from("<H", tileData[26:28])[0]
        s = tileData[28:64]
        self.Name = (s.decode('utf-16')).rstrip("\x00")
        if (contentLength > 0):
            xml = tileXmlData[(self.Index * 0x1400):(self.Index * 0x1400) + contentLength]
            self.Xml = xml.decode('utf-8')


class Chunk(object):

    def __init__(self, filepos):
        self.FilePos = filepos
        self.Tiles = []
        self.Toasts = []
        self.Badge = None
        self.Flags = None

    def IsChunkUsed(self, chunkData):
        flags = struct.unpack_from("<8B", chunkData[0x20:0x28])
        if flags[0] == 0:
            return False
        return True

    def ParseChunk(self, chunkData):
        # print("Processing chunk @ 0x%X" % self.FilePos)
        # First 20 bytes are only populated in first chunk, as file header
        signature, version, lastNotificationDateQword, nextNotificationId, unknown = struct.unpack_from("<4sIQII",
                                                                                                        chunkData[:24])
        self.Flags = struct.unpack_from("<8B", chunkData[0x20:0x28])

        # parse Push URI and Badge
        self.Badge = Badge()
        self.Badge.ParseBadge(chunkData[0x28:0x958])

        # parse TILES now
        for i in range(0, 5):
            tile = Tile()
            tile.ParseTile(chunkData[0x958 + (i * 0x40): 0x958 + ((i + 1) * 0x40)], chunkData[0xA98:0x6E98])
            if not ((tile.NotificationId == 0) and (tile.Type == 0)):
                self.Tiles.append(tile)

        # parse TOASTS now
        numToastEntries = self.Flags[4]
        for i in range(0, numToastEntries):
            toast = Toast()
            toast.ParseToast(chunkData[0x6E98 + (i * 0x60): 0x6E98 + ((i + 1) * 0x60)], chunkData[0x9418:0x23810])
            self.Toasts.append(toast)


def ParseDb(file, Chunks):
    file.seek(0)
    filepos = 0
    while True:
        chunkData = file.read(0x23810)
        if len(chunkData) < 0x23810:
            break
        else:
            chunk = Chunk(filepos)
            if chunk.IsChunkUsed(chunkData):  # Is this efficient? Find out!
                chunk.ParseChunk(chunkData)
                Chunks.append(chunk)
        filepos += 0x23810


def process_db(path, chunks):
    # print("\nProcessing: " + path)
    try:
        with open(path, "rb") as file:
            # print("Opened notifications db " + file.name)
            if is_valid_app_db(file):
                ParseDb(file, chunks)
                return True
            else:
                print("Not a valid db file. This only works with a windows 10 appdb.dat file.")

    except Exception as ex:
        # err = sys.exc_info()[0]
        print("Error opening Notification database: " + str(ex))
        traceback.print_exc()
    return False


def itertext(tree):
    tag = tree.tag
    if not isinstance(tag, str) and tag is not None:
        return
    if tree.text:
        yield tree.text
    for e in tree:
        for s in e.itertext():
            yield s
        if e.tail:
            yield e.tail


# http://stackoverflow.com/questions/24045892/why-does-elementtree-reject-utf-16-xml-declarations-with-encoding-incorrect
# ElementTree treats input as binary need to encode utf16 to binary.

def get_xml_content(xml):
    _input = xml.replace("\r", "").replace("\n", "")
    content = ""
    if len(_input) > 0:
        try:
            if re.search('utf-16', _input, re.IGNORECASE):
                _input = _input.encode('utf-16-le')
            else:
                _input = _input.encode('utf-8')
            tree = ET.fromstring(_input)
            content = " ".join(itertext(tree))
        except:
            print("XML err for: " + _input + " LEN=" + str(len(_input)))
            traceback.print_exc()
            pass
    return " ".join(content.split())  # Removes extra spaces by doing split and join.