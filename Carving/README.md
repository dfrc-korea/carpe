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

### Interface Design
ModuleComponentInterface는 추상 클래스로 하위 클래스에서 몇 가지 method를 구현해야 합니다.
1. module_open(id)
- 모듈 객체를 열 때 처리해야할 과정을 호출합니다.
2. module_close(id)
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
10. checkObjectLoaded(class)
- 객체 테이블에 class가 등록되었는지 확인합니다. 결과에 대한 bool 값이 리턴됩니다.
11. getLoadedObjectList()
- 객체 테이블을 사전 형식으로 복사합니다. 리턴된 객체를 수정해도 반영되지 않습니다. 
