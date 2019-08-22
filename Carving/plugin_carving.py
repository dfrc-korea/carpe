#-*- coding: utf-8 -*-
#!/usr/bin/python3

import os,sys,time,binascii
import pickle
import shutil
import pandas as pd

from multiprocessing import Process, Lock

from moduleInterface.defines   import ModuleConstant
from moduleInterface.interface import ModuleComponentInterface
from moduleInterface.actuator  import Actuator
from structureReader import structureReader as sr

sys.path.append(os.path.abspath(os.path.dirname(__file__)+"{0}include".format(os.sep)))
sys.path.append(os.path.abspath(os.path.dirname(__file__)+"{0}Code".format(os.sep)))        # For carving module

from plugin_carving_defines import C_defy
from Include.carpe_db       import Mariadb


"""
    Key      :Value
    "name"   :"CarvingManager",      # 모듈 이름
    "author" :"",                    # 모듈 작성자
    "ver"    :"0.1",                 # 모듈 버전
    "id"     :0,                     # onload 시 고유 ID (int 형)
    "param"  :"이미지 경로", "CASE명" # 모듈 파라미터
    "encode" :"utf-8",               # 인코딩 방식
    "base"   :0,                     # Base 주소(오프셋)
    "excl"   :False                  # 모듈의 유니크(배타적) 속성
"""

# CarvingManager : DB 수정권한 없음 (For safety)
class CarvingManager(ModuleComponentInterface,C_defy):
    def __init__(self,debug=False,out=None,logBuffer=0x409600):
        super().__init__()
        self.__cursor      = None
        self.__cache       = os.path.dirname(__file__)+os.sep+".cache"+os.sep
        self.__db          = None
        self.__dest_path   = ".{0}result".format(os.sep)
        self.__fd          = None
        self.__hit         = {}
        self.__parser      = sr.StructureReader()
        self.__data        = dict()
        self.__save        = True
        self.__enable      = False
        self.lock          = Lock()
        self.__Return      = C_defy.Return
        self.__Instruction = C_defy.WorkLoad

        """ Module Manager """
        self.__actuator    = Actuator()
        self.defaultModuleLoaderFile = str(__file__).split(os.sep)[0]+os.sep+"config.txt"
        self.moduleLoaderFile        = self.defaultModuleLoaderFile

        """ Logger """
        self.debug         = debug
        self.logBuffer     = logBuffer
        self.__lp          = None
        self.__out         = out

        if(type(self.__out)==str):
            self.__stdout      = str(__file__).split(os.sep)[0]+os.sep+str(self.__out)
            self.__stdout_old  = self.__stdout+".old"
            self.__out         = True
        else:
            self.__out         = False
        
        self.__log_open()

    def __del__(self):
        try:
            if(self.__lp!=None):
                self.__lp.close()
            if(self.__cursor!=None):
                self.__cursor.close()
            if(self.__db!=None):
                self.__db.close()
        except:pass

    def __str__(self):
        print("Carving Manager")

    def __log_open(self):
        if(self.__out==True):
            if(os.path.exists(self.__stdout)):
                if(os.path.getsize(self.__stdout)<self.logBuffer):
                    self.__lp = open(self.__stdout,'a+')
                    return
                else:
                    try:
                        shutil.move(self.__stdout,self.__stdout_old)
                    except:
                        self.__out = False
                        return
            self.__lp = open(self.__stdout,'w')
            self.__log_write("INFO","Main::Initiate carving plugin log.",always=True) 
        else:
            self.__lp   = None

    def __log_write(self,level,context,always=False,init=False):
        if((self.debug==True or always==True) and self.__lp==None):
            print("[{0}] At:{1} Text:{2}".format(level,time.ctime(),context))
        elif((self.debug==True or always==True) and (self.__lp!=None and init==True)):
            self.__lp.close()
            self.__log_open()
        elif((self.debug==True or always==True) and self.__lp!=None):
            try:
                self.__lp.write("[{0}]::At::{1}::Text::{2}\n".format(level,time.ctime(),context))
                self.__lp.flush()
            except:self.__lp==None

    def __cleanup(self):
        if(self.__fd!=None):
            try:self.__fd.close()
            except:pass
            self.__fd = None



    def __load_config(self):
        self.__log_write("INFO","Loader::Start to module load...",always=True)
        if(self.__actuator.loadModuleClassAs("module_config","ModuleConfiguration","config")==False):
            self.__log_write("ERR_","Loader::[module_config] module is not loaded. system exit.",always=True)
            return False
        self.__actuator.open("config",2,self.lock)
        self.__actuator.set( "config",ModuleConstant.FILE_ATTRIBUTE,ModuleConstant.CONFIG_FILE)
        self.__actuator.call("config",ModuleConstant.DESCRIPTION,"Carving Module List")

    def ___load_module(self):
        self.__actuator.call("config",ModuleConstant.INIT,self.moduleLoaderFile)
        modlist = self.__actuator.call("config",ModuleConstant.GETALL,None).values()
        self.__log_write("INFO","Loader::[module_config] Read module list from {0}.".format(self.moduleLoaderFile),always=True)
        if(len(modlist)==0):
            self.__log_write("INFO","Loader::[module_config] No module to import.",always=True)
            return False
        for i in modlist:
            i   = i.split(",")
            if(len(i)!=3):continue
            res = self.__actuator.loadModuleClassAs(i[0],i[1],i[2])
            self.__log_write("INFO","Loader::loading module result [{0:>2}] name [{1:<16}]".format(res,i[0]),always=True)
            if(res==False):
                self.__log_write("WARN","Loader::[{0:<16}] module is not loaded.".format(i[0]),always=True)
        self.__log_write("INFO","Loader::Completed.",always=True)
        return True

    def __load_module(self):
        self.__actuator.clear()
        self.__actuator.init()
        ret = self.__load_config()
        if(ret==False):
            return False
        return self.___load_module()

    def __call_sub_module(self,_request,start,end,cluster,etype='euc-kr'):
        self.__actuator.set(_request,ModuleConstant.FILE_ATTRIBUTE,self.__i_path)  # File to carve
        self.__actuator.set(_request,ModuleConstant.IMAGE_BASE,start)  # Set offset of the file base
        self.__actuator.set(_request,ModuleConstant.IMAGE_LAST,end)
        self.__actuator.set(_request,ModuleConstant.CLUSTER_SIZE,cluster)
        self.__actuator.set(_request,ModuleConstant.ENCODE,etype)
        return self.__actuator.call(_request,None,None)



    def __connect_master(self,cred):
        db = Mariadb()
        try:
            self.__cursor = db.i_open(cred.get('ip'),cred.get('port'),cred.get('id'),cred.get('password'),cred.get('category'))
            self.__db = db
            return C_defy.Return.SUCCESS
        except:
            db.close()
            return C_defy.Return.EFAIL_DB

    def __evaluate(self):
        try:
            fd = os.open(self.__i_path,os.O_RDONLY)
            os.close(fd)
            return ModuleConstant.Return.SUCCESS
        except:return ModuleConstant.Return.EINVAL_FILE

    # This job have to work exclusively
    def __excl_get_master_data(self):
        try:
            self.__cursor.execute('select * from carpe_block_info where p_id = %s',self.__part_id)
            return self.__cursor.fetchall()
        except:
            return C_defy.Return.EFAIL_DB
        
    def __scan_signature(self,data):
        dataIndex    = 0
        dataLength   = len(data)
        crafted_data = list()
        
        while(dataIndex<dataLength):
            (start,end) = (data[dataIndex][2]*self.__blocksize+self.__par_startoffset,
                           data[dataIndex][3]*self.__blocksize+self.__par_startoffset)
            self.__parser.bgoto(start,os.SEEK_SET)
            info = self.__scan_block(start,end)
            if(info!=[]):
                crafted_data.append((data[dataIndex],info))
            dataIndex+=1

        return crafted_data

    def __scan_block(self,start,end):
        current = start
        info    = list()
        
        while(current<=end):
            _info = self.__scan(current)
            if(_info[1]!=None):
                info.append(_info)
            current+=self.__blocksize
        
        return info

    def __scan(self,offset):
        flag   = 0
        keys   = None
        buffer = self.__parser.bread_raw(offset,self.__blocksize,os.SEEK_SET)
        if(buffer==None):
            return (offset,keys,flag)
        
        for key in C_defy.Signature.Sig:
            temp = C_defy.Signature.Sig[key]
            if binascii.b2a_hex(buffer[temp[1]:temp[2]])==temp[0]:
                keys = key
                # 특정 파일포맷에 대한 추가 검증 알고리즘
                if key=='aac_1' or key=='aac_2' :
                    if binascii.b2a_hex(buffer[7:8])==b'21':
                        flag = 1
                break
        
        return (offset,keys,flag)

    def __carving(self,data,enable):
        dataIndex  = 0
        dataLength = len(data)-1
        isDone     = False
        self.__data  = dict()
        self.__parser.bgoto(0,os.SEEK_SET)

        while(dataIndex<dataLength):
            internalIndex  = 0
            internalList   = data[dataIndex][1]
            internalLength = len(internalList)-1
            
            if(internalList==[]):
                dataIndex+=1
                continue

            while(internalIndex<internalLength):
                self.__extractor(internalList[internalIndex][1],   # extensions
                                 internalList[internalIndex][0],   # start offset to carve
                                 internalList[internalIndex+1][0], # last offset to carve
                                 enable)
                internalIndex+=1

            while((dataIndex<dataLength) and (data[dataIndex+1][1]==[])):
                dataIndex+=1
            
            # 블록에 있는 마지막 데이터 처리
            if(dataIndex>=dataLength):
                lastPtr = os.path.getsize(self.__i_path)
                isDone  = True
            else:
                lastPtr = data[dataIndex+1][0][2] * self.__blocksize
            self.__extractor(internalList[internalLength][1],      # extensions
                             internalList[internalLength][0],      # start offset to carve
                             lastPtr,                              # last offset to carve
                             enable)
            dataIndex+=1

        # 마지막 블록처리
        if(isDone==False):
            internalIndex  = 0
            internalList   = data[dataIndex][1]
            internalLength = len(internalList)-1
            while(internalIndex<internalLength):
                self.__extractor(internalList[internalIndex][1],   # extensions
                                 internalList[internalIndex][0],   # start offset to carve
                                 internalList[internalIndex+1][0], # last offset to carve
                                 enable)
                internalIndex+=1

            lastPtr = os.path.getsize(self.__i_path)
            self.__extractor(internalList[internalLength][1],      # extensions
                             internalList[internalLength][0],      # start offset to carve
                             lastPtr,                              # last offset to carve
                             enable)
            
    # Extract file(s) from image.
    def __extractor(self,ext,start,last,enable=True):

        value   = self.__hit.get(ext,None)
        if(value==None):
            self.__hit.update({ext:[1,0]})
            value = [1,0]
        else:
            self.__hit.update({ext:[value[0]+1,value[1]]})
            value   = self.__hit.get(ext)

        result = self.__call_sub_module(ext,start,last,self.__blocksize)
        if(type(result)==tuple):
            result = [list(result)]

        if(len(result[0])==4):
            result[0].pop(0)

        fd     = None
        wrtn   = 0
        length = len(result)

        path   = self.__dest_path+os.sep+ext+os.sep
        fname  = path+str(hex(start))+"."+ext
        if(result[0][0]==False or result[0][1]==0):
            return (fname,wrtn)

        if(not os.path.exists(path)):
            self.__log_write("INFO","Extract::create a result directory at {0}".format(path))
            os.makedirs(path)


        if(enable==False):
            self.__hit.update({ext:[value[0],value[1]+1]})
            self.__data.update({str(hex(start)):(ext,start,last,abs(last-start))})
            self.__log_write("DBG_","Calculated::type:{0} name:{1} copied:{2} bytes details:{3}".format(ext,fname,hex(wrtn),result[0]))
            return (fname,wrtn)

        try:
            fd = open(fname,'wb')
        except:
            self.__log_write("ERR_","Extract::an error while creating file:{0}.".format(path))
            return ModuleConstant.Return.EINVAL_NONE
    
        self.__hit.update({ext:[value[0],value[1]+1]})
        self.__data.update({str(hex(start)):(ext,start,last,abs(last-start))})

        if(length==1):
            byte2copy = abs(last-start)
            self.__parser.bgoto(start,os.SEEK_SET)

            while(byte2copy>0):
                if(byte2copy<self.__sectorsize):
                    data = self.__parser.bread_raw(0,byte2copy)
                    wrtn +=fd.write(data)
                    byte2copy-=byte2copy
                    break
                data = self.__parser.bread_raw(0,self.__sectorsize)
                wrtn +=fd.write(data)
                byte2copy-=self.__sectorsize
        else:
            i = 0
            while(i<length):
                byte2copy = result[i][1]
                self.__parser.bgoto(result[i][0],os.SEEK_SET)

                while(byte2copy>0):
                    if(byte2copy<self.__sectorsize):
                        data     = self.__parser.bread_raw(0,byte2copy)
                        zerofill = bytearray(self.__sectorsize-byte2copy)
                        wrtn +=fd.write(data)
                        wrtn +=fd.write(zerofill)
                        byte2copy-=byte2copy
                    else:
                        data = self.__parser.bread_raw(0,self.__sectorsize)
                        wrtn +=fd.write(data)
                        byte2copy-=self.__sectorsize
                i+=1
            
        fd.close()
        self.__log_write("DBG_","Extract::type:{0} name:{1} copied:{2} bytes details:{3}".format(ext,fname,hex(wrtn),result[0]))
        return (fname,wrtn) 

    def __save_result(self,data):
        print(self.__get_cache_master())
        if(not os.path.exists(self.__get_cache_master())):
            os.makedirs(self.__get_cache_master())

        fname = self.get_bin_file()
        with open(fname,'wb') as file:
            pickle.dump(data,file)

        fname = self.get_cbin_file()
        with open(fname,'wb') as file:
            pickle.dump(self.__data,file)
        self.__data = dict()

    def __import_result(self,path):
        data = ""
        with open(path,'rb') as file:
            try:data = pickle.load(file)
            except:pass
        return data

    @property
    def hit(self):
        return self.__hit.copy()

    @property
    def Instruction(self):
        return self.__Instruction

    @property
    def enable(self):
        return self.__enable

    @enable.setter
    def enable(self,boolean):
        if(type(boolean)==bool):
            self.__enable = boolean

    @property
    def save(self):
        return self.__save

    @save.setter
    def save(self,boolean):
        if(type(boolean)==bool):
            self.__save = boolean

    @property
    def Return(self):
        return self.__Return

    def __get_cache_partition(self):
        return self.__cache+self.__part_id+os.sep

    def __get_cache_master(self):
        return self.__cache+self.__part_id+os.sep+os.path.basename(self.__i_path)+os.sep

    def get_bin_file(self):
        return self.__get_cache_master()+os.path.basename(self.__i_path)+".bin"

    def get_cbin_file(self):
        return self.__get_cache_master()+os.path.basename(self.__i_path)+".cbin"

    def get_csv_file(self):
        return self.__get_cache_master()+os.path.basename(self.__i_path)+".csv"

    # @ Module Interface

    def module_open(self,id=1):             # Reserved method for multiprocessing
        pass
    def module_close(self):                 # Reserved method for multiprocessing
        pass
    def set_attrib(self,key,value):         # 모듈 호출자가 모듈 속성 변경/추가하는 method interface
        pass
    def get_attrib(self,key,value=None):    # 모듈 호출자가 모듈 속성 획득하는 method interface
        pass

    def execute(self,cmd=None,option=None):
        if(cmd==C_defy.WorkLoad.PARAMETER):
            if(type(option)!=dict):
                return ModuleConstant.Return.EINVAL_TYPE
            self.__part_id         = option.get("p_id",None)
            self.__blocksize       = option.get("block",4096)
            self.__sectorsize      = option.get("sector",512)
            self.__par_startoffset = option.get("start",0)
            self.__i_path          = option.get("path",None)
            self.__dest_path       = option.get("dest",".{0}result".format(os.sep))
            self.__log_write("INFO","Main::Request to set parameters.",always=True)

        elif(cmd==C_defy.WorkLoad.LOAD_MODULE):
            self.__log_write("INFO","Main::Request to load module(s).",always=True)
            return self.__load_module()

        elif(cmd==C_defy.WorkLoad.CONNECT_DB):
            if(type(option)!=dict):
                return ModuleConstant.Return.EINVAL_TYPE
            self.__log_write("INFO","Main::Request to connect to master database.",always=True)  
            return self.__connect_master(option)

        elif(cmd==C_defy.WorkLoad.DISCONNECT_DB):
            self.__log_write("INFO","Main::Request to clean up. It would be disconnected with the master database.",always=True) 
            if(self.__cursor!=None):
                self.__cursor.close()
                self.__cursor = None
            if(self.__db!=None):
                self.__db.close()
                self.__db = None

        elif(cmd==C_defy.WorkLoad.EXEC and option==None):
            self.__hit = {}
            self.__log_write("","",always=True,init=True)
            self.__log_write("INFO","Main::Request to run carving process.",always=True)  
            
            data  = self.__excl_get_master_data()
            if(data==C_defy.Return.EFAIL_DB):
                self.__log_write("ERR_","Carving::Cannot connect master database.",always=True)
                return None
            if(self.__evaluate()!=ModuleConstant.Return.SUCCESS):
                self.__log_write("ERR_","Carving::Cannot read the target file.",always=True)
                return ModuleConstant.Return.EINVAL_FILE

            self.__parser.get_file_handle(self.__i_path,0,1)
            if(os.path.exists(self.__dest_path)):
                self.__log_write("DBG_","Extract::clear the current workspace:{0}".format(self.__dest_path))
                shutil.rmtree(self.__dest_path)

            start = time.time()
            data = self.__scan_signature(data)
            self.__carving(data,self.__enable)
            self.__log_write("DBG_","Carving::processing time:{0}.".format(time.time()-start))

            if(self.__save!=False):
                self.__save_result(data)

            self.__parser.cleanup()
            self.__log_write("INFO","Carving::result:{0}".format(self.__hit),always=True)
            del data
            return self.__hit.copy()

        elif(cmd==C_defy.WorkLoad.REPLAY):
            self.__hit = {}
            self.__log_write("INFO","Main::Request to re-run carving process from stored data.",always=True)

            data = self.__import_result(self.get_bin_file())
            if(data==""):
                return ModuleConstant.Return.EINVAL_FILE

            self.__log_write("INFO","Main::Data loaded from {0}".format(option),always=True)
            
            self.__parser.get_file_handle(self.__i_path,0,1)
            start = time.time() 

            self.__carving(data,True)
            self.__log_write("DBG_","Carving::processing time:{0}.".format(time.time()-start))
            
            self.__parser.cleanup()
            self.__log_write("INFO","Carving::result:{0}".format(self.__hit),always=True)
            del data
            return self.__hit.copy()

        elif(cmd==C_defy.WorkLoad.SELECT_ONE):
            self.__hit = {}
            self.__log_write("INFO","Main::Request to re-run carving process from stored data.",always=True)
            if(type(option)!=dict):
                return ModuleConstant.Return.EINVAL_TYPE

            tmp = option.get("name",None)
            if(type(tmp)!=str):
                return ModuleConstant.Return.EINVAL_TYPE
            
            data = self.__import_result(option.get("path",self.get_cbin_file()))
            if(data==""):
                return ModuleConstant.Return.EINVAL_FILE
            if(type(data)!=dict):
                return ModuleConstant.Return.EINVAL_FILE
            
            target = data.get(tmp,None)
            if(target==None):
                return ModuleConstant.Return.EINVAL_NONE
            if(len(target)!=4):
                return ModuleConstant.Return.EINVAL_TYPE
            
            self.__parser.get_file_handle(self.__i_path,0,1)
            try:self.__extractor(target[0],target[1],target[2])
            except:self.__log_write("DBG_","Carving::Cannot carving some specific object:{0}.".format(target[1]),always=True)
            self.__parser.cleanup()
            self.__data = dict()
            del data
            return self.__hit.copy()

        elif(cmd==C_defy.WorkLoad.SELECT_LIST):
            self.__hit = {}
            target = list()
            self.__log_write("INFO","Main::Request to re-run carving process from stored data.",always=True)
            if(type(option)!=dict):
                return ModuleConstant.Return.EINVAL_TYPE

            selected = option.get("name",None)
            if(type(selected)!=list):
                return ModuleConstant.Return.EINVAL_TYPE

            data = self.__import_result(option.get("path",self.get_cbin_file()))
            if(data==""):
                return ModuleConstant.Return.EINVAL_FILE
            if(type(data)!=dict):
                return ModuleConstant.Return.EINVAL_FILE

            for i in selected:
                tmp = data.get(i,None)
                if(type(tmp)==tuple and len(tmp)==4):
                    target.append(tmp)

            if(target==[]):
                return ModuleConstant.Return.EINVAL_NONE
            self.__parser.get_file_handle(self.__i_path,0,1)
            for i in target:
                try:self.__extractor(i[0],i[1],i[2])
                except:self.__log_write("DBG_","Carving::Cannot carving some specific object:{0}.".format(target[1]),always=True)
            self.__parser.cleanup()
            self.__data = dict()
            del data
            return self.__hit.copy()

        elif(cmd==C_defy.WorkLoad.POLICY):
            if(type(option)!=dict):
                return ModuleConstant.Return.EINVAL_TYPE
            self.__log_write("INFO","Main::Change carving policies.",always=True)
            self.__config     = option.get("config",self.defaultModuleLoaderFile)
            self.__enable     = option.get("enable",True)
            self.__save       = option.get("save",True)
            return ModuleConstant.Return.SUCCESS

        elif(cmd==C_defy.WorkLoad.EXPORT_CACHE):
            self.__log_write("INFO","Main::Export cache data as object:{0}".format(self.__i_path),always=True)
            return self.__import_result(option.get("path",self.get_cbin_file()))

        elif(cmd==C_defy.WorkLoad.EXPORT_CACHE_TO_CSV):
            data = self.__import_result(self.get_cbin_file())
            if(type(data)!=dict):
                return ModuleConstant.Return.EINVAL_TYPE
            
            df   = pd.DataFrame.from_dict(data,columns=C_defy.COLUMNS,orient='index')
            df.to_csv(self.get_csv_file(),mode='w')
            del data
            self.__log_write("INFO","Main::Export cache data to csv:{0}.".format(self.get_csv_file()),always=True)
            return self.get_csv_file()

        elif(cmd==C_defy.WorkLoad.REMOVE_CACHE):
            # 현재 이미지에 대한 캐시를 삭제
            if(option==None):
                try:
                    shutil.rmtree(self.__get_cache_master())
                    self.__log_write("INFO","Main::Clean cache data:{0}.".format(self.__get_cache_master()),always=True)
                    return ModuleConstant.Return.SUCCESS
                except:
                    return ModuleConstant.Return.EINVAL_FILE
            # 현재 파티션에 대한 캐시 삭제
            elif(option==1):
                try:
                    shutil.rmtree(self.__get_cache_partition())
                    self.__log_write("INFO","Main::Clean cache data:{0}.".format(self.__get_cache_partition()),always=True)
                    return ModuleConstant.Return.SUCCESS
                except:
                    return ModuleConstant.Return.EINVAL_FILE
            elif(type(option)==str):
                try:
                    shutil.rmtree(self.__cache+os.sep+option)
                    self.__log_write("INFO","Main::Clean cache data:{0}.".format(self.__cache+option),always=True)
                    return ModuleConstant.Return.SUCCESS
                except:
                    return ModuleConstant.Return.EINVAL_FILE
            else:
                try:
                    shutil.rmtree(".cache")
                    self.__log_write("INFO","Main::Clean all cache data.",always=True)
                    return ModuleConstant.Return.SUCCESS
                except:
                    return ModuleConstant.Return.EINVAL_FILE

        else:
            return C_defy.Return.EIOCTL


if __name__ == '__main__':

    # PARAMETER :
    """
    {
        "case":"TEST_2",
        "block":4096,               # Block size
        "sector":512,               # Sector size
        "start":0x10000,            # Start offset (par-offset)
        "path":"D:\\iitp_carv\\[NTFS]_Carving_Test_Image1.001", # Image to carve
        #"dest":".{0}result".format(os.sep), # Output directory
    }
    """
    # CONNECT_DB :
    """
    {
        "ip":'218.145.27.66',       # 2세부 addr
        "port":23306,               # 2세부 port
        "id":'root',                # 2세부 ID
        "password":'dfrc4738',      # 2세부 P/W
        "category":'carpe_3'        # 2새부 Database
    }
    """
    # POLICY :
    """
    {
        "enable":True,              # 카빙 추출 기능 활성화(
                                        True :캐시정보 기록 및 파일 추출
                                        False:캐시정보만 기록(Lazy))
        "save":True                 # 카빙 캐시 정보 저장(*.bin, *.cbin)
    }
    """
    # SELECT_ONE/SELECT_LIST
    """
    {
        "path":path                 # .cbin 파일 경로
        "name":name                 # 필수 : 확장자 제외한 파일 이름(오프셋 값)
    }
    {
        "path":path                 # .cbin 파일 경로
        "name":[]                   # 필수 : 확장자 제외한 파일 이름 목록(오프셋 값)
    }
    """
    # CARVING_OPCODE :
    """
    Carving Opcode:
        # manage.Instruction.Opcode
        Opcode                Param      Return     Description
        -----------------------------------------------------------------------------------------------------------------
        LOAD_MODULE           None         Int      # 카빙에 사용되는 모듈 등록
        PARAMETER             Dict         Int      # 작업 파라미터 설정
        CONNECT_DB            Dict         Int      # Master DB에 연결
        DISCONNECT_DB         None         Int      # Master DB와의 세션 종료
        EXEC                  None         Dict     # (enable=True일 때) 카빙 작업 실행 및 (save=True일 때) 캐시 데이터 생성
        REPLAY                None         Dict     # (eanble과 관계없음) 캐시 데이터를 이용해 현재 이미지에 대한 카빙 작업
        SELECT_ONE            Dict         Dict     # 캐시 데이터를 이용해 한 파일만 추출
        SELECT_LIST           Dict         Dict     # 캐시 데이터를 이용해 name 리스트에 있는 파일만 추출
        POLICY                Dict         Int      # 카빙 정책 설정 (즉시 추출/캐시 저장)
        EXPORT_CACHE          None         Object   # 캐시 데이터를 Code에 반환
        EXPORT_CACHE_TO_CSV   None         String   # 캐시된 목록을 csv형식으로 반환. 파일 경로 리턴
        REMOVE_CACHE          None/1/str/* Int      # 현재 이미지/파티션/특정 이미지/모든 캐시 삭제
        -----------------------------------------------------------------------------------------------------------------
        # cache path : ${CarvingPath}/.cache/partition_id/[image_name]/[image_name].(bin/cbin/csv)
        # Return Dict Format :
            {"Format":[찾은 시그니처 파일 수,검증 통과한 파일 수],}
    """

    manage = CarvingManager(debug=False,out="carving.log")

    res = manage.execute(C_defy.WorkLoad.LOAD_MODULE)

    if(res==False):
        sys.exit(0)

    res = manage.execute(C_defy.WorkLoad.CONNECT_DB,
                    {
                        "ip":'218.145.27.66',
                        "port":23306,
                        "id":'root',
                        "password":'dfrc4738',
                        "category":'carpe_3'
                    }
    )

    if(res==C_defy.Return.EFAIL_DB):
        sys.exit(0)

    manage.enable   = False
    manage.save     = True

    manage.execute(C_defy.WorkLoad.PARAMETER,
                    {
                        "p_id":"TEST_2",
                        "block":4096,
                        "sector":512,
                        "start":0x10000,
                        "path":"D:\\iitp_carv\\[NTFS]_Carving_Test_Image1.001",
                    }
    )

    manage.execute(C_defy.WorkLoad.EXEC)

    manage.execute(C_defy.WorkLoad.DISCONNECT_DB)

    manage.execute(C_defy.WorkLoad.EXPORT_CACHE_TO_CSV)

    #print(manage.execute(C_defy.WorkLoad.SELECT_LIST,{"name":["0x1c2c000","0x2aaa000"]}))
    manage.execute(C_defy.WorkLoad.REPLAY,manage.get_bin_file())
    #manage.execute(C_defy.WorkLoad.REMOVE_CACHE)

    sys.exit(0)
