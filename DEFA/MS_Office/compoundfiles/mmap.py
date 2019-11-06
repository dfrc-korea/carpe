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
try:
    range = xrange
except NameError:
    pass


import sys
PY2 = sys.version_info[0] == 2
import io
import threading


class FakeMemoryMap(object):
    """
    Provides an mmap-style interface for streams without a file descriptor.

    The :class:`FakeMemoryMap` class can be used to emulate a memory-mapped
    file in cases where a seekable file-like object is provided that doesn't
    have a file descriptor (e.g. in-memory streams), or where a file descriptor
    exists but "real" mmap cannot be used for other reasons (e.g.
    >2Gb files on a 32-bit OS).

    The emulated mapping is thread-safe, read-only, but obviously will be
    considerably slower than using a "real" mmap. All methods of a real
    read-only mmap are emulated (:meth:`find`, :meth:`read_byte`,
    :meth:`close`, etc.) so instances can be used as drop-in replacements.

    Currently the emulation only covers the entire file (it cannot be limited
    to a sub-range of the file as with real mmap).
    """

    def __init__(self, f):
        self._lock = threading.Lock()
        self._file = f
        with self._lock:
            f.seek(0, io.SEEK_END)
            self._size = f.tell()
            f.seek(0)

    def _read_only(self):
        raise TypeError('fake mmap is read-only')

    def __len__(self):
        return self._size

    def __getitem__(self, key):
        with self._lock:
            save_pos = self._file.tell()
            try:
                if not isinstance(key, slice):
                    if key < 0:
                        key += self._size
                    if not (0 <= key < self._size):
                        raise IndexError('fake mmap index out of range')
                    self._file.seek(key)
                    if PY2:
                        return self._file.read(1)
                    return ord(self._file.read(1))
                step = 1 if key.step is None else key.step
                if step > 0:
                    start = min(self._size, max(0, (
                        0 if key.start is None else
                        key.start + self._size if key.start < 0 else
                        key.start
                        )))
                    stop = min(self._size, max(0, (
                        self._size if key.stop is None else
                        key.stop + self._size if key.stop < 0 else
                        key.stop
                        )))
                    self._file.seek(start)
                    if start >= stop:
                        return b''
                    return self._file.read(stop - start)[::step]
                elif step < 0:
                    start = min(self._size, max(0, (
                        -1 if key.stop is None else
                        key.stop + self._size if key.stop < 0 else
                        key.stop
                        ) + 1))
                    stop = min(self._size, max(0, (
                        self._size - 1 if key.start is None else
                        key.start + self._size if key.start < 0 else
                        key.start
                        ) + 1))
                    self._file.seek(start)
                    if start >= stop:
                        return b''
                    return self._file.read(stop - start)[::-1][::-step]
                else:
                    raise ValueError('slice step cannot be zero')
            finally:
                self._file.seek(save_pos)

    def __contains__(self, value):
        # This operates rather oddly with memory-maps; it returns a valid
        # answer if value is a single byte. Otherwise, it returns False
        if len(value) == 1:
            return self.find(value) != 1
        return False

    def __setitem__(self, index, value):
        self._read_only()

    def close(self):
        pass

    def find(self, string, start=None, end=None):
        # XXX Naive find; replace with Boyer-Moore?
        l = len(string)
        start = min(self._size, max(0,
            0 if start is None else
            self._size + start if start < 0 else
            start
            ))
        end = min(self._size, max(0,
            self._size if end is None else
            self._size + end if end < 0 else
            end
            ))
        for i in range(start, end - l + 1):
            if self[i:i + l] == string:
                return i
        return -1

    def flush(self, offset=None, size=None):
        # Seems like this should raise a read-only error, but real read-only
        # mmaps don't so we don't either
        pass

    def move(self, dest, src, count):
        self._read_only()

    def read(self, num):
        with self._lock:
            return self._file.read(num)

    def read_byte(self):
        # XXX Beyond EOF = ValueError
        with self._lock:
            if PY2:
                return self._file.read(1)
            return ord(self._file.read(1))

    def readline(self):
        with self._lock:
            return self._file.readline()

    def resize(self, newsize):
        self._read_only()

    def rfind(self, string, start=None, end=None):
        # XXX Naive find; replace with Boyer-Moore?
        l = len(string)
        start = min(self._size, max(0,
            0 if start is None else
            self._size + start if start < 0 else
            start
            ))
        end = min(self._size, max(0,
            self._size if end is None else
            self._size + end if end < 0 else
            end
            ))
        print(start, end, l)
        print(list(range(end - l, start - 1, -1)))
        for i in range(end - l, start - 1, -1):
            if self[i:i + l] == string:
                return i
        return -1

    def seek(self, pos, whence=io.SEEK_SET):
        with self._lock:
            self._file.seek(pos, whence)
            return self._file.tell()

    def size(self):
        return self._size

    def tell(self):
        with self._lock:
            return self._file.tell()

    def write(self, string):
        self._read_only()

    def write_byte(self, byte):
        self._read_only()

