#-*- coding: utf-8 -*-
#!/usr/bin/python3

import os,sys,time,binascii
import pymysql

sys.path.append(os.path.abspath(os.path.dirname(__file__)+"{0}Code".format(os.sep)))
sys.path.append(os.path.abspath(os.path.dirname(__file__)+"{0}include".format(os.sep)))

from defines         import *
from interface       import ModuleComponentInterface
from actuator  import Actuator

from Carving_Management_Defines import C_defy
from Include.carpe_db import Mariadb

"""
    Key      :Value
    "name"   :"Carpe_Management",    # 모듈 이름
    "author" :"Gimin Hur",      # 모듈 작성자
    "ver"    :"0.1",        # 모듈 버전
    "id"     :0,            # onload 시 고유 ID (int 형)
    "param"  :"이미지 경로", "CASE명" # 모듈 파라미터
    "encode" :"utf-8",      # 인코딩 방식
    "base"   :0,            # Base 주소(오프셋)
    "excl"   :False         # 모듈의 유니크(배타적) 속성
"""

class Management(ModuleComponentInterface,C_defy):
    def __init__(self,debug=True):
        super().__init__()
        self.__actor    = Actuator()
        self.cursor   = None
        self.debug    = debug
        self.destPath = ".{0}result".format(os.sep)
        self.hits     = {}

    def get_file_handle(self,path):
        try:
            self.__fd = open(path,'rb')
        except:
            return ModuleConstant.Return.EINVAL_FILE
        self.__fd.seek(0,os.SEEK_SET)
        return ModuleConstant.Return.SUCCESS

    def goto(self,offset,mode):
        return self.__fd.seek(offset,mode)

    def cleanup(self):
        if(self.__fd!=None):
            try:self.__fd.close()
            except:pass
            self.__fd = None

    def _load_module(self,module,cls,alias=None):
        if(alias!=None):
            self.__actor.loadLibraryAs(module,alias)
            return self.__actor.loadClass(alias,cls)
        else:
            self.__actor.loadLibrary(module)
            return self.__actor.loadClass(module,cls)

    def loadModule(self):
        if(self.debug):
            self.debug_text("INFO","loading module result [{1:>2}] name [{0:>10}]".format("alz",self._load_module("module_alz","ModuleALZ","alz")))
            self.debug_text("INFO","loading module result [{1:>2}] name [{0:>10}]".format("avi",self._load_module("module_avi","ModuleAVI","avi")))
            self.debug_text("INFO","loading module result [{1:>2}] name [{0:>10}]".format("bmp",self._load_module("module_bmp","ModuleBMP","bmp")))
            self.debug_text("INFO","loading module result [{1:>2}] name [{0:>10}]".format("compound",self._load_module("module_compound","ModuleCOMPOUND","compound")))
            self.debug_text("INFO","loading module result [{1:>2}] name [{0:>10}]".format("dbx",self._load_module("module_dbx","ModuleDBX","dbx")))
            self.debug_text("INFO","loading module result [{1:>2}] name [{0:>10}]".format("eml",self._load_module("module_eml","ModuleEML","eml")))
            self.debug_text("INFO","loading module result [{1:>2}] name [{0:>10}]".format("exif",self._load_module("module_exif","ModuleEXIF","exif")))
            self.debug_text("INFO","loading module result [{1:>2}] name [{0:>10}]".format("gif",self._load_module("module_gif","ModuleGIF","gif")))
            self.debug_text("INFO","loading module result [{1:>2}] name [{0:>10}]".format("hwp",self._load_module("module_hwp","ModuleHWP","hwp")))
            self.debug_text("INFO","loading module result [{1:>2}] name [{0:>10}]".format("jfif",self._load_module("module_jfif","ModuleJFIF","jfif")))
            self.debug_text("INFO","loading module result [{1:>2}] name [{0:>10}]".format("pdf",self._load_module("module_pdf","ModulePDF","pdf")))
            self.debug_text("INFO","loading module result [{1:>2}] name [{0:>10}]".format("png",self._load_module("module_png","ModulePNG","png")))
            self.debug_text("INFO","loading module result [{1:>2}] name [{0:>10}]".format("pst",self._load_module("module_pst","ModulePST","pst")))
            self.debug_text("INFO","loading module result [{1:>2}] name [{0:>10}]".format("wav",self._load_module("module_wav","ModuleWAV","wav")))
            self.debug_text("INFO","loading module result [{1:>2}] name [{0:>10}]".format("zip",self._load_module("module_zip","ModuleZIP","zip")))
        else:
            self._loadModule("module_alz","ModuleALZ","alz")
            self._loadModule("module_avi","ModuleAVI","avi")
            self._loadModule("module_bmp","ModuleBMP","bmp")
            self._loadModule("module_compound","ModuleCOMPOUND","compound")
            self._loadModule("module_dbx","ModuleDBX","dbx")
            self._loadModule("module_eml","ModuleEML","eml")
            self._loadModule("module_exif","ModuleEXIF","exif")
            self._loadModule("module_gif","ModuleGIF","gif")
            self._loadModule("module_hwp","ModuleHWP","hwp")
            self._loadModule("module_jfif","ModuleJFIF","jfif")
            self._loadModule("module_pdf","ModulePDF","pdf")
            self._loadModule("module_png","ModulePNG","png")
            self._loadModule("module_pst","ModulePST","pst")
            self._loadModule("module_wav","ModuleWAV","wav")
            self._loadModule("module_zip","ModuleZIP","zip")

    def debug_text(self,level,context,always=False):
        if(self.debug==True or always==True):
            print("[{0}] {1}".format(level,context))

    def carving_conn(self,cred):
        if(cred.get('init')==True):
            conn = pymysql.connect(host=cred.get('ip'),port=cred.get('port'),user=cred.get('id'),passwd=cred.get('password'))
            conn.cursor().execute("create database {0}".format(cred.get('category')))
            conn.close()
            del conn
        try :
            db = Mariadb()
            cursor = db.i_open(cred.get('ip'),cred.get('port'),cred.get('id'),cred.get('password'),cred.get('category'))
            return cursor
        except Exception :
            self.debug_text("ERROR","Carving DB connection ERROR.")
            exit(C_defy.Return.EFAIL_DB)

    def db_conn_create(self,cursor,cred):
        db = Mariadb()
        # CARPE DB 연결 및 정보 추출
        try :
            cursor1 = db.i_open(cred.get('ip'),cred.get('port'),cred.get('id'),cred.get('password'),cred.get('category'))
            cursor1.execute('select * from carpe_block_info where p_id = %s', self.case)
            data = cursor1.fetchall()
            cursor1.execute('show create table carpe_block_info')
            c_table_query = cursor1.fetchone()
        except Exception :
            self.debug_text("ERROR","CARPE DB connection ERROR.")
            exit(C_defy.Return.EFAIL_DB)
        # Table 존재여부 확인 및 테이블 생성
        try :
            cursor.execute('show tables like "carpe_block_info"')
            temp = cursor.fetchone()
            if temp is not None :
                pass
            else :
                cursor.execute(c_table_query[1])
                
            cursor.execute('select count(*) from carpe_block_info where p_id = %s', self.case)
            init_count = cursor.fetchone()
            if len(data) == init_count[0] :
                self.debug_text("WARNING","This case is already finished Convert DB processing in carving.")
                pass
            else :
                start = time.time()
                cursor.execute('start transaction')
                for row in data :
                    cursor.execute('insert into carpe_block_info values (%s,%s,%s,%s)',(row[0],row[1],row[2],row[3]))
                cursor.execute('commit')
                self.debug_text("DEBUG","copy db time : {0}".format(time.time() - start))
                cursor.execute(db.CREATE_HELPER['datamap'])
                self.convert_db(cursor)
        except Exception:
            self.debug_text("ERROR","unallocated area DB porting ERROR")
        cursor1.close()
        db.close()

    def convert_db(self,cursor):
        try :
            cursor.execute('select * from carpe_block_info where p_id = %s',self.case)
            data = cursor.fetchall()
            start = time.time()
            # 모든 미할당 블록을 DB 레코드로 변경하는 코드부분 [NULL 영역.]
            for row in data :
                map_id = ((row[2] * self.blocksize)+self.par_startoffset) / self.blocksize
                end_id = ((row[3] * self.blocksize)+self.par_startoffset) / self.blocksize
                cursor.execute('start transaction')
                while map_id <= end_id :
                    sql = 'insert into datamap (blk_num,block_id) values(%s, %s)'
                    cursor.execute(sql,(map_id, row[0]))
                    map_id = map_id + 1
                cursor.execute('commit')
            self.debug_text("DEBUG","converting time : {0}.".format(time.time() - start))
        except Exception :
            self.debug_text("ERROR","check signature module ERROR.")

    def Fast_Detect(self, cursor):
        try :
            FP = open(self.I_path,'rb')
            FP.seek(self.par_startoffset)
            C_offset = self.par_startoffset
            Max_offset = os.path.getsize(self.I_path)
            flag = 0
            isthere = 0

            # (현) Block 단위로 Signature 스캔 진행
            # Block 안의 Sector 단위에 대한 처리 방법 고려하기 - Schema
            start = time.time()
            while C_offset <= Max_offset :
                buffer = FP.read(self.blocksize)
                for key in C_defy.Signature.Sig :
                    temp = C_defy.Signature.Sig[key]
                    if binascii.b2a_hex(buffer[temp[1]:temp[2]]) == temp[0] :
                        # 특정 파일포맷에 대한 추가 검증 알고리즘
                        if key == 'aac_1' or key == 'aac_2' :
                            if binascii.b2a_hex(buffer[7:8]) == b'21' :
                                flag = 1
                        # DB 업데이트
                        isthere = cursor.execute('select * from datamap where blk_num = %s', C_offset/self.blocksize)
                        if flag == 0 and isthere == 1:
                            cursor.execute('update datamap set blk_type = %s,blk_sig = %s, blk_stat = %s where blk_num = %s',('sig',key,'carving',C_offset/self.blocksize))
                        #print("[DEBUG] : Find : ",key,"  Offset : ",hex(C_offset))
                    flag = 0
                    isthere = 0
                C_offset += self.blocksize
                FP.seek(C_offset)
            self.debug_text("DEBUG","converting time : {0}.".format(time.time() - start))
        except Exception :
            self.debug_text("ERROR","Fast Signature Detector ERROR.")

    def carving(self,cursor):
        cursor.execute('select block_id, blk_num, blk_sig from datamap where blk_sig is not null')
        data = cursor.fetchall()
        i = 0
        total = len(data)
        self.hit = {}
        for sigblk in data :
            # 맨 마지막 레코드
            if (self.hit.get(data[i][2])==None):
                self.hit.update({data[i][2]:[-1,0]})
            
            value   = self.hit.get(data[i][2])
            self.hit.update({data[i][2]:[value[0]+1,value[1]]})
            value   = self.hit.get(data[i][2])

            if i+1 == total:
                end_pos = os.path.getsize(self.I_path)
                result  = self.call_sub_module(data[i][2],data[i][1]*self.blocksize,end_pos,1024)

                if(type(result)==tuple):
                    result = [list(result)]

                if(len(result[0])==4):
                    result[0].pop(0)

                #print(data[i][2],hex(data[i][1]*self.blocksize),result)
                if(result[0][1]>0):
                    self.hit.update({data[i][2]:[value[0],value[1]+1]})
                    #self.extractor(result) #파일 추출 모듈

            else :
                # 같은 블록에 여러개의 sig가 발견
                if sigblk[0] == data[i+1][0] :
                    result = self.call_sub_module(data[i][2],data[i][1]*self.blocksize,data[i+1][1]*self.blocksize,self.blocksize)
                    
                    if(type(result)==tuple):
                        result = [list(result)]

                    if(len(result[0])==4):
                        result[0].pop(0)

                    #print(data[i][2],hex(data[i][1]*self.blocksize),result)
                    if(result[0][1]>0):
                        self.hit.update({data[i][2]:[value[0],value[1]+1]})
                        #self.extractor(result) #파일 추출 모듈
                # 다른 블록으로 변경됨

                else :
                    cursor.execute('select blk_num from datamap where blk_num > %s and block_id = %s order by blk_num desc',(sigblk[1],sigblk[0]))
                    end_pos = cursor.fetchone()
                    if(end_pos!=None):
                        result = self.call_sub_module(data[i][2],data[i][1]*self.blocksize,end_pos[0]*self.blocksize,1024)

                        if(type(result)==tuple):
                            result = [list(result)]

                        if(len(result[0])==4):
                            result[0].pop(0)

                        #print(data[i][2],hex(data[i][1]*self.blocksize),result)
                        if(result[0][1]>0):
                            self.hit.update({data[i][2]:[value[0],value[1]+1]})
                            #self.extractor(result) #파일 추출 모듈
            i += 1

    def call_sub_module(self,_request,start,end,cluster,etype='euc-kr'):
        self.__actor.set(_request, ModuleConstant.FILE_ATTRIBUTE,self.I_path)  # File to carve
        self.__actor.set(_request, ModuleConstant.IMAGE_BASE, start)  # Set offset of the file base
        self.__actor.set(_request, ModuleConstant.IMAGE_LAST, end)
        self.__actor.set(_request, ModuleConstant.CLUSTER_SIZE, cluster)
        self.__actor.set(_request, ModuleConstant.ENCODE, etype)
        return self.__actor.call(_request, None, None)

    # Extract file(s) from image.
    def extractor(self,extension,result,disable):
        if(disable==True):
            return ModuleConstant.Return.EINVAL_TYPE

        fname  = self.destPath+os.sep+str(time.time())+"."+extension
        length = len(result)

        try:
            fd = open(fname,'wb')
        except:
            return ModuleConstant.Return.EINVAL_NONE

        if(length==1):
            wrtn = 0
            byte2copy = result[0][1]
            self.goto(result[0][0],os.SEEK_SET)

            while(byte2copy<=0):
                if(byte2copy<self.blocksize):
                    data = self.__fd.read(byte2copy)
                    wrtn +=self.fd.write(data)
                    byte2copy-=byte2copy
                    break
                data = self.__fd.read(self.blocksize)
                wrtn +=self.fd.write(data)
                byte2copy-=self.blocksize
            fd.close()
        else:
            wrtn = 0
            i    = 0
            while(i==length):
                byte2copy = result[i][1]
                self.goto(result[i][0],os.SEEK_SET)

                while(byte2copy<=0):
                    if(byte2copy<self.blocksize):
                        data    = self.__fd.read(byte2copy)
                        zerofill = bytearray(self.blocksize-byte2copy)
                        wrtn +=self.fd.write(data)
                        wrtn +=self.fd.write(zerofill)
                        byte2copy-=byte2copy
                    else:
                        data = self.__fd.read(self.blocksize)
                        wrtn +=self.fd.write(data)
                        byte2copy-=self.blocksize
                fd.close()
        
        return (fname,wrtn) 
    

    def module_open(self,id=1):             # Reserved method for multiprocessing
        pass
    def module_close(self):                 # Reserved method for multiprocessing
        pass
    def set_attrib(self,key,value):         # 모듈 호출자가 모듈 속성 변경/추가하는 method interface
        pass
    def get_attrib(self,key,value=None):    # 모듈 호출자가 모듈 속성 획득하는 method interface
        pass

    def execute(self,cmd=None,option=None):
        if(cmd==ModuleConstant.PARAMETER):
            self.data            = 0
            self.case            = option.get("case",None)
            self.blocksize       = option.get("block",4096)
            self.sectorsize      = option.get("sector",512)
            self.par_startoffset = option.get("start",0)
            self.I_path          = option.get("path",None)
            self.destPath        = option.get("dest",".{0}result".format(os.sep))

        elif(cmd==ModuleConstant.LOAD_MODULE):
            self.loadModule()

        elif(cmd==ModuleConstant.CONNECT_DB):
            self.cursor = self.carving_conn(option)

        elif(cmd==ModuleConstant.CREATE_DB):
            if(self.cursor!=None):
                self.db_conn_create(self.cursor,option)

        elif(cmd==ModuleConstant.DISCONNECT_DB):
            if(self.cursor!=None):
                self.cursor.close()
                self.cursor = None

        elif(cmd==ModuleConstant.EXEC and option==None):
            self.Fast_Detect(self.cursor) # 시그니처 탐지
            start = time.time()
            self.carving(self.cursor)     # 카빙 동작
            self.debug_text("DEBUG","carving time : {0}.".format(time.time() - start))
            self.debug_text("INFO",self.hit)


if __name__ == '__main__':
    manage = Management()
    
    manage.execute(ModuleConstant.LOAD_MODULE)

    manage.execute(ModuleConstant.PARAMETER,
                    {
                        "case":"TEST_2",
                        "block":4096,
                        "sector":512,
                        "start":0x10000,
                        "path":"D:\\iitp_carv\\[NTFS]_Carving_Test_Image1.001"
                    }
    )
    
    manage.execute(ModuleConstant.CONNECT_DB,
                    {
                        "ip":'localhost',
                        "port":0,
                        "id":'root',
                        "password":HIDE,
                        "category":'carving',
                        "init":False
                    }
    )
    
    manage.execute(ModuleConstant.CREATE_DB,
                    {
                        "ip":'218.145.27.66',
                        "port":23306,
                        "id":'root',
                        "password":HIDE,
                        "category":'carpe_3'
                    }
    )
    
    manage.execute(ModuleConstant.EXEC)
    
    manage.execute(ModuleConstant.DISCONNECT_DB)

    sys.exit(0)