# -*- coding: utf-8 -*-
from .modules.utils.takeout_case import Case
from .modules.preprocessor.takeout_data_parser import DataParser


def parse_google_takeout(src_path):
    case = Case(src_path)
    return DataParser.parse_takeout_data(case)
