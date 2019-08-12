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
str = type('')


import warnings
import datetime as dt
from pprint import pformat

from compoundfiles.errors import (
    CompoundFileDirLoopError,
    CompoundFileDirEntryWarning,
    CompoundFileDirNameWarning,
    CompoundFileDirTypeWarning,
    CompoundFileDirIndexWarning,
    CompoundFileDirTimeWarning,
    CompoundFileDirSectorWarning,
    CompoundFileDirSizeWarning,
    )
from compoundfiles.const import (
    NO_STREAM,
    DIR_INVALID,
    DIR_STORAGE,
    DIR_STREAM,
    DIR_ROOT,
    DIR_HEADER,
    FILENAME_ENCODING,
    )


class CompoundFileEntity(object):
    """
    Represents an entity in an OLE Compound Document.

    An entity in an OLE Compound Document can be a "stream" (analogous to a
    file in a file-system) which has a :attr:`size` and can be opened by a call
    to the parent object's :meth:`~CompoundFileReader.open` method.
    Alternatively, it can be a "storage" (analogous to a directory in a
    file-system), which has no size but has :attr:`created` and
    :attr:`modified` time-stamps, and can contain other streams and storages.

    If the entity is a storage, it will act as an iterable read-only sequence,
    indexable by ordinal or by name, and compatible with the ``in`` operator
    and built-in :func:`len` function.

    .. attribute:: created

        For storage entities (where :attr:`isdir` is ``True``), this returns
        the creation date of the storage. Returns ``None`` for stream entities.

    .. attribute:: isdir

        Returns True if this is a storage entity which can contain other
        entities.

    .. attribute:: isfile

        Returns True if this is a stream entity which can be opened.

    .. attribute:: modified

        For storage entities (where :attr:`isdir` is True), this returns the
        last modification date of the storage. Returns ``None`` for stream
        entities.

    .. attribute:: name

        Returns the name of entity. This can be up to 31 characters long and
        may contain any character representable in UTF-16 except the NULL
        character. Names are considered case-insensitive for comparison
        purposes.

    .. attribute:: size

        For stream entities (where :attr:`isfile` is ``True``), this returns
        the number of bytes occupied by the stream. Returns 0 for storage
        entities.
    """

    def __init__(self, parent, stream, index):
        super(CompoundFileEntity, self).__init__()
        self._index = index
        self._children = None
        (
            name,
            name_len,
            self._entry_type,
            self._entry_color,
            self._left_index,
            self._right_index,
            self._child_index,
            self.uuid,
            user_flags,
            created,
            modified,
            self._start_sector,
            size_low,
            size_high,
        ) = DIR_HEADER.unpack(stream.read(DIR_HEADER.size))



        #### 2019.07.23 Kim Junho ####
        size_high = 0
        if created > 0x200000000000000:
            created = 0
        if modified > 0x200000000000000:
            modified = 0

        if self._entry_type == DIR_STREAM:
            self.uuid = b'\0' * 16

        if name[0:1] == b'\x00':
            return

        for i in range(0, name.find(b'\x00\x00') + 3, 2):
            if name[i+1:i+2] != b'\x00':
                return

        if name.find(b'\x00\x00'):
            self.name = name[:name.find(b'\x00\x00') + 3].decode('utf-16le')
        #self.name = name[:name.].decode('utf-16le')

        #### 2019.07.23 Kim Junho ####




        #self.name = name.decode('utf-16le')

        try:
            self.name = self.name[:self.name.index('\0')]
        except ValueError:
            """
            warnings.warn(
                CompoundFileDirNameWarning(
                    'missing NULL terminator in name'))
            """
            self.name = self.name[:(name_len // 2) - 1]
        if index == 0:
            if self._entry_type != DIR_ROOT:
                """
                warnings.warn(
                    CompoundFileDirTypeWarning('invalid type'))
                """
            self._entry_type = DIR_ROOT
        elif not self._entry_type in (DIR_STREAM, DIR_STORAGE, DIR_INVALID):
            """
            warnings.warn(
                CompoundFileDirTypeWarning('invalid type'))
            """
            self._entry_type = DIR_INVALID
        if self._entry_type == DIR_INVALID:
            if self.name != '':
                """
                warnings.warn(
                    CompoundFileDirNameWarning('non-empty name'))
                """
                pass
            if name_len != 0:
                """
                warnings.warn(
                    CompoundFileDirNameWarning('non-zero name length'))
                """
                pass
            if user_flags != 0:
                """
                warnings.warn(
                    CompoundFileDirEntryWarning('non-zero user flags'))
                """
                pass
        else:
            # Name length is in bytes, including NULL terminator ... for a
            # unicode encoded name ... *headdesk*
            if (len(self.name) + 1) * 2 != name_len:
                """
                warnings.warn(
                    CompoundFileDirNameWarning('invalid name length (%d)' % name_len))
                """
                pass
        if self._entry_type in (DIR_INVALID, DIR_ROOT):
            if self._left_index != NO_STREAM:
                """
                warnings.warn(
                    CompoundFileDirIndexWarning('invalid left sibling'))
                """
                pass
            if self._right_index != NO_STREAM:
                """
                warnings.warn(
                    CompoundFileDirIndexWarning('invalid right sibling'))
                """
                pass
            self._left_index = NO_STREAM
            self._right_index = NO_STREAM
        if self._entry_type in (DIR_INVALID, DIR_STREAM):
            if self._child_index != NO_STREAM:
                """
                warnings.warn(
                    CompoundFileDirIndexWarning('invalid child index'))
                """
                pass
            if self.uuid != b'\0' * 16:
                """
                warnings.warn(
                    CompoundFileDirEntryWarning('non-zero UUID'))
                """
                pass
            if created != 0:
                """
                warnings.warn(
                    CompoundFileDirTimeWarning('non-zero creation timestamp'))
                """
                pass
            if modified != 0:
                """
                warnings.warn(
                    CompoundFileDirTimeWarning('non-zero modification timestamp'))
                """
                pass
            self._child_index = NO_STREAM
            self.uuid = b'\0' * 16
            created = 0
            modified = 0
        if self._entry_type in (DIR_INVALID, DIR_STORAGE):
            if self._start_sector != 0:
                """
                warnings.warn(
                    CompoundFileDirSectorWarning(
                        'non-zero start sector (%d)' % self._start_sector))
                """
                pass
            if size_low != 0:
                """
                warnings.warn(
                    CompoundFileDirSizeWarning(
                        'non-zero size low-bits (%d)' % size_low))
                """
                pass
            if size_high != 0:
                """
                warnings.warn(
                    CompoundFileDirSizeWarning(
                        'non-zero size high-bits (%d)' % size_high))
                """
                pass
            self._start_sector = 0
            size_low = 0
            size_high = 0
        if parent._normal_sector_size == 512:
            # Surely this should be checking DLL version instead of sector
            # size?! But the spec does state sector size ...
            if size_high != 0:
                """
                warnings.warn(
                    CompoundFileDirSizeWarning(
                        'invalid size in small sector file'))
                """
                size_high = 0
            if size_low >= 1<<31:
                """
                warnings.warn(
                    CompoundFileDirSizeWarning(
                        'size too large for small sector file'))
                """
                pass
        self.size = (size_high << 32) | size_low
        epoch = dt.datetime(1601, 1, 1)

        self.created = (
                epoch + dt.timedelta(microseconds=created // 10)
                if created != 0 else None)


        self.modified = (
                epoch + dt.timedelta(microseconds=created // 10)
                if modified != 0 else None)


    @property
    def isfile(self):
        return self._entry_type == DIR_STREAM

    @property
    def isdir(self):
        return self._entry_type in (DIR_STORAGE, DIR_ROOT)

    def _build_tree(self, entries):

        def walk(index):
            node = entries[index]
            entries[index] = None
            if node is None:
                raise CompoundFileDirLoopError(
                    'loop detected in directory hierarchy '
                    '(points to index %d)' % index)
            if node._left_index != NO_STREAM:
                try:
                    walk(node._left_index)
                except IndexError:
                    """
                    warnings.warn(
                        CompoundFileDirIndexWarning(
                            'invalid left index (%d) in entry at '
                            'index %d' % (node._left_index, index)))
                    """
                    pass
            self._children.append(node)
            if node._right_index != NO_STREAM:
                try:
                    walk(node._right_index)
                except IndexError:
                    """
                    warnings.warn(
                        CompoundFileDirIndexWarning(
                            'invalid right index (%d) in entry at '
                            'index %d' % (node._right_index, index)))
                    """
                    pass
            node._build_tree(entries)

        if self.isdir:
            self._children = []
            try:
                walk(self._child_index)
            except IndexError:
                if self._child_index != NO_STREAM:
                    """
                    warnings.warn(
                        CompoundFileDirIndexWarning('invalid child index'))
                    """
                    pass

    def __len__(self):
        return len(self._children)

    def __iter__(self):
        return iter(self._children)

    def __contains__(self, name_or_obj):
        if isinstance(name_or_obj, bytes):
            name_or_obj = name_or_obj.decode(FILENAME_ENCODING)
        if isinstance(name_or_obj, str):
            try:
                self.__getitem__(name_or_obj)
                return True
            except KeyError:
                return False
        else:
            return name_or_obj in self._children

    def __getitem__(self, index_or_name):
        if isinstance(index_or_name, bytes):
            index_or_name = index_or_name.decode(FILENAME_ENCODING)
        if isinstance(index_or_name, str):
            name = index_or_name.lower()
            for item in self._children:
                if item.name.lower() == name:
                    return item
            raise KeyError(index_or_name)
        else:
            return self._children[index_or_name]

    def __repr__(self):
        return (
            "<CompoundFileEntity name='%s'>" % self.name
            if self.isfile else
            pformat([
                "<CompoundFileEntity dir='%s'>" % c.name
                if c.isdir else
                repr(c)
                for c in self._children
                ])
            if self.isdir else
            "<CompoundFileEntry ???>"
            )

