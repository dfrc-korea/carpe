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


import io
import warnings
from array import array
from abc import abstractmethod

from compoundfiles.errors import (
    CompoundFileNoMiniFatError,
    CompoundFileNormalLoopError,
    CompoundFileDirSizeWarning,
    CompoundFileTruncatedWarning,
    )
from compoundfiles.const import END_OF_CHAIN


class CompoundFileStream(io.RawIOBase):
    """
    Abstract base class for streams within an OLE Compound Document.

    Instances of :class:`CompoundFileStream` are not constructed
    directly, but are returned by the :meth:`CompoundFileReader.open` method.
    They support all common methods associated with read-only streams
    (:meth:`read`, :meth:`seek`, :meth:`tell`, and so forth).
    """
    def __init__(self):
        super(CompoundFileStream, self).__init__()
        self._sectors = array(native_str('L'))
        self._sector_index = None
        self._sector_offset = None

    def _load_sectors(self, start, fat):
        # To guard against cyclic FAT chains we use the tortoise'n'hare
        # algorithm here. If hare is ever equal to tortoise after a step, then
        # the hare somehow got transported behind the tortoise (via a loop) so
        # we raise an error
        hare = start
        tortoise = start
        while tortoise != END_OF_CHAIN:
            self._sectors.append(tortoise)
            tortoise = fat[tortoise]
            if hare != END_OF_CHAIN:
                hare = fat[hare]
                if hare != END_OF_CHAIN:
                    hare = fat[hare]
                    if hare == tortoise:
                        raise CompoundFileNormalLoopError(
                                'cyclic FAT chain found starting at %d' % start)

    @abstractmethod
    def _set_pos(self, value):
        raise NotImplementedError

    def readable(self):
        """
        Returns ``True``, indicating that the stream supports :meth:`read`.
        """
        return True

    def writable(self):
        """
        Returns ``False``, indicating that the stream doesn't support
        :meth:`write` or :meth:`truncate`.
        """
        return False

    def seekable(self):
        """
        Returns ``True``, indicating that the stream supports :meth:`seek`.
        """
        return True

    def tell(self):
        """
        Return the current stream position.
        """
        return (self._sector_index * self._sector_size) + self._sector_offset

    def seek(self, offset, whence=io.SEEK_SET):
        """
        Change the stream position to the given byte *offset*. *offset* is
        interpreted relative to the position indicated by *whence*. Values for
        *whence* are:

        * ``SEEK_SET`` or ``0`` - start of the stream (the default); *offset*
          should be zero or positive

        * ``SEEK_CUR`` or ``1`` - current stream position; *offset* may be
          negative

        * ``SEEK_END`` or ``2`` - end of the stream; *offset* is usually
          negative

        Return the new absolute position.
        """
        if whence == io.SEEK_CUR:
            offset = self.tell() + offset
        elif whence == io.SEEK_END:
            offset = self._length + offset
        if offset < 0:
            raise ValueError(
                    'New position is before the start of the stream')
        self._set_pos(offset)
        return offset

    @abstractmethod
    def read1(self, n=-1):
        """
        Read up to *n* bytes from the stream using only a single call to the
        underlying object.

        In the case of :class:`CompoundFileStream` this roughly corresponds to
        returning the content from the current position up to the end of the
        current sector.
        """
        raise NotImplementedError

    def read(self, n=-1):
        """
        Read up to *n* bytes from the stream and return them. As a convenience,
        if *n* is unspecified or -1, :meth:`readall` is called. Fewer than *n*
        bytes may be returned if there are fewer than *n* bytes from the
        current stream position to the end of the stream.

        If 0 bytes are returned, and *n* was not 0, this indicates end of the
        stream.
        """
        if n == -1:
            n = max(0, self._length - self.tell())
        else:
            n = max(0, min(n, self._length - self.tell()))
            #n = 512
        result = bytearray(n)
        i = 0
        while i < n:
            buf = self.read1(n - i)
            if not buf:
                warnings.warn(
                    CompoundFileTruncatedWarning(
                        'compound document appears to be truncated'))
                break
            result[i:i + len(buf)] = buf
            i += len(buf)
        return bytes(result)


class CompoundFileNormalStream(CompoundFileStream):
    def __init__(self, parent, start, length=None):
        super(CompoundFileNormalStream, self).__init__()
        self._load_sectors(start, parent._normal_fat)
        self._sector_size = parent._normal_sector_size
        self._header_size = parent._header_size
        self._mmap = parent._mmap
        min_length = (len(self._sectors) - 1) * self._sector_size
        max_length = len(self._sectors) * self._sector_size
        if length is None:
            self._length = max_length
        elif not (min_length <= length <= max_length):
            warnings.warn(
                CompoundFileDirSizeWarning(
                    'length (%d) of stream at sector %d exceeds bounds '
                    '(%d-%d)' % (length, start, min_length, max_length)))
            self._length = max_length
        else:
            self._length = length
        self._set_pos(0)

    def close(self):
        self._mmap = None

    def _set_pos(self, value):
        self._sector_index = value // self._sector_size
        self._sector_offset = value % self._sector_size

    def read1(self, n=-1):
        if n == -1:
            n = max(0, self._length - self.tell())
        else:
            n = max(0, min(n, self._length - self.tell()))
        n = min(n, self._sector_size - self._sector_offset)
        if n == 0:
            return b''
        offset = (
                self._header_size + (
                self._sectors[self._sector_index] * self._sector_size) +
                self._sector_offset)
        result = self._mmap[offset:offset + n]
        self._set_pos(self.tell() + n)
        return result


class CompoundFileMiniStream(CompoundFileStream):
    def __init__(self, parent, start, length=None):
        super(CompoundFileMiniStream, self).__init__()
        if not parent._mini_fat:
            raise CompoundFileNoMiniFatError(
                'no mini FAT in compound document')
        self._load_sectors(start, parent._mini_fat)
        self._sector_size = parent._mini_sector_size
        self._header_size = 0
        self._file = CompoundFileNormalStream(
                parent, parent.root._start_sector, parent.root.size)
        max_length = len(self._sectors) * self._sector_size
        if length is not None and length > max_length:
            warnings.warn(
                CompoundFileDirSizeWarning(
                    'length (%d) of stream at sector %d exceeds '
                    'max (%d)' % (length, start, max_length)))
        self._length = min(max_length, length or max_length)
        self._set_pos(0)

    def close(self):
        try:
            self._file.close()
        finally:
            self._file = None

    def _set_pos(self, value):
        self._sector_index = value // self._sector_size
        self._sector_offset = value % self._sector_size
        if self._sector_index < len(self._sectors):
            self._file.seek(
                    self._header_size +
                    (self._sectors[self._sector_index] * self._sector_size) +
                    self._sector_offset)

    def read1(self, n=-1):
        if n == -1:
            n = max(0, self._length - self.tell())
        else:
            n = max(0, min(n, self._length - self.tell()))
        n = min(n, self._sector_size - self._sector_offset)
        if n == 0:
            return b''
        result = self._file.read1(n)
        # Only perform a seek to a different sector if we've crossed into one
        if self._sector_offset + n < self._sector_size:
            self._sector_offset += n
        else:
            self._set_pos(self.tell() + n)
        return result

