# -*- coding: utf-8 -*-

#!/usr/bin/python3

from abc import *

class ModuleComponentInterface(metaclass=ABCMeta):
    def __init__(self):
        self.__status   = 0
        self.fHandle    = 0
        self.attrib     = {
            "name"   :"default",
            "author" :"carpe",
            "ver"    :"0.0",
            "id"     :0,
            "param"  :"None",
            "encode" :"utf-8",
            "base"   :0,
            "last"   :0,
            "excl"   :False,
        }

    def __del__(self):
        pass

    @property
    def errno(self):
        return self.__status

    @property
    def id(self):
        return self.get_attrib("id",0)

    def status(self,status):
        if(type(status)==int):
            self.__status = status

    def update_attrib(self,key,value):
        self.attrib.update({key:value})

    @abstractmethod
    def module_open(self,id=2):             # Reserved method for multiprocessing
        self.__status = 0
        self.attrib.update({"id":int(id)})
    @abstractmethod
    def module_close(self):                 # Reserved method for multiprocessing
        pass
    @abstractmethod
    def set_attrib(self,key,value):         # 모듈 호출자가 모듈 속성 변경/추가하는 method interface
        pass
    @abstractmethod
    def get_attrib(self,key,value=None):    # 모듈 호출자가 모듈 속성 획득하는 method interface
        pass
    @abstractmethod
    def execute(self,cmd=None,option=None): # 모듈 호출자가 모듈을 실행하는 method
        pass
