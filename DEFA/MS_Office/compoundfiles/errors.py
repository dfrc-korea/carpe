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


class CompoundFileError(IOError):
    """
    Base class for exceptions arising from reading compound documents.
    """

class CompoundFileHeaderError(CompoundFileError):
    """
    Base class for exceptions caused by issues in the document header.
    """

class CompoundFileMasterFatError(CompoundFileError):
    """
    Base class for exceptions caused by issues in the master FAT.
    """

class CompoundFileNormalFatError(CompoundFileError):
    """
    Base class for exceptions caused by issues in the normal FAT.
    """

class CompoundFileMiniFatError(CompoundFileError):
    """
    Base class for exceptions caused by issues in the mini FAT.
    """

class CompoundFileDirEntryError(CompoundFileError):
    """
    Base class for errors caused by issues in directory entries.
    """

class CompoundFileInvalidMagicError(CompoundFileHeaderError):
    """
    Error raised when a compound document has an invalid magic number.
    """

class CompoundFileInvalidBomError(CompoundFileHeaderError):
    """
    Error raised when a compound document is anything other than little-endian.
    """

class CompoundFileLargeNormalFatError(CompoundFileNormalFatError):
    """
    Error raised when the document has an excessively large FAT.
    """

class CompoundFileNormalLoopError(CompoundFileNormalFatError):
    """
    Error raised when a cycle is detected in a FAT chain.
    """

class CompoundFileLargeMiniFatError(CompoundFileMiniFatError):
    """
    Error raised when the document has an excessively large mini FAT.
    """

class CompoundFileNoMiniFatError(CompoundFileMiniFatError):
    """
    Error raised when the document has no mini-FAT, but an attempt is made
    to open a file that should belong to the mini-FAT.
    """

class CompoundFileMasterLoopError(CompoundFileMasterFatError):
    """
    Error raised when a loop is detected in the master FAT.
    """

class CompoundFileDirLoopError(CompoundFileDirEntryError):
    """
    Error raised when a loop is detected in the directory hierarchy.
    """

class CompoundFileNotFoundError(CompoundFileError):
    """
    Error raised when a named stream/storage isn't found.
    """

class CompoundFileNotStreamError(CompoundFileError):
    """
    Error raised when an attempt is made to open a storage.
    """


class CompoundFileWarning(Warning):
    """
    Base class for warnings arising from reading compound documents.
    """

class CompoundFileHeaderWarning(CompoundFileWarning):
    """
    Base class for warnings about header attributes.
    """

class CompoundFileMasterFatWarning(CompoundFileWarning):
    """
    Base class for warnings about master FAT issues.
    """

class CompoundFileNormalFatWarning(CompoundFileWarning):
    """
    Base class for warnings about normal FAT issues.
    """

class CompoundFileMiniFatWarning(CompoundFileWarning):
    """
    Base class for warnings about mini FAT issues.
    """

class CompoundFileDirEntryWarning(CompoundFileWarning):
    """
    Base class for warnings about directory entry issues.
    """

class CompoundFileSectorSizeWarning(CompoundFileHeaderWarning):
    """
    Base class for warnings about strange sector sizes in compound documents.
    """

class CompoundFileVersionWarning(CompoundFileHeaderWarning):
    """
    Warnings about unknown library versions.
    """

class CompoundFileMasterSectorWarning(CompoundFileNormalFatWarning):
    """
    Warnings about mis-marked master FAT sectors.
    """

class CompoundFileNormalSectorWarning(CompoundFileNormalFatWarning):
    """
    Warnings about mis-marked normal FAT sectors.
    """

class CompoundFileDirNameWarning(CompoundFileDirEntryWarning):
    """
    Warnings about invalid directory entry names.
    """

class CompoundFileDirTypeWarning(CompoundFileDirEntryWarning):
    """
    Warnings about invalid directory entry types.
    """

class CompoundFileDirIndexWarning(CompoundFileDirEntryWarning):
    """
    Warnings about directory sibling or child indexes.
    """

class CompoundFileDirTimeWarning(CompoundFileDirEntryWarning):
    """
    Warnings about directory entry timestamps.
    """

class CompoundFileDirSectorWarning(CompoundFileDirEntryWarning):
    """
    Warnings about directory start sectors.
    """

class CompoundFileDirSizeWarning(CompoundFileDirEntryWarning):
    """
    Warnings about directory size entries.
    """

class CompoundFileTruncatedWarning(CompoundFileWarning):
    """
    Warning about a truncated compound file.
    """

class CompoundFileEmulationWarning(CompoundFileWarning):
    """
    Warning about using an emulated memory-map.
    """

