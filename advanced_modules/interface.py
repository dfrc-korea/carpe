# -*- coding: utf-8 -*-

import os
import abc
import yaml

from dfvfs.helpers import file_system_searcher
from dfvfs.resolver import resolver as path_spec_resolver

from engine import path_extractors
from engine import path_helper
from modules import logger

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
    def Analyze(self, configuration, source_path_spec):
        """
        Analyze
        """

    def LoadTargetFileToMemory(self, source_path_spec, configuration, file_path, data_stream_name = None):

        try:
            find_spec = file_system_searcher.FindSpec(
                case_sensitive=False, location=file_path,
                location_separator=source_path_spec.location)
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


    def ExtractTargetFileToPath(self, source_path_spec, configuration, file_path, output_path, data_stream_name = None):

        try:
            find_spec = file_system_searcher.FindSpec(
                case_sensitive=False, location=file_path,
                location_separator=source_path_spec.location)
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
                        file = open(output_path + os.sep + file_entry.name + '_' + data_stream_name, 'wb')
                        file.write(file_object.read(file_object._size))
                        file.close()

                    except IOError as exception:
                        # TODO: replace location by display name.
                        location = getattr(file_entry.path_spec, 'location', '')
                        logger.error(
                            'Failed to extract file "{0:s}" : {1:s}'.format(data_stream_name, exception))
                        return False

                    finally:
                        file_object.close()

                elif not data_stream_name:
                    file_object = file_entry.GetFileObject()

                    if not file_object:
                        return False

                    try:
                        file = open(output_path + os.sep + file_entry.name, 'wb')
                        file.write(file_object.read(file_object._size))
                        file.close()
                    except IOError as exception:
                        logger.error(
                            'Failed to extract file "{0:s}" : {1:s}'.format(display_name, exception))
                    finally:
                        file_object.close()


            except KeyboardInterrupt:
                return False

    def LoadSchemaFromYaml(self, _yaml_path):

        if not os.path.exists(_yaml_path):
            return False

        yaml_data = open(_yaml_path, 'r')
        data = yaml_data.read()

        self._schema = yaml.safe_load(data)
        if not self._schema:
            return False
        return True

    def CreateTable(self, _cursor):

        if not self._schema:
            return False

        # Read YAML Data Stream
        name = self._schema['Name']
        table = self._schema['Table'][0]['TableName']
        columns = self._schema['Table'][0]['Columns']
        types = self._schema['Table'][0]['Types']

        query = []
        query.append("CREATE TABLE ")
        query.append(table)
        query.append("(")

        for i in range(len(columns)):
            query.append(columns[i] + " ")

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

    def check_table_from_yaml(self, configuration, yaml_list, table_list):
        # Create all table
        for count in range(0, len(yaml_list)):
            if not self.LoadSchemaFromYaml(yaml_list[count]):
                logger.error('cannot load schema from yaml: {0:s}'.format(table_list[count]))
                return False
            # If table is not existed, create table
            if not configuration.cursor.check_table_exist(table_list[count]):
                ret = self.CreateTable(configuration.cursor)
                if not ret:
                    logger.error('cannot create database table name: {0:s}'.format(table_list[count]))
                    return False
        return True

