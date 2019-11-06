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
import struct as st
import warnings
import mmap
import errno
from array import array

from .errors import (
    CompoundFileError,
    CompoundFileInvalidMagicError,
    CompoundFileInvalidBomError,
    CompoundFileLargeNormalFatError,
    CompoundFileLargeMiniFatError,
    CompoundFileMasterLoopError,
    CompoundFileNotFoundError,
    CompoundFileNotStreamError,
    CompoundFileMasterFatWarning,
    CompoundFileNormalFatWarning,
    CompoundFileMiniFatWarning,
    CompoundFileHeaderWarning,
    CompoundFileVersionWarning,
    CompoundFileSectorSizeWarning,
    CompoundFileMasterSectorWarning,
    CompoundFileNormalSectorWarning,
    CompoundFileEmulationWarning,
    )
from .mmap import FakeMemoryMap
from .entities import CompoundFileEntity
from .streams import (
    CompoundFileNormalStream,
    CompoundFileMiniStream,
    )
from .const import (
    COMPOUND_MAGIC,
    FREE_SECTOR,
    END_OF_CHAIN,
    NORMAL_FAT_SECTOR,
    MASTER_FAT_SECTOR,
    MAX_NORMAL_SECTOR,
    COMPOUND_HEADER,
    DIR_HEADER,
    FILENAME_ENCODING,
    )


# Good grief! Since my last in-source rant it appears someone in MS actually
# figured out how to write a decent spec! Unfortunately it appears someone in
# the marketing department also thought that yet another name change was in
# order so the Advanced Authoring Format (formerly known as OLE Compound
# Documents) is now known as the Compound File Binary File Format.
#
# Anyway, silly name changes aside, the point is that someone's actually
# written a decent spec this time rather than the half-assed AAF spec which
# read like adhoc notes on a reference implementation. The URL is (currently)
#
#   http://msdn.microsoft.com/en-gb/library/dd942138.aspx
#
# But given how MSDN changes its URLs you might just be better off Googling for
# "MS CFB" which'll find it (assuming they haven't changed the name again for
# kicks). The file format is still a pile of steaming underwear in places
# (unicode names with byte-length fields...) but as long as the spec is clear
# and well written I can forgive that (after all, it's hard to change something
# as established as this).
#
# In the interests of trying to keep naming vaguely consistent and sensible
# here's a translation list with the names we'll be using first and the names
# other documents use after:
#
#   normal-FAT = FAT = SAT
#   master-FAT = DIFAT = DIF = MSAT
#   mini-FAT = miniFAT = SSAT
#
# And here's a brief description of the compound document structure:
#
# Compound documents consist of a header, followed by a number of equally sized
# sectors numbered incrementally. Within the sectors are stored the master-FAT,
# normal-FAT, and (optional) mini-FAT, directory entries, and file streams. A
# FAT is simply a linked list of sectors, with each sector pointing to the
# next in the chain, the last holding the END_OF_CHAIN value.
#
# The master-FAT (the location of which is determined by the header) stores
# which sectors are occupied by the normal-FAT. It must be read first in order
# to read sectors that make up the normal-FAT in order.
#
# The normal-FAT stores the locations of directory entries, file streams, and
# tracks which sectors are allocated to the master-FAT and itself.
#
# The mini-FAT (if present) is stored as a file stream, virtually divided into
# smaller sectors for the purposes of efficiently storing files smaller than
# the normal sector size.

class CompoundFileReader(object):
    """
    Provides an interface for reading `OLE Compound Document`_ files.

    The :class:`CompoundFileReader` class provides a relatively simple
    interface for interpreting the content of Microsoft's `OLE Compound
    Document`_ files. These files can be thought of as a file-system in a file
    (or a loop-mounted FAT file-system for Unix folk).

    The class can be constructed with a filename or a file-like object. In the
    latter case, the object must support the ``read``, ``seek``, and ``tell``
    methods. For optimal usage, it should also provide a valid file descriptor
    in response to a call to ``fileno``, but this is not mandatory.

    The :attr:`root` attribute represents the root storage entity in the
    compound document. An :meth:`open` method is provided which (given a
    :class:`CompoundFileEntity` instance representing a stream), returns a
    file-like object representing the content of the stream.

    Finally, the context manager protocol is also supported, permitting usage
    of the class like so::

        with CompoundFileReader('foo.doc') as doc:
            # Iterate over items in the root directory of the compound document
            for entry in doc.root:
                # If any entry is a file, attempt to read the data from it
                if entry.isfile:
                    with doc.open(entry) as f:
                        f.read()

    .. attribute:: root

        The root attribute represents the root storage entity in the compound
        document. As a :class:`CompoundFileEntity` instance, it (and child
        storages) can be enumerated, accessed by index, or by name (like a
        dict) to obtain :class:`CompoundFileEntity` instances representing the
        content of the compound document.

        Both :class:`CompoundFileReader` and :class:`CompoundFileEntity`
        support human-readable representations making it relatively simple to
        browse and extract information from compound documents simply by using
        the interactive Python command line.
    """

    def __init__(self, filename_or_obj):
        super(CompoundFileReader, self).__init__()
        if isinstance(filename_or_obj, (str, bytes)):
            self._opened = True
            self._file = io.open(filename_or_obj, 'rb')
        else:
            self._opened = False
            self._file = filename_or_obj
        try:
            fd = self._file.fileno()
        except (IOError, AttributeError):
            # It's a file-like object without a valid file descriptor; use
            # our fake mmap class (if it supports seek and tell)
            try:
                self._file.seek(0)
                self._file.tell()
            except (IOError, AttributeError):
                raise TypeError(
                    'filename_or_obj must support fileno(), '
                    'or seek() and tell()')
            else:
                """
                warnings.warn(
                    CompoundFileEmulationWarning(
                        'file-like object has no file descriptor; using '
                        'slower emulated mmap'))
                """
                self._mmap = FakeMemoryMap(filename_or_obj)
        else:
            try:
                self._mmap = mmap.mmap(fd, 0, access=mmap.ACCESS_READ)
            except EnvironmentError as e:
                if e.errno == errno.ENOMEM:
                    """
                    warnings.warn(
                        CompoundFileEmulationWarning(
                            'unable to map all of file into memory; using '
                            'slower emulated mmap (use a 64-bit Python '
                            'installation to avoid this)'))
                    """
                    self._mmap = FakeMemoryMap(filename_or_obj)
                else:
                    raise

        self._master_fat = None
        self._normal_fat = None
        self._mini_fat = None
        self.root = None
        (
            magic,
            uuid,
            self._minor_version,
            self._dll_version,
            bom,
            normal_sector_size,
            mini_sector_size,
            unused,
            self._dir_sector_count,
            self._normal_sector_count,
            self._dir_first_sector,
            txn_signature,
            self._mini_size_limit,
            self._mini_first_sector,
            self._mini_sector_count,
            self._master_first_sector,
            self._master_sector_count,
        ) = COMPOUND_HEADER.unpack(self._mmap[:COMPOUND_HEADER.size])

        # Check the header for basic correctness
        if magic != COMPOUND_MAGIC:
            raise CompoundFileInvalidMagicError(
                    '%s does not appear to be an OLE compound '
                    'document' % filename_or_obj)
        if bom == 0xFEFF:
            raise CompoundFileInvalidBomError(
                    '%s uses an unsupported byte ordering (big '
                    'endian)' % filename_or_obj)
        elif bom != 0xFFFE:
            raise CompoundFileInvalidBomError(
                    'unable to determine byte ordering of %s' % filename_or_obj)
        self._normal_sector_size = 1 << normal_sector_size
        self._mini_sector_size = 1 << mini_sector_size
        if not (128 <= self._normal_sector_size <= 1048576):
            """
            warnings.warn(
                CompoundFileSectorSizeWarning(
                    'FAT sector size is silly (%d bytes), '
                    'assuming 512' % self._normal_sector_size))
            """
            self._normal_sector_size = 512
        if not (8 <= self._mini_sector_size < self._normal_sector_size):
            """
            warnings.warn(
                CompoundFileSectorSizeWarning(
                    'mini FAT sector size is silly (%d bytes), '
                    'assuming 64' % self._mini_sector_size))
            """
            self._mini_sector_size = 64
        self._normal_sector_format = st.Struct(
                native_str('<%dL' % (self._normal_sector_size // 4)))
        self._mini_sector_format = st.Struct(
                native_str('<%dL' % (self._mini_sector_size // 4)))
        assert self._normal_sector_size == self._normal_sector_format.size
        assert self._mini_sector_size == self._mini_sector_format.size

        # More correctness checks, but mostly warnings at this stage
        if self._dll_version == 3:
            if self._normal_sector_size != 512:
                """
                warnings.warn(
                    CompoundFileSectorSizeWarning(
                        'unexpected sector size in v3 file '
                        '(%d)' % self._normal_sector_size))
                """
            if self._dir_sector_count != 0:
                """
                warnings.warn(
                    CompoundFileHeaderWarning(
                        'directory chain sector count is non-zero '
                        '(%d)' % self._dir_sector_count))
                        
                """
        elif self._dll_version == 4:
            if self._normal_sector_size != 4096:
                """
                warnings.warn(
                    CompoundFileSectorSizeWarning(
                        'unexpected sector size in v4 file '
                        '(%d)' % self._normal_sector_size))
                """
        else:
            """
            warnings.warn(
                CompoundFileVersionWarning(
                    'unrecognized DLL version (%d)' % self._dll_version))
            """
            pass
        if self._mini_sector_size != 64:
            """
            warnings.warn(
                CompoundFileSectorSizeWarning(
                    'unexpected mini sector size '
                    '(%d)' % self._mini_sector_size))
            """
            pass
        if uuid != (b'\0' * 16):
            """
            warnings.warn(
                CompoundFileHeaderWarning(
                    'CLSID of compound file is non-zero (%r)' % uuid))
            """
            pass
        if txn_signature != 0:
            """
            warnings.warn(
                CompoundFileHeaderWarning(
                    'transaction signature is non-zero (%d)' % txn_signature))
            """
            pass
        if unused != (b'\0' * 6):
            """
            warnings.warn(
                CompoundFileHeaderWarning(
                    'unused header bytes are non-zero (%r)' % unused))
            """
            pass
        self._file_size = self._mmap.size()
        self._header_size = max(self._normal_sector_size, 512)
        self._max_sector = (self._file_size - self._header_size) // self._normal_sector_size
        self._load_normal_fat(self._load_master_fat())
        self._load_mini_fat()
        self._load_directory()

    def open(self, filename_or_entity):
        """
        Return a file-like object with the content of the specified entity.

        Given a :class:`CompoundFileEntity` instance which represents a stream,
        or a string representing the path to one (using ``/`` separators), this
        method returns an instance of :class:`CompoundFileStream` which can be
        used to read the content of the stream.
        """
        if isinstance(filename_or_entity, bytes):
            filename_or_entity = filename_or_entity.decode(FILENAME_ENCODING)
        if isinstance(filename_or_entity, str):
            entity = self.root
            for name in filename_or_entity.split('/'):
                if name:
                    try:
                        entity = entity[name]
                    except KeyError:
                        raise CompoundFileNotFoundError(
                                'unable to locate %s in compound '
                                'file' % filename_or_entity)
            filename_or_entity = entity
        if not filename_or_entity.isfile:
            raise CompoundFileNotStreamError(
                    '%s is not a stream' % filename_or_entity.name)
        cls = (
                CompoundFileMiniStream
                if filename_or_entity.size < self._mini_size_limit else
                CompoundFileNormalStream)
        return cls(
                self, filename_or_entity._start_sector,
                filename_or_entity.size)

    def close(self):
        try:
            self._mmap.close()
            if self._opened:
                self._file.close()
        finally:
            self._mmap = None
            self._file = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def _read_sector(self, sector):
        if sector > self._max_sector:
            raise CompoundFileError('read from invalid sector (%d)' % sector)
        offset = self._header_size + (sector * self._normal_sector_size)
        return self._mmap[offset:offset + self._normal_sector_size]

    def _load_master_fat(self):
        # Note: when reading the master-FAT we deliberately disregard the
        # master-FAT sector count read from the header as implementations may
        # set this incorrectly. Instead, we scan for END_OF_CHAIN (or
        # FREE_SECTOR) in the DIFAT after each read and stop when we find it.
        # In order to avoid infinite loops (in the case of a stupid or
        # malicious file) we keep track of each sector we seek to and quit in
        # the event of a repeat
        self._master_fat = array(native_str('L'))
        count = self._master_sector_count
        checked = 0
        sectors = set()

        # Special case: the first 109 entries are stored at the end of the file
        # header and the next sector of the master-FAT is stored in the header
        offset = COMPOUND_HEADER.size
        self._master_fat.extend(
                st.unpack(native_str('<109L'),
                    self._mmap[offset:offset + (109 * 4)]))
        sector = self._master_first_sector
        if count == 0 and sector == FREE_SECTOR:
            """
            warnings.warn(
                CompoundFileMasterFatWarning(
                    'DIFAT extension pointer is FREE_SECTOR, assuming no '
                    'extension'))
            """
            sector = END_OF_CHAIN
        elif count == 0 and sector != END_OF_CHAIN:
            """
            warnings.warn(
                CompoundFileMasterFatWarning(
                    'DIFAT extension pointer with zero count'))
            """
            pass
        elif count != 0 and sector == END_OF_CHAIN:
            """
            warnings.warn(
                CompoundFileMasterFatWarning(
                    'DIFAT chained from header, or incorrect count'))
            """
            sector = self._master_fat.pop()

        while True:
            # Check for an END_OF_CHAIN marker in the existing stream
            for index in range(checked, len(self._master_fat)):
                value = self._master_fat[index]
                if value > self._max_sector:
                    if value in (END_OF_CHAIN, FREE_SECTOR):
                        pass
                    elif value > MAX_NORMAL_SECTOR:
                        """
                        warnings.warn(
                            CompoundFileMasterFatWarning(
                                'DIFAT terminated by invalid special '
                                'value (%d)' % value))
                        """
                        pass
                    else:
                        """
                        warnings.warn(
                            CompoundFileMasterFatWarning(
                                'sector in DIFAT chain beyond file '
                                'end (%d)' % value))
                        """
                        pass
                    value = END_OF_CHAIN
                    break
            if value == END_OF_CHAIN:
                del self._master_fat[index:]
                break
            elif sector == END_OF_CHAIN:
                break
            checked = len(self._master_fat)
            # Step case: if we're reading a subsequent block we need to seek to
            # the indicated sector, read it, and find the next sector in the
            # last value
            count -= 1
            sectors.add(sector)
            self._master_fat.extend(
                    self._normal_sector_format.unpack(
                        self._read_sector(sector)))
            # Guard against malicious files which could cause excessive memory
            # allocation when reading the normal-FAT. If the normal-FAT alone
            # would exceed 100Mb of RAM, raise an error
            if len(self._master_fat) * self._normal_sector_size > 100*1024*1024:
                raise CompoundFileLargeNormalFatError(
                        'excessively large FAT (malicious file?)')
            sector = self._master_fat.pop()
            if sector in sectors:
                raise CompoundFileMasterLoopError(
                        'DIFAT loop encountered (sector %d)' % sector)

        if count > 0:
            """
            warnings.warn(
                CompoundFileMasterFatWarning(
                    'DIFAT end encountered early (expected %d more sectors)' % count))
            """
            pass
        elif count < 0:
            """
            warnings.warn(
                CompoundFileMasterFatWarning(
                    'DIFAT end encountered late (overran by %d sectors)' % -count))
            """
            pass
        self._master_sector_count -= count
        if len(self._master_fat) != self._normal_sector_count:
            """
            warnings.warn(
                CompoundFileMasterFatWarning(
                    'DIFAT length does not match FAT sector count '
                    '(%d != %d)' % (len(self._master_fat), self._normal_sector_count)))
            """
            self._normal_sector_count = len(self._master_fat)
        return sectors

    def _load_normal_fat(self, master_sectors):
        # Again, when reading the FAT we deliberately disregard the normal-FAT
        # sector count from the header as some implementations get it wrong.
        # Instead, we just read the sectors that the master-FAT chain tells us
        # to (no need to check for loops or invalid sectors here though - the
        # _load_master_fat method takes of those). After reading the normal-FAT
        # we check the master-FAT and normal-FAT sectors are marked correctly.
        self._normal_fat = array(native_str('L'))
        # XXX This is the major cost at the moment - reading the fragmented
        # sectors of the FAT into an array. Perhaps look at optimizing reads
        # of contiguous sectors? Or make the array lazy-read whenever a block
        # needs filling?
        for sector in self._master_fat:
            self._normal_fat.extend(
                    self._normal_sector_format.unpack(
                        self._read_sector(sector)))

        # The following simply verifies that all normal-FAT and master-FAT
        # sectors are marked appropriately in the normal-FAT
        for master_sector in master_sectors:
            if self._normal_fat[master_sector] != MASTER_FAT_SECTOR:
                """
                warnings.warn(
                    CompoundFileMasterSectorWarning(
                        'DIFAT sector %d marked incorrectly in FAT '
                        '(%d != %d)' % (
                            master_sector,
                            self._normal_fat[master_sector],
                            MASTER_FAT_SECTOR,
                            )
                        ))
                """
                self._normal_fat[master_sector] = MASTER_FAT_SECTOR
        for normal_sector in self._master_fat:
            if self._normal_fat[normal_sector] != NORMAL_FAT_SECTOR:
                """
                warnings.warn(
                    CompoundFileNormalSectorWarning(
                        'FAT sector %d marked incorrectly in FAT '
                        '(%d != %d)' % (
                            normal_sector,
                            self._normal_fat[normal_sector],
                            NORMAL_FAT_SECTOR,
                            )
                        ))
                """
                self._normal_fat[normal_sector] = NORMAL_FAT_SECTOR

    def _load_mini_fat(self):
        # Guard against malicious files which could cause excessive memory
        # allocation when reading the mini-FAT. If the mini-FAT alone
        # would exceed 100Mb of RAM, raise an error
        if self._mini_sector_count * self._normal_sector_size > 100*1024*1024:
            raise CompoundFileLargeMiniFatError(
                    'excessively large mini-FAT (malicious file?)')
        self._mini_fat = array(native_str('L'))

        # Construction of the stream below will construct the list of sectors
        # the mini-FAT occupies, and will constrain the length to the declared
        # mini-FAT sector count, or the number of occupied sectors (whichever
        # is shorter)
        if self._mini_first_sector == FREE_SECTOR:
            """
            warnings.warn(
                CompoundFileMiniFatWarning(
                    'mini FAT first sector set to FREE_SECTOR'))
            """
            self._mini_first_sector = END_OF_CHAIN
        elif self._max_sector < self._mini_first_sector <= MAX_NORMAL_SECTOR:
            """
            warnings.warn(
                CompoundFileMiniFatWarning(
                    'mini FAT first sector beyond file end '
                    '(%d)' % self._mini_first_sector))
            """
            self._mini_first_sector = END_OF_CHAIN
        if self._mini_first_sector != END_OF_CHAIN:
            with CompoundFileNormalStream(
                    self, self._mini_first_sector,
                    self._mini_sector_count * self._normal_sector_size) as stream:
                for i in range(stream._length // self._normal_sector_size):
                    self._mini_fat.extend(
                            self._normal_sector_format.unpack(
                                stream.read(self._normal_sector_format.size)))

    def _load_directory(self):
        # When reading the directory we don't attempt to accurately reconstruct
        # the red-black tree, partially because some implementations don't
        # write a correct red-black tree and partially because it doesn't
        # matter for users of the library. Instead we simply read the whole
        # stream of directory entries and construct a hierarchy of
        # CompoundFileEntity objects from this.
        #
        # In older compound files we have no idea how many entries are actually
        # in the directory, so we calculate an upper bound from the directory
        # stream's length
        stream = CompoundFileNormalStream(self, self._dir_first_sector)
        entries = [
                CompoundFileEntity(self, stream, index)
                for index in range(stream._length // DIR_HEADER.size)
                ]
        self.root = entries[0]
        # Blank out the root entry; necessary to ensure cycle detection works
        # properly in the _build_tree method
        entries[0] = None
        self.root._build_tree(entries)

    def __len__(self):
        return len(self.root)

    def __getitem__(self, key):
        return self.root[key]

    def __contains__(self, key):
        return key in self.root

