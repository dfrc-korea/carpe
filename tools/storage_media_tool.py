# -*- coding: utf-8 -*-

import os
import copy
import uuid
import hashlib
import codecs
import configparser
from pyarrow import csv
import pathlib
import platform

from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.lib import errors as dfvfs_errors
from dfvfs.lib import tsk_partition as dfvfs_partition
from dfvfs.lib import vshadow as dfvfs_vshadow
from dfvfs.path import factory as path_spec_factory
from dfvfs.volume import tsk_volume_system
from dfvfs.volume import apfs_volume_system
from dfvfs.volume import vshadow_volume_system
from dfvfs.credentials import manager as credentials_manager
from dfvfs.helpers import source_scanner
from dfvfs.resolver import resolver as dfvfs_resolver

from tools import logger, tools
from containers import carpe_file as CarpeFile
from utility import definitions
from utility import errors
from engine import path_extractors
from engine.preprocessors import signature_tool
from engine import path_helper


class StorageMediaTool(tools.CLITool):
    _BINARY_DATA_CREDENTIAL_TYPES = ['key_data']

    _SUPPORTED_CREDENTIAL_TYPES = [
        'key_data', 'password', 'recovery_password', 'startup_key']

    def __init__(self, input_reader=None, output_writer=None):
        super(StorageMediaTool, self).__init__(
            input_reader=input_reader, output_writer=output_writer)

        self.case_id = None
        self.evidence_id = None
        self._custom_artifacts_path = None
        self._artifact_definitions_path = None

        self._source_scanner = source_scanner.SourceScanner()
        self._source_path_specs = []
        self._storage_file_path = None
        self._credentials = []

        config = configparser.ConfigParser()
        conf_file = os.path.dirname(
            os.path.dirname(os.path.abspath(__file__))) + os.sep + 'config' + os.sep + 'carpe.conf'
        if not os.path.exists(conf_file):
            raise Exception('%s file does not exist.\n' % conf_file)
        config.read(conf_file)
        root_storage_path = config.get('paths', 'root_storage_path')
        root_tmp_path = config.get('paths', 'root_tmp_path')

        self._root_storage_path = root_storage_path
        self._root_tmp_path = root_tmp_path

        self._partition_list = {}
        self._partitions = None
        self._volumes = None
        self._process_vss = False
        self._vss_only = False
        self._vss_stores = None

        self.standalone_check = None
        self.signature_check = None
        self._signature_tool = signature_tool.SignatureTool()
        self._rds = None
        self._rds_set = None

    def _ParseStorageMediaOptions(self, options):
        self._ParseSourcePathOption(options)
        self._ParseOutputPathOption(options)

        self._ParseStorageMediaImageOptions(options)
        self._ParseVSSProcessingOptions(options)
        self._ParseCredentialOptions(options)

    def _ParseSourcePathOption(self, options):
        self._source_path = self.ParseStringOption(options, 'source')
        if self._source_path:
            self._source_path = os.path.abspath(self._source_path)

        if not self._source_path and self.standalone_check:
            raise errors.BadConfigOption('Missing source path.')
        elif not self.case_id and not self.evidence_id and not self.standalone_check:
            #raise print("Check your Source: Missing source path.")
            raise errors.BadConfigOption('Missing source path.')


    def _ParseOutputPathOption(self, options):
        self._output_file_path = self.ParseStringOption(options, 'output_file', ".\\CARPE-Result")
        if self._output_file_path:
            self._output_file_path = os.path.abspath(self._output_file_path)

    def _ParseCredentialOptions(self, options):
        """Parses the credential options.

        Args:
          options (argparse.Namespace): command line arguments.

        Raises:
          BadConfigOption: if the options are invalid.
        """
        credentials = getattr(options, 'credentials', [])
        if not isinstance(credentials, list):
            raise errors.BadConfigOption('Unsupported credentials value.')

        for credential_string in credentials:
            credential_type, _, credential_data = credential_string.partition(':')
            if not credential_type or not credential_data:
                raise errors.BadConfigOption(
                    'Badly formatted credential: {0:s}.'.format(credential_string))

            if credential_type not in self._SUPPORTED_CREDENTIAL_TYPES:
                raise errors.BadConfigOption(
                    'Unsupported credential type for: {0:s}.'.format(
                        credential_string))

            if credential_type in self._BINARY_DATA_CREDENTIAL_TYPES:
                try:
                    credential_data = codecs.decode(credential_data, 'hex')
                except TypeError:
                    raise errors.BadConfigOption(
                        'Unsupported credential data for: {0:s}.'.format(
                            credential_string))

            self._credentials.append((credential_type, credential_data))

    def _ParseStorageMediaImageOptions(self, options):

        self._partitions = getattr(options, 'partitions', 'all')
        if self._partitions:
            try:
                self._ParseVolumeIdentifiersString(self._partitions, prefix='p')
            except ValueError:
                raise errors.BadConfigOption('Unsupported partitions')

        self._volumes = getattr(options, 'volumes', None)
        if self._volumes:
            try:
                self._ParseVolumeIdentifiersString(self._volumes, prefix='apfs')
            except ValueError:
                raise errors.BadConfigOption('Unsupported volumes')

    def _ParseVSSProcessingOptions(self, options):

        vss_only = False
        vss_stores = None

        self._process_vss = getattr(options, 'process_vss', False)
        if self._process_vss:
            vss_only = getattr(options, 'vss_only', False)
            vss_stores = getattr(options, 'vss_stores', None)

        if vss_stores:
            try:
                self._ParseVolumeIdentifiersString(vss_stores, prefix='vss')
            except ValueError:
                raise errors.BadConfigOption('Unsupported VSS stores')

        self._vss_only = vss_only
        self._vss_stores = vss_stores

    def AddCredentialOptions(self, argument_group):
        """Adds the credential options to the argument group.

        The credential options are use to unlock encrypted volumes.

        Args:
          argument_group (argparse._ArgumentGroup): argparse argument group.
        """
        argument_group.add_argument(
            '--credential', action='append', default=[], type=str,
            dest='credentials', metavar='TYPE:DATA', help=(
                'Define a credentials that can be used to unlock encrypted '
                'volumes e.g. BitLocker. The credential is defined as type:data '
                'e.g. "password:BDE-test". Supported credential types are: '
                '{0:s}. Binary key data is expected to be passed in BASE-16 '
                'encoding (hexadecimal). WARNING credentials passed via command '
                'line arguments can end up in logs, so use this option with '
                'care.').format(', '.join(self._SUPPORTED_CREDENTIAL_TYPES)))

    def AddStorageMediaImageOptions(self, argument_group):

        argument_group.add_argument(
            '--partitions', '--partition', dest='partitions', action='store',
            type=str, default=None, help=(
                'Define partitions to be processed. A range of '
                'partitions can be defined as: "3..5". Multiple partitions can '
                'be defined as: "1,3,5" (a list of comma separated values). '
                'Ranges and lists can also be combined as: "1,3..5". The first '
                'partition is 1. All partitions can be specified with: "all".'))

        argument_group.add_argument(
            '--volumes', '--volume', dest='volumes', action='store', type=str,
            default=None, help=(
                'Define volumes to be processed. A range of volumes can be defined '
                'as: "3..5". Multiple volumes can be defined as: "1,3,5" (a list '
                'of comma separated values). Ranges and lists can also be combined '
                'as: "1,3..5". The first volume is 1. All volumes can be specified '
                'with: "all".'))

    def AddVSSProcessingOptions(self, argument_group):

        argument_group.add_argument(
            '--process_vss', '--process-vss', dest='process_vss', action='store_true',
            default=False, help=(
                'Do not scan for Volume Shadow Snapshots (VSS). This means that '
                'Volume Shadow Snapshots (VSS) are not processed.'))

        argument_group.add_argument(
            '--vss_only', '--vss-only', dest='vss_only', action='store_true',
            default=False, help=(
                'Do not process the current volume if Volume Shadow Snapshots '
                '(VSS) have been selected.'))

        argument_group.add_argument(
            '--vss_stores', '--vss-stores', dest='vss_stores', action='store',
            type=str, default=None, help=(
                'Define Volume Shadow Snapshots (VSS) (or stores that need to be '
                'processed. A range of stores can be defined as: "3..5". '
                'Multiple stores can be defined as: "1,3,5" (a list of comma '
                'separated values). Ranges and lists can also be combined as: '
                '"1,3..5". The first store is 1. All stores can be defined as: '
                '"all".'))

    def CreateStorageAndTempPath(self, cursor, case_id=None, evd_id=None):

        if not case_id or not evd_id:
            print("ERROR: Missing Case ID or Evidence ID.")
            return

        if self._source_path is None:
            query = 'SELECT evd_path FROM evidence_info WHERE case_id="' + case_id + '" AND evd_id="' + evd_id + '";'
            try:
                evd_path = cursor.execute_query(query)
                if evd_path is None:
                    raise ValueError
                self._source_path = os.path.join(self._root_storage_path, evd_path[0])
            except ValueError:
                logger.error('Evidence is not exist: \'evd_path\' is None')
                raise Exception('Evidence is not exist: \'evd_path\' is None')
            except Exception as exception:
                logger.error('database execution failed: {0!s}'.format(exception))
                raise Exception('database execution failed: {0!s}'.format(exception))

        if not os.path.isdir(os.path.join(self._root_tmp_path, case_id)):
            os.mkdir(os.path.join(self._root_tmp_path, case_id))

        self._tmp_path = os.path.join(os.path.join(self._root_tmp_path, case_id), evd_id)
        if not os.path.isdir(self._tmp_path):
            os.mkdir(self._tmp_path)

    def ScanSource(self, source_path):

        # In Saas Carpe, Source is lnk
        if os.path.islink(source_path):
            source_path = os.readlink(source_path)
            # source_path = os.path.realpath(source_path)

        if (not source_path.startswith('\\\\.\\') and
                not os.path.exists(source_path)):
            raise errors.SourceScannerError(
                'No such device, file or directory: {0:s}.'.format(source_path))

        scan_context = source_scanner.SourceScannerContext()
        scan_context.OpenSourcePath(source_path)

        try:
            self._source_scanner.Scan(scan_context)
        except (ValueError, dfvfs_errors.BackEndError) as exception:
            raise errors.SourceScannerError(
                'Unable to scan source with error: {0!s}.'.format(exception))

        # 경로를 입력받을 때
        if scan_context.source_type not in (
                scan_context.SOURCE_TYPE_STORAGE_MEDIA_DEVICE,
                scan_context.SOURCE_TYPE_STORAGE_MEDIA_IMAGE):
            scan_node = scan_context.GetRootScanNode()

            self._source_path_specs.append(scan_node.path_spec)
            return scan_context

        # Get the first node where where we need to decide what to process.
        scan_node = scan_context.GetRootScanNode()
        while len(scan_node.sub_nodes) == 1:
            scan_node = scan_node.sub_nodes[0]

        # if type_indicator가 TSK_PARTITION이 아닌 경우
        base_path_specs = []
        if scan_node.type_indicator != (
                dfvfs_definitions.TYPE_INDICATOR_TSK_PARTITION):
            self._ScanVolume(scan_context, scan_node, base_path_specs)

        # type_indicator가 TSK_PARTITION인 경우
        else:
            # Determine which partition needs to be processed.
            partition_identifiers = self._GetTSKPartitionIdentifiers(scan_node)
            if not partition_identifiers:
                raise errors.SourceScannerError('No partitions found.')

            for partition_identifier in partition_identifiers:
                location = '/{0:s}'.format(partition_identifier)
                sub_scan_node = scan_node.GetSubNodeByLocation(location)
                self._ScanVolume(scan_context, sub_scan_node, base_path_specs)

        if not base_path_specs:
            raise errors.SourceScannerError(
                'No supported file system found in source.')

        self._source_path_specs = base_path_specs

        return scan_context

    def _ScanVolume(self, scan_context, scan_node, base_path_specs):

        if not scan_node or not scan_node.path_spec:
            raise errors.SourceScannerError('Invalid or missing scan node.')

        if scan_context.IsLockedScanNode(scan_node.path_spec):
            # The source scanner found a locked volume and we need a credential to unlock it.
            self._ScanEncryptedVolume(scan_context, scan_node)

            if scan_context.IsLockedScanNode(scan_node.path_spec):
                return

        if scan_node.IsVolumeSystemRoot():
            self._ScanVolumeSystemRoot(scan_context, scan_node, base_path_specs)

        elif scan_node.IsFileSystem():
            self._ScanFileSystem(scan_node, base_path_specs)

        elif scan_node.type_indicator == dfvfs_definitions.TYPE_INDICATOR_VSHADOW:
            if self._process_vss:
                # TODO: look into building VSS store on demand.

                # We "optimize" here for user experience, alternatively we could scan
                # for a file system instead of hard coding a TSK child path
                # specification.
                path_spec = path_spec_factory.Factory.NewPathSpec(
                    dfvfs_definitions.TYPE_INDICATOR_TSK, location='/',
                    parent=scan_node.path_spec)

                base_path_specs.append(path_spec)

        elif not scan_node.sub_nodes:
            if scan_node.type_indicator == dfvfs_definitions.TYPE_INDICATOR_TSK_PARTITION:
                base_path_specs.append(scan_node.path_spec)

        else:
            for sub_scan_node in scan_node.sub_nodes:
                self._ScanVolume(scan_context, sub_scan_node, base_path_specs)

    def _ScanEncryptedVolume(self, scan_context, scan_node):
        """Scans an encrypted volume scan node for volume and file systems.

        Args:
          scan_context (SourceScannerContext): source scanner context.
          scan_node (SourceScanNode): volume scan node.

        Raises:
          SourceScannerError: if the format of or within the source is not
              supported, the scan node is invalid or there are no credentials
              defined for the format.
        """
        if not scan_node or not scan_node.path_spec:
            raise errors.SourceScannerError('Invalid or missing scan node.')

        credentials = credentials_manager.CredentialsManager.GetCredentials(
            scan_node.path_spec)
        if not credentials:
            raise errors.SourceScannerError('Missing credentials for scan node.')

        credentials_dict = dict(self._credentials)

        is_unlocked = False
        for credential_type in credentials.CREDENTIALS:
            credential_data = credentials_dict.get(credential_type, None)
            if not credential_data:
                continue

            is_unlocked = self._source_scanner.Unlock(
                scan_context, scan_node.path_spec, credential_type, credential_data)
            if is_unlocked:
                break

        if not is_unlocked:
            raise errors.Error('unlocked')
            # is_unlocked = self._PromptUserForEncryptedVolumeCredential(
            #     scan_context, scan_node, credentials)

        if is_unlocked:
            self._source_scanner.Scan(
                scan_context, scan_path_spec=scan_node.path_spec)

    def _ScanFileSystem(self, scan_node, base_path_specs):

        if not scan_node or not scan_node.path_spec:
            raise errors.SourceScannerError(
                'Invalid or missing file system scan node.')

        base_path_specs.append(scan_node.path_spec)

    def _ScanVolumeSystemRoot(self, scan_context, scan_node, base_path_specs):

        if not scan_node or not scan_node.path_spec:
            raise errors.SourceScannerError('Invalid scan node.')

        if scan_node.type_indicator == (
                dfvfs_definitions.TYPE_INDICATOR_APFS_CONTAINER):
            volume_identifiers = self._GetAPFSVolumeIdentifiers(scan_node)

        elif scan_node.type_indicator == dfvfs_definitions.TYPE_INDICATOR_VSHADOW:
            # if scan_node.type_indicator == dfvfs_definitions.TYPE_INDICATOR_VSHADOW:
            if self._process_vss:
                volume_identifiers = self._GetVSSStoreIdentifiers(scan_node)
                # Process VSS stores (snapshots) starting with the most recent one.
                volume_identifiers.reverse()
            else:
                volume_identifiers = []

        else:
            raise errors.SourceScannerError(
                'Unsupported volume system type: {0:s}.'.format(
                    scan_node.type_indicator))

        for volume_identifier in volume_identifiers:
            location = '/{0:s}'.format(volume_identifier)
            sub_scan_node = scan_node.GetSubNodeByLocation(location)
            if not sub_scan_node:
                raise errors.SourceScannerError(
                    'Scan node missing for volume identifier: {0:s}.'.format(
                        volume_identifier))

            self._ScanVolume(scan_context, sub_scan_node, base_path_specs)

    def _GetTSKPartitionIdentifiers(self, scan_node):

        if not scan_node or not scan_node.path_spec:
            raise errors.SourceScannerError('Invalid scan node.')

        volume_system = tsk_volume_system.TSKVolumeSystem()
        volume_system.Open(scan_node.path_spec)

        volume_identifiers = self._source_scanner.GetVolumeIdentifiers(
            volume_system)
        if not volume_identifiers:
            return []

        # TODO: refactor self._partitions to use scan options.
        if self._partitions:
            if self._partitions == 'all':
                partitions = range(1, volume_system.number_of_volumes + 1)
            else:
                partitions = self._ParseVolumeIdentifiersString(
                    self._partitions, prefix='p')

            selected_volume_identifiers = self._NormalizedVolumeIdentifiers(
                volume_system, partitions, prefix='p')

            if not set(selected_volume_identifiers).difference(volume_identifiers):
                return selected_volume_identifiers

        if len(volume_identifiers) == 1:
            return volume_identifiers

        return self._NormalizedVolumeIdentifiers(
            volume_system, volume_identifiers, prefix='p')

    def _GetAPFSVolumeIdentifiers(self, scan_node):
        """Determines the APFS volume identifiers.

        Args:
          scan_node (dfvfs.SourceScanNode): scan node.

        Returns:
          list[str]: APFS volume identifiers.

        Raises:
          SourceScannerError: if the format of or within the source is not
              supported or the the scan node is invalid.
          UserAbort: if the user requested to abort.
        """
        if not scan_node or not scan_node.path_spec:
            raise errors.SourceScannerError('Invalid scan node.')

        volume_system = apfs_volume_system.APFSVolumeSystem()
        volume_system.Open(scan_node.path_spec)

        volume_identifiers = self._source_scanner.GetVolumeIdentifiers(
            volume_system)
        if not volume_identifiers:
            return []

        # TODO: refactor self._volumes to use scan options.
        if self._volumes:
            if self._volumes == 'all':
                volumes = range(1, volume_system.number_of_volumes + 1)
            else:
                volumes = self._ParseVolumeIdentifiersString(
                    self._volumes, prefix='apfs')

            selected_volume_identifiers = self._NormalizedVolumeIdentifiers(
                volume_system, volumes, prefix='apfs')

            if not set(selected_volume_identifiers).difference(volume_identifiers):
                return selected_volume_identifiers

        """if len(volume_identifiers) > 1:
            try:
                volume_identifiers = self._PromptUserForAPFSVolumeIdentifiers(
                    volume_system, volume_identifiers)
            except KeyboardInterrupt:
                raise errors.UserAbort('File system scan aborted.')"""

        return self._NormalizedVolumeIdentifiers(
            volume_system, volume_identifiers, prefix='apfs')

    def _GetVSSStoreIdentifiers(self, scan_node):

        if not scan_node or not scan_node.path_spec:
            raise errors.SourceScannerError('Invalid scan node.')

        volume_system = vshadow_volume_system.VShadowVolumeSystem()
        volume_system.Open(scan_node.path_spec)

        volume_identifiers = self._source_scanner.GetVolumeIdentifiers(
            volume_system)
        if not volume_identifiers:
            return []

        # TODO: refactor to use scan options.
        if self._vss_stores:
            if self._vss_stores == 'all':
                vss_stores = range(1, volume_system.number_of_volumes + 1)
            else:
                vss_stores = self._ParseVolumeIdentifiersString(
                    self._vss_stores, prefix='vss')

            selected_volume_identifiers = self._NormalizedVolumeIdentifiers(
                volume_system, vss_stores, prefix='vss')

            if not set(selected_volume_identifiers).difference(volume_identifiers):
                return selected_volume_identifiers

        return self._NormalizedVolumeIdentifiers(
            volume_system, volume_identifiers, prefix='vss')

    def _ParseVolumeIdentifiersString(self, volume_identifiers_string, prefix='v'):

        prefix_length = 0
        if prefix:
            prefix_length = len(prefix)

        if not volume_identifiers_string:
            return []

        if volume_identifiers_string == 'all':
            return ['all']

        volume_identifiers = set()
        for identifiers_range in volume_identifiers_string.split(','):
            # Determine if the range is formatted as 1..3 otherwise it indicates
            # a single volume identifier.
            if '..' in identifiers_range:
                first_identifier, last_identifier = identifiers_range.split('..')

                if first_identifier.startswith(prefix):
                    first_identifier = first_identifier[prefix_length:]

                if last_identifier.startswith(prefix):
                    last_identifier = last_identifier[prefix_length:]

                try:
                    first_identifier = int(first_identifier, 10)
                    last_identifier = int(last_identifier, 10)
                except ValueError:
                    raise ValueError('Invalid volume identifiers range: {0:s}.'.format(
                        identifiers_range))

                for volume_identifier in range(first_identifier, last_identifier + 1):
                    if volume_identifier not in volume_identifiers:
                        volume_identifier = '{0:s}{1:d}'.format(prefix, volume_identifier)
                        volume_identifiers.add(volume_identifier)
            else:
                identifier = identifiers_range
                if identifier.startswith(prefix):
                    identifier = identifiers_range[prefix_length:]

                try:
                    volume_identifier = int(identifier, 10)
                except ValueError:
                    raise ValueError('Invalid volume identifier range: {0:s}.'.format(
                        identifiers_range))

                volume_identifier = '{0:s}{1:d}'.format(prefix, volume_identifier)
                volume_identifiers.add(volume_identifier)

        # Note that sorted will return a list.
        return sorted(volume_identifiers)

    def _NormalizedVolumeIdentifiers(self, volume_system, volume_identifiers, prefix='v'):

        normalized_volume_identifiers = []
        for volume_identifier in volume_identifiers:
            if isinstance(volume_identifier, int):
                volume_identifier = '{0:s}{1:d}'.format(prefix, volume_identifier)

            elif not volume_identifier.startswith(prefix):
                try:
                    volume_identifier = int(volume_identifier, 10)
                    volume_identifier = '{0:s}{1:d}'.format(prefix, volume_identifier)
                except (TypeError, ValueError):
                    pass

            try:
                volume = volume_system.GetVolumeByIdentifier(volume_identifier)
            except KeyError:
                volume = None

            if not volume:
                raise errors.SourceScannerError(
                    'Volume missing for identifier: {0:s}.'.format(volume_identifier))

            normalized_volume_identifiers.append(volume_identifier)

        return normalized_volume_identifiers

    def LoadReferenceDataSet(self):
        try:
            self._rds = csv.read_csv('/home/carpe/rds/NSRLFile.txt')
            self._rds_set = set([x.upper() for x in self._rds.columns[0].to_pylist()])
        except KeyboardInterrupt:
            raise errors.UserAbort('File system scan aborted.')

    def InsertImageInformation(self):
        if not self._source_path_specs:
            logger.error('source is empty')
            return

        disk_info = []
        for path_spec in self._source_path_specs:
            filesystem_type = None
            bytes_per_cluster = 0

            if path_spec.type_indicator == dfvfs_definitions.TYPE_INDICATOR_OS:
                block_size = 0
                block_count = 0
                filesystem = None
                base_path_spec = path_spec

                disk_info.append({
                    "base_path_spec": base_path_spec, "type_indicator": path_spec.type_indicator,
                    "length": block_count * block_size, "bytes_per_sector": block_size, "start_sector": 0,
                    "bytes_per_cluster": block_size,
                    "vol_name": 'p1', "identifier": None, "par_label": None, "filesystem": filesystem
                })
                self._InsertDiskInfo(disk_info)
                return disk_info

            if not path_spec.parent:
                return False

            if path_spec.parent.IsVolumeSystem():
                if path_spec.IsFileSystem():
                    fs = dfvfs_resolver.Resolver.OpenFileSystem(path_spec)
                    if path_spec.type_indicator == dfvfs_definitions.TYPE_INDICATOR_TSK:
                        fs_info = fs.GetFsInfo()
                        filesystem_type = getattr(fs_info.info, 'ftype', None)
                        bytes_per_cluster = getattr(fs_info.info, 'block_size', 0)
                    elif path_spec.type_indicator == dfvfs_definitions.TYPE_INDICATOR_NTFS:
                        filesystem_type = fs.type_indicator
                        bytes_per_cluster = fs._fsntfs_volume.cluster_block_size
                path_spec = path_spec.parent

            try:
                file_system = dfvfs_resolver.Resolver.OpenFileSystem(path_spec)
            except Exception as e:
                print("No Filesystem")
                return False

            # VolumeSystem: Partition(gpt, mbr), APFS Container, LVM, VSHADOW
            if path_spec.type_indicator == dfvfs_definitions.TYPE_INDICATOR_TSK_PARTITION:

                tsk_volumes = file_system.GetTSKVolume()
                vol_part, _ = dfvfs_partition.GetTSKVsPartByPathSpec(tsk_volumes, path_spec)

                if dfvfs_partition.TSKVsPartIsAllocated(vol_part):
                    bytes_per_sector = dfvfs_partition.TSKVolumeGetBytesPerSector(vol_part)
                    length = dfvfs_partition.TSKVsPartGetNumberOfSectors(vol_part)
                    start_sector = dfvfs_partition.TSKVsPartGetStartSector(vol_part)
                    par_label = getattr(vol_part, 'desc', None)
                    try:
                        temp = par_label.decode('ascii')
                        par_label = temp
                    except UnicodeDecodeError:
                        par_label = par_label.decode('utf-8')
                    volume_name = getattr(path_spec, 'location', None)[1:]
                    base_path_spec = path_spec
                    disk_info.append({
                        "base_path_spec": base_path_spec, "type_indicator": path_spec.type_indicator,
                        "length": length * bytes_per_sector, "bytes_per_sector": bytes_per_sector,
                        "start_sector": start_sector, "bytes_per_cluster": bytes_per_cluster,
                        "vol_name": volume_name, "identifier": None,
                        "par_label": par_label, "filesystem": filesystem_type
                    })

            # filesystem
            elif path_spec.type_indicator == dfvfs_definitions.TYPE_INDICATOR_TSK:
                file_system = dfvfs_resolver.Resolver.OpenFileSystem(path_spec)
                fs_info = file_system.GetFsInfo()
                sector_size = getattr(fs_info.info, 'dev_bsize', 0)
                block_size = getattr(fs_info.info, 'block_size', 0)
                block_count = getattr(fs_info.info, 'block_count', 0)
                filesystem = getattr(fs_info.info, 'ftype', None)
                base_path_spec = path_spec

                disk_info.append({
                    "base_path_spec": base_path_spec, "type_indicator": path_spec.type_indicator,
                    "length": block_count * block_size, "bytes_per_sector": sector_size, "start_sector": 0,
                    "bytes_per_cluster": block_size,
                    "vol_name": 'p1', "identifier": None, "par_label": None, "filesystem": filesystem
                })

            elif path_spec.type_indicator == dfvfs_definitions.TYPE_INDICATOR_NTFS:
                file_system = dfvfs_resolver.Resolver.OpenFileSystem(path_spec)
                sector_size = getattr(file_system._fsntfs_volume, 'bytes_per_sector', 0)
                block_size = getattr(file_system._fsntfs_volume, 'cluster_block_size', 0)
                # TODO: there is no block_count in libfsntfs
                filesystem = 'NTFS'
                par_label = getattr(file_system._fsntfs_volume, 'name', None)
                size = getattr(file_system._file_object._file_object, 'cluster_block_size', 0)
                base_path_spec = path_spec

                disk_info.append({
                    "base_path_spec": base_path_spec, "type_indicator": path_spec.type_indicator,
                    "length": size, "bytes_per_sector": sector_size, "start_sector": 0,
                    "bytes_per_cluster": block_size,
                    "vol_name": 'p1', "identifier": None, "par_label": par_label, "filesystem": filesystem
                })

            elif path_spec.type_indicator == dfvfs_definitions.TYPE_INDICATOR_VSHADOW and self._process_vss:
                vss_volumes = file_system.GetVShadowVolume()
                store_index = dfvfs_vshadow.VShadowPathSpecGetStoreIndex(path_spec)

                vss_part = list(vss_volumes.stores)[store_index]
                length = vss_part.volume_size
                identifier = getattr(vss_part, 'identifier', None)
                volume_name = getattr(path_spec, 'location', None)[1:]
                base_path_spec = path_spec
                disk_info.append({
                    "base_path_spec": base_path_spec, "type_indicator": path_spec.type_indicator,
                    "length": length, "bytes_per_sector": None, "start_sector": None,
                    "bytes_per_cluster": None, "vol_name": volume_name,
                    "identifier": identifier, "par_label": None, "filesystem": None
                })

        self._InsertDiskInfo(disk_info)
        # for V&V test
        return disk_info

    def _InsertDiskInfo(self, disk_info):

        for disk in disk_info:
            if str(disk['type_indicator']) == dfvfs_definitions.TYPE_INDICATOR_VSHADOW:
                par_id = 'v1' + str(uuid.uuid4()).replace('-', '')
            else:
                par_id = 'p1' + str(uuid.uuid4()).replace('-', '')
            par_name = str(disk['vol_name'])
            par_type = str(disk['type_indicator'])
            sector_size = str(disk['bytes_per_sector'])
            par_size = str(disk['length'])
            start_sector = str(disk['start_sector'])
            bytes_per_cluster = str(disk['bytes_per_cluster'])
            par_label = str(disk['par_label'])
            filesystem = str(disk['filesystem'])

            try:
                query = "INSERT INTO partition_info(par_id, par_name, evd_id, par_type, sector_size, par_size, " \
                        "start_sector, cluster_size, par_label, filesystem) VALUES('" \
                        + par_id + "', '" + par_name + "', '" + self.evidence_id + "', '" + par_type + "', '" + \
                        sector_size + "', '" + par_size + "', '" + start_sector + "', '" + bytes_per_cluster + \
                        "', '" + par_label + "', '" + filesystem + "');"
                self._cursor.execute_query(query)

                partition_dir = \
                    self._root_tmp_path + os.sep + self.case_id + os.sep + self.evidence_id + os.sep + par_id
                if not os.path.exists(partition_dir):
                    os.mkdir(partition_dir)

                self._partition_list[par_name] = par_id

            except Exception as exception:
                self._output_writer.Write(exception)

    def InsertFileInformation(self):

        path_spec_extractor = path_extractors.PathSpecExtractor()

        path_spec_generator = path_spec_extractor.ExtractPathSpecs(
            self._source_path_specs, find_specs=None, recurse_file_system=False,
            resolver_context=self._resolver_context)

        for path_spec in path_spec_generator:

            if path_spec.IsFileSystem():
                self._RecursiveFileSearch(path_spec)
            elif path_spec.type_indicator == 'OS':
                self._RecursiveFileSearchForOS(path_spec)
            else:
                logger.warning('{0!s} filesystem was not detected.'.format(path_spec.location))

    def _RecursiveFileSearch(self, path_spec):

        if path_spec.type_indicator == dfvfs_definitions.TYPE_INDICATOR_TSK and \
                path_spec.parent.TYPE_INDICATOR != 'VSHADOW':
            self._ProcessFileOrDirectoryForTSK(path_spec)
            pass
        elif path_spec.parent.TYPE_INDICATOR == 'VSHADOW' and self._process_vss:
            self._ProcessFileOrDirectoryForTSK(path_spec)
            pass
        elif path_spec.type_indicator == dfvfs_definitions.TYPE_INDICATOR_NTFS:
            self._ProcessFileOrDirectoryForNTFS(path_spec)
        else:
            logger.warning('{0!s} No filesystem was found.'.format(path_spec.location))
            return

    def _RecursiveFileSearchForOS(self, path_spec):

        if path_spec.type_indicator == dfvfs_definitions.TYPE_INDICATOR_OS:
            self._ProcessFileOrDirectoryForOS(path_spec, 'root')
        else:
            logger.warning('{0!s} No file or directory was found.'.format(path_spec.location))
            return

    def _ProcessFileOrDirectoryForTSK(self, path_spec, parent_id=None):

        current_display_name = path_helper.PathHelper.GetDisplayNameForPathSpec(path_spec)

        file_entry = dfvfs_resolver.Resolver.OpenFileEntry(path_spec)

        if file_entry is None:
            logger.warning('Unable to open file entry with path spec: {0:s}'.format(current_display_name))
            return

        current_id = file_entry._tsk_file.info.meta.addr

        try:
            if file_entry.IsDirectory():
                for sub_file_entry in file_entry.sub_file_entries:
                    try:
                        if not sub_file_entry.IsAllocated():
                            continue

                    except dfvfs_errors.BackEndError as exception:
                        logger.warning(
                            'Unable to process file: {0:s} with error: {1!s}'.format(
                                sub_file_entry.path_spec.comparable.replace('\n', ';'), exception))
                        continue

                    if sub_file_entry.type_indicator == dfvfs_definitions.TYPE_INDICATOR_TSK:
                        if file_entry.IsRoot() and sub_file_entry.name == '$OrphanFiles':
                            continue

                    self._ProcessFileOrDirectoryForTSK(sub_file_entry.path_spec, current_id)

        except dfvfs_errors.AccessError as exception:
            logger.warning(
                'Unable to access file: {0:s} with error: {1!s}'.format(
                    file_entry.path_spec.comparable.replace(
                        '\n', ';'), exception))

        self._InsertFileInfoForTSK(file_entry, parent_id=parent_id)
        file_entry = None

    def _InsertFileInfoForTSK(self, file_entry, parent_id=0):

        if file_entry.name in ['', '.', '..']:
            return

        files = []
        tsk_file = file_entry.GetTSKFile()
        file = CarpeFile.CarpeFile()
        file._name = file_entry.name

        if len(self._partition_list) > 1:
            parent_location = getattr(file_entry.path_spec.parent, 'location', None)
            file._p_id = self._partition_list[parent_location[1:]]
        else:
            file._p_id = self._partition_list[list(self._partition_list.keys())[0]]  # check

        location = getattr(file_entry.path_spec, 'location', None)

        if location is None:
            return
        else:
            file._parent_path = 'root' + str(pathlib.PurePosixPath(location).parent)

        file._parent_id = parent_id

        # entry_type
        if file_entry.entry_type == 'file':
            file._dir_type = 5
            _, file._extension = os.path.splitext(file_entry.name)
            if file._extension:
                file._extension = file._extension[1:]
        elif file_entry.entry_type == 'directory':
            file._dir_type = 3
        else:
            if file_entry.name == '$MBR' or file_entry.name == '$FAT1' or file_entry.name == '$FAT2':
                file._dir_type = 10
            elif file_entry.name == '$OrphanFiles':
                file._dir_type = 11
            else:
                file._dir_type = 0

        file._meta_type = [lambda: 0, lambda: int(tsk_file.info.meta.type)][tsk_file.info.meta is not None]()
        file._file_id = tsk_file.info.meta.addr
        stat = file_entry._GetStat()
        file._size = [lambda: 0, lambda: stat.size][stat.size is not None]()
        file._mode = [lambda: 0, lambda: stat.mode][stat.mode is not None]()
        # TODO: meta_seq not found, temporarily set to 0
        file._meta_seq = 0
        file._gid = [lambda: 0, lambda: stat.gid][stat.gid is not None]()
        file._uid = [lambda: 0, lambda: stat.uid][stat.uid is not None]()
        file._ads = len(file_entry.data_streams)
        # TODO: temporarily set to ino > {0:d}-{1:d}-{2:d}
        # file._inode = stat.ino

        for attribute in file_entry.attributes:

            if attribute.attribute_type in definitions.ATTRIBUTE_TYPES_TO_ANALYZE:
                try:
                    file._inode = [lambda: "{0:d}".format(tsk_file.info.meta.addr),
                                   lambda: "{0:d}-{1:d}-{2:d}".format(tsk_file.info.meta.addr, int(attribute.info.type),
                                                                      attribute.info.id)] \
                        [tsk_file.info.fs_info.ftype in [definitions.TSK_FS_TYPE_NTFS,
                                                         definitions.TSK_FS_TYPE_NTFS_DETECT]]()
                except AttributeError:
                    raise AttributeError

                # $Standard_Information
                if attribute.attribute_type in definitions.ATTRIBUTE_TYPES_TO_ANALYZE_TIME:
                    file._mtime = [lambda: 0, lambda: tsk_file.info.meta.mtime][
                        tsk_file.info.meta.mtime is not None]()
                    file._atime = [lambda: 0, lambda: tsk_file.info.meta.atime][
                        tsk_file.info.meta.atime is not None]()
                    file._etime = [lambda: 0, lambda: tsk_file.info.meta.ctime][
                        tsk_file.info.meta.ctime is not None]()
                    file._ctime = [lambda: 0, lambda: tsk_file.info.meta.crtime][
                        tsk_file.info.meta.crtime is not None]()

                    file._mtime_nano = [lambda: 0, lambda: tsk_file.info.meta.mtime_nano][
                        tsk_file.info.meta.mtime_nano is not None]()
                    file._atime_nano = [lambda: 0, lambda: tsk_file.info.meta.atime_nano][
                        tsk_file.info.meta.atime_nano is not None]()
                    file._etime_nano = [lambda: 0, lambda: tsk_file.info.meta.ctime_nano][
                        tsk_file.info.meta.ctime_nano is not None]()
                    file._ctime_nano = [lambda: 0, lambda: tsk_file.info.meta.crtime_nano][
                        tsk_file.info.meta.crtime_nano is not None]()

                # $FileName
                if attribute.attribute_type in definitions.ATTRIBUTE_TYPES_TO_ANALYZE_ADDITIONAL_TIME:
                    file._additional_mtime = [lambda: 0, lambda: tsk_file.info.meta.mtime][
                        tsk_file.info.meta.mtime is not None]()
                    file._additional_atime = [lambda: 0, lambda: tsk_file.info.meta.atime][
                        tsk_file.info.meta.atime is not None]()
                    file._additional_etime = [lambda: 0, lambda: tsk_file.info.meta.ctime][
                        tsk_file.info.meta.ctime is not None]()
                    file._additional_ctime = [lambda: 0, lambda: tsk_file.info.meta.crtime][
                        tsk_file.info.meta.crtime is not None]()

                    file._additional_mtime_nano = [lambda: 0, lambda: tsk_file.info.meta.mtime_nano][
                        tsk_file.info.meta.mtime_nano is not None]()
                    file._additional_atime_nano = [lambda: 0, lambda: tsk_file.info.meta.atime_nano][
                        tsk_file.info.meta.atime_nano is not None]()
                    file._additional_etime_nano = [lambda: 0, lambda: tsk_file.info.meta.ctime_nano][
                        tsk_file.info.meta.ctime_nano is not None]()
                    file._additional_ctime_nano = [lambda: 0, lambda: tsk_file.info.meta.crtime_nano][
                        tsk_file.info.meta.crtime_nano is not None]()
            else:
                logger.info('[{0!s}]Deal with other attribute types'.format(file_entry.name))

        if file_entry.IsFile():
            for data_stream in file_entry.data_streams:
                signature_result = ''
                hash_result = ''
                rds_result = ''
                if self.signature_check and file._size > 0 and file_entry.IsFile():

                    file_object = file_entry.GetFileObject(data_stream_name=data_stream.name)

                    if not file_object:
                        return False

                    try:
                        results = self._signature_tool.ScanFileObject(file_object)

                        if results:
                            sig = results[0].identifier.split(':')
                            signature_result = sig[0]
                        # else:
                        #     file_object.seek(0, os.SEEK_SET)
                        #     file_content = file_object.read()
                        #     self._signature_tool.siga.Identify(file_content)

                        #     if self._signature_tool.siga.ext:
                        #         signature_result = self._signature_tool.siga.ext[1:]

                    except IOError as exception:
                        raise errors.BackEndError(
                            'Unable to scan file: error: {0:s}'.format(exception))
                    #finally:
                        #file_object.close()

                if self.rds_check and file._size > 0 and file_entry.IsFile():

                    file_object = file_entry.GetFileObject(data_stream_name=data_stream.name)

                    if not file_object:
                        return False

                    try:
                        hash_result = hashlib.sha1(file_object.read(file._size)).hexdigest().upper()
                    except Exception as exception:
                        # raise errors.HashCalculateError(
                        #     'Failed to compute SHA1 hash for file({0:s}): error: {1:s} '.format(file_entry.name,
                        #                                                                         exception))
                        print(f'Failed to compute SHA1 hash for file: {file_entry.name}')
                        print(f'Exception: {exception}')
                        continue

                    #finally:
                        #file_object.close()

                    if hash_result in self._rds_set:
                        rds_result = "Matching"
                    else:
                        rds_result = "Not Matching"

                if data_stream.name:
                    file_ads = CarpeFile.CarpeFile()
                    file_ads.__dict__ = file.__dict__.copy()
                    file_ads._name = file._name + ":" + data_stream.name
                    file_ads._extension = ''
                    file_ads._size = data_stream._tsk_attribute.info.size
                    file_ads._sig_type = signature_result
                    file_ads._sha1 = hash_result
                    file_ads._rds_existed = rds_result
                    files.append(file_ads)
                else:
                    file._sig_type = signature_result
                    file._sha1 = hash_result
                    file._rds_existed = rds_result
                    files.append(file)
        else:
            files.append(file)

        # for slack
        _temp_files = copy.deepcopy(files)
        for _temp_file in _temp_files:
            slack_size = 0
            if file._size > 0 and _temp_file._size % tsk_file.info.fs_info.block_size > 0:
                slack_size = tsk_file.info.fs_info.block_size - (_temp_file._size % tsk_file.info.fs_info.block_size)

            if slack_size > 0:
                file_slack = CarpeFile.CarpeFile()
                file_slack._size = slack_size
                file_slack._file_id = _temp_file._file_id
                file_slack._p_id = _temp_file._p_id
                file_slack._parent_path = _temp_file._parent_path
                file_slack._type = 7
                file_slack._name = _temp_file._name + '-slack'
                files.append(file_slack)

        self._InsertFileInfoRecords(files)
        # print(file._name +":"+ str(file._sha1) + ":"+str(file._sig_type))

    def _ProcessFileOrDirectoryForNTFS(self, path_spec, parent_id=None):
        current_display_name = path_helper.PathHelper.GetDisplayNameForPathSpec(path_spec)

        file_entry = dfvfs_resolver.Resolver.OpenFileEntry(
            path_spec)

        if file_entry is None:
            logger.warning('Unable to open file entry with path spec: {0:s}'.format(current_display_name))
            return

        if file_entry.IsRoot():
            current_id = 5
        else:
            current_id = file_entry.path_spec.mft_entry

        try:
            if file_entry.IsDirectory():
                try:
                    for sub_file_entry in file_entry.sub_file_entries:
                        try:
                            if not sub_file_entry.IsAllocated():
                                continue

                        except dfvfs_errors.BackEndError as exception:
                            logger.warning(

                                'Unable to process file: {0:s} with error: {1!s}'.format(
                                    sub_file_entry.path_spec.comparable.replace(
                                        '\n', ';'), exception))
                            continue

                        if sub_file_entry.type_indicator == dfvfs_definitions.TYPE_INDICATOR_NTFS:
                            if file_entry.IsRoot() and sub_file_entry.name == '$OrphanFiles':
                                continue

                        self._ProcessFileOrDirectoryForNTFS(sub_file_entry.path_spec, current_id)
                except Exception as e:
                    logger.error(e)
        except dfvfs_errors.AccessError as exception:
            logger.warning(
                'Unable to access file: {0:s} with error: {1!s}'.format(
                    file_entry.path_spec.comparable.replace(
                        '\n', ';'), exception))

        self._InsertFileInfoForNTFS(file_entry, parent_id=parent_id)
        file_entry = None

    def _InsertFileInfoForNTFS(self, file_entry, parent_id=0):
        if file_entry.name in ['', '.', '..']:
            return

        files = []
        file = CarpeFile.CarpeFile()

        file._name = file_entry.name

        if len(self._partition_list) > 1:
            parent_location = getattr(file_entry.path_spec.parent, 'location', None)
            file._p_id = self._partition_list[parent_location[1:]]
        else:
            file._p_id = self._partition_list[list(self._partition_list.keys())[0]]  # check

        location = getattr(file_entry.path_spec, 'location', None)

        if location is None:
            return
        else:
            file._parent_path = 'root' + str(pathlib.PureWindowsPath(location).parent)

        file._parent_id = parent_id

        # entry_type
        if file_entry.entry_type == 'file':
            file._dir_type = 5
            _, file._extension = os.path.splitext(file_entry.name)
            if file._extension:
                file._extension = file._extension[1:]
        elif file_entry.entry_type == 'directory':
            file._dir_type = 3
        else:
            if file_entry.name == '$OrphanFiles':
                file._dir_type = 11
            else:
                file._dir_type = 0

        file._file_id = file_entry.path_spec.mft_entry
        file._meta_type = [lambda: 0, lambda: int(file_entry.path_spec.mft_attribute)][
            file_entry.path_spec.mft_attribute is not None]()
        stat = file_entry._GetStat()
        file._size = [lambda: 0, lambda: stat.size][stat.size is not None]()
        file._mode = [lambda: 0, lambda: stat.mode][stat.mode is not None]()
        # TODO: meta_seq not found, temporarily set to 0
        file._meta_seq = 0
        file._gid = [lambda: 0, lambda: stat.gid][stat.gid is not None]()
        file._uid = [lambda: 0, lambda: stat.uid][stat.uid is not None]()
        file._ads = len(file_entry.data_streams)
        # TODO: temporarily set to ino > {0:d}-{1:d}-{2:d}
        file._inode = stat.ino

        for attribute in file_entry.attributes:
            # NTFS
            if attribute.attribute_type in definitions.ATTRIBUTE_TYPES_TO_ANALYZE:

                # file._inode = "{0:d}-{1:d}-{2:d}".format(file_entry.path_spec.mft_entry, int(attribute.info.type),
                #                                                    attribute.info.id)

                # $Standard_Information
                if attribute.attribute_type == definitions.TSK_FS_ATTR_TYPE_NTFS_SI:
                    file._mtime = [lambda: 0, lambda: attribute.modification_time.timestamp // 10000000][
                        attribute.modification_time is not None]()
                    file._atime = [lambda: 0, lambda: attribute.access_time.timestamp // 10000000][
                        attribute.access_time is not None]()
                    file._ctime = [lambda: 0, lambda: attribute.creation_time.timestamp // 10000000][
                        attribute.creation_time is not None]()
                    file._etime = [lambda: 0, lambda: attribute.entry_modification_time.timestamp // 10000000][
                        attribute.entry_modification_time is not None]()

                    file._mtime_nano = [lambda: 0, lambda: attribute.modification_time.timestamp % 10000000][
                        attribute.modification_time.timestamp is not None]()
                    file._atime_nano = [lambda: 0, lambda: attribute.access_time.timestamp % 10000000][
                        attribute.access_time is not None]()
                    file._ctime_nano = [lambda: 0, lambda: attribute.creation_time.timestamp % 10000000][
                        attribute.creation_time is not None]()
                    file._etime_nano = [lambda: 0, lambda: attribute.entry_modification_time.timestamp % 10000000][
                        attribute.entry_modification_time is not None]()

                # $FileName
                if attribute.attribute_type == definitions.TSK_FS_ATTR_TYPE_NTFS_FNAME:
                    file._additional_mtime = [lambda: 0, lambda: attribute.modification_time.timestamp // 10000000][
                        attribute.modification_time is not None]()
                    file._additional_atime = [lambda: 0, lambda: attribute.access_time.timestamp // 10000000][
                        attribute.access_time is not None]()
                    file._additional_ctime = [lambda: 0, lambda: attribute.creation_time.timestamp // 10000000][
                        attribute.creation_time is not None]()
                    file._additional_etime = \
                    [lambda: 0, lambda: attribute.entry_modification_time.timestamp // 10000000][
                        attribute.entry_modification_time is not None]()

                    file._additional_mtime_nano = [lambda: 0, lambda: attribute.modification_time.timestamp % 10000000][
                        attribute.modification_time.timestamp is not None]()
                    file._additional_atime_nano = [lambda: 0, lambda: attribute.access_time.timestamp % 10000000][
                        attribute.access_time is not None]()
                    file._additional_ctime_nano = [lambda: 0, lambda: attribute.creation_time.timestamp % 10000000][
                        attribute.creation_time is not None]()
                    file._additional_etime_nano = \
                    [lambda: 0, lambda: attribute.entry_modification_time.timestamp % 10000000][
                        attribute.entry_modification_time is not None]()

            else:
                logger.info('[{0!s}]Deal with other attribute types'.format(file_entry.name))

        if file_entry.IsFile():
            for data_stream in file_entry.data_streams:
                signature_result = ''
                hash_result = ''
                rds_result = ''

                if self.signature_check and file._size > 0 and file_entry.IsFile():

                    file_object = file_entry.GetFileObject(data_stream_name=data_stream.name)

                    if not file_object:
                        return False

                    try:
                        results = self._signature_tool.ScanFileObject(file_object)

                        if results:
                            sig = results[0].identifier.split(':')
                            signature_result = sig[0]
                        # else:
                        #     file_object.seek(0, os.SEEK_SET)
                        #     file_content = file_object.read(4096)
                        #     self._signature_tool.siga.Identify(file_content)

                        #     if self._signature_tool.siga.ext:
                        #         signature_result = self._signature_tool.siga.ext[1:]
                    except IOError as exception:
                        raise errors.BackEndError(
                            'Unable to scan file: error: {0:s}'.format(exception))
                    # finally:
                    #     file_object.close()

                if self.rds_check and file._size > 0 and file_entry.IsFile():

                    file_object = file_entry.GetFileObject(data_stream_name=data_stream.name)

                    if not file_object:
                        return False

                    try:
                        hash_result = hashlib.sha1(file_object.read(file._size)).hexdigest().upper()
                    except Exception as exception:
                        # raise errors.HashCalculateError(
                        #     'Failed to compute SHA1 hash for file({0:s}): error: {1:s} '.format(file_entry.name,
                        #                                                                         exception))
                        print(f'Failed to compute SHA1 hash for file: {file_entry.name}')
                        print(f'Exception: {exception}')
                        continue

                    #finally:
#                        file_object.close()

                    if hash_result in self._rds_set:
                        rds_result = "Matching"
                    else:
                        rds_result = "Not Matching"

                if data_stream.name:
                    file_ads = CarpeFile.CarpeFile()
                    file_ads.__dict__ = file.__dict__.copy()
                    file_ads._name = file._name + ":" + data_stream.name
                    file_ads._extension = ''
                    file_ads._size = data_stream._fsntfs_data_stream.size
                    file_ads._sig_type = signature_result
                    file_ads._sha1 = hash_result
                    file_ads._rds_existed = rds_result
                    files.append(file_ads)
                else:
                    file._sig_type = signature_result
                    file._sha1 = hash_result
                    file._rds_existed = rds_result
                    files.append(file)
        else:
            files.append(file)

        # for slack
        _temp_files = copy.deepcopy(files)
        for _temp_file in _temp_files:
            slack_size = 0
            if file._size > 0 and _temp_file._size % file_entry._file_system._fsntfs_volume.cluster_block_size > 0:
                slack_size = file_entry._file_system._fsntfs_volume.cluster_block_size - (
                            _temp_file._size % file_entry._file_system._fsntfs_volume.cluster_block_size)

            if slack_size > 0:
                file_slack = CarpeFile.CarpeFile()
                file_slack._size = slack_size
                file_slack._file_id = _temp_file._file_id
                file_slack._p_id = _temp_file._p_id
                file_slack._parent_path = _temp_file._parent_path
                file_slack._type = 7
                file_slack._name = _temp_file._name + '-slack'
                files.append(file_slack)

        self._InsertFileInfoRecords(files)

    def _ProcessFileOrDirectoryForOS(self, path_spec, parent_id=None):
        current_display_name = path_helper.PathHelper.GetDisplayNameForPathSpec(path_spec)

        file_entry = dfvfs_resolver.Resolver.OpenFileEntry(
            path_spec)

        if file_entry is None:
            logger.warning('Unable to open file entry with path spec: {0:s}'.format(current_display_name))
            return

        # TODO: root inode
        if parent_id == 'root':
            current_id = 5
        else:
            current_id = file_entry._stat_info.st_ino

        try:
            if file_entry.IsDirectory():

                for sub_file_entry in file_entry.sub_file_entries:
                    try:
                        if not sub_file_entry.IsAllocated():
                            continue

                    except dfvfs_errors.BackEndError as exception:
                        logger.warning(
                            'Unable to process file: {0:s} with error: {1!s}'.format(
                                sub_file_entry.path_spec.comparable.replace(
                                    '\n', ';'), exception))
                        continue

                    if sub_file_entry.type_indicator == dfvfs_definitions.TYPE_INDICATOR_OS:
                        if file_entry.IsRoot() and sub_file_entry.name == '$OrphanFiles':
                            continue

                    self._ProcessFileOrDirectoryForOS(sub_file_entry.path_spec, current_id)

        except dfvfs_errors.AccessError as exception:
            logger.warning(
                'Unable to access file: {0:s} with error: {1!s}'.format(
                    file_entry.path_spec.comparable.replace(
                        '\n', ';'), exception))

        self._InsertFileInfoForOS(file_entry, parent_id=parent_id)
        file_entry = None

    def _InsertFileInfoForOS(self, file_entry, parent_id=0):
        if file_entry.name in ['', '.', '..']:
            return

        files = []
        file = CarpeFile.CarpeFile()
        file._name = file_entry.name

        if len(self._partition_list) > 1:
            parent_location = getattr(file_entry.path_spec.parent, 'location', None)
            file._p_id = self._partition_list[parent_location[1:]]
        else:
            file._p_id = self._partition_list[list(self._partition_list.keys())[0]]  # check

        location = getattr(file_entry.path_spec, 'location', None)

        if location is None:
            return
        else:
            file._parent_path = os.path.dirname(location)

        file._parent_id = parent_id

        # entry_type
        if file_entry.entry_type == 'file':
            file._dir_type = 5
            _, file._extension = os.path.splitext(file_entry.name)
            if file._extension:
                file._extension = file._extension[1:]
        elif file_entry.entry_type == 'directory':
            file._dir_type = 3
        else:
            if file_entry.name == '$MBR' or file_entry.name == '$FAT1' or file_entry.name == '$FAT2':
                file._dir_type = 10
            elif file_entry.name == '$OrphanFiles':
                file._dir_type = 11
            else:
                file._dir_type = 0

        file._file_id = file_entry._stat_info.st_ino
        # TODO: meta_type not found, temporarily set to 0
        file._meta_type = 0
        stat = file_entry._GetStat()
        file._size = [lambda: 0, lambda: stat.size][stat.size is not None]()
        file._mode = [lambda: 0, lambda: stat.mode][stat.mode is not None]()
        # TODO: meta_seq not found, temporarily set to 0
        file._meta_seq = 0
        file._gid = [lambda: 0, lambda: stat.gid][stat.gid is not None]()
        file._uid = [lambda: 0, lambda: stat.uid][stat.uid is not None]()
        file._ads = len(file_entry.data_streams)
        # TODO: temporarily set to ino > {0:d}-{1:d}-{2:d}
        file._inode = stat.ino

        time_divide = 0
        try:
            if len(str(file_entry.creation_time.timestamp)) > 17:
                time_divide = 1000000000
        except:
            time_divide = 10000000

        # when Windows image input
        if platform.platform()[0:7] == 'Windows':
            file._ctime = [lambda: 0, lambda: file_entry.creation_time.timestamp // time_divide] \
                [file_entry.creation_time.timestamp is not None]()
            file._ctime_nano = [lambda: 0, lambda: file_entry.creation_time.timestamp % time_divide] \
                [file_entry.creation_time.timestamp is not None]()
            file._mtime = [lambda: 0, lambda: file_entry.modification_time.timestamp // time_divide] \
                [file_entry.modification_time.timestamp is not None]()
            file._mtime_nano = [lambda: 0, lambda: file_entry.modification_time.timestamp % time_divide] \
                [file_entry.modification_time.timestamp is not None]()
            file._atime = [lambda: 0, lambda: file_entry.access_time.timestamp // time_divide] \
                [file_entry.access_time.timestamp is not None]()
            file._atime_nano = [lambda: 0, lambda: file_entry.access_time.timestamp % time_divide] \
                [file_entry.access_time.timestamp is not None]()
            # file._crtime = [lambda: 0, lambda: file_entry.modification_time.timestamp // 10000000] \
            #     [file_entry.modification_time.timestamp is not None]()
            # file._crtime_nano = [lambda: 0, lambda: file_entry.modification_time.timestamp % 10000000] \
            #     [file_entry.modification_time.timestamp is not None]()

        # when Linux Server
        else :
            file._ctime = [lambda: 0, lambda: file_entry.creation_time.timestamp // time_divide] \
                [file_entry.creation_time is not None]()
            file._ctime_nano = [lambda: 0, lambda: file_entry.creation_time.timestamp % time_divide] \
                [file_entry.creation_time is not None]()
            file._mtime = [lambda: 0, lambda: file_entry.modification_time.timestamp // time_divide] \
                [file_entry.modification_time is not None]()
            file._mtime_nano = [lambda: 0, lambda: file_entry.modification_time.timestamp % time_divide] \
                [file_entry.modification_time is not None]()
            file._atime = [lambda: 0, lambda: file_entry.access_time.timestamp // time_divide] \
                [file_entry.access_time is not None]()
            file._atime_nano = [lambda: 0, lambda: file_entry.access_time.timestamp % time_divide] \
                [file_entry.access_time is not None]()
            # file._crtime = [lambda: 0, lambda: file_entry.modification_time.timestamp // 10000000] \
            #     [file_entry.modification_time.timestamp is not None]()
            # file._crtime_nano = [lambda: 0, lambda: file_entry.modification_time.timestamp % 10000000] \
            #     [file_entry.modification_time.timestamp is not None]()


        if file_entry.IsFile():
            for data_stream in file_entry.data_streams:
                signature_result = ''
                hash_result = ''
                rds_result = ''
                if self.signature_check and file._size > 0 and file_entry.IsFile():

                    file_object = file_entry.GetFileObject(data_stream_name=data_stream.name)

                    if not file_object:
                        return False

                    try:
                        results = self._signature_tool.ScanFileObject(file_object)

                        if results:
                            sig = results[0].identifier.split(':')
                            signature_result = sig[0]
                        # else:
                        #     file_object.seek(0, os.SEEK_SET)
                        #     file_content = file_object.read(4096)
                        #     self._signature_tool.siga.Identify(file_content)

                        #     if self._signature_tool.siga.ext:
                        #         signature_result = self._signature_tool.siga.ext[1:]

                    except IOError as exception:
                        raise errors.BackEndError(
                            'Unable to scan file: error: {0:s}'.format(exception))
                    #finally:
                        #file_object.close()

                if self.rds_check and file._size > 0 and file_entry.IsFile():

                    file_object = file_entry.GetFileObject(data_stream_name=data_stream.name)

                    if not file_object:
                        return False

                    try:
                        hash_result = hashlib.sha1(file_object.read(file._size)).hexdigest().upper()
                    except Exception as exception:
                        # raise errors.HashCalculateError(
                        #     'Failed to compute SHA1 hash for file({0:s}): error: {1:s} '.format(file_entry.name,
                        #                                                                         exception))
                        print(f'Failed to compute SHA1 hash for file: {file_entry.name}')
                        print(f'Exception: {exception}')
                        continue

                    #finally:
                        #file_object.close()

                    if hash_result in self._rds_set:
                        rds_result = "Matching"
                    else:
                        rds_result = "Not Matching"

                if data_stream.name:
                    file_ads = CarpeFile.CarpeFile()
                    file_ads.__dict__ = file.__dict__.copy()
                    file_ads._name = file._name + ":" + data_stream.name
                    file_ads._extension = ''
                    file_ads._size = data_stream._fsntfs_data_stream.size
                    file_ads._sig_type = signature_result
                    file_ads._sha1 = hash_result
                    file_ads._rds_existed = rds_result
                    files.append(file_ads)
                else:
                    file._sig_type = signature_result
                    file._sha1 = hash_result
                    file._rds_existed = rds_result
                    files.append(file)
        else:
            files.append(file)

        self._InsertFileInfoRecords(files)

    def _InsertFileInfoRecords(self, files):
        file_list = map(lambda f: f.toTuple(), files)
        for file in file_list:
            if file is not None:
                try:
                    query = self._cursor.insert_query_builder("file_info")
                    query = (query + "values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, "
                                     "%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, "
                                     "%s, %s, %s)")
                    self._cursor.bulk_execute(query, (file,))
                except Exception as exception:
                    logger.error(exception)
        # self._cursor.commit()

    def set_partition_list(self):
        query = f"SELECT par_name, par_id FROM partition_info WHERE evd_id='{self.evidence_id}'"
        results = self._cursor.execute_query_mul(query)
        self._partition_list = dict(results)
