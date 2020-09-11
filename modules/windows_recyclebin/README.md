동작환경>

Python 3


실행방법> 

지정된 쓰레기통 폴더(Recycle Bin Path)의 파일들을 보여줍니다. 모든 결과는 json 포맷으로 출력됩니다.

python3 RecycleBinParser.py <Recycle Bin Path> [/to_file:<Output Filename>]

사용예>

> python3 RecycleBinParser.py C:\$Recycle.Bin\S-1-5-42-2867809058-3762516759-3994543984-1102                         결과를 화면에 보여줍니다.
> python3 RecycleBinParser.py C:\$Recycle.Bin\S-1-5-42-2867809058-3762516759-3994543984-1102 /to_file:r.json         결과를 r.json 파일에 저장합니다.
> python3 -d RecycleBinParser.py C:\$Recycle.Bin\S-1-5-42-2867809058-3762516759-3994543984-1102                      (debug mode로) 결과를 화면에 보여줍니다.
