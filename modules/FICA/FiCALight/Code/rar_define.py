# -*- coding:utf-8 -*-

# rarfile.py
#
# Copyright (c) 2005-2016  Marko Kreen <markokr@gmail.com>
#
# Permission to use, copy, modify, and/or distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
# OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

from __future__ import division, print_function

import sys
import os
import errno
import struct

from struct import pack, unpack, Struct
from binascii import crc32, hexlify
from tempfile import mkstemp
from subprocess import Popen, PIPE, STDOUT
from io import RawIOBase
from hashlib import sha1, sha256
from hmac import HMAC
from datetime import datetime, timedelta, tzinfo

from structureReader import structureReader as sr


# fixed offset timezone, for UTC
try:
    from datetime import timezone
except ImportError:
    class timezone(tzinfo):
        """Compat timezone."""
        __slots__ = ('_ofs', '_name')
        _DST = timedelta(0)

        def __init__(self, offset, name):
            super(timezone, self).__init__()
            self._ofs, self._name = offset, name

        def utcoffset(self, dt):
            return self._ofs

        def tzname(self, dt):
            return self._name

        def dst(self, dt):
            return self._DST

# only needed for encryped headers
try:
    try:
        from cryptography.hazmat.primitives.ciphers import algorithms, modes, Cipher
        from cryptography.hazmat.backends import default_backend
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.kdf import pbkdf2

        class AES_CBC_Decrypt(object):
            """Decrypt API"""
            def __init__(self, key, iv):
                ciph = Cipher(algorithms.AES(key), modes.CBC(iv), default_backend())
                self.decrypt = ciph.decryptor().update

        def pbkdf2_sha256(password, salt, iters):
            """PBKDF2 with HMAC-SHA256"""
            ctx = pbkdf2.PBKDF2HMAC(hashes.SHA256(), 32, salt, iters, default_backend())
            return ctx.derive(password)

    except ImportError:
        from Crypto.Cipher import AES
        from Crypto.Protocol import KDF

        class AES_CBC_Decrypt(object):
            """Decrypt API"""
            def __init__(self, key, iv):
                self.decrypt = AES.new(key, AES.MODE_CBC, iv).decrypt

        def pbkdf2_sha256(password, salt, iters):
            """PBKDF2 with HMAC-SHA256"""
            return KDF.PBKDF2(password, salt, 32, iters, hmac_sha256)

    _have_crypto = 1
except ImportError:
    _have_crypto = 0

try:
    try:
        from hashlib import blake2s
        _have_blake2 = True
    except ImportError:
        from pyblake2 import blake2s
        _have_blake2 = True
except ImportError:
    _have_blake2 = False

# compat with 2.x
if sys.hexversion < 0x3000000:
    def rar_crc32(data, prev=0):
        """CRC32 with unsigned values.
        """
        if (prev > 0) and (prev & 0x80000000):
            prev -= (1 << 32)
        res = crc32(data, prev)
        if res < 0:
            res += (1 << 32)
        return res
    tohex = hexlify
    _byte_code = ord
else:  # pragma: no cover
    def tohex(data):
        """Return hex string."""
        return hexlify(data).decode('ascii')
    rar_crc32 = crc32
    unicode = str
    _byte_code = int   # noqa

# don't break 2.6 completely
if sys.hexversion < 0x2070000:
    memoryview = lambda x: x  # noqa


#: default fallback charset
DEFAULT_CHARSET = "windows-1252"

#: list of encodings to try, with fallback to DEFAULT_CHARSET if none succeed
TRY_ENCODINGS = ('utf8', 'utf-16le')

#: 'unrar', 'rar' or full path to either one
UNRAR_TOOL = "unrar"

#: Command line args to use for opening file for reading.
OPEN_ARGS = ('p', '-inul')

#: Command line args to use for extracting file to disk.
EXTRACT_ARGS = ('x', '-y', '-idq')

#: args for testrar()
TEST_ARGS = ('t', '-idq')

#
# Allow use of tool that is not compatible with unrar.
#
# By default use 'bsdtar' which is 'tar' program that
# sits on top of libarchive.
#
# Problems with libarchive RAR backend:
# - Does not support solid archives.
# - Does not support password-protected archives.
#

ALT_TOOL = 'bsdtar'
ALT_OPEN_ARGS = ('-x', '--to-stdout', '-f')
ALT_EXTRACT_ARGS = ('-x', '-f')
ALT_TEST_ARGS = ('-t', '-f')
ALT_CHECK_ARGS = ('--help',)

#ALT_TOOL = 'unar'
#ALT_OPEN_ARGS = ('-o', '-')
#ALT_EXTRACT_ARGS = ()
#ALT_TEST_ARGS = ('-test',) # does not work
#ALT_CHECK_ARGS = ('-v',)

#: whether to speed up decompression by using tmp archive
USE_EXTRACT_HACK = 1

#: limit the filesize for tmp archive usage
HACK_SIZE_LIMIT = 20 * 1024 * 1024

#: Separator for path name components.  RAR internally uses '\\'.
#: Use '/' to be similar with zipfile.
PATH_SEP = '/'

##
## rar constants
##

# block types
RAR_BLOCK_MARK          = 0x72  # r
RAR_BLOCK_MAIN          = 0x73  # s
RAR_BLOCK_FILE          = 0x74  # t
RAR_BLOCK_OLD_COMMENT   = 0x75  # u
RAR_BLOCK_OLD_EXTRA     = 0x76  # v
RAR_BLOCK_OLD_SUB       = 0x77  # w
RAR_BLOCK_OLD_RECOVERY  = 0x78  # x
RAR_BLOCK_OLD_AUTH      = 0x79  # y
RAR_BLOCK_SUB           = 0x7a  # z
RAR_BLOCK_ENDARC        = 0x7b  # {

# flags for RAR_BLOCK_MAIN
RAR_MAIN_VOLUME         = 0x0001
RAR_MAIN_COMMENT        = 0x0002
RAR_MAIN_LOCK           = 0x0004
RAR_MAIN_SOLID          = 0x0008
RAR_MAIN_NEWNUMBERING   = 0x0010
RAR_MAIN_AUTH           = 0x0020
RAR_MAIN_RECOVERY       = 0x0040
RAR_MAIN_PASSWORD       = 0x0080
RAR_MAIN_FIRSTVOLUME    = 0x0100
RAR_MAIN_ENCRYPTVER     = 0x0200

# flags for RAR_BLOCK_FILE
RAR_FILE_SPLIT_BEFORE   = 0x0001
RAR_FILE_SPLIT_AFTER    = 0x0002
RAR_FILE_PASSWORD       = 0x0004
RAR_FILE_COMMENT        = 0x0008
RAR_FILE_SOLID          = 0x0010
RAR_FILE_DICTMASK       = 0x00e0
RAR_FILE_DICT64         = 0x0000
RAR_FILE_DICT128        = 0x0020
RAR_FILE_DICT256        = 0x0040
RAR_FILE_DICT512        = 0x0060
RAR_FILE_DICT1024       = 0x0080
RAR_FILE_DICT2048       = 0x00a0
RAR_FILE_DICT4096       = 0x00c0
RAR_FILE_DIRECTORY      = 0x00e0
RAR_FILE_LARGE          = 0x0100
RAR_FILE_UNICODE        = 0x0200
RAR_FILE_SALT           = 0x0400
RAR_FILE_VERSION        = 0x0800
RAR_FILE_EXTTIME        = 0x1000
RAR_FILE_EXTFLAGS       = 0x2000

# flags for RAR_BLOCK_ENDARC
RAR_ENDARC_NEXT_VOLUME  = 0x0001
RAR_ENDARC_DATACRC      = 0x0002
RAR_ENDARC_REVSPACE     = 0x0004
RAR_ENDARC_VOLNR        = 0x0008

# flags common to all blocks
RAR_SKIP_IF_UNKNOWN     = 0x4000
RAR_LONG_BLOCK          = 0x8000

# Host OS types
RAR_OS_MSDOS = 0
RAR_OS_OS2   = 1
RAR_OS_WIN32 = 2
RAR_OS_UNIX  = 3
RAR_OS_MACOS = 4
RAR_OS_BEOS  = 5

# Compression methods - '0'..'5'
RAR_M0 = 0x30
RAR_M1 = 0x31
RAR_M2 = 0x32
RAR_M3 = 0x33
RAR_M4 = 0x34
RAR_M5 = 0x35

#
# RAR5 constants
#

RAR5_BLOCK_MAIN = 1
RAR5_BLOCK_FILE = 2
RAR5_BLOCK_SERVICE = 3
RAR5_BLOCK_ENCRYPTION = 4
RAR5_BLOCK_ENDARC = 5

RAR5_BLOCK_FLAG_EXTRA_DATA = 0x01
RAR5_BLOCK_FLAG_DATA_AREA = 0x02
RAR5_BLOCK_FLAG_SKIP_IF_UNKNOWN = 0x04
RAR5_BLOCK_FLAG_SPLIT_BEFORE = 0x08
RAR5_BLOCK_FLAG_SPLIT_AFTER = 0x10
RAR5_BLOCK_FLAG_DEPENDS_PREV = 0x20
RAR5_BLOCK_FLAG_KEEP_WITH_PARENT = 0x40

RAR5_MAIN_FLAG_ISVOL = 0x01
RAR5_MAIN_FLAG_HAS_VOLNR = 0x02
RAR5_MAIN_FLAG_SOLID = 0x04
RAR5_MAIN_FLAG_RECOVERY = 0x08
RAR5_MAIN_FLAG_LOCKED = 0x10

RAR5_FILE_FLAG_ISDIR = 0x01
RAR5_FILE_FLAG_HAS_MTIME = 0x02
RAR5_FILE_FLAG_HAS_CRC32 = 0x04
RAR5_FILE_FLAG_UNKNOWN_SIZE = 0x08

RAR5_COMPR_SOLID = 0x40

RAR5_ENC_FLAG_HAS_CHECKVAL = 0x01

RAR5_ENDARC_FLAG_NEXT_VOL = 0x01

RAR5_XFILE_ENCRYPTION = 1
RAR5_XFILE_HASH = 2
RAR5_XFILE_TIME = 3
RAR5_XFILE_VERSION = 4
RAR5_XFILE_REDIR = 5
RAR5_XFILE_OWNER = 6
RAR5_XFILE_SERVICE = 7

RAR5_XTIME_UNIXTIME = 0x01
RAR5_XTIME_HAS_MTIME = 0x02
RAR5_XTIME_HAS_CTIME = 0x04
RAR5_XTIME_HAS_ATIME = 0x08

RAR5_XENC_CIPHER_AES256 = 0

RAR5_XENC_CHECKVAL = 0x01
RAR5_XENC_TWEAKED = 0x02

RAR5_XHASH_BLAKE2SP = 0

RAR5_XREDIR_UNIX_SYMLINK = 1
RAR5_XREDIR_WINDOWS_SYMLINK = 2
RAR5_XREDIR_WINDOWS_JUNCTION = 3
RAR5_XREDIR_HARD_LINK = 4
RAR5_XREDIR_FILE_COPY = 5

RAR5_XREDIR_ISDIR = 0x01

RAR5_XOWNER_UNAME = 0x01
RAR5_XOWNER_GNAME = 0x02
RAR5_XOWNER_UID = 0x04
RAR5_XOWNER_GID = 0x08

RAR5_OS_WINDOWS = 0
RAR5_OS_UNIX = 1

##
## internal constants
##

RAR_ID  = b"Rar!\x1a\x07\x00"
RAR5_ID = b"Rar!\x1a\x07\x01\x00"
ZERO    = b'\0'
EMPTY   = b''
UTC     = timezone(timedelta(0), 'UTC')
BSIZE   = 32 * 1024

##
## Public interface
##

class Error(Exception):
    """Base class for rarfile errors."""

class BadRarFile(Error):
    """Incorrect data in archive."""

class NotRarFile(Error):
    """The file is not RAR archive."""

class BadRarName(Error):
    """Cannot guess multipart name components."""

class NoRarEntry(Error):
    """File not found in RAR"""

class PasswordRequired(Error):
    """File requires password"""

class NeedFirstVolume(Error):
    """Need to start from first volume."""

class NoCrypto(Error):
    """Cannot parse encrypted headers - no crypto available."""

class RarExecError(Error):
    """Problem reported by unrar/rar."""

class RarWarning(RarExecError):
    """Non-fatal error"""

class RarFatalError(RarExecError):
    """Fatal error"""

class RarCRCError(RarExecError):
    """CRC error during unpacking"""

class RarLockedArchiveError(RarExecError):
    """Must not modify locked archive"""

class RarWriteError(RarExecError):
    """Write error"""

class RarOpenError(RarExecError):
    """Open error"""

class RarUserError(RarExecError):
    """User error"""

class RarMemoryError(RarExecError):
    """Memory error"""

class RarCreateError(RarExecError):
    """Create error"""

class RarNoFilesError(RarExecError):
    """No files that match pattern were found"""

class RarUserBreak(RarExecError):
    """User stop"""

class RarWrongPassword(RarExecError):
    """Incorrect password"""

class RarUnknownError(RarExecError):
    """Unknown exit code"""

class RarSignalExit(RarExecError):
    """Unrar exited with signal"""

class RarCannotExec(RarExecError):
    """Executable not found."""


class RarInfo(object):

    # zipfile-compatible fields
    filename        = None
    file_size       = None
    compress_size   = None
    date_time       = None
    comment         = None
    CRC             = None
    volume          = None
    orig_filename   = None

    # optional extended time fields, datetime() objects.
    mtime           = None
    ctime           = None
    atime           = None

    extract_version = None
    mode            = None
    host_os         = None
    compress_type   = None

    # rar3-only fields
    comment         = None
    arctime         = None

    # rar5-only fields
    blake2sp_hash   = None
    file_redir      = None

    # internal fields
    flags           = 0
    type            = None

    def isdir(self):
        """Returns True if entry is a directory.
        """
        if self.type == RAR_BLOCK_FILE:
            return (self.flags & RAR_FILE_DIRECTORY) == RAR_FILE_DIRECTORY
        return False

    def needs_password(self):
        """Returns True if data is stored password-protected.
        """
        if self.type == RAR_BLOCK_FILE:
            return (self.flags & RAR_FILE_PASSWORD) > 0
        return False


class RarFileParser(object):
    """Parse RAR structure, provide access to files in archive.
    """

    #: Archive comment.  Unicode string or None.
    comment = None

    def __init__(self, charset=None, info_callback=None,
                 crc_check=True, errors="stop"):

        self._charset = charset or DEFAULT_CHARSET
        self._info_callback = info_callback
        self._crc_check     = crc_check
        self._password      = None
        self._file_parser   = None

        if errors == "stop":
            self._strict = False
        elif errors == "strict":
            self._strict = True
        else:
            return False

    def __enter__(self):
        """Open context."""
        return self

    def __exit__(self, typ, value, traceback):
        """Exit context"""
        self.close()

    def parse(self,rarfile,ver,start=0,last=0):
        self._rarfile = rarfile
        return self._parse(ver,start,last)

    def _parse(self,ver,start,last):
        if ver == 3:
            p3 = RAR3Parser(self._rarfile, self._password, self._crc_check,
                            self._charset, self._strict, self._info_callback,start)
            self._file_parser = p3  # noqa
        elif ver == 5:
            p5 = RAR5Parser(self._rarfile, self._password, self._crc_check,
                            self._charset, self._strict, self._info_callback,start)
            self._file_parser = p5  # noqa
        else:
            return -1
        return self._file_parser.parse()

# File format parsing

class CommonParser(object):
    """Shared parser parts."""
    _main           = None
    _hdrenc_main    = None
    _needs_password = False
    _fd             = None
    _expect_sig     = None
    _parse_error    = None
    _password       = None

    def __init__(self, rarfile, password, crc_check, charset, strict, info_cb, start):
        self._rarfile       = rarfile
        self._password      = password
        self._crc_check     = crc_check
        self._charset       = charset
        self._strict        = strict
        self._info_callback = info_cb
        self._info_list     = []
        self._info_map      = {}
        self._start         = start

    def has_header_encryption(self):
        """Returns True if headers are encrypted
        """
        if self._hdrenc_main:
            return True
        if self._main:
            if self._main.flags & RAR_MAIN_PASSWORD:
                return True
        return False

    def setpassword(self, psw):
        """Set cached password."""
        self._password = psw

    # read rar
    def parse(self):
        """Process file."""
        self._fd = None
        try:
            capacity = self._parse_real()
        finally:
            if self._fd:
                self._fd.close()
                self._fd = None
        return capacity

    def _parse_real(self):
        fd = XFile(self._rarfile)
        fd.seek(self._start,os.SEEK_SET)
        
        self._fd = fd
        sig = fd.read(len(self._expect_sig))
        if sig != self._expect_sig:
            return -1

        volume    = 0  # first vol (.rar) is 0
        endarc    = False
        volfile   = self._rarfile
        capacity  = 0
        while 1:
            if endarc:
                h = None    # don't read past ENDARC
            else:
                h = self._parse_header(fd)
            if not h:
                break
            if h.type == RAR_BLOCK_MAIN and not self._main:
                self._main = h
                if h.flags & RAR_MAIN_PASSWORD:
                    self._needs_password = True
                    if not self._password:
                        break
            elif h.type == RAR_BLOCK_ENDARC:
                endarc = True
            if h.needs_password():
                self._needs_password = True
            # go to next header
            if h.add_size > 0:
                fd.seek(h.data_offset + h.add_size, 0)
            
            capacity = fd.tell()-self._start

        return capacity

    # read single header
    def _parse_header(self, fd):
        try:
            # handle encrypted headers
            if (self._main and self._main.flags & RAR_MAIN_PASSWORD) or self._hdrenc_main:
                if not self._password:
                    return
                fd = self._decrypt_header(fd)

            # now read actual header
            return self._parse_block_header(fd)
        except struct.error:
            return None


# RAR3 format
#

class Rar3Info(RarInfo):
    """RAR3 specific fields."""
    extract_version = 15
    salt            = None
    add_size        = 0
    header_crc      = None
    header_size     = None
    header_offset   = None
    data_offset     = None
    _md_class       = None
    _md_expect      = None

    # make sure some rar5 fields are always present
    file_redir      = None
    blake2sp_hash   = None

    def _must_disable_hack(self):
        if self.type == RAR_BLOCK_FILE:
            if self.flags & RAR_FILE_PASSWORD:
                return True
            elif self.flags & (RAR_FILE_SPLIT_BEFORE | RAR_FILE_SPLIT_AFTER):
                return True
        elif self.type == RAR_BLOCK_MAIN:
            if self.flags & (RAR_MAIN_SOLID | RAR_MAIN_PASSWORD):
                return True
        return False


class RAR3Parser(CommonParser):
    """Parse RAR3 file format.
    """
    _expect_sig = RAR_ID
    _last_aes_key = (None, None, None)   # (salt, key, iv)

    def _decrypt_header(self, fd):
        if not _have_crypto:
            return (False,0,0,-2)
        salt = fd.read(8)
        if self._last_aes_key[0] == salt:
            key, iv = self._last_aes_key[1:]
        else:
            key, iv = rar3_s2k(self._password, salt)
            self._last_aes_key = (salt, key, iv)
        return HeaderDecrypt(fd, key, iv)

    # common header
    def _parse_block_header(self, fd):
        h = Rar3Info()
        h.header_offset = fd.tell()

        # read and parse base header
        buf = fd.read(S_BLK_HDR.size)
        if not buf:
            return None
        t = S_BLK_HDR.unpack_from(buf)
        h.header_crc, h.type, h.flags, h.header_size = t

        # read full header
        if h.header_size > S_BLK_HDR.size:
            hdata = buf + fd.read(h.header_size-S_BLK_HDR.size)
        else:
            hdata = buf
        h.data_offset = fd.tell()

        # unexpected EOF?
        if len(hdata) != h.header_size:
            return None

        pos = S_BLK_HDR.size

        # block has data assiciated with it?
        if h.flags & RAR_LONG_BLOCK:
            h.add_size, pos = load_le32(hdata, pos)
        else:
            h.add_size = 0

        # parse interesting ones, decide header boundaries for crc
        if h.type == RAR_BLOCK_MARK:
            return h
        elif h.type == RAR_BLOCK_MAIN:
            pos += 6
            if h.flags & RAR_MAIN_ENCRYPTVER:
                pos += 1
            crc_pos = pos
            if h.flags & RAR_MAIN_COMMENT:
                self._parse_subblocks(h, hdata, pos)
        elif h.type == RAR_BLOCK_FILE:
            pos = self._parse_file_header(h, hdata, pos - 4)
            crc_pos = pos
            if h.flags & RAR_FILE_COMMENT:
                pos = self._parse_subblocks(h, hdata, pos)
        elif h.type == RAR_BLOCK_SUB:
            pos = self._parse_file_header(h, hdata, pos - 4)
            crc_pos = h.header_size
        elif h.type == RAR_BLOCK_OLD_AUTH:
            pos += 8
            crc_pos = pos
        elif h.type == RAR_BLOCK_OLD_EXTRA:
            pos += 7
            crc_pos = pos
        else:
            crc_pos = h.header_size

        # check crc
        if h.type == RAR_BLOCK_OLD_SUB:
            crcdat = hdata[2:] + fd.read(h.add_size)
        else:
            crcdat = hdata[2:crc_pos]

        calc_crc = rar_crc32(crcdat) & 0xFFFF

        # return good header
        if h.header_crc == calc_crc:
            return h

        # instead panicing, send eof
        return None

    # read file-specific header
    def _parse_file_header(self, h, hdata, pos):
        fld = S_FILE_HDR.unpack_from(hdata, pos)
        pos += S_FILE_HDR.size

        h.compress_size = fld[0]
        h.file_size     = fld[1]
        h.host_os       = fld[2]
        h.CRC           = fld[3]
        h.date_time     = parse_dos_time(fld[4])
        h.mtime         = to_datetime(h.date_time)
        h.extract_version = fld[5]
        h.compress_type = fld[6]
        name_size       = fld[7]
        h.mode          = fld[8]

        h._md_class     = CRC32Context
        h._md_expect    = h.CRC

        if h.flags & RAR_FILE_LARGE:
            h1, pos = load_le32(hdata, pos)
            h2, pos = load_le32(hdata, pos)
            h.compress_size |= h1 << 32
            h.file_size |= h2 << 32
            h.add_size = h.compress_size

        name, pos = load_bytes(hdata, name_size, pos)
        if h.flags & RAR_FILE_UNICODE:
            nul = name.find(ZERO)
            h.orig_filename = name[:nul]
            u = UnicodeFilename(h.orig_filename, name[nul + 1:])
            h.filename = u.decode()

            # if parsing failed fall back to simple name
            if u.failed:
                h.filename = self._decode(h.orig_filename)
        else:
            h.orig_filename = name
            h.filename = self._decode(name)

        # change separator, if requested
        if PATH_SEP != '\\':
            h.filename = h.filename.replace('\\', PATH_SEP)

        if h.flags & RAR_FILE_SALT:
            h.salt, pos = load_bytes(hdata, 8, pos)
        else:
            h.salt = None

        # optional extended time stamps
        if h.flags & RAR_FILE_EXTTIME:
            pos = _parse_ext_time(h, hdata, pos)
        else:
            h.mtime = h.atime = h.ctime = h.arctime = None

        return pos

    # find old-style comment subblock
    def _parse_subblocks(self, h, hdata, pos):
        while pos < len(hdata):
            # ordinary block header
            t = S_BLK_HDR.unpack_from(hdata, pos)
            ___scrc, stype, sflags, slen = t
            pos_next = pos + slen
            pos += S_BLK_HDR.size

            # corrupt header
            if pos_next < pos:
                break

            # followed by block-specific header
            if stype == RAR_BLOCK_OLD_COMMENT and pos + S_COMMENT_HDR.size <= pos_next:
                declen, ver, meth, crc = S_COMMENT_HDR.unpack_from(hdata, pos)
                pos += S_COMMENT_HDR.size
                data = hdata[pos : pos_next]
                #cmt = rar3_decompress(ver, meth, data, declen, sflags,
                #                      crc, self._password)
                #if not self._crc_check:
                #    h.comment = self._decode_comment(cmt)
                #elif rar_crc32(cmt) & 0xFFFF == crc:
                #    h.comment = self._decode_comment(cmt)

            pos = pos_next
        return pos

    def _read_comment_v3(self, inf, psw=None):
        pass

    def _decode(self, val):
        for c in TRY_ENCODINGS:
            try:
                return val.decode(c)
            except UnicodeError:
                pass
        return val.decode(self._charset, 'replace')

    def _decode_comment(self, val):
        return self._decode(val)


#
# RAR5 format
#

class Rar5Info(RarInfo):
    """Shared fields for RAR5 records.
    """
    extract_version  = 50
    header_crc       = None
    header_size      = None
    header_offset    = None
    data_offset      = None

    # type=all
    block_type       = None
    block_flags      = None
    add_size         = 0
    block_extra_size = 0

    # type=MAIN
    volume_number    = None
    _md_class        = None
    _md_expect       = None

    def _must_disable_hack(self):
        return False

class Rar5BaseFile(Rar5Info):
    """Shared sturct for file & service record.
    """
    type            = -1
    file_flags      = None
    file_encryption = (0, 0, 0, EMPTY, EMPTY, EMPTY)
    file_compress_flags = None
    file_redir      = None
    file_owner      = None
    file_version    = None
    blake2sp_hash   = None

    def _must_disable_hack(self):
        if self.flags & RAR_FILE_PASSWORD:
            return True
        if self.block_flags & (RAR5_BLOCK_FLAG_SPLIT_BEFORE | RAR5_BLOCK_FLAG_SPLIT_AFTER):
            return True
        if self.file_compress_flags & RAR5_COMPR_SOLID:
            return True
        if self.file_redir:
            return True
        return False


class Rar5FileInfo(Rar5BaseFile):
    """RAR5 file record.
    """
    type = RAR_BLOCK_FILE


class Rar5ServiceInfo(Rar5BaseFile):
    """RAR5 service record.
    """
    type = RAR_BLOCK_SUB


class Rar5MainInfo(Rar5Info):
    """RAR5 archive main record.
    """
    type = RAR_BLOCK_MAIN
    main_flags = None
    main_volume_number = None

    def _must_disable_hack(self):
        if self.main_flags & RAR5_MAIN_FLAG_SOLID:
            return True
        return False


class Rar5EncryptionInfo(Rar5Info):
    """RAR5 archive header encryption record."""
    type                    = RAR5_BLOCK_ENCRYPTION
    encryption_algo        = None
    encryption_flags       = None
    encryption_kdf_count   = None
    encryption_salt        = None
    encryption_check_value = None

    def needs_password(self):
        return True


class Rar5EndArcInfo(Rar5Info):
    """RAR5 end of archive record."""
    type = RAR_BLOCK_ENDARC
    endarc_flags = None


class RAR5Parser(CommonParser):
    """Parse RAR5 format.
    """
    _expect_sig  = RAR5_ID
    _hdrenc_main = None

    # AES encrypted headers
    _last_aes256_key = (-1, None, None)   # (kdf_count, salt, key)

    def _gen_key(self, kdf_count, salt):
        if self._last_aes256_key[:2] == (kdf_count, salt):
            return self._last_aes256_key[2]
        if kdf_count > 24:
            return (False,0,0,-2)
        psw = self._password
        if isinstance(psw, unicode):
            psw = psw.encode('utf8')
        key = pbkdf2_sha256(psw, salt, 1 << kdf_count)
        self._last_aes256_key = (kdf_count, salt, key)
        return key

    def _decrypt_header(self, fd):
        if not _have_crypto:
            return (False,0,0,-2)
        h = self._hdrenc_main
        key = self._gen_key(h.encryption_kdf_count, h.encryption_salt)
        iv = fd.read(16)
        return HeaderDecrypt(fd, key, iv)

    # common header
    def _parse_block_header(self, fd):
        header_offset = fd.tell()

        preload = 4 + 3
        start_bytes = fd.read(preload)
        header_crc, pos = load_le32(start_bytes, 0)
        hdrlen, pos = load_vint(start_bytes, pos)
        if hdrlen > 2 * 1024 * 1024:
            return None
        header_size = pos + hdrlen

        # read full header, check for EOF
        hdata = start_bytes + fd.read(header_size - len(start_bytes))
        if len(hdata) != header_size:
            self._set_error('Unexpected EOF when reading header')
            return None
        data_offset = fd.tell()

        calc_crc = rar_crc32(memoryview(hdata)[4:])
        if header_crc != calc_crc:
            # header parsing failed.
            self._set_error('Header CRC error: exp=%x got=%x (xlen = %d)',
                            header_crc, calc_crc, len(hdata))
            return None

        block_type, pos = load_vint(hdata, pos)

        if block_type == RAR5_BLOCK_MAIN:
            h, pos = self._parse_block_common(Rar5MainInfo(), hdata)
            h = self._parse_main_block(h, hdata, pos)
        elif block_type == RAR5_BLOCK_FILE:
            h, pos = self._parse_block_common(Rar5FileInfo(), hdata)
            h = self._parse_file_block(h, hdata, pos)
        elif block_type == RAR5_BLOCK_SERVICE:
            h, pos = self._parse_block_common(Rar5ServiceInfo(), hdata)
            h = self._parse_file_block(h, hdata, pos)
        elif block_type == RAR5_BLOCK_ENCRYPTION:
            h, pos = self._parse_block_common(Rar5EncryptionInfo(), hdata)
            h = self._parse_encryption_block(h, hdata, pos)
        elif block_type == RAR5_BLOCK_ENDARC:
            h, pos = self._parse_block_common(Rar5EndArcInfo(), hdata)
            h = self._parse_endarc_block(h, hdata, pos)
        else:
            h = None
        if h:
            h.header_offset = header_offset
            h.data_offset = data_offset
        return h

    def _parse_block_common(self, h, hdata):
        h.header_crc, pos = load_le32(hdata, 0)
        hdrlen, pos = load_vint(hdata, pos)
        h.header_size = hdrlen + pos
        h.block_type, pos = load_vint(hdata, pos)
        h.block_flags, pos = load_vint(hdata, pos)

        if h.block_flags & RAR5_BLOCK_FLAG_EXTRA_DATA:
            h.block_extra_size, pos = load_vint(hdata, pos)
        if h.block_flags & RAR5_BLOCK_FLAG_DATA_AREA:
            h.add_size, pos = load_vint(hdata, pos)

        h.compress_size = h.add_size

        if h.block_flags & RAR5_BLOCK_FLAG_SKIP_IF_UNKNOWN:
            h.flags |= RAR_SKIP_IF_UNKNOWN
        if h.block_flags & RAR5_BLOCK_FLAG_DATA_AREA:
            h.flags |= RAR_LONG_BLOCK
        return h, pos

    def _parse_main_block(self, h, hdata, pos):
        h.main_flags, pos = load_vint(hdata, pos)
        if h.main_flags & RAR5_MAIN_FLAG_HAS_VOLNR:
            h.main_volume_number = load_vint(hdata, pos)

        h.flags |= RAR_MAIN_NEWNUMBERING
        if h.main_flags & RAR5_MAIN_FLAG_SOLID:
            h.flags |= RAR_MAIN_SOLID
        if h.main_flags & RAR5_MAIN_FLAG_ISVOL:
            h.flags |= RAR_MAIN_VOLUME
        if h.main_flags & RAR5_MAIN_FLAG_RECOVERY:
            h.flags |= RAR_MAIN_RECOVERY
        if self._hdrenc_main:
            h.flags |= RAR_MAIN_PASSWORD
        if h.main_flags & RAR5_MAIN_FLAG_HAS_VOLNR == 0:
            h.flags |= RAR_MAIN_FIRSTVOLUME

        return h

    def _parse_file_block(self, h, hdata, pos):
        h.file_flags, pos = load_vint(hdata, pos)
        h.file_size, pos = load_vint(hdata, pos)
        h.mode, pos = load_vint(hdata, pos)

        if h.file_flags & RAR5_FILE_FLAG_HAS_MTIME:
            h.mtime, pos = load_unixtime(hdata, pos)
            h.date_time = h.mtime.timetuple()[:6]
        if h.file_flags & RAR5_FILE_FLAG_HAS_CRC32:
            h.CRC, pos = load_le32(hdata, pos)
            h._md_class = CRC32Context
            h._md_expect = h.CRC

        h.file_compress_flags, pos = load_vint(hdata, pos)
        h.file_host_os, pos = load_vint(hdata, pos)
        h.orig_filename, pos = load_vstr(hdata, pos)
        h.filename = h.orig_filename.decode('utf8', 'replace')

        # use compatible values
        if h.file_host_os == RAR5_OS_WINDOWS:
            h.host_os = RAR_OS_WIN32
        else:
            h.host_os = RAR_OS_UNIX
        h.compress_type = RAR_M0 + ((h.file_compress_flags >> 7) & 7)

        if h.block_extra_size:
            # allow 1 byte of garbage
            while pos < len(hdata) - 1:
                xsize, pos = load_vint(hdata, pos)
                xdata, pos = load_bytes(hdata, xsize, pos)
                self._process_file_extra(h, xdata)

        if h.block_flags & RAR5_BLOCK_FLAG_SPLIT_BEFORE:
            h.flags |= RAR_FILE_SPLIT_BEFORE
        if h.block_flags & RAR5_BLOCK_FLAG_SPLIT_AFTER:
            h.flags |= RAR_FILE_SPLIT_AFTER
        if h.file_flags & RAR5_FILE_FLAG_ISDIR:
            h.flags |= RAR_FILE_DIRECTORY
        if h.file_compress_flags & RAR5_COMPR_SOLID:
            h.flags |= RAR_FILE_SOLID

        return h

    def _parse_endarc_block(self, h, hdata, pos):
        h.endarc_flags, pos = load_vint(hdata, pos)
        if h.endarc_flags & RAR5_ENDARC_FLAG_NEXT_VOL:
            h.flags |= RAR_ENDARC_NEXT_VOLUME
        return h

    def _parse_encryption_block(self, h, hdata, pos):
        h.encryption_algo, pos = load_vint(hdata, pos)
        h.encryption_flags, pos = load_vint(hdata, pos)
        h.encryption_kdf_count, pos = load_byte(hdata, pos)
        h.encryption_salt, pos = load_bytes(hdata, 16, pos)
        if h.encryption_flags & RAR5_ENC_FLAG_HAS_CHECKVAL:
            h.encryption_check_value = load_bytes(hdata, 12, pos)
        if h.encryption_algo != RAR5_XENC_CIPHER_AES256:
            return None
        self._hdrenc_main = h
        return h

    # file extra record
    def _process_file_extra(self, h, xdata):
        xtype, pos = load_vint(xdata, 0)
        if xtype == RAR5_XFILE_TIME:
            self._parse_file_xtime(h, xdata, pos)
        elif xtype == RAR5_XFILE_ENCRYPTION:
            self._parse_file_encryption(h, xdata, pos)
        elif xtype == RAR5_XFILE_HASH:
            self._parse_file_hash(h, xdata, pos)
        elif xtype == RAR5_XFILE_VERSION:
            self._parse_file_version(h, xdata, pos)
        elif xtype == RAR5_XFILE_REDIR:
            self._parse_file_redir(h, xdata, pos)
        elif xtype == RAR5_XFILE_OWNER:
            self._parse_file_owner(h, xdata, pos)
        elif xtype == RAR5_XFILE_SERVICE:
            pass
        else:
            pass

    # extra block for file time record
    def _parse_file_xtime(self, h, xdata, pos):
        tflags, pos = load_vint(xdata, pos)
        ldr = load_windowstime
        if tflags & RAR5_XTIME_UNIXTIME:
            ldr = load_unixtime
        if tflags & RAR5_XTIME_HAS_MTIME:
            h.mtime, pos = ldr(xdata, pos)
            h.date_time = h.mtime.timetuple()[:6]
        if tflags & RAR5_XTIME_HAS_CTIME:
            h.ctime, pos = ldr(xdata, pos)
        if tflags & RAR5_XTIME_HAS_ATIME:
            h.atime, pos = ldr(xdata, pos)

    # just remember encryption info
    def _parse_file_encryption(self, h, xdata, pos):
        algo, pos = load_vint(xdata, pos)
        flags, pos = load_vint(xdata, pos)
        kdf_count, pos = load_byte(xdata, pos)
        salt, pos = load_bytes(xdata, 16, pos)
        iv, pos = load_bytes(xdata, 16, pos)
        checkval = None
        if flags & RAR5_XENC_CHECKVAL:
            checkval, pos = load_bytes(xdata, 12, pos)
        if flags & RAR5_XENC_TWEAKED:
            h._md_expect = None
            h._md_class = NoHashContext

        h.file_encryption = (algo, flags, kdf_count, salt, iv, checkval)
        h.flags |= RAR_FILE_PASSWORD

    def _parse_file_hash(self, h, xdata, pos):
        hash_type, pos = load_vint(xdata, pos)
        if hash_type == RAR5_XHASH_BLAKE2SP:
            h.blake2sp_hash, pos = load_bytes(xdata, 32, pos)
            if _have_blake2 and (h.file_encryption[1] & RAR5_XENC_TWEAKED) == 0:
                h._md_class = Blake2SP
                h._md_expect = h.blake2sp_hash

    def _parse_file_version(self, h, xdata, pos):
        flags, pos = load_vint(xdata, pos)
        version, pos = load_vint(xdata, pos)
        h.file_version = (flags, version)

    def _parse_file_redir(self, h, xdata, pos):
        redir_type, pos = load_vint(xdata, pos)
        redir_flags, pos = load_vint(xdata, pos)
        redir_name, pos = load_vstr(xdata, pos)
        redir_name = redir_name.decode('utf8', 'replace')
        h.file_redir = (redir_type, redir_flags, redir_name)

    def _parse_file_owner(self, h, xdata, pos):
        user_name = group_name = user_id = group_id = None

        flags, pos = load_vint(xdata, pos)
        if flags & RAR5_XOWNER_UNAME:
            user_name, pos = load_vstr(xdata, pos)
        if flags & RAR5_XOWNER_GNAME:
            group_name, pos = load_vstr(xdata, pos)
        if flags & RAR5_XOWNER_UID:
            user_id, pos = load_vint(xdata, pos)
        if flags & RAR5_XOWNER_GID:
            group_id, pos = load_vint(xdata, pos)

        h.file_owner = (user_name, group_name, user_id, group_id)

 
##
## Utility classes
##

class UnicodeFilename(object):
    """Handle RAR3 unicode filename decompression.
    """
    def __init__(self, name, encdata):
        self.std_name = bytearray(name)
        self.encdata = bytearray(encdata)
        self.pos = self.encpos = 0
        self.buf = bytearray()
        self.failed = 0

    def enc_byte(self):
        """Copy encoded byte."""
        try:
            c = self.encdata[self.encpos]
            self.encpos += 1
            return c
        except IndexError:
            self.failed = 1
            return 0

    def std_byte(self):
        """Copy byte from 8-bit representation."""
        try:
            return self.std_name[self.pos]
        except IndexError:
            self.failed = 1
            return ord('?')

    def put(self, lo, hi):
        """Copy 16-bit value to _result."""
        self.buf.append(lo)
        self.buf.append(hi)
        self.pos += 1

    def decode(self):
        """Decompress compressed UTF16 value."""
        hi = self.enc_byte()
        flagbits = 0
        while self.encpos < len(self.encdata):
            if flagbits == 0:
                flags = self.enc_byte()
                flagbits = 8
            flagbits -= 2
            t = (flags >> flagbits) & 3
            if t == 0:
                self.put(self.enc_byte(), 0)
            elif t == 1:
                self.put(self.enc_byte(), hi)
            elif t == 2:
                self.put(self.enc_byte(), self.enc_byte())
            else:
                n = self.enc_byte()
                if n & 0x80:
                    c = self.enc_byte()
                    for _ in range((n & 0x7f) + 2):
                        lo = (self.std_byte() + c) & 0xFF
                        self.put(lo, hi)
                else:
                    for _ in range(n + 2):
                        self.put(self.std_byte(), 0)
        return self.buf.decode("utf-16le", "replace")

class HeaderDecrypt(object):
    """File-like object that decrypts from another file"""
    def __init__(self, f, key, iv):
        self.f = f
        self.ciph = AES_CBC_Decrypt(key, iv)
        self.buf = EMPTY

    def tell(self):
        """Current file pos - works only on block boundaries."""
        return self.f.tell()

    def read(self, cnt=None):
        """Read and decrypt."""
        if cnt > 8 * 1024:
            return None

        # consume old data
        if cnt <= len(self.buf):
            res = self.buf[:cnt]
            self.buf = self.buf[cnt:]
            return res
        res = self.buf
        self.buf = EMPTY
        cnt -= len(res)

        # decrypt new data
        blklen = 16
        while cnt > 0:
            enc = self.f.read(blklen)
            if len(enc) < blklen:
                break
            dec = self.ciph.decrypt(enc)
            if cnt >= len(dec):
                res += dec
                cnt -= len(dec)
            else:
                res += dec[:cnt]
                self.buf = dec[cnt:]
                cnt = 0

        return res


# handle (filename|filelike) object
class XFile(object):
    """Input may be filename or file object.
    """
    __slots__ = ('_fd', '_need_close')

    def __init__(self, xfile, bufsize=1024):
        if is_filelike(xfile):
            self._need_close = False
            self._fd = xfile
            self._fd.seek(0)
        else:
            self._need_close = True
            self._fd = open(xfile, 'rb', bufsize)

    def read(self, n=None):
        """Read from file."""
        return self._fd.read(n)

    def tell(self):
        """Return file pos."""
        return self._fd.tell()

    def seek(self, ofs, whence=0):
        """Move file pos."""
        return self._fd.seek(ofs, whence)

    def readinto(self, dst):
        """Read into buffer."""
        return self._fd.readinto(dst)

    def close(self):
        """Close file object."""
        if self._need_close:
            self._fd.close()

    def __enter__(self):
        return self

    def __exit__(self, typ, val, tb):
        self.close()


class NoHashContext(object):
    """No-op hash function."""
    def __init__(self, data=None):
        """Initialize"""
    def update(self, data):
        """Update data"""
    def digest(self):
        """Final hash"""
    def hexdigest(self):
        """Hexadecimal digest."""


class CRC32Context(object):
    """Hash context that uses CRC32."""
    __slots__ = ['_crc']

    def __init__(self, data=None):
        self._crc = 0
        if data:
            self.update(data)

    def update(self, data):
        """Process data."""
        self._crc = rar_crc32(data, self._crc)

    def digest(self):
        """Final hash."""
        return self._crc

    def hexdigest(self):
        """Hexadecimal digest."""
        return '%08x' % self.digest()


class Blake2SP(object):
    """Blake2sp hash context.
    """
    __slots__ = ['_thread', '_buf', '_cur', '_digest']
    digest_size = 32
    block_size = 64
    parallelism = 8

    def __init__(self, data=None):
        self._buf = b''
        self._cur = 0
        self._digest = None
        self._thread = []

        for i in range(self.parallelism):
            ctx = self._blake2s(i, 0, i == (self.parallelism - 1))
            self._thread.append(ctx)

        if data:
            self.update(data)

    def _blake2s(self, ofs, depth, is_last):
        return blake2s(node_offset=ofs, node_depth=depth, last_node=is_last,
                       depth=2, inner_size=32, fanout=self.parallelism)

    def _add_block(self, blk):
        self._thread[self._cur].update(blk)
        self._cur = (self._cur + 1) % self.parallelism

    def update(self, data):
        """Hash data.
        """
        view = memoryview(data)
        bs = self.block_size
        if self._buf:
            need = bs - len(self._buf)
            if len(view) < need:
                self._buf += view.tobytes()
                return
            self._add_block(self._buf + view[:need].tobytes())
            view = view[need:]
        while len(view) >= bs:
            self._add_block(view[:bs])
            view = view[bs:]
        self._buf = view.tobytes()

    def digest(self):
        """Return final digest value.
        """
        if self._digest is None:
            if self._buf:
                self._add_block(self._buf)
                self._buf = EMPTY
            ctx = self._blake2s(0, 1, True)
            for t in self._thread:
                ctx.update(t.digest())
            self._digest = ctx.digest()
        return self._digest

    def hexdigest(self):
        """Hexadecimal digest."""
        return tohex(self.digest())


class Rar3Sha1(object):
    """Bug-compat for SHA1
    """
    digest_size = 20
    block_size = 64

    _BLK_BE = struct.Struct(b'>16L')
    _BLK_LE = struct.Struct(b'<16L')

    __slots__ = ('_nbytes', '_md', '_rarbug')

    def __init__(self, data=b'', rarbug=False):
        self._md = sha1()
        self._nbytes = 0
        self._rarbug = rarbug
        self.update(data)

    def update(self, data):
        """Process more data."""
        self._md.update(data)
        bufpos = self._nbytes & 63
        self._nbytes += len(data)

        if self._rarbug and len(data) > 64:
            dpos = self.block_size - bufpos
            while dpos + self.block_size <= len(data):
                self._corrupt(data, dpos)
                dpos += self.block_size

    def digest(self):
        """Return final state."""
        return self._md.digest()

    def hexdigest(self):
        """Return final state as hex string."""
        return self._md.hexdigest()

    def _corrupt(self, data, dpos):
        """Corruption from SHA1 core."""
        ws = list(self._BLK_BE.unpack_from(data, dpos))
        for t in range(16, 80):
            tmp = ws[(t - 3) & 15] ^ ws[(t - 8) & 15] ^ ws[(t - 14) & 15] ^ ws[(t - 16) & 15]
            ws[t & 15] = ((tmp << 1) | (tmp >> (32 - 1))) & 0xFFFFFFFF
        self._BLK_LE.pack_into(data, dpos, *ws)


##
## Utility functions
##

S_LONG = Struct('<L')
S_SHORT = Struct('<H')
S_BYTE = Struct('<B')

S_BLK_HDR = Struct('<HBHH')
S_FILE_HDR = Struct('<LLBLLBBHL')
S_COMMENT_HDR = Struct('<HBBH')


def load_vint(buf, pos):
    """Load variable-size int."""
    limit = min(pos + 11, len(buf))
    res = ofs = 0
    while pos < limit:
        b = _byte_code(buf[pos])
        res += ((b & 0x7F) << ofs)
        pos += 1
        ofs += 7
        if b < 0x80:
            return res, pos
    return (0,0)


def load_byte(buf, pos):
    """Load single byte"""
    end = pos + 1
    if end > len(buf):
        return (0,0)
    return S_BYTE.unpack_from(buf, pos)[0], end


def load_le32(buf, pos):
    """Load little-endian 32-bit integer"""
    end = pos + 4
    if end > len(buf):
        return (0,0)
    return S_LONG.unpack_from(buf, pos)[0], pos + 4


def load_bytes(buf, num, pos):
    """Load sequence of bytes"""
    end = pos + num
    if end > len(buf):
        return (0,0)
    return buf[pos : end], end


def load_vstr(buf, pos):
    """Load bytes prefixed by vint length"""
    slen, pos = load_vint(buf, pos)
    return load_bytes(buf, slen, pos)


def load_dostime(buf, pos):
    """Load LE32 dos timestamp"""
    stamp, pos = load_le32(buf, pos)
    tup = parse_dos_time(stamp)
    return to_datetime(tup), pos


def load_unixtime(buf, pos):
    """Load LE32 unix timestamp"""
    secs, pos = load_le32(buf, pos)
    dt = datetime.fromtimestamp(secs, UTC)
    return dt, pos


def load_windowstime(buf, pos):
    """Load LE64 windows timestamp"""
    # unix epoch (1970) in seconds from windows epoch (1601)
    unix_epoch = 11644473600
    val1, pos = load_le32(buf, pos)
    val2, pos = load_le32(buf, pos)
    secs, n1secs = divmod((val2 << 32) | val1, 10000000)
    dt = datetime.fromtimestamp(secs - unix_epoch, UTC)
    dt = dt.replace(microsecond=n1secs // 10)
    return dt, pos

# rar3 extended time fields
def _parse_ext_time(h, data, pos):
    # flags and rest of data can be missing
    flags = 0
    if pos + 2 <= len(data):
        flags = S_SHORT.unpack_from(data, pos)[0]
        pos += 2

    mtime, pos     = _parse_xtime(flags >> 3 * 4, data, pos, h.mtime)
    h.ctime, pos   = _parse_xtime(flags >> 2 * 4, data, pos)
    h.atime, pos   = _parse_xtime(flags >> 1 * 4, data, pos)
    h.arctime, pos = _parse_xtime(flags >> 0 * 4, data, pos)
    if mtime:
        h.mtime = mtime
        h.date_time = mtime.timetuple()[:6]
    return pos


# rar3 one extended time field
def _parse_xtime(flag, data, pos, basetime=None):
    res = None
    if flag & 8:
        if not basetime:
            basetime, pos = load_dostime(data, pos)

        # load second fractions
        rem = 0
        cnt = flag & 3
        for _ in range(cnt):
            b, pos = load_byte(data, pos)
            rem = (b << 16) | (rem >> 8)

        # convert 100ns units to microseconds
        usec = rem // 10
        if usec > 1000000:
            usec = 999999

        # dostime has room for 30 seconds only, correct if needed
        if flag & 4 and basetime.second < 59:
            res = basetime.replace(microsecond=usec, second=basetime.second + 1)
        else:
            res = basetime.replace(microsecond=usec)
    return res, pos


def is_filelike(obj):
    """Filename or file object?
    """
    if isinstance(obj, (bytes, unicode)):
        return False
    res = True
    for a in ('read', 'tell', 'seek'):
        res = res and hasattr(obj, a)
    if not res:
        raise ValueError("Invalid object passed as file")
    return True


def rar3_s2k(psw, salt):
    """String-to-key hash for RAR3.
    """
    if not isinstance(psw, unicode):
        psw = psw.decode('utf8')
    seed = bytearray(psw.encode('utf-16le') + salt)
    h = Rar3Sha1(rarbug=True)
    iv = EMPTY
    for i in range(16):
        for j in range(0x4000):
            cnt = S_LONG.pack(i * 0x4000 + j)
            h.update(seed)
            h.update(cnt[:3])
            if j == 0:
                iv += h.digest()[19:20]
    key_be = h.digest()[:16]
    key_le = pack("<LLLL", *unpack(">LLLL", key_be))
    return key_le, iv

def to_datetime(t):
    """Convert 6-part time tuple into datetime object.
    """
    if t is None:
        return None

    # extract values
    year, mon, day, h, m, s = t

    # assume the values are valid
    try:
        return datetime(year, mon, day, h, m, s)
    except ValueError:
        pass

    # sanitize invalid values
    mday = (0, 31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
    if mon < 1:
        mon = 1
    if mon > 12:
        mon = 12
    if day < 1:
        day = 1
    if day > mday[mon]:
        day = mday[mon]
    if h > 23:
        h = 23
    if m > 59:
        m = 59
    if s > 59:
        s = 59
    if mon == 2 and day == 29:
        try:
            return datetime(year, mon, day, h, m, s)
        except ValueError:
            day = 28
    return datetime(year, mon, day, h, m, s)


def parse_dos_time(stamp):
    """Parse standard 32-bit DOS timestamp.
    """
    sec, stamp = stamp & 0x1F, stamp >> 5
    mn,  stamp = stamp & 0x3F, stamp >> 6
    hr,  stamp = stamp & 0x1F, stamp >> 5
    day, stamp = stamp & 0x1F, stamp >> 5
    mon, stamp = stamp & 0x0F, stamp >> 4
    yr = (stamp & 0x7F) + 1980
    return (yr, mon, day, hr, mn, sec * 2)

def add_password_arg(cmd, psw, ___required=False):
    """Append password switch to commandline.
    """
    if UNRAR_TOOL == ALT_TOOL:
        return
    if psw is not None:
        cmd.append('-p' + psw)
    else:
        cmd.append('-p-')

def hmac_sha256(key, data):
    """HMAC-SHA256"""
    return HMAC(key, data, sha256).digest()
