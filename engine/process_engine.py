# -*- coding: utf-8 -*-

import os

from artifacts import errors as artifacts_errors
from artifacts import reader as artifacts_reader
from artifacts import registry as artifacts_registry
from dfvfs.lib import errors as dfvfs_errors
from dfvfs.path import factory as path_spec_factory
from dfvfs.helpers import file_system_searcher
from dfvfs.resolver import resolver as path_spec_resolver
from dfvfs.lib import definitions as dfvfs_definitions

from engine import logger, knowledge_base
from engine.preprocessors import manager as preprocess_manager
from modules import manager as modules_manager
from modules import interface as modules_interface
from advanced_modules import manager as advanced_modules_manager
from advanced_modules import interface as advanced_modules_interface

from utility import definitions
from utility import errors
from datetime import datetime


class ProcessEngine(object):

    def __init__(self):
        super(ProcessEngine, self).__init__()
        self._current_display_name = ''
        self._pid = os.getpid()
        self._modules = None
        self.knowledge_base = knowledge_base.KnowledgeBase()

    def SetProcessModules(self, module_filter_expression):
        self._modules = modules_manager.ModulesManager.GetModuleObjects(
            module_filter_expression=module_filter_expression)

        if not self._modules:
            raise errors.BadConfigOption

    def SetProcessAdvancedModules(self, advanced_module_filter_expression):
        self._advanced_modules = advanced_modules_manager.AdvancedModulesManager.GetModuleObjects(
            advanced_module_filter_expression=advanced_module_filter_expression)

        if not self._advanced_modules:
            raise errors.BadConfigOption

    def Preprocess(self, artifacts_registry_object, source_path_specs, resolver_context=None):
        detected_operating_systems = []
        for source_path_spec in source_path_specs:
            if source_path_spec.IsFileSystem():
                try:
                    file_system, mount_point = self._GetSourceFileSystem(
                        source_path_spec, resolver_context=resolver_context)
                except (RuntimeError, dfvfs_errors.BackEndError) as exception:
                    logger.error(exception)
                    continue

                try:
                    searcher = file_system_searcher.FileSystemSearcher(
                        file_system, mount_point)

                    operating_system = self._DetermineOperatingSystem(searcher)
                    if operating_system != definitions.OPERATING_SYSTEM_FAMILY_UNKNOWN:
                        preprocess_manager.PreprocessPluginsManager.RunPlugins(
                            artifacts_registry_object, file_system, mount_point, self.knowledge_base)

                    detected_operating_systems.append(operating_system)
                except:
                    pass
                # finally:
                #     file_system.Close()

        if detected_operating_systems:
            logger.info('Preprocessing detected operating systems: {0:s}'.format(
                ', '.join(detected_operating_systems)))
            self.knowledge_base.SetValue(
                'operating_system', detected_operating_systems)

    def Process(self, configuration):
        and_flag = False
        macos_flag = False

        for source_path_spec in configuration.source_path_specs:
            if source_path_spec.IsFileSystem() \
                    or source_path_spec.type_indicator == dfvfs_definitions.TYPE_INDICATOR_OS:
                try:
                    par_id = self.get_partition_id(source_path_spec, configuration)
                    # if configuration.source_type == 'directory' or 'file':

                    for module_name in self._modules:
                        module = self._modules.get(module_name, None)

                        if source_path_spec.TYPE_INDICATOR == 'APFS':  # for APFS & GUI
                            if module.NAME != 'macos_connector':
                                module.print_run_info(module.DESCRIPTION, start=True)
                                module.print_run_info(module.DESCRIPTION, start=False)
                                continue

                        if isinstance(module, modules_interface.ModuleConnector):
                            # Android Forensic Module
                            if module_name == 'andforensics_connector':
                                if not and_flag:
                                    module.print_run_info(module.DESCRIPTION, start=True)
                                    module.Connect(par_id=par_id, configuration=configuration,
                                                   source_path_spec=source_path_spec,
                                                   knowledge_base=self.knowledge_base)
                                    module.print_run_info(module.DESCRIPTION, start=False)
                                    and_flag = True
                                else:  # for GUI
                                    module.print_run_info(module.DESCRIPTION, start=True)
                                    module.print_run_info(module.DESCRIPTION, start=False)
                                    
                            # Skip these modules
                            elif module_name in ['andforensics_connector',
                                                 'fica_connector', 'extract_connector',
                                                 'image_classification_connector']:
                                pass
                            elif module_name == 'macos_connector':
                                if not macos_flag:
                                    module.print_run_info(module.DESCRIPTION, start=True)
                                    module.Connect(par_id='', configuration=configuration,
                                                   source_path_spec=source_path_spec,
                                                   knowledge_base=self.knowledge_base)
                                    module.print_run_info(module.DESCRIPTION, start=False)
                                    macos_flag = True
                                else:  # for GUI
                                    module.print_run_info(module.DESCRIPTION, start=True)
                                    module.print_run_info(module.DESCRIPTION, start=False)
                                    
                            # Other modules
                            else:
                                module.print_run_info(module.DESCRIPTION, start=True)
                                module.Connect(par_id=par_id,
                                               configuration=configuration,
                                               source_path_spec=source_path_spec,
                                               knowledge_base=self.knowledge_base)
                                module.print_run_info(module.DESCRIPTION, start=False)


                except RuntimeError as exception:
                    raise errors.BackEndError('The module cannot be connected: {0!s}'.format(exception))


    def ProcessAdvancedModules(self, configuration):
        os_usage_history_flag = False
        for source_path_spec in configuration.source_path_specs:
            if source_path_spec.IsFileSystem() \
                    or source_path_spec.type_indicator == dfvfs_definitions.TYPE_INDICATOR_OS:
                try:
                    par_id = self.get_partition_id(source_path_spec, configuration)
                    for advanced_module_name in self._advanced_modules:
                        advanced_module = self._advanced_modules.get(advanced_module_name, None)
                        if isinstance(advanced_module, advanced_modules_interface.AdvancedModuleAnalyzer):

                            if advanced_module_name == 'lv2_os_usage_history_analyzer':  # usage_history는 한 번만
                                if not os_usage_history_flag:
                                    advanced_module.print_run_info(advanced_module.DESCRIPTION, start=True)
                                    if source_path_spec.TYPE_INDICATOR == 'NTFS':
                                        advanced_module.Analyze(par_id=par_id,
                                                                configuration=configuration,
                                                                source_path_spec=source_path_spec,
                                                                knowledge_base=self.knowledge_base)
                                        os_usage_history_flag = True
                                    advanced_module.print_run_info(advanced_module.DESCRIPTION, start=False)
                                    continue
                                else:  # for GUI
                                    advanced_module.print_run_info(advanced_module.DESCRIPTION, start=True)
                                    advanced_module.print_run_info(advanced_module.DESCRIPTION, start=False)
                                    print()
                                    continue

                            advanced_module.print_run_info(advanced_module.DESCRIPTION, start=True)
                            advanced_module.Analyze(par_id=par_id,
                                                    configuration=configuration,
                                                    source_path_spec=source_path_spec,
                                                    knowledge_base=self.knowledge_base)
                            advanced_module.print_run_info(advanced_module.DESCRIPTION, start=False)
                except RuntimeError as exception:
                    raise errors.BackEndError(('The module cannot be connected: {0!s}').format(exception))

    def process_carve(self, configuration, is_partition=False):
        module = self._modules.get('fica_connector', None)

        if module is None:
            return

        if is_partition:
            for source_path_spec in configuration.source_path_specs:
                # Image
                if source_path_spec.IsFileSystem():
                    par_id = self.get_partition_id(source_path_spec, configuration)
                # File
                else:
                    par_id = configuration.partition_list['p1']

                module.print_run_info(module.DESCRIPTION, start=True)
                module.Connect(par_id=par_id,
                               configuration=configuration,
                               source_path_spec=source_path_spec,
                               knowledge_base=self.knowledge_base)
                module.print_run_info(module.DESCRIPTION, start=False)

        else:
            module.print_run_info(module.DESCRIPTION, start=True)
            module.Connect(configuration=configuration,
                           knowledge_base=self.knowledge_base)
            module.print_run_info(module.DESCRIPTION, start=False)

    def _GetSourceFileSystem(self, source_path_spec, resolver_context=None):

        if not source_path_spec:
            raise RuntimeError('Missing source path specification.')

        file_system = path_spec_resolver.Resolver.OpenFileSystem(
            source_path_spec, resolver_context=resolver_context)

        type_indicator = source_path_spec.type_indicator
        if path_spec_factory.Factory.IsSystemLevelTypeIndicator(type_indicator):
            mount_point = source_path_spec
        else:
            mount_point = source_path_spec.parent

        return file_system, mount_point

    def _DetermineOperatingSystem(self, searcher):

        find_specs = [
            file_system_searcher.FindSpec(
                case_sensitive=False, location='/etc',
                location_separator='/'),
            file_system_searcher.FindSpec(
                case_sensitive=False, location='/System/Library',
                location_separator='/'),
            file_system_searcher.FindSpec(
                case_sensitive=False, location='\\Windows\\System32',
                location_separator='\\'),
            file_system_searcher.FindSpec(
                case_sensitive=False, location='\\WINNT\\System32',
                location_separator='\\'),
            file_system_searcher.FindSpec(
                case_sensitive=False, location='\\WINNT35\\System32',
                location_separator='\\'),
            file_system_searcher.FindSpec(
                case_sensitive=False, location='\\WTSRV\\System32',
                location_separator='\\')]

        locations = []
        for path_spec in searcher.Find(find_specs=find_specs):
            relative_path = searcher.GetRelativePath(path_spec)
            if relative_path:
                locations.append(relative_path.lower())

        # We need to check for both forward and backward slashes since the path
        # spec will be OS dependent, as in running the tool on Windows will return
        # Windows paths (backward slash) vs. forward slash on *NIX systems.
        windows_locations = set([
            '/windows/system32', '\\windows\\system32', '/winnt/system32',
            '\\winnt\\system32', '/winnt35/system32', '\\winnt35\\system32',
            '\\wtsrv\\system32', '/wtsrv/system32'])

        operating_system = definitions.OPERATING_SYSTEM_FAMILY_UNKNOWN
        if windows_locations.intersection(set(locations)):
            operating_system = definitions.OPERATING_SYSTEM_FAMILY_WINDOWS_NT

        elif '/system/library' in locations:
            operating_system = definitions.OPERATING_SYSTEM_FAMILY_MACOS

        elif '/etc' in locations:
            operating_system = definitions.OPERATING_SYSTEM_FAMILY_LINUX

        return operating_system

    @classmethod
    def BuildArtifactsRegistry(
            cls, artifact_definitions_path, custom_artifacts_path):

        if artifact_definitions_path and not os.path.isdir(
                artifact_definitions_path):
            raise errors.BadConfigOption(
                'No such artifacts filter file: {0:s}.'.format(
                    artifact_definitions_path))

        if custom_artifacts_path and not os.path.isfile(custom_artifacts_path):
            raise errors.BadConfigOption(
                'No such artifacts filter file: {0:s}.'.format(custom_artifacts_path))

        registry = artifacts_registry.ArtifactDefinitionsRegistry()
        reader = artifacts_reader.YamlArtifactsReader()

        try:
            registry.ReadFromDirectory(reader, artifact_definitions_path)

        except (KeyError, artifacts_errors.FormatError) as exception:
            raise errors.BadConfigOption((
                                             'Unable to read artifact definitions from: {0:s} with error: '
                                             '{1!s}').format(artifact_definitions_path, exception))

        if custom_artifacts_path:
            try:
                registry.ReadFromFile(reader, custom_artifacts_path)

            except (KeyError, artifacts_errors.FormatError) as exception:
                raise errors.BadConfigOption((
                                                 'Unable to read artifact definitions from: {0:s} with error: '
                                                 '{1!s}').format(custom_artifacts_path, exception))
        return registry

    def get_partition_id(self, source_path_spec, configuration):
        if len(configuration.partition_list) > 1:
            parent_location = getattr(source_path_spec.parent, 'location', None)
            par_id = configuration.partition_list[parent_location[1:]]
        elif len(configuration.partition_list) == 0:
            par_id = ''
        else:
            par_id = configuration.partition_list[list(configuration.partition_list.keys())[0]]
        #print(f'[{self.print_now_time()}] Partition ID: {par_id}')
        return par_id

    def print_now_time(self):
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]