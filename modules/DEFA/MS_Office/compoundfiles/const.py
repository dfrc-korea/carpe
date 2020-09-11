#!/usr/bin/env python
# vim: set et sw=4 sts=4 fileencoding=utf-8:
#
# A library for reading Microsoft's OLE Compound Document format
# Copyright (c) 2014 Dave Hughes <dave@waveform.org.uk>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from __future__ import (
    unicode_literals,
    absolute_import,
    print_function,
    division,
    )
native_str = str
str = type('')


import struct as st


# Magic identifier at the start of the file
COMPOUND_MAGIC = b'\xD0\xCF\x11\xE0\xA1\xB1\x1A\xE1'

FREE_SECTOR       = 0xFFFFFFFF # denotes an unallocated (free) sector
END_OF_CHAIN      = 0xFFFFFFFE # denotes the end of a stream chain
NORMAL_FAT_SECTOR = 0xFFFFFFFD # denotes a sector used for the regular FAT
MASTER_FAT_SECTOR = 0xFFFFFFFC # denotes a sector used for the master FAT
MAX_NORMAL_SECTOR = 0xFFFFFFFA # the maximum sector in a file

MAX_REG_SID    = 0xFFFFFFFA # maximum directory entry ID
NO_STREAM      = 0xFFFFFFFF # unallocated directory entry

DIR_INVALID    = 0 # unknown/empty(?) storage type
DIR_STORAGE    = 1 # element is a storage (dir) object
DIR_STREAM     = 2 # element is a stream (file) object
DIR_LOCKBYTES  = 3 # element is an ILockBytes object
DIR_PROPERTY   = 4 # element is an IPropertyStorage object
DIR_ROOT       = 5 # element is the root storage object

FILENAME_ENCODING = 'latin-1'


COMPOUND_HEADER = st.Struct(native_str(''.join((
    native_str('<'),    # little-endian format
    native_str('8s'),   # magic string
    native_str('16s'),  # file UUID (unused)
    native_str('H'),    # file header major version
    native_str('H'),    # file header minor version
    native_str('H'),    # byte order mark
    native_str('H'),    # sector size (actual size is 2**sector_size)
    native_str('H'),    # mini sector size (actual size is 2**short_sector_size)
    native_str('6s'),   # unused
    native_str('L'),    # directory chain sector count
    native_str('L'),    # normal-FAT sector count
    native_str('L'),    # ID of first sector of the normal-FAT
    native_str('L'),    # transaction signature (unused)
    native_str('L'),    # minimum size of a normal stream
    native_str('L'),    # ID of first sector of the mini-FAT
    native_str('L'),    # mini-FAT sector count
    native_str('L'),    # ID of first sector of the master-FAT
    native_str('L'),    # master-FAT sector count
    ))))

DIR_HEADER = st.Struct(native_str(''.join((
    native_str('<'),    # little-endian format
    native_str('64s'),  # NULL-terminated filename in UTF-16 little-endian encoding
    native_str('H'),    # length of filename in bytes (why?!)
    native_str('B'),    # dir-entry type
    native_str('B'),    # red (0) or black (1) entry
    native_str('L'),    # ID of left-sibling node
    native_str('L'),    # ID of right-sibling node
    native_str('L'),    # ID of children's root node
    native_str('16s'),  # dir-entry UUID (unused)
    native_str('L'),    # user flags (unused)
    native_str('Q'),    # creation timestamp
    native_str('Q'),    # modification timestamp
    native_str('L'),    # start sector of stream
    native_str('L'),    # low 32-bits of stream size
    native_str('L'),    # high 32-bits of stream size
    ))))

