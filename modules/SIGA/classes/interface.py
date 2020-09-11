# -*- coding: utf-8 -*-

from abc import *

class Common(metaclass=ABCMeta):

    def __init__(self, input):
        self.input = input

    def get_filename(self):
        print(self.filename)

    def get_metadata(self):
        print('Metadata')

    def get_text(self):
        print('Content')

    def get_structure(self):
        print('Structure')

    @abstractmethod
    def identifyFormatFromFile(self):
        print('Identify File')

    @abstractmethod
    def identifyFormatFromMemory(self):
        print('Identify Memory')

    @abstractmethod
    def validate(self):
        print('Validate')

    @abstractmethod
    def parse(self):
        print('Parsing')

