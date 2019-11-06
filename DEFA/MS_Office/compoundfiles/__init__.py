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

"""
Most of the work in this package was derived from the specification for `OLE
Compound Document`_ files published by OpenOffice, and the specification for
the `Advanced Authoring Format`_ (AAF) published by Microsoft.

.. _OLE Compound Document: http://www.openoffice.org/sc/compdocfileformat.pdf
.. _Advanced Authoring Format: http://www.amwa.tv/downloads/specifications/aafcontainerspec-v1.0.1.pdf


CompoundFileReader
==================

.. autoclass:: CompoundFileReader
    :members:


CompoundFileStream
==================

.. autoclass:: CompoundFileStream
    :members:


CompoundFileEntity
==================

.. autoclass:: CompoundFileEntity
    :members:


Exceptions
==========

.. autoexception:: CompoundFileError

.. autoexception:: CompoundFileWarning

"""

from __future__ import (
    unicode_literals,
    absolute_import,
    print_function,
    division,
    )
str = type('')


from compoundfiles.errors import (
    CompoundFileError,
    CompoundFileHeaderError,
    CompoundFileMasterFatError,
    CompoundFileNormalFatError,
    CompoundFileMiniFatError,
    CompoundFileDirEntryError,
    CompoundFileInvalidMagicError,
    CompoundFileInvalidBomError,
    CompoundFileLargeNormalFatError,
    CompoundFileLargeMiniFatError,
    CompoundFileNoMiniFatError,
    CompoundFileMasterLoopError,
    CompoundFileNormalLoopError,
    CompoundFileDirLoopError,
    CompoundFileNotFoundError,
    CompoundFileNotStreamError,
    CompoundFileWarning,
    CompoundFileHeaderWarning,
    CompoundFileMasterFatWarning,
    CompoundFileNormalFatWarning,
    CompoundFileMiniFatWarning,
    CompoundFileVersionWarning,
    CompoundFileSectorSizeWarning,
    CompoundFileMasterSectorWarning,
    CompoundFileNormalSectorWarning,
    CompoundFileDirEntryWarning,
    CompoundFileDirNameWarning,
    CompoundFileDirTypeWarning,
    CompoundFileDirIndexWarning,
    CompoundFileDirTimeWarning,
    CompoundFileDirSectorWarning,
    CompoundFileDirSizeWarning,
    CompoundFileTruncatedWarning,
    CompoundFileEmulationWarning,
    )
from compoundfiles.streams import CompoundFileStream
from compoundfiles.entities import CompoundFileEntity
from compoundfiles.reader import CompoundFileReader

