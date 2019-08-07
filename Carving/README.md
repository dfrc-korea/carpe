# carpe
Carpe Forensics

## Python package dependency
1. moduleInterface @ Gibartes :
- The convention of the current module system
2. structureReader @ Gibartes :
- The byte structured stream parser for carving module


# The description about Module Interface (moduleInterface)

## ModuleComoponentInterface
[ ModuleComoponentInterface Class ]

### Interface implementation
ModuleComponentInterface는 추상 클래스로 하위 클래스에서 몇 가지 method를 구현해야 합니다.
1. module_open(id)
- 모듈 객체를 열 때 처리해야할 과정을 호출합니다.
2. module_close()
- 모듈 객체를 닫을 때 처리해야할 과정을 호출합니다.
3. get_attrib(key)
- 모듈의 속성을 key에 대응되는 값으로 얻습니다. 모듈 속성은 사전 형태로 정의되어 있습니다.
4. set_attrib(key,value=None)
- 모듈의 속성을 key에 해당되는 내용을 value로 설정합니다.
5. execute(cmd=None,option=None)
- 모듈의 동작 메서드를 실행합니다. 이 코드 내부에 ioctl처럼 동작을 구현하십시오.
### Accessible Variables and Methods - etc.
1. errno
- 모듈의 상태 값을 얻습니다.
2. id
- 모듈의 ID를 얻습니다. 기본적으로는 0(Unallocated)입니다.
3. attrib
- 모듈의 속성 정보를 가지고 있습니다. 사전 형태로 이루어져 있습니다.
4. status(stat)
- 모듈의 상태를 stat 값으로 설정합니다.
5. update_attrib(key,value)
- 모듈의 속성을 업데이트합니다. 이 함수를 통해 모듈의 하위 클래스에서 set_attrib를 구현하면 됩니다.


## Actuator
[ Actuator Class ]

### Methods - Manage
1. init()
- Actuator 클래스의 초기화 작업을 수행합니다. 모듈 테이블과 객체 테이블이 모두 비워집니다.
2. clear()
- Actuator 클래스의 모듈 테이블과 객체 테이블 내의 객체들을 메모리에서 삭제하고 테이블을 비웁니다.
### Methods - Executor
1. open(object,id,value)
- 모듈 객체를 열 때 처리해야할 과정을 호출합니다.
2. close(object,id,value)
- 모듈 객체를 닫을 때 처리해야할 과정을 호출합니다.
3. get(object,attr)
- 모듈 객체에 해당하는 속성 정보를 얻습니다.
4. set(object,attr,value)
- 모듈 객체에 해당하는 속성(attr) 정보를 value로 추가 및 변경합니다.
5. call(object,cmd,option)
- 모듈 객체를 명령 프로토콜(cmd)를 가지고 파라미터(option)을 부여하여 실행합니다. 모듈 실행 결과가 리턴됩니다.
### Methods - Loader
1. loadLibrary(module)
- module 이름을 가진 라이브러리를 모듈 테이블로 로드합니다. 인자 module은 string 타입입니다. 결과에 대한 bool 값이 리턴됩니다.
2. loadLibraryAs(module,alias)
- module 이름을 가진 파이썬 라이브러리를 alias의 이름으로 모듈 테이블 로드합니다. alias를 이용해 모듈 테이블에서 해당 객체를 검색할 수 있습니다. 결과에 대한 bool 값이 리턴됩니다. 인자 module과 alias는 string 타입입니다.
3. unloadLibrary(module)
- 모듈 테이블에 등록된 모듈을 언로드합니다. 인자 module은 string 타입입니다. 결과에 대한 bool 값이 리턴됩니다.
4. loadClass(module,class)
- 모듈 내 클래스를 객체를 생성하고, 객체가 성공적으로 생성되면 객체 테이블에 등록합니다. 이 작업이 성공하려면 module이 모듈 테이블에 존재해야 합니다. 인자 module과 class는 string 타입이고, class는 module 내부에 있는 class 이름입니다. 결과에 대한 bool 값이 리턴됩니다.
5. loadObject(name,class)
- class 객체를 name으로 객체 테이블에 등록합니다. 인자 module과 class는 string 타입입니다.
6. unloadObject(name)
- name으로 객체 테이블에 등록된 객체를 제거합니다.
7. getModuleHandle(module)
- 모듈 테이블에 module로 등록되었는지 확인합니다.
8. checkModuleLoaded(namespace)
- 모듈의 이름공간이 모듈 테이블에 로드 되어있는지 점검합니다. 결과에 대한 bool 값이 리턴됩니다.
9. getLoadedModuleList()
- 모듈 테이블을 사전 형식으로 복사합니다. 리턴된 객체를 수정해도 반영되지 않습니다. 
10. checkObjectLoaded(name)
- 객체 테이블에 name으로 배정된 class가 등록되어 있는지 확인합니다. 결과에 대한 bool 값이 리턴됩니다.
11. getLoadedObjectList()
- 객체 테이블을 사전 형식으로 복사합니다. 리턴된 객체를 수정해도 반영되지 않습니다. 


# The Description of Carving Plugin

## Management
### Class Management(debug=False,out=None,logBuffer=0x409600)
- Carving 작업을 수행할 Management Class입니다. Management Class는 ModuleComponentInterface의 원칙에 따라 구성하였으므로 Actuator Class에 붙여 실행시킬 수 있습니다. debug모드이면 진행 과정에 대한 자세한 내용이 출력되며, out에 파일이름을 넣으면 해당 파일로 데이터가 출력됩니다. logBuffer는 최대 log 파일 크기로 기본적으로 0x409600Bytes 으로 설정되어 있습니다. Management Class는 6가지의 작업이 정의되어 있습니다.
```python
    manage = Management(debug=False,out="carving.log")
```
1. LOAD_MODULE
- Management Class에는 기본적으로 탑재된 Carving Module이 존재하지 않으며 config.txt를 읽어 config.txt에 기록된 모듈을 임포트합니다. 이 작업을 통해 Management Class는 동적으로 모듈을 필요할 때마다 불러들여 사용할 수 있습니다. 이 작업은 모듈 추가가 되지 않으면 Management 클래스의 Life time 동안 한번만 실행해도 됩니다. config.txt에 기록된 모듈이 모두 사용이 불가능한 상태이거나 module_config.py 파일이 없으면 False가 리턴됩니다.
```python
    result = manage.execute(ModuleConstant.LOAD_MODULE)
    if(result==False):
        Handle_an_exception()
        ...
```
2. PARAMETER
- Managemet Class의 기본 파라미터들을 설정합니다. 이 파라미터 값들은 동 레벨의 다른 모듈과 공유하지 않으므로 set_attrib()를 사용하지 않았습니다. "dest"와 "confing" 파라미터를 각각 PARAMETER 인자에 추가하면 추출될 폴더와 기본 config.txt가 아닌 다른 이름의 모듈 리스트가 적힌 설정 파일을 읽을 수 있습니다.
```python
    manage.execute(ModuleConstant.PARAMETER,
                    {
                        "case":"CaseName",
                        "block":4096,
                        "sector":512,
                        "start":0x10000,
                        "path":"./img/disk.img"
                    }
    )
```
3. CONNECT_DB
- 특정 Case에 대한 Local Database에 연결합니다.
```python
    manage.execute(ModuleConstant.CONNECT_DB,
                    {
                        "ip":'localhost',
                        "port":0,
                        "id":'loacl_id',
                        "password":'local_password',
                        "category":'carving',
                        "init":False
                    }
    )
```
4. CREATE_DB
- 원격 Database에 연결하고 Local Database로 필요한 데이터를 가져옵니다.
```python
    manage.execute(ModuleConstant.CREATE_DB,
                    {
                        "ip":'remote ip',
                        "port":remote_port,
                        "id":'remote_id',
                        "password":'remote_password',
                        "category":'remote_database'
                    }
    )
```
5. EXEC
- 시그니처 스캔 및 카빙 작업을 수행합니다. 1~4단계가 완료되어야 합니다. 파라미터 설정의 "dest" 영역에 기록된 곳에 추출된 파일들이 확장자별로 저장됩니다.
```python
    manage.execute(ModuleConstant.EXEC)
```
6. DISCONNECT_DB
- Local Database를 닫습니다.
```python
    manage.execute(ModuleConstant.DISCONNECT_DB)
```

