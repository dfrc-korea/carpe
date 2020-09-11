# -*- coding: utf-8 -*-

class Configuration(object):

    def __init__(self):

        super(Configuration, self).__init__()
        self.case_id = None
        self.evidence_id = None
        self.source_type = None
        self.source_path = None
        self.source_path_specs = []
        self.output_file_path = None
        self.tmp_path = None
        self.root_storage_path = None
        self.root_tmp_path = None
        self.module_filter_expression = None
        self.advanced_module_filter_expression = None
        self.resolver_context = None
        self.cursor = None
        self.partition_list = {}
        self.operating_systems = []
        self.standalone_check = None