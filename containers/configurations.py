# -*- coding: utf-8 -*-

import pytz
import dateutil.parser


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
        self.sector_size = None
        self.cluster_size = None

    @staticmethod
    def apply_time_zone(timestamp, time_zone):
        if timestamp is None or timestamp == '' or timestamp == 0 or timestamp == '0':
            return timestamp
        try:
            date = dateutil.parser.parse(timestamp)
        except:
            return 0

        try:
            local_date = date.replace(tzinfo=pytz.utc).astimezone(time_zone).isoformat()
        except OverflowError as e:
            print(f"Convert Timezone Error : {str(e)}")
            local_date = ''
        return local_date
