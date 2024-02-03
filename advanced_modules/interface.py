# -*- coding: utf-8 -*-

import os
import abc
import sys

import yaml
from datetime import datetime

import pytsk3

from dfvfs.helpers import file_system_searcher
from dfvfs.resolver import resolver as path_spec_resolver
from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.lib import errors as dfvfs_errors
from dfvfs.lib import tsk_image

from engine import path_extractors
from engine import path_helper
from advanced_modules import logger


class BaseAnalyzer(object):

    NAME = 'base_analyzer'
    DESCRIPTION = ''

    _plugin_classes = None

    def __init__(self):
        super(BaseAnalyzer, self).__init__()
        self._default_plugin = None
        self._plugins = None
        self._schema = None
        self.EnablePlugins([])

    @classmethod
    def DeregisterPlugin(cls, plugin_class):
        plugin_name = plugin_class.NAME.lower()
        if plugin_name not in cls._plugin_classes:
            raise KeyError(
                'Plugin class not set for name: {0:s}.'.format(
                    plugin_class.NAME))

        del cls._plugin_classes[plugin_name]

    def EnablePlugins(self, plugin_includes):
        self._plugins = []
        if not self._plugin_classes:
            return

        default_plugin_name = '{0:s}_default'.format(self.NAME)
        for plugin_name, plugin_class in iter(self._plugin_classes.items()):
            if plugin_name == default_plugin_name:
                self._default_plugin = plugin_class()
                continue

            if plugin_includes and plugin_name not in plugin_includes:
                continue

            plugin_object = plugin_class()
            self._plugins.append(plugin_object)

        """
        if "*" in plugin_includes:
          for _, plugin_class in iter(self._plugin_classes.items()):
            plugin_object = plugin_class()
            self._plugins.append(plugin_object)
        """

    # TODO: move this to a filter.
    # pylint: disable=redundant-returns-doc
    @classmethod
    def GetFormatSpecification(cls):
        """Retrieves the format specification.

        Returns:
          FormatSpecification: a format specification or None if not available.
        """
        return

    @classmethod
    def GetPluginObjectByName(cls, plugin_name):
        """Retrieves a specific plugin object by its name.

        Args:
          plugin_name (str): name of the plugin.

        Returns:
          BasePlugin: a plugin object or None if not available.
        """
        plugin_class = cls._plugin_classes.get(plugin_name, None)
        if plugin_class:
            return plugin_class()

        return None

    @classmethod
    def GetPlugins(cls):
        """Retrieves the registered plugins.

        Yields:
          tuple[str, type]: name and class of the plugin.
        """
        for plugin_name, plugin_class in iter(cls._plugin_classes.items()):
            yield plugin_name, plugin_class

    @classmethod
    def RegisterPlugin(cls, plugin_class):
        """Registers a plugin class.

        The plugin classes are identified based on their lower case name.

        Args:
          plugin_class (type): class of the plugin.

        Raises:
          KeyError: if plugin class is already set for the corresponding name.
        """
        plugin_name = plugin_class.NAME.lower()
        if plugin_name in cls._plugin_classes:
            raise KeyError((
                'Plugin class already set for name: {0:s}.').format(
                plugin_class.NAME))

        cls._plugin_classes[plugin_name] = plugin_class

    @classmethod
    def RegisterPlugins(cls, plugin_classes):
        """Registers plugin classes.

        Args:
          plugin_classes (list[type]): classes of plugins.

        Raises:
          KeyError: if plugin class is already set for the corresponding name.
        """
        for plugin_class in plugin_classes:
            cls.RegisterPlugin(plugin_class)

    @classmethod
    def SupportsPlugins(cls):
        """Determines if a caller supports plugins.

        Returns:
          bool: True if the caller supports plugins.
        """
        return cls._plugin_classes is not None


class AdvancedModuleAnalyzer(BaseAnalyzer):

    def __init__(self):
        super(AdvancedModuleAnalyzer, self).__init__()
        self._path_spec_extractor = path_extractors.PathSpecExtractor()

    @abc.abstractmethod
    def Analyze(self, par_id, configuration, source_path_spec, knowledge_base):
        """
        Analyze
        """

    def BuildFindSpecs(self, paths, path_separator, environment_variables=None):
        """Builds find specifications from path filters.

        Args:
          path_filters (list[PathFilter]): path filters.
          environment_variables (Optional[list[EnvironmentVariableArtifact]]):
              environment variables.

        Returns:
          list[dfvfs.FindSpec]: find specifications for the file source type.
        """
        find_specs = []
        for path in paths:
            # Since paths are regular expression the path separator is escaped.
            if path_separator == '\\':
                path_separator = '\\\\'
            else:
                path_separator = path_separator

            expand_path = False
            path_segments = path.split(path_separator)
            for index, path_segment in enumerate(path_segments):
                if len(path_segment) <= 2:
                    continue

                if path_segment[0] == '{' and path_segment[-1] == '}':
                    # Rewrite legacy path expansion attributes, such as {systemroot}
                    # into %SystemRoot%.
                    path_segment = '%{0:s}%'.format(path_segment[1:-1])
                    path_segments[index] = path_segment

                if path_segment[0] == '%' and path_segment[-1] == '%':
                    expand_path = True

            if expand_path:
                path_segments = path_helper.PathHelper.ExpandWindowsPathSegments(
                    path_segments, environment_variables)

            if path_segments[0] != '':
                logger.warning(
                    'The path filter must be defined as an absolute path: ''{0:s}'.format(path))
                continue

            # Strip the root path segment.
            path_segments.pop(0)

            if not path_segments[-1]:
                logger.warning(
                    'Empty last path segment in path: {0:s}'.format(path))
                continue

            find_spec = file_system_searcher.FindSpec(
                case_sensitive=False, location_regex=path_segments)

            find_specs.append(find_spec)

        return find_specs

    def get_tsk_file_system(self, source_path_spec, configuration):
        file_object = path_spec_resolver.Resolver.OpenFileObject(
            source_path_spec.parent, resolver_context=configuration.resolver_context)
        tsk_image_object = tsk_image.TSKFileSystemImage(file_object)
        tsk_file_system = pytsk3.FS_Info(tsk_image_object)
        return tsk_file_system

    def extract_file_object(self, tsk_file_system, inode):
        f = tsk_file_system.open_meta(inode)
        return f.read_random(0, f.info.meta.size)

    def extract_file_to_path(self, tsk_file_system, inode, file_name, output_path):
        file_object = tsk_file_system.open_meta(inode)
        try:
            output_file = open(output_path + os.sep + file_name, 'wb')
            file_size = file_object.info.meta.size
            if file_size > 0:
                data = file_object.read_random(0, file_object.info.meta.size)
                output_file.write(data)
            output_file.close()
        except Exception:
            print('Extract Error')
            return False

    def LoadTargetFileToMemory(self, source_path_spec, configuration,
                               file_path=None, file_spec=None, data_stream_name=None):
        try:
            if not file_spec:
                find_spec = file_system_searcher.FindSpec(
                    case_sensitive=False, location=file_path, location_separator=source_path_spec.location)
            else:
                find_spec = file_spec
        except ValueError as exception:
            logger.error(
                'Unable to build find specification for path: "{0:s}" with '
                'error: {1!s}'.format(file_path, exception))

        path_spec_generator = self._path_spec_extractor.ExtractPathSpecs(
            [source_path_spec], find_specs=[find_spec], recurse_file_system=False,
            resolver_context=configuration.resolver_context)

        for path_spec in path_spec_generator:
            display_name = path_helper.PathHelper.GetDisplayNameForPathSpec(path_spec)

            try:
                file_entry = path_spec_resolver.Resolver.OpenFileEntry(
                    path_spec, resolver_context=configuration.resolver_context)

                if file_entry is None or not file_entry.IsFile():
                    logger.warning(
                        'Unable to open file entry with path spec: {0:s}'.format(
                            display_name))
                    return False

                if data_stream_name:
                    file_object = file_entry.GetFileObject(data_stream_name=data_stream_name)

                    if not file_object:
                        return False

                    return file_object

                elif not data_stream_name:
                    file_object = file_entry.GetFileObject()

                    if not file_object:
                        return False

                    return file_object

            except KeyboardInterrupt:
                return False

    def ExtractTargetFileToPath(self, source_path_spec, configuration,
                                file_path=None, file_spec=None, output_path=None, data_stream_name=None):
        # TODO: find_spec 있을 경우 처리 해야함. Load참조

        try:
            if not file_spec:
                find_spec = file_system_searcher.FindSpec(
                    case_sensitive=False, location=file_path, location_separator=source_path_spec.location)
            else:
                find_spec = file_spec
        except ValueError as exception:
            logger.error(
                'Unable to build find specification for path: "{0:s}" with '
                'error: {1!s}'.format(file_path, exception))

        path_spec_generator = self._path_spec_extractor.ExtractPathSpecs(
            [source_path_spec], find_specs=[find_spec], recurse_file_system=False,
            resolver_context=configuration.resolver_context)

        for path_spec in path_spec_generator:
            display_name = path_helper.PathHelper.GetDisplayNameForPathSpec(path_spec)
            try:
                file_entry = path_spec_resolver.Resolver.OpenFileEntry(
                    path_spec, resolver_context=configuration.resolver_context)

                if file_entry is None or not file_entry.IsFile():
                    logger.warning(
                        'Unable to open file entry with path spec: {0:s}'.format(
                            display_name))
                    return False

                if data_stream_name:
                    file_object = file_entry.GetFileObject(data_stream_name=data_stream_name)

                    if not file_object:
                        return False

                    try:
                        buffer_size = 65536
                        file = open(output_path + os.sep + file_entry.name + '_' + data_stream_name, 'wb')
                        file_object.seek(0, os.SEEK_SET)
                        data = file_object.read(buffer_size)
                        while data:
                            file.write(data)
                            data = file_object.read(buffer_size)
                        file.close()

                    except IOError as exception:
                        # TODO: replace location by display name.
                        location = getattr(file_entry.path_spec, 'location', '')
                        logger.error(
                            'Failed to extract file "{0:s}" : {1!s}'.format(data_stream_name, exception))
                        return False

                    # finally:
                    #     file_object.close()

                elif not data_stream_name:
                    file_object = file_entry.GetFileObject()

                    if not file_object:
                        return False

                    try:
                        buffer_size = 65536
                        file = open(output_path + os.sep + file_entry.name, 'wb')
                        file_object.seek(0, os.SEEK_SET)
                        data = file_object.read(buffer_size)
                        while data:
                            file.write(data)
                            data = file_object.read(buffer_size)
                        file.close()
                    except IOError as exception:
                        logger.error(
                            'Failed to extract file "{0:s}" : {1!s}'.format(display_name, exception))
                    # finally:
                    #     file_object.close()

            except KeyboardInterrupt:
                return False

    def ExtractTargetDirToPath(self, source_path_spec, configuration, dir_path=None, file_spec=None, output_path=None):
        """Extract target directory to path

            Args:
                source_path_spec:
                configuration:
                dir_path:
                output_path:
        """
        try:
            if not file_spec:
                find_spec = file_system_searcher.FindSpec(
                    case_sensitive=False, location=dir_path,
                    location_separator=source_path_spec.location)
            else:
                find_spec = file_spec

        except ValueError as exception:
            logger.error(
                'Unable to build find specification for path: "{0:s}" with '
                'error: {1!s}'.format(dir_path, exception))

        path_spec_generator = self._path_spec_extractor.ExtractPathSpecs(
            [source_path_spec], find_specs=[find_spec], recurse_file_system=False,
            resolver_context=configuration.resolver_context)

        for path_spec in path_spec_generator:
            self.DirectoryTraversal(path_spec, output_path)

    def DirectoryTraversal(self, path_spec, output_path):
        if not os.path.exists(output_path):
            os.mkdir(output_path)

        _path_specs = []
        _path_specs.append(path_spec)

        self.RecursiveDirOrFileSearch(path_spec, output_path)

    def RecursiveDirOrFileSearch(self, path_spec, output_path):
        display_name = path_helper.PathHelper.GetDisplayNameForPathSpec(path_spec)

        file_entry = path_spec_resolver.Resolver.OpenFileEntry(path_spec)
        if file_entry is None:
            logger.warning(
                'Unable to open file entry with path spec: {0:s}'.format(
                    display_name))
            return False

        if file_entry.IsDirectory():
            if not os.path.exists(output_path + os.sep + file_entry.name):
                os.mkdir(output_path + os.sep + file_entry.name)

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

                if sub_file_entry.type_indicator == dfvfs_definitions.TYPE_INDICATOR_TSK:
                    if file_entry.IsRoot() and sub_file_entry.name == '$OrphanFiles':
                        continue

                self.RecursiveDirOrFileSearch(sub_file_entry.path_spec, output_path + os.sep + file_entry.name)

        if file_entry.IsFile():

            for data_stream in file_entry.data_streams:
                file_object = file_entry.GetFileObject(data_stream_name=data_stream.name)
                if not file_object:
                    return False
                try:
                    buffer_size = 65536
                    file = open(output_path + os.sep + file_entry.name, 'wb')
                    file_object.seek(0, os.SEEK_SET)
                    data = file_object.read(buffer_size)
                    while data:
                        file.write(data)
                        data = file_object.read(buffer_size)
                    file.close()

                except IOError as exception:
                    print(display_name)
                    logger.error(
                        'Failed to extract file "{0:s}" : {1!s}'.format(display_name, exception))
                finally:
                    file_object.close()

    def LoadSchemaFromYaml(self, _yaml_path):

        if not os.path.exists(_yaml_path):
            return False

        yaml_data = open(_yaml_path, 'r')
        data = yaml_data.read()

        self._schema = yaml.safe_load(data)
        if not self._schema:
            return False
        return True

    def CreateTable(self, _cursor, _standalone_check=False):

        if not self._schema:
            return False

        # Read YAML Data Stream
        name = self._schema['Name']
        table = self._schema['Table'][0]['TableName']
        columns = self._schema['Table'][0]['Columns']
        types = self._schema['Table'][0]['Types']

        query = ["CREATE TABLE ", table, "("]

        for i in range(len(columns)):
            if _standalone_check:
                # For standalone mode: escape special character like '$'
                query.append('"' + columns[i] + '" ')
            else:
                query.append(columns[i] + ' ')

            if columns[i][:11].lower() == 'foreign key' or columns[i][:11].lower() == 'primary key':
                pass
            else:
                for j in range(0, len(types[i])):
                    if j == len(types) - 1:
                        query.append(types[i][j])
                    else:
                        query.append(types[i][j] + " ")

            if i != (len(columns) - 1):
                query.append(",")
            else:
                query.append(");")

        query = ''.join(query)

        _cursor.execute_query(query)

        return True

    def CreateTableWithSchema(self, _cursor, _table_name, _schema, _standalone_check=False):

        if not _schema:
            return False

        query = ["CREATE TABLE ", _table_name, "("]

        for i in range(0, len(_schema)):
            if _standalone_check:
                # For standalone mode: escape special character like '$'
                query.append('"' + _schema[i] + '" ')
            else:
                query.append('`' + _schema[i] + '` TEXT')

                if _schema[i][:11].lower() == 'foreign key' or _schema[i][:11].lower() == 'primary key':
                    pass
                else:
                    # TODO: 타입 처리 해야함
                    pass
                    """
                    for j in range(0, len(types[i])):
                        if j == len(types) - 1:
                            query.append(types[i][j])
                        else:
                            query.append(types[i][j] + " ")"""

                if i != (len(_schema) - 1):
                    query.append(",")
                else:
                    query.append(");")

        query = ''.join(query)

        _cursor.execute_query(query)

        return True

    def check_table_from_yaml(self, configuration, yaml_list, table_list):
        # Create all table
        for count in range(0, len(yaml_list)):
            if not self.LoadSchemaFromYaml(yaml_list[count]):
                logger.error('cannot load schema from yaml: {0:s}'.format(table_list[count]))
                return False
            # If table is not existed, create table
            if not configuration.cursor.check_table_exist(table_list[count]):
                ret = self.CreateTable(configuration.cursor, configuration.standalone_check)
                if not ret:
                    logger.error('cannot create database table name: {0:s}'.format(table_list[count]))
                    return False
        return True

    def print_now_time(self):
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]

    def print_run_info(self, module_name, start=True):
        if start:
            print(f'[{self.print_now_time()}] [MODULE] {module_name} Start', file=sys.stdout)
            sys.stdout.flush()
        else:
            print(f'[{self.print_now_time()}] [MODULE] {module_name} End', file=sys.stdout)
            sys.stdout.flush()

    def GetQuerySeparator(self, source_path_spec, configuration):
        if source_path_spec.location == "/":
            return "/"
        if configuration.standalone_check:
            return "\\"
        return "\\\\\\\\"

    def GetPathSeparator(self, source_path_spec):
        if source_path_spec.location == "/":
            return "/"
        return "\\"
