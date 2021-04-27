# -*- coding: utf-8 -*-

import copy

from dfvfs.helpers import file_system_searcher
from dfvfs.resolver import resolver as path_spec_resolver
from dfvfs.lib import errors as dfvfs_errors
from dfvfs.lib import definitions as dfvfs_definitions

from engine import logger
from utility import errors

class PathSpecExtractor():
    """Path specification extractor.

    A path specification extractor extracts path specification from a source
    directory, file or storage media device or image.
    """

    _MAXIMUM_DEPTH = 255

    def __init__(self, duplicate_file_check=False):
        """Initializes a path specification extractor.

        The source collector discovers all the file entries in the source.
        The source can be a single file, directory or a volume within
        a storage media image or device.

        Args:
          duplicate_file_check (Optional[bool]): True if duplicate files should
              be ignored.
        """
        super(PathSpecExtractor, self).__init__()
        self._duplicate_file_check = duplicate_file_check
        self._hashlist = {}

    def ExtractPathSpecs(
            self, path_specs, find_specs=None, recurse_file_system=True,
            resolver_context=None):
        """Extracts path specification from a specific source.

        Args:
          path_specs (Optional[list[dfvfs.PathSpec]]): path specifications.
          find_specs (Optional[list[dfvfs.FindSpec]]): find specifications
              used in path specification extraction.
          recurse_file_system (Optional[bool]): True if extraction should
              recurse into a file system.
          resolver_context (Optional[dfvfs.Context]): resolver context.

        Yields:
          dfvfs.PathSpec: path specification of a file entry found in the source.
        """
        for path_spec in path_specs:
            for extracted_path_spec in self._ExtractPathSpecs(
                    path_spec, find_specs=find_specs,
                    recurse_file_system=recurse_file_system,
                    resolver_context=resolver_context):
                yield extracted_path_spec

    def _ExtractPathSpecs(
            self, path_spec, find_specs=None, recurse_file_system=True,
            resolver_context=None):
        """Extracts path specification from a specific source.

        Args:
          path_spec (dfvfs.PathSpec): path specification.
          find_specs (Optional[list[dfvfs.FindSpec]]): find specifications
              used in path specification extraction.
          recurse_file_system (Optional[bool]): True if extraction should
              recurse into a file system.
          resolver_context (Optional[dfvfs.Context]): resolver context.

        Yields:
          dfvfs.PathSpec: path specification of a file entry found in the source.
        """
        file_entry = None
        try:
            file_entry = path_spec_resolver.Resolver.OpenFileEntry(
                path_spec, resolver_context=resolver_context)
        except (dfvfs_errors.AccessError,
                dfvfs_errors.BackEndError,
                dfvfs_errors.PathSpecError) as exception:
            logger.error('Unable to open file entry with error: {0!s}'.format(exception))

        if not file_entry:
            logger.warning('Unable to open: {0:s}'.format(path_spec.comparable))

        elif (not file_entry.IsDirectory() and not file_entry.IsFile() and
              not file_entry.IsDevice()):
            logger.warning('Source path specification not a device, file or directory.\n' '{0:s}'.
                           format(path_spec.comparable))

        elif file_entry.IsFile():
            yield path_spec

        else:
            for extracted_path_spec in self._ExtractPathSpecsFromFileSystem(
                    path_spec, find_specs=find_specs,
                    recurse_file_system=recurse_file_system,
                    resolver_context=resolver_context):
                yield extracted_path_spec

    def _ExtractPathSpecsFromDirectory(self, file_entry, depth=0):
        """Extracts path specification from a directory.

        Args:
          file_entry (dfvfs.FileEntry): file entry that refers to the directory.
          depth (Optional[int]): current depth where 0 represents the file system
              root.

        Yields:
          dfvfs.PathSpec: path specification of a file entry found in the directory.

        Raises:
          MaximumRecursionDepth: when the maximum recursion depth is reached.
        """
        if depth >= self._MAXIMUM_DEPTH:
            raise errors.MaximumRecursionDepth('Maximum recursion depth reached.')

        # Need to do a breadth-first search otherwise we'll hit the Python
        # maximum recursion depth.
        sub_directories = []

        for sub_file_entry in file_entry.sub_file_entries:
            try:
                if not sub_file_entry.IsAllocated() or sub_file_entry.IsLink():
                    continue
            except dfvfs_errors.BackEndError as exception:
                logger.warning(
                    'Unable to process file: {0:s} with error: {1!s}'.format(
                        sub_file_entry.path_spec.comparable.replace(
                            '\n', ';'), exception))
                continue

            # For TSK-based file entries only, ignore the virtual /$OrphanFiles
            # directory.
            if sub_file_entry.type_indicator == dfvfs_definitions.TYPE_INDICATOR_TSK:
                if file_entry.IsRoot() and sub_file_entry.name == '$OrphanFiles':
                    continue

            if sub_file_entry.IsDirectory():
                sub_directories.append(sub_file_entry)

            elif sub_file_entry.IsFile():
                # If we are dealing with a VSS we want to calculate a hash
                # value based on available timestamps and compare that to previously
                # calculated hash values, and only include the file into the queue if
                # the hash does not match.
                if self._duplicate_file_check:
                    hash_value = self._CalculateNTFSTimeHash(sub_file_entry)

                    inode = getattr(sub_file_entry.path_spec, 'inode', 0)
                    if inode in self._hashlist:
                        if hash_value in self._hashlist[inode]:
                            continue

                    self._hashlist.setdefault(inode, []).append(hash_value)

            for path_spec in self._ExtractPathSpecsFromFile(sub_file_entry):
                yield path_spec

        for sub_file_entry in sub_directories:
            try:
                for path_spec in self._ExtractPathSpecsFromDirectory(
                        sub_file_entry, depth=(depth + 1)):
                    yield path_spec

            except (
                    IOError, dfvfs_errors.AccessError, dfvfs_errors.BackEndError,
                    dfvfs_errors.PathSpecError) as exception:
                logger.warning('{0!s}'.format(exception))

    def _ExtractPathSpecsFromFile(self, file_entry):
        """Extracts path specification from a file.

        Args:
          file_entry (dfvfs.FileEntry): file entry that refers to the file.

        Yields:
          dfvfs.PathSpec: path specification of a file entry found in the file.
        """
        produced_main_path_spec = False
        for data_stream in file_entry.data_streams:
            # Make a copy so we don't make the changes on a path specification
            # directly. Otherwise already produced path specifications can be
            # altered in the process.
            path_spec = copy.deepcopy(file_entry.path_spec)
            if data_stream.name:
                setattr(path_spec, 'data_stream', data_stream.name)
            yield path_spec

            if not data_stream.name:
                produced_main_path_spec = True

        if not produced_main_path_spec:
            yield file_entry.path_spec

    def _ExtractPathSpecsFromFileSystem(
            self, path_spec, find_specs=None, recurse_file_system=True,
            resolver_context=None):
        """Extracts path specification from a file system within a specific source.

        Args:
          path_spec (dfvfs.PathSpec): path specification of the root of
              the file system.
          find_specs (Optional[list[dfvfs.FindSpec]]): find specifications
              used in path specification extraction.
          recurse_file_system (Optional[bool]): True if extraction should
              recurse into a file system.
          resolver_context (Optional[dfvfs.Context]): resolver context.

        Yields:
          dfvfs.PathSpec: path specification of a file entry found in
              the file system.
        """
        file_system = None
        try:
            file_system = path_spec_resolver.Resolver.OpenFileSystem(
                path_spec, resolver_context=resolver_context)
        except (dfvfs_errors.AccessError,
                dfvfs_errors.BackEndError,
                dfvfs_errors.PathSpecError) as exception:
            logger.error('Unable to open file system with error: {0!s}'.format(exception))

        if file_system:
            try:
                if find_specs:
                    searcher = file_system_searcher.FileSystemSearcher(file_system, path_spec)
                    for extracted_path_spec in searcher.Find(find_specs=find_specs):
                        yield extracted_path_spec

                elif recurse_file_system:
                    file_entry = file_system.GetFileEntryByPathSpec(path_spec)
                    if file_entry:
                        for extracted_path_spec in self._ExtractPathSpecsFromDirectory(file_entry):
                            yield extracted_path_spec

                else:
                    yield path_spec

            except (dfvfs_errors.AccessError,
                    dfvfs_errors.BackEndError,
                    dfvfs_errors.PathSpecError) as exception:
                logger.warning('{0!s}'.format(exception))

            #finally:
                #file_system.Close()


