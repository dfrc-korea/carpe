#-*- coding: utf-8 -*-

#!/usr/bin/python3

# 실전 예제

import os
from collections import OrderedDict

from moduleInterface.defines   import *
from moduleInterface.interface import ModuleComponentInterface
#from defines   import *
#from interface import ModuleComponentInterface

from multiprocessing import Process, Lock

class ModuleConfiguration(ModuleComponentInterface):

    def __init__(self):
        super().__init__()
        self.lock        = False
        self.__dirty     = False
        self.__content   = OrderedDict()
        self.path        = ModuleConstant.DEFINE_PATH
        self.description = "Module_Configuration\n"

        self.set_attrib(ModuleConstant.NAME,"configuration")   # 모듈 기본 속성 이름 재정의
        self.set_attrib(ModuleConstant.VERSION,"0.1")          # 모듈 기본 속성 버전 재정의
        self.set_attrib(ModuleConstant.AUTHOR,"HK")            # 모듈 기본 속성 작성자 재정의
        self.set_attrib(ModuleConstant.EXCLUSIVE,True)         # 모듈 기본 속성 배타적(유니크) 속성 정의

    def init(self,path):
        if(path==None):
            self.path  = ModuleConstant.DEFINE_PATH + self.get_attrib(ModuleConstant.FILE_ATTRIBUTE)
        else:
            self.path  = path
        try:
            self.__read__()
        except:
            self.__initialize__()

    def __del__(self):
        pass

    def __read__(self):
        with open(self.path,"r+") as file:
            line = file.readline()
            if(line==['']):return
            while line:
                try:
                    line = file.readline().split(':',1)
                    if(line[0].startswith("%")==False and line[0].startswith("#")==False):
                        self.__content.update({line[0].strip():line[1].strip()})
                except:break

    def __initialize__(self):
        with open(self.path,"w+") as file:
            file.write(self.description)
        self.status = ModuleConstant.Return.SUCCESS

    def set(self,key,value):
        # 환경 변수에 대한 값 설정/추가/변경
        self.__content.update({key.lower():value.strip()})
        self.__dirty = True

    def get(self,key):
        # 환경 변수에 대한 값 리턴/없으면 None 타입 리턴
        return self.__content.get(key.lower(),None)

    def save(self):
        # 변경된 환경 변수를 저장
        if(self.__dirty == True):
            with open(self.path,"w") as file:
                file.write(self.description)
                for item,value in self.__content.items():
                    file.write("{0}:{1}\n".format(item.lower(),value.strip()))
            self.__dirty = False

    def getAll(self):
        # 환경 변수 내용 전체를 복사. 외부에서 변경시 반영 안 됨
        return self.__content.copy()

    """ Interfaces """

    def module_open(self,id,lock):
        # Reserved method for multiprocessing
        super().module_open(id)
        self.lock = lock
        # 배타적 접근 권한 개체

    def module_close(self):
        # Reserved method for multiprocessing
        pass

    def set_attrib(self,key,value):
        # 모듈 호출자가 모듈 속성 변경/추가하는 method interface
        self.update_attrib(key,value)

    def get_attrib(self,key,value=None):
        # 모듈 호출자가 모듈 속성 획득하는 method interface
        return self.attrib.get(key)

    def execute(self,cmd=ModuleConstant.READ,option=None):
        # 모듈 호출자가 모듈을 실행하는 method
        # 프로세스 내부에서 배타적 접근 보장
        ret = ModuleConstant.Return.SUCCESS
        self.lock.acquire()
        if(cmd==ModuleConstant.INIT):
            self.init(option)
            ret = self.__content
        elif(cmd==ModuleConstant.READ):
            ret = self.get(option)
        elif(cmd==ModuleConstant.WRITE):
            self.set(option[0],option[1])
        elif(cmd==ModuleConstant.SAVE):
            self.save()
        elif(cmd==ModuleConstant.GETALL):
            ret = self.getAll()
        elif(cmd==ModuleConstant.DESCRIPTION):
            if(type(option)==None):ret = self.description
            else:
                try:
                    self.description = str(option).strip().replace("\n",",").replace(":"," ")+"\n"
                    ret = self.description
                except:ret = None
        self.lock.release()
        return ret


if __name__ == '__main__':
    lock = Lock()
    mm = ModuleConfiguration()
    mm.module_open(2,lock)
    print("Loaded module ID :",mm.get_attrib(ModuleConstant.ID))

    mm.set_attrib(ModuleConstant.FILE_ATTRIBUTE,ModuleConstant.CONFIG_FILE)
    
    mm.execute(ModuleConstant.INIT,"config.txt")

    mm.execute(ModuleConstant.WRITE,["path",os.path.abspath(os.path.dirname(__file__))])
    mm.execute(ModuleConstant.WRITE,["dependency","Windows"])
    print("Read Test        : ",mm.execute(ModuleConstant.READ,"path"))

    copy_obj = mm.getAll()
    print("Original Before  : ",mm.execute(ModuleConstant.READ,"dependency"))
    print("Copy Object Bef  : ",copy_obj.get("dependency"))

    mm.execute(ModuleConstant.WRITE,["dependency","Ubuntu"])
    mm.execute(ModuleConstant.SAVE)

    print("Original After   : ",mm.execute(ModuleConstant.READ,"dependency"))
    print("Copy Object Aft  : ",copy_obj.get("dependency"))
    mm.module_close()
    del mm