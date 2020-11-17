# -*- coding: utf-8 -*-
"""The extraction tool."""

from dfvfs.resolver import context as dfvfs_context

from tools import logger
from tools import storage_media_tool
from engine import process_engine
from containers import configurations
from engine.preprocessors import signature_tool


class ExtractionTool(storage_media_tool.StorageMediaTool,
                     signature_tool.SignatureTool):

    def __init__(self, input_reader=None, output_writer=None):

        super(ExtractionTool, self).__init__(
            input_reader=input_reader, output_writer=output_writer)

        self._resolver_context = dfvfs_context.Context()
        self._module_filter_expression = None
        self._advanced_module_filter_expression = None
        self._operating_systems = []

    def _CreateProcessingConfiguration(self):

        configuration = configurations.Configuration()
        configuration.standalone_check = self.standalone_check
        configuration.case_id = self.case_id
        configuration.evidence_id = self.evidence_id
        configuration.source_path = self._source_path
        configuration.source_type = self._source_type
        configuration.source_path_specs = self._source_path_specs
        configuration.output_file_path = self._output_file_path
        configuration.tmp_path = self._tmp_path
        configuration.root_storage_path = self._root_storage_path
        configuration.root_tmp_path = self._root_tmp_path

        configuration.module_filter_expression = self._module_filter_expression
        configuration.advanced_module_filter_expression = self._advanced_module_filter_expression
        configuration.resolver_context = self._resolver_context
        configuration.cursor = self._cursor
        configuration.partition_list = self._partition_list
        configuration.operating_systems = self._operating_systems

        configuration.sector_size = self.sector_size
        configuration.cluster_size = self.cluster_size

        return configuration

    def _Preprocess(self, engine):
        logger.debug('Starting preprocessing.')

        try:
            artifacts_registry = process_engine.ProcessEngine.BuildArtifactsRegistry(
                self._artifact_definitions_path, self._custom_artifacts_path)
            engine.Preprocess(
                artifacts_registry, self._source_path_specs,
                resolver_context=self._resolver_context)

        except IOError as exception:
            logger.error('Unable to preprocess with error: {0!s}'.format(exception))

        logger.debug('Preprocessing done.')
