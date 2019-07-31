#-*- coding: utf-8 -*-
#!/usr/bin/python3

import os,sys,time,binascii

sys.path.append(os.path.abspath(os.path.dirname(__file__)+"\\Code"))
sys.path.append(os.path.abspath(os.path.dirname(__file__)+"\\include"))

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
    def __init__(self):
        super().__init__()
        self.actor  = Actuator()
        self.cursor = None

    def _loadModule(self,module,cls,alias=None):
        if(alias!=None):
            self.actor.loadLibraryAs(module,alias)
            return self.actor.loadClass(alias,cls)
        else:
            self.actor.loadLibrary(module)
            return self.actor.loadClass(module,cls)

    def loadModule(self):
        print("Load : {0} {1}".format("alz",self._loadModule("module_alz","ModuleALZ","alz")))
        print("Load : {0} {1}".format("avi",self._loadModule("module_avi","ModuleAVI","avi")))
        print("Load : {0} {1}".format("bmp",self._loadModule("module_bmp","ModuleBMP","bmp")))
        print("Load : {0} {1}".format("compound",self._loadModule("module_compound","ModuleCOMPOUND","compound")))
        print("Load : {0} {1}".format("dbx",self._loadModule("module_dbx","ModuleDBX","dbx")))
        print("Load : {0} {1}".format("eml",self._loadModule("module_eml","ModuleEML","eml")))
        print("Load : {0} {1}".format("exif",self._loadModule("module_exif","ModuleEXIF","exif")))
        print("Load : {0} {1}".format("gif",self._loadModule("module_gif","ModuleGIF","gif")))
        print("Load : {0} {1}".format("hwp",self._loadModule("module_hwp","ModuleHWP","hwp")))
        print("Load : {0} {1}".format("jfif",self._loadModule("module_jfif","ModuleJFIF","jfif")))
        print("Load : {0} {1}".format("pdf",self._loadModule("module_pdf","ModulePDF","pdf")))
        print("Load : {0} {1}".format("png",self._loadModule("module_png","ModulePNG","png")))
        print("Load : {0} {1}".format("pst",self._loadModule("module_pst","ModulePST","pst")))
        print("Load : {0} {1}".format("wav",self._loadModule("module_wav","ModuleWAV","wav")))
        print("Load : {0} {1}".format("zip",self._loadModule("module_zip","ModuleZIP","zip")))

    def carving_conn(self):
        try :
            db = Mariadb()
            cursor = db.i_open('localhost', 0, 'root', 'dfrc4738', 'carving')
            return cursor
        except Exception :
            print("[ERROR] Carving DB connection ERROR")
            exit(C_defy.Return.EFAIL_DB)

    def db_conn_create(self,cursor):
        db = Mariadb()
        # CARPE DB 연결 및 정보 추출
        try :
            cursor1 = db.i_open('218.145.27.66',23306,'root','dfrc4738','carpe_3')
            cursor1.execute('select * from carpe_block_info where p_id = %s', self.case)
            data = cursor1.fetchall()
            cursor1.execute('show create table carpe_block_info')
            c_table_query = cursor1.fetchone()
        except Exception :
            print("[ERROR] CARPE DB connection ERROR")
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
                print("[WARNING] this case is already finished Convert DB processing in carving")
                pass
            else :
                start = time.time()
                cursor.execute('start transaction')
                for row in data :
                    cursor.execute('insert into carpe_block_info values (%s,%s,%s,%s)',(row[0],row[1],row[2],row[3]))
                cursor.execute('commit')
                print("[DEBUG] copy db time : ",time.time() - start)
                cursor.execute(db.CREATE_HELPER['datamap'])
                self.convert_db(cursor)
        except Exception:
            print("[ERROR] unallocated area DB porting ERROR")
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
            print("[DEBUG] converting time : ", time.time() - start)
        except Exception :
            print("[ERROR] check signature module ERROR")

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
            print("[DEBUG] converting time : ", time.time() - start)
        except Exception :
            print("[ERROR] Fast Signature Detector ERROR")

    def carving(self,cursor):
        cursor.execute('select block_id, blk_num, blk_sig from datamap where blk_sig is not null')
        data = cursor.fetchall()
        i = 0
        total = len(data)
        for sigblk in data :
            # 맨 마지막 레코드
            if i+1 == total:
                end_pos = os.path.getsize(self.I_path)
                result = self.r_module(data[i][2],data[i][1]*self.blocksize,end_pos,1024)
                print(result)
                #파일 추출 모듈
            else :
                # 같은 블록에 여러개의 sig가 발견
                if sigblk[0] == data[i+1][0] :
                    #print("같은 블록에 여러개의 sig가 발견")
                    result = self.r_module(data[i][2],data[i][1]*self.blocksize,data[i+1][1]*self.blocksize,self.blocksize)
                    print(result)
                    #파일 추출 모듈
                else :
                    #print("다른 블록으로 변경됨")
                    cursor.execute('select blk_num from datamap where blk_num > %s and block_id = %s order by blk_num desc',(sigblk[1],sigblk[0]))
                    end_pos = cursor.fetchone()
                    if(end_pos!=None):
                        result = self.r_module(data[i][2],data[i][1]*self.blocksize,end_pos[0]*self.blocksize,1024)
                        print(result)
                    #파일 추출 모듈
            
            i += 1

    def r_module(self,_request,start,end,cluster,etype='euc-kr'):
        self.actor.set(_request, ModuleConstant.FILE_ATTRIBUTE,self.I_path)  # File to carve
        self.actor.set(_request, ModuleConstant.IMAGE_BASE, start)  # Set offset of the file base
        self.actor.set(_request, ModuleConstant.IMAGE_LAST, end)
        self.actor.set(_request, ModuleConstant.CLUSTER_SIZE, cluster)
        self.actor.set(_request, ModuleConstant.ENCODE, etype)
        return self.actor.call(_request, None, None)

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
            self.data = 0
            self.case = option.get("case",None)
            self.blocksize = option.get("block",4096)
            self.sectorsize = option.get("sector",512)
            self.par_startoffset = option.get("start",0)
            self.I_path = option.get("path",None)

        elif(cmd==ModuleConstant.LOAD_MODULE):
            self.loadModule()

        elif(cmd==ModuleConstant.CONNECT_DB):
            self.cursor = self.carving_conn()

        elif(cmd==ModuleConstant.CREATE_DB):
            if(self.cursor!=None):
                self.db_conn_create(self.cursor)

        elif(cmd==ModuleConstant.DISCONNECT_DB):
            if(self.cursor!=None):
                self.cursor.close()
                self.cursor = None

        elif(cmd==ModuleConstant.EXEC and optiond==None):
            self.Fast_Detect(self.cursor) # 시그니처 탐지
            self.carving(self.cursor) # 카빙 동작


if __name__ == '__main__':
    manage = Management()
    manage.execute(ModuleConstant.PARAMETER,
                    {
                        "case":"TEST_2",
                        "block":4096,
                        "sector":512,
                        "start":0x10000,
                        "path":"D:\\iitp_carv\\[NTFS] Carving_Test_Image1.001"
                    }
    )
    manage.execute(ModuleConstant.LOAD_MODULE)
    manage.execute(ModuleConstant.CONNECT_DB)
    manage.execute(ModuleConstant.CREATE_DB)
    manage.execute(ModuleConstant.EXEC)
    manage.execute(ModuleConstant.DISCONNECT_DB)

    sys.exit(0)
